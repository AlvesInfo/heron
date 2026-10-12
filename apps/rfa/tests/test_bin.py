# pylint: disable=E0401,W0621
"""
FR : Tests des contrôles, de l'insertion, du post-traitement et de la génération des RFA
EN : Tests for RFA controls, insertion, post processing and generation

created at: 2026-10-12
created by: Paulo ALVES
"""
import datetime
import logging
from typing import ClassVar
from decimal import Decimal
from uuid import uuid4

import pytest

from apps.edi.models import EdiImport
from apps.rfa import tasks as rfa_tasks
from apps.rfa.bin.rfa_controls import (
    get_axe_rfa_period,
    have_rfa_to_be_invoiced,
    supplier_control_cct,
    supplier_control_validation,
)
from apps.rfa.bin.rfa_insertions import RfaPeriodError, get_open_period, get_sql_kwargs, insert_rfa
from apps.rfa.bin.rfa_post_insert import rfa_post_update
from apps.rfa.imports import import_rfa_pool
from apps.rfa.imports.import_rfa_pool import generate_rfa
from apps.rfa.loops import rfa_loop_pool
from apps.rfa.loops.rfa_loop_pool import rfa_generation_launch
from apps.rfa.tasks import launch_rfa_generation
from apps.rfa.tests.conftest import RFA_PERIOD

pytestmark = pytest.mark.django_db


# CONTRÔLES ========================================================================================


def test_controle_validation_fournisseurs(rfa_data, make_edi_import, make_supplier_rate, make_edi_import_control):
    """Message vide, au singulier ou au pluriel selon les fournisseurs à RFA non validés"""
    assert supplier_control_validation() == ""

    rfa_data["control"].valid = False
    rfa_data["control"].save()
    assert supplier_control_validation() == "Les Factures du Fournisseur FOUR001 - FOURN UN, ne sont pas validées"

    make_supplier_rate("FOUR002", "0.1", name="Fournisseur Deux")
    make_edi_import("FOUR002", "ART-9", uuid_control=None)
    message = supplier_control_validation()
    assert message.startswith("Les Factures des Fournisseurs ")
    assert "FOUR002 - Fournisseur Deux" in message
    assert message.endswith(", ne sont pas validées")

    make_edi_import("FOUR003", "ART-8", uuid_control=make_edi_import_control(valid=False))
    assert "FOUR003" not in supplier_control_validation()


def test_controle_cct(rfa_data, make_edi_import, make_supplier_rate):
    assert supplier_control_cct() == ""

    make_edi_import("FOUR001", "ART-3", cct_uuid_identification=None)
    assert supplier_control_cct() == "Des CCT n'ont pas été renseignés dans les Factures du Fournisseur FOUR001 - FOURN UN"

    make_supplier_rate("FOUR002", "0.1", name="Fournisseur Deux")
    make_edi_import("FOUR002", "ART-9")
    message = supplier_control_cct()
    assert message.startswith("Des CCT n'ont pas été renseignés dans les Factures des Fournisseurs ")
    assert "FOUR002 - Fournisseur Deux" in message


def test_rfa_a_generer(rfa_data):
    """Le fournisseur est proposé tant que ses factures passent les filtres de l'insertion"""
    assert have_rfa_to_be_invoiced() == ["FOUR001"]

    EdiImport.objects.filter(third_party_num="FOUR001").update(flow_name="rfa_flow")
    assert have_rfa_to_be_invoiced() == []


@pytest.mark.parametrize(
    "exclusion",
    ["signboard", "client", "client_supplier", "section_pro", "section_rfa", "rate"],
)
def test_rfa_a_generer_exclusions(
    rfa_data, exclusion, make_signboard_exclusion, make_client_exclusion, make_client_supplier_exclusion,
    make_section_pro_exclusion,
):
    """Chaque exclusion (ou l'absence de section RFA / de taux) retire le fournisseur"""
    if exclusion == "signboard":
        make_signboard_exclusion("ACF")
    elif exclusion == "client":
        make_client_exclusion(rfa_data["maison"])
    elif exclusion == "client_supplier":
        make_client_supplier_exclusion(rfa_data["maison"], "FOUR001")
    elif exclusion == "section_pro":
        make_section_pro_exclusion("OPT")
    elif exclusion == "section_rfa":
        # FlagsTable.delete est un champ booléen : suppression via le QuerySet
        type(rfa_data["section_rfa"]).objects.filter(pk=rfa_data["section_rfa"].pk).delete()
    else:
        type(rfa_data["rate"]).objects.filter(pk=rfa_data["rate"].pk).delete()

    assert have_rfa_to_be_invoiced() == []


