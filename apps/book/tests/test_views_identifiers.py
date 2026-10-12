# pylint: disable=E0401,W0621
"""FR : Tests des vues des identifiants cct par fournisseur (apps/book/views/identifiers_views.py)


EN : Tests for supplier cct identifiers views

created at: 2026-10-11
created by: Paulo ALVES
"""

import logging

import pytest
from django.contrib.messages import get_messages
from django.urls import reverse

from apps.book.models import SupplierCct
from apps.book.views import identifiers_views
from apps.core.bin.encoders import set_base_64_str
from apps.core.models import ChangesTrace
from apps.edi.models import EdiImport
from conftest import patched_attrs

pytestmark = pytest.mark.django_db

BACK_URL = "/book/societies_list/"


def _messages(response):
    return [(message.level, message.message) for message in get_messages(response.wsgi_request)]


def _identifiers(third_party_num):
    return dict(
        SupplierCct.objects.filter(third_party_num=third_party_num).values_list(
            "cct_uuid_identification__cct", "cct_identifier"
        )
    )


@pytest.fixture
def supplier(make_society, make_cct, make_maison, make_supplier_cct):
    """Un fournisseur avec deux cct identifiés (maisons ouvertes), un autre fournisseur sur le même cct"""
    society = make_society("FOUR001", name="Fournisseur", is_client=False)
    paris = make_supplier_cct(society, make_cct("AF0001", name="Paris"), "PAR|")
    lyon = make_supplier_cct(society, make_cct("AF0002", name="Lyon"), "LYO|")
    make_maison("AF0001")
    make_maison("AF0002")
    make_supplier_cct(make_society("FOUR002", is_client=False), make_cct("AF0001"), "X|")
    return {"society": society, "paris": paris, "lyon": lyon}


def _url(third_party_num="FOUR001"):
    return reverse(
        "book:supplier_cct_identifier", args=[third_party_num, set_base_64_str(BACK_URL)]
    )


def _formset_data(*rows):
    """Données du formset : (instance, identifiant saisi)"""
    data = {
        "form-TOTAL_FORMS": len(rows),
        "form-INITIAL_FORMS": len(rows),
        "form-MIN_NUM_FORMS": 0,
        "form-MAX_NUM_FORMS": len(rows),
    }

    for index, (instance, identifier) in enumerate(rows):
        data[f"form-{index}-id"] = instance.pk
        data[f"form-{index}-cct_identifier"] = identifier

    return data


# ÉCRAN DES IDENTIFIANTS ===========================================================================


def test_identifiants_get(logged_client, supplier):
    """Les cct du fournisseur sont listés dans l'ordre des codes, avec le chevron de retour décodé"""
    response = logged_client.get(_url())

    assert response.status_code == 200
    assert response.context["titre_table"] == "Identifiants des CCT pour le tiers FOUR001"
    assert response.context["count"] == 2
    assert response.context["chevron_retour"] == BACK_URL
    assert response.context["third_party_num"] == "FOUR001"
    assert [row["cct_uuid_identification__cct"] for row in response.context["queryset"]] == [
        "AF0001",
        "AF0002",
    ]
    assert logged_client.session["level"] == 20


@pytest.mark.usefixtures("automate")
def test_identifiants_get_cree_les_cct_manquants(logged_client, make_society, make_maison):
    """Les maisons ouvertes sans identifiant pour ce tiers sont ajoutées avec leur cct par défaut"""
    make_society("NEWS001", is_client=False)
    make_maison("AF0001")
    make_maison("AF0002")

    response = logged_client.get(_url("NEWS001"))

    assert response.status_code == 200
    assert response.context["count"] == 2
    assert _identifiers("NEWS001") == {"AF0001": "AF0001|", "AF0002": "AF0002|"}


def test_identifiants_get_en_erreur(logged_client, supplier, monkeypatch, caplog):
    """Une erreur inattendue est journalisée, l'écran s'affiche vide avec le message"""

    def _boom(**_kwargs):
        raise RuntimeError("sql cassé")

    with (
        patched_attrs(monkeypatch, identifiers_views, add_news_cct_sage=_boom),
        caplog.at_level(logging.ERROR, logger="views"),
    ):
        response = logged_client.get(_url())

    assert response.status_code == 200
    assert response.context["count"] == 0
    assert response.context["chevron_retour"] == reverse("book:societies_list")
    assert _messages(response) == [(50, "Une erreur c'est produite, veuillez consulter les logs")]
    assert logged_client.session["level"] == 50
    assert "sql cassé" in caplog.text


