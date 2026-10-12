"""
Tests des utilitaires de l'app edi (saisie manuelle, traces, contrôles orphelins)
"""

import pytest

from apps.core.models import ChangesTrace
from apps.data_flux.models import Trace
from apps.edi.bin import edi_utilites
from apps.edi.models import EdiImportControl


@pytest.mark.parametrize(
    ("sens", "expected"),
    [
        ("2", {"purchase_invoice": "true", "sale_invoice": "true"}),
        ("1", {"purchase_invoice": "false", "sale_invoice": "true"}),
        ("0", {"purchase_invoice": "true", "sale_invoice": "false"}),
        ("", {"purchase_invoice": "true", "sale_invoice": "false"}),
    ],
)
def test_get_sens(sens, expected):
    assert edi_utilites.get_sens(sens) == expected


def test_set_trace_hand_invoice_error(make_user):
    user = make_user()

    edi_utilites.set_trace_hand_invoice("marchandises", "FA1", user, errors=True)

    trace = Trace.objects.get()
    assert trace.trace_name == "Saisie Facture de Marchandises"
    assert trace.file_name == "Ecran de saisie : edi/create_hand_invoices/marchandises/"
    assert trace.errors is True
    assert trace.comment == "Saisie de la facture N° FA1"
    assert trace.created_by == user
    assert trace.invoices is True
    assert ChangesTrace.objects.count() == 0


def test_set_trace_hand_invoice_success_creates_changes_traces(make_user, make_edi_import):
    user = make_user()
    lines = [make_edi_import(invoice_number="FA2"), make_edi_import(invoice_number="FA2")]

    edi_utilites.set_trace_hand_invoice("personnel", "FA2", user, edi_objects=lines, numbers=2)

    trace = Trace.objects.get()
    assert trace.errors is False
    assert trace.created_numbers_records == 2
    changes = list(ChangesTrace.objects.order_by("pk"))
    assert len(changes) == 2
    assert changes[0].action_type == 1
    assert changes[0].action_by == user
    assert changes[0].before == {}
    assert changes[0].after["invoice_number"] == "FA2"
    assert "_state" not in changes[0].after
    assert changes[0].difference["après"]["invoice_number"] == "FA2"
    assert changes[0].model_name == "ediimport"
    assert changes[0].db_table == "edi_ediimport"
    assert "f_back" not in changes[0].function_name
    assert len(changes[0].function_name) <= 255


def _data_dict(category_lines):
    return {"entete": {"third_party_num": "FOUR001"}, "lignes": category_lines}


def test_data_dict_invoices_clean_marchandises_filters_and_sorts():
    data = _data_dict(
        [
            {"num": 2, "reference_article": "B"},
            {"num": 3, "reference_article": ""},
            {"num": 1, "reference_article": "A"},
        ]
    )

    edi_utilites.data_dict_invoices_clean("marchandises", data)

    assert [line["reference_article"] for line in data["lignes"]] == ["A", "B"]
    assert data["entete"] == {"third_party_num": "FOUR001"}


def test_data_dict_invoices_clean_formation():
    data = _data_dict([{"num": 1, "reference_article": "A", "initial_date": "2026-03-17", "qty": "5"}])

    edi_utilites.data_dict_invoices_clean("formation", data)

    assert data["entete"]["third_party_num"] == "ZFORM"
    assert data["entete"]["sens"] == "1"
    line = data["lignes"][0]
    assert line["qty"] == "1"
    assert line["unit_weight"] == "9"
    assert line["formation_month"] == "2026-03-01"


def test_data_dict_invoices_clean_personnel():
    data = _data_dict([{"num": 1, "reference_article": "A"}])

    edi_utilites.data_dict_invoices_clean("personnel", data)

    assert data["entete"]["sens"] == "1"
    assert data["lignes"][0]["unit_weight"] == "7"


def test_get_query_articles_marchandises():
    assert edi_utilites.get_query_articles("marchandises") == ""


def test_get_query_articles_by_category(make_article, make_big_category, make_society):
    society = make_society("ZFORM", is_client=False)
    formation = make_big_category("Formation")
    article = make_article(reference="FORM-1", society=society, big_category=formation, libelle="Formation vente")
    heron = make_article(
        reference="FORM-2", society=society, big_category=formation, libelle="x", libelle_heron="Libellé héron"
    )
    make_article(reference="PERS-1", society=society, big_category=make_big_category("Personnel"))

    results = edi_utilites.get_query_articles(formation.slug_name)

    assert results[0] == {"pk": "", "model": "---"}
    assert {"pk": article.pk, "model": "ZFORM - FORM-1 - Formation vente"} in results
    assert {"pk": heron.pk, "model": "ZFORM - FORM-2 - Libellé héron"} in results
    assert len(results) == 3


def test_delete_orphans_controls(make_edi_import_control, make_edi_import):
    orphan = make_edi_import_control()
    linked = make_edi_import_control()
    make_edi_import(uuid_control=linked)

    edi_utilites.delete_orphans_controls()

    assert EdiImportControl.objects.filter(pk=linked.pk).exists()
    assert not EdiImportControl.objects.filter(pk=orphan.pk).exists()


def test_set_signboard(make_edi_import, make_maison):
    maison = make_maison()
    line = make_edi_import(cct_uuid_identification=maison, code_center=None)

    edi_utilites.set_signboard([line])

    line.refresh_from_db()
    assert line.code_center == maison.center_purchase.code
    assert line.code_signboard == maison.sign_board.code


def test_get_personal_profession_type(make_nature):
    opticien = make_nature("Opticien", for_personnel=True, for_contact=False, to_display="OPT")
    make_nature("Gérant")

    results = edi_utilites.get_personal_profession_type()

    assert results == [
        {"uuid_identification": "", "to_display": "---"},
        {"uuid_identification": opticien.uuid_identification, "to_display": "OPT"},
    ]