def test_periode_axe_rfa(make_edi_validation):
    assert get_axe_rfa_period() == f"{datetime.date.today().year}RFA"

    make_edi_validation(datetime.date(2026, 3, 1), final=True)
    assert get_axe_rfa_period() == f"{datetime.date.today().year}RFA"

    make_edi_validation(datetime.date(2026, 4, 1), final=None)
    assert get_axe_rfa_period() == "2026RFA_04"


# INSERTION ========================================================================================


def test_arguments_sql(rfa_data):
    uuid = uuid4()

    kwargs = get_sql_kwargs("FOUR001", RFA_PERIOD, uuid)

    assert kwargs["uuid_identification"] == uuid
    assert kwargs["third_party_num"] == "FOUR001"
    assert kwargs["supplier"] == kwargs["siret_payeur"] == "FOURN UN RFA"
    assert kwargs["supplier_ident"] == "F1"
    assert kwargs["supplier_name"] == "FOURN UN"
    assert kwargs["invoice_number"] == "FOUR001_01_2026_"
    assert kwargs["invoice_date"] == "2026-01-31"
    assert kwargs["reference_article"] == RFA_PERIOD
    assert kwargs["libelle"] == "RFA FOURN UN 01/2026"
    assert kwargs["flow_name"] == "rfa_flow"


def test_arguments_sql_identifiant_vide(rfa_data):
    """Sans identifiant fournisseur de centrale, supplier_ident est vide (et non « None »)"""
    from apps.book.models import Society  # pylint: disable=C0415

    Society.objects.filter(third_party_num="FOUR001").update(centers_suppliers_indentifier=None)

    assert get_sql_kwargs("FOUR001", RFA_PERIOD, uuid4())["supplier_ident"] == ""


def test_arguments_sql_sans_periode_ouverte(rfa_data):
    """Sans période de facturation ouverte, l'erreur est explicite"""
    rfa_data["validation"].final = True
    rfa_data["validation"].save()

    assert get_open_period() is None

    with pytest.raises(RfaPeriodError, match="Aucune période de facturation ouverte"):
        get_sql_kwargs("FOUR001", RFA_PERIOD, uuid4())


def test_insertion_et_post_traitement(rfa_data):
    """Une ligne de RFA (avoir) est insérée par maison : 5 % de 150 = 7,50 HT, TVA 5,5 %"""
    uuid = uuid4()

    inserted = insert_rfa("FOUR001", RFA_PERIOD, uuid)

    rfa = EdiImport.objects.get(uuid_identification=uuid)
    assert inserted == 1
    assert (rfa.third_party_num, rfa.flow_name, rfa.origin.origin) == ("FOUR001", "rfa_flow", 12)
    assert rfa.origin.origin_name == "RFA MENSUELLE"
    assert (rfa.code_maison, rfa.maison) == ("AF0001", "Maison AF0001")
    assert rfa.invoice_number == "FOUR001_01_2026_381"
    assert (rfa.invoice_type, rfa.qty) == ("381", Decimal("-1"))
    assert rfa.invoice_date == datetime.date(2026, 1, 31)
    assert (rfa.gross_amount, rfa.net_amount) == (Decimal("-165"), Decimal("-7.5"))
    assert (rfa.vat_rate, rfa.vat_amount, rfa.amount_with_vat) == (Decimal("5.5"), Decimal("-0.41"), Decimal("-7.91"))
    assert rfa.sale_invoice is True
    assert rfa.purchase_invoice is False

    rfa_post_update(uuid)

    rfa.refresh_from_db()
    assert rfa.vat_rate == Decimal("0.055")
    assert (rfa.invoice_amount_without_tax, rfa.invoice_amount_tax, rfa.invoice_amount_with_tax) == (
        Decimal("-7.5"), Decimal("-0.41"), Decimal("-7.91"),
    )

    # Les RFA déjà générées ne sont ni reproposées ni recomptées
    assert have_rfa_to_be_invoiced() == []
    assert insert_rfa("FOUR001", RFA_PERIOD, uuid4()) == 1