def test_identifiants_post_sans_modification(logged_client, supplier):
    data = _formset_data((supplier["paris"], "PAR|"), (supplier["lyon"], "LYO|"))

    response = logged_client.post(_url(), data)

    assert response.status_code == 200
    assert _messages(response) == [(50, "Vous n'avez rien modifié !")]
    assert logged_client.session["level"] == 50
    assert ChangesTrace.objects.count() == 0


def test_identifiants_post_modification_tracee(logged_client, supplier, make_edi_import):
    """L'identifiant ajouté est enregistré, tracé, et rattache les imports edi sans cct"""
    edi = make_edi_import(
        "FOUR001", "ART-1", code_maison="P2", cct_uuid_identification=None, valid=True
    )
    data = _formset_data((supplier["paris"], "PAR|P2|"), (supplier["lyon"], "LYO|"))

    response = logged_client.post(_url(), data)

    assert response.status_code == 200
    assert _messages(response) == [(20, "Les identifiants du cct AF0001, on bien été changés.")]
    assert logged_client.session["level"] == 20
    assert _identifiers("FOUR001") == {"AF0001": "PAR|P2|", "AF0002": "LYO|"}
    trace = ChangesTrace.objects.get()
    assert trace.model_name == "suppliercct"
    assert trace.difference["avant"]["cct_identifier"] == "PAR|"
    assert trace.difference["après"]["cct_identifier"] == "PAR|P2|"
    assert SupplierCct.objects.get(pk=supplier["paris"].pk).modified_by == logged_client.user
    assert (
        EdiImport.objects.get(pk=edi.pk).cct_uuid_identification.cct
        == supplier["paris"].cct_uuid_identification
    )


def test_identifiants_post_identifiant_deja_present_ou_pris(logged_client, supplier):
    """Même liste sans le "|" final : rien à changer ; identifiant d'un autre cct du tiers : refusé"""
    data = _formset_data((supplier["paris"], "PAR"), (supplier["lyon"], "LYO|PAR|"))

    response = logged_client.post(_url(), data)

    assert response.status_code == 200
    assert _messages(response) == [
        (50, "Vous n'avez rien modifié !"),
        (50, "L'identifiant PAR est déjà utilisé dans le cct AF0001"),
    ]
    assert _identifiers("FOUR001") == {"AF0001": "PAR|", "AF0002": "LYO|"}


def test_identifiants_post_formset_invalide(logged_client, supplier, caplog):
    data = _formset_data((supplier["paris"], "x" * 151))

    with caplog.at_level(logging.ERROR, logger="views"):
        response = logged_client.post(_url(), data)

    assert response.status_code == 200
    assert _messages(response) == [(50, "Une erreur c'est produite, veuillez consulter les logs")]
    assert "erreur form" in caplog.text
    assert _identifiers("FOUR001")["AF0001"] == "PAR|"


# CHANGEMENT UNITAIRE (AJAX) =======================================================================


def test_changement_unitaire_hors_ajax(client, logged_client, supplier):
    """Sans ajax ou sans POST : retour à l'accueil"""
    assert logged_client.post(
        reverse("book:change_supplier_cct_unit"), {"pk": supplier["paris"].pk}
    ).url == reverse("home")
    assert client.get(reverse("book:change_supplier_cct_unit")).status_code in {302, 403}


def test_changement_unitaire_ajoute_le_pipe_final(ajax_client, supplier, make_edi_import):
    edi = make_edi_import(
        "FOUR001", "ART-1", code_maison="P2", cct_uuid_identification=None, valid=True
    )

    response = ajax_client.post(
        reverse("book:change_supplier_cct_unit"),
        {"pk": supplier["paris"].pk, "cct_identifier": "PAR|P2"},
    )

    assert response.status_code == 200
    assert response.json() == {"success": "success"}
    assert _identifiers("FOUR001")["AF0001"] == "PAR|P2|"
    assert _messages(response) == [(20, "Les identifiants du cct AF0001, on bien été changés.")]
    assert ajax_client.session["level"] == 20
    assert ChangesTrace.objects.get().difference["après"]["cct_identifier"] == "PAR|P2|"
    assert (
        EdiImport.objects.get(pk=edi.pk).cct_uuid_identification.cct
        == supplier["paris"].cct_uuid_identification
    )