def test_insertion_facture_positive(rfa_data):
    """Des montants négatifs chez le fournisseur donnent une facture (380) de RFA"""
    EdiImport.objects.filter(third_party_num="FOUR001").update(net_amount=Decimal("-100"), gross_amount=Decimal("-100"))

    insert_rfa("FOUR001", RFA_PERIOD, uuid4())

    rfa = EdiImport.objects.get(flow_name="rfa_flow")
    assert (rfa.invoice_type, rfa.qty, rfa.net_amount) == ("380", Decimal("1"), Decimal("10"))


def test_generate_rfa(rfa_data, make_trace):
    trace = make_trace(flow_name="rfa_flow")

    result = generate_rfa("FOUR001", RFA_PERIOD, trace)

    trace.refresh_from_db()
    assert result == "Import : rfa_flow\n"
    assert trace.created_numbers_records == 1
    assert EdiImport.objects.filter(uuid_identification=trace.uuid_identification).count() == 1


# TÂCHE CELERY =====================================================================================


def test_tache_generation_succes(rfa_data, make_user, monkeypatch):
    user = make_user()
    calls = []

    def _fake_generate(supplier, period, trace):
        calls.append((supplier, period))
        trace.created_numbers_records = 3
        return "Import : rfa_flow\n"

    monkeypatch.setattr(rfa_tasks, "generate_rfa", _fake_generate)

    result = launch_rfa_generation(user.pk, "FOUR001", RFA_PERIOD)

    from apps.data_flux.models import Trace  # pylint: disable=C0415

    trace = Trace.objects.get(file_name="Generate RFA : FOUR001")
    assert calls == [("FOUR001", RFA_PERIOD)]
    assert "RFA intégrées avec sucess" in result["Génération des RFA"]
    assert (trace.errors, trace.invoices, trace.created_by) == (False, True, user)
    assert trace.time_to_process is not None
    assert trace.final_at is not None


def test_tache_generation_sans_periode_ouverte(rfa_data, make_user):
    """La cause (pas de période ouverte) est écrite dans la trace et renvoyée à l'écran"""
    rfa_data["validation"].final = True
    rfa_data["validation"].save()

    result = launch_rfa_generation(make_user().pk, "FOUR001", RFA_PERIOD)

    from apps.data_flux.models import Trace  # pylint: disable=C0415

    trace = Trace.objects.get(file_name="Generate RFA : FOUR001")
    assert trace.errors is True
    assert trace.comment.startswith("Aucune période de facturation ouverte")
    assert "Aucune période de facturation ouverte" in result["Génération des RFA"]
    assert result["Génération des RFA"].startswith("Erreur")


@pytest.mark.parametrize(
    ("error", "expected"),
    [(TypeError("type cassé"), "TypeError : type cassé"), (RuntimeError("boom"), "")],
)
def test_tache_generation_erreurs(rfa_data, make_user, monkeypatch, caplog, error, expected):
    """TypeError est détaillée dans le retour, les autres erreurs seulement journalisées"""
    caplog.set_level(logging.ERROR, logger="edi")

    def _raise(*_args, **_kwargs):
        raise error

    monkeypatch.setattr(rfa_tasks, "generate_rfa", _raise)

    result = launch_rfa_generation(make_user().pk, "FOUR001", RFA_PERIOD)

    from apps.data_flux.models import Trace  # pylint: disable=C0415

    trace = Trace.objects.get(file_name="Generate RFA : FOUR001")
    assert result["Génération des RFA"].startswith("Erreur - ")
    assert expected in result["Génération des RFA"]
    assert "Une erreur c'est produite" in result["Génération des RFA"]
    assert trace.errors is True
    assert "Une erreur c'est produite" in trace.comment
    assert any(str(error) in record.getMessage() for record in caplog.records)


def test_import_rfa_pool_module():
    assert import_rfa_pool.generate_rfa is generate_rfa


# BOUCLE DE LANCEMENT ==============================================================================


class _FakeGroup:
    """Simule un groupe celery dont .get renvoie le résultat préparé"""

    results: ClassVar[list] = []

    def __init__(self, *signatures):
        self.signatures = signatures

    def __call__(self):
        return self

    def get(self, _timeout):
        return self.results.pop(0)


@pytest.fixture
def fake_celery(monkeypatch):
    """Remplace group et signature de la boucle : enregistre les signatures et sert les résultats"""
    signatures = []
    monkeypatch.setattr(rfa_loop_pool, "group", _FakeGroup)
    monkeypatch.setattr(rfa_loop_pool.celery_app, "signature", lambda name, kwargs: signatures.append((name, kwargs)) or (name, kwargs))

    def _prepare(*results):
        _FakeGroup.results = list(results)
        return signatures

    return _prepare


def test_lancement_generation(fake_celery, make_user):
    """Une tâche par fournisseur puis le nettoyage SQL ; l'action en cours est relâchée"""
    from apps.parameters.models import ActionInProgress  # pylint: disable=C0415

    signatures = fake_celery([{"Génération des RFA": "RFA intégrées avec sucess, en 2 s"}], ["clean"])
    user = make_user()

    erreur, info = rfa_generation_launch(user.pk, ["FOUR001", "FOUR002"], RFA_PERIOD)

    assert (erreur, info) == (False, "RFA intégrées avec sucess, en 2 s")
    assert [name for name, _ in signatures] == ["rfa_generation_launch_task", "rfa_generation_launch_task", "sql_clean_general"]
    assert signatures[0][1] == {"user_pk": user.pk, "supplier_origin": "FOUR001", "period_rfa": RFA_PERIOD}
    assert ActionInProgress.objects.get(action="rfa_generation").in_progress is False


def test_lancement_generation_erreur_et_chaine(fake_celery, make_user):
    user = make_user()
    fake_celery([{"Génération des RFA": r"Erreur - type cassé\n"}], ["clean"])
    erreur, info = rfa_generation_launch(user.pk, ["FOUR001"], RFA_PERIOD)
    assert (erreur, info) == (True, "Erreur - type cassé")

    fake_celery(r"texte brut\n", ["clean"])
    assert rfa_generation_launch(user.pk, ["FOUR001"], RFA_PERIOD) == (False, "texte brut")


def test_lancement_generation_exception(monkeypatch, make_user, caplog):
    """Une exception du groupe celery est journalisée et renvoie un message vide"""
    caplog.set_level(logging.ERROR, logger="imports")

    def _raise(*_args, **_kwargs):
        raise RuntimeError("broker injoignable")

    monkeypatch.setattr(rfa_loop_pool, "group", _raise)

    assert rfa_generation_launch(make_user().pk, ["FOUR001"], RFA_PERIOD) == (False, "")
    assert any("broker injoignable" in record.getMessage() for record in caplog.records)


def test_lancement_generation_sans_action(monkeypatch, make_user):
    """Si l'action ne peut être lue, rien n'est lancé et le finally ne plante pas"""

    def _raise(**_kwargs):
        raise RuntimeError("base indisponible")

    monkeypatch.setattr(rfa_loop_pool, "get_action", _raise)

    assert rfa_generation_launch(make_user().pk, ["FOUR001"], RFA_PERIOD) == (False, "")


def test_lancement_attend_la_fin_de_l_action_en_cours(fake_celery, make_user, monkeypatch):
    """Une action déjà en cours est relue jusqu'à sa libération"""
    from apps.parameters.bin.core import get_action  # pylint: disable=C0415

    fake_celery([{"Génération des RFA": "ok"}], ["clean"])
    busy = get_action(action="rfa_generation")
    busy.in_progress = True
    busy.save()
    states = iter([True, False])

    def _get_action(action):
        current = get_action(action=action)
        current.in_progress = next(states)
        return current

    monkeypatch.setattr(rfa_loop_pool, "get_action", _get_action)

    assert rfa_generation_launch(make_user().pk, ["FOUR001"], RFA_PERIOD) == (False, "ok")