def test_changement_unitaire_efface_l_identifiant(ajax_client, supplier):
    response = ajax_client.post(
        reverse("book:change_supplier_cct_unit"), {"pk": supplier["lyon"].pk, "cct_identifier": ""}
    )

    assert response.json() == {"success": "success"}
    assert _identifiers("FOUR001")["AF0002"] is None


@pytest.mark.parametrize(
    ("identifier", "expected"),
    [
        ("PAR", "Vous n'avez rien modifié !"),
        ("LYO|", "L'identifiant LYO est déjà utilisé dans le cct AF0002"),
    ],
)
def test_changement_unitaire_refuse(ajax_client, supplier, identifier, expected):
    response = ajax_client.post(
        reverse("book:change_supplier_cct_unit"),
        {"pk": supplier["paris"].pk, "cct_identifier": identifier},
    )

    assert response.json() == {"success": "success"}
    assert _messages(response) == [(50, expected)]
    assert ajax_client.session["level"] == 50
    assert _identifiers("FOUR001")["AF0001"] == "PAR|"


def test_changement_unitaire_trace_sans_changement(ajax_client, supplier, monkeypatch):
    """Si la trace ne constate aucun changement, son message est renvoyé"""
    with patched_attrs(
        monkeypatch,
        identifiers_views,
        trace_change=lambda *_a, **_k: (False, "Vous n'avez rien modifié !"),
    ):
        response = ajax_client.post(
            reverse("book:change_supplier_cct_unit"),
            {"pk": supplier["paris"].pk, "cct_identifier": "NOUVEAU|"},
        )

    assert _messages(response) == [(50, "Vous n'avez rien modifié !")]
    assert ChangesTrace.objects.count() == 0


def test_changement_unitaire_formulaire_invalide(ajax_client, supplier, caplog):
    with caplog.at_level(logging.ERROR, logger="views"):
        response = ajax_client.post(
            reverse("book:change_supplier_cct_unit"),
            {"pk": supplier["paris"].pk, "cct_identifier": "x" * 151},
        )

    assert response.json() == {"success": "success"}
    assert _messages(response)[0][0] == 50
    assert "cct_change, form invalid" in caplog.text


def test_changement_unitaire_identifiant_inconnu(ajax_client, supplier):
    assert (
        ajax_client.post(
            reverse("book:change_supplier_cct_unit"), {"pk": 999999, "cct_identifier": "A|"}
        ).status_code
        == 404
    )


# EXPORT EXCEL =====================================================================================


def test_export_des_identifiants(logged_client, supplier):
    response = logged_client.get(reverse("book:export_list_supplier_cct", args=["FOUR001"]))

    assert response.status_code == 200
    assert response["Content-Disposition"].startswith(
        "attachment; filename=Identifiants_cct_FOUR001_"
    )
    assert response.content[:2] == b"PK"


def test_export_des_identifiants_hors_get(logged_client, supplier):
    """Hors GET, retour à la fiche du tiers dans la liste complète"""
    response = logged_client.post(reverse("book:export_list_supplier_cct", args=["FOUR001"]))

    assert response.status_code == 302
    assert response.url == reverse("book:society_update", args=[supplier["society"].pk, "alls"])


def test_export_des_identifiants_en_erreur(logged_client, supplier, monkeypatch, caplog):
    def _boom(*_args, **_kwargs):
        raise RuntimeError("excel cassé")

    with (
        patched_attrs(monkeypatch, identifiers_views, excel_liste_supplier_cct=_boom),
        caplog.at_level(logging.ERROR, logger="views"),
    ):
        response = logged_client.get(reverse("book:export_list_supplier_cct", args=["FOUR001"]))

    assert response.status_code == 302
    assert response.url == reverse("book:society_update", args=[supplier["society"].pk, "alls"])
    assert logged_client.session["level"] == 50
    assert "export du listing Excel des indentifiants CCT" in _messages(response)[0][1]
    assert "export_list_supplier_cct" in caplog.text


def test_export_des_identifiants_tiers_inconnu(logged_client):
    assert (
        logged_client.post(reverse("book:export_list_supplier_cct", args=["ABSENT"])).status_code
        == 404
    )
