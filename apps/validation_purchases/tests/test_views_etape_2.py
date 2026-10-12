"""Tests des vues des étapes 2.1 (intégrations), 2.1.A, 2.1.B, 2.2 et des intégrations sans tiers"""

import logging
import uuid

import pytest
from django.urls import reverse

from apps.core.models import ChangesTrace
from apps.edi.models import EdiImport, EdiImportControl, EdiValidation
from apps.validation_purchases.tests.helpers_views import encode, messages_of
from apps.validation_purchases.views import (
    views_etape_2_1,
    views_etape_2_1_A,
    views_etape_2_1_B,
    views_etape_2_2,
    views_without_third_party_num,
)
from conftest import patched_attrs

pytestmark = pytest.mark.django_db
HOME = reverse("home")


def url(name, **kwargs):
    return reverse(f"validation_purchases:{name}", kwargs=kwargs or None)


# 2.1 - INTEGRATIONS ===============================================================================
def test_integration_purchases_sans_tiers_redirige(logged_client, make_edi_import):
    make_edi_import(third_party_num="")

    response = logged_client.get(url("integration_purchases"))

    assert response.status_code == 302
    assert response.url == url("purchase_without_suppliers")


def test_integration_purchases_sans_lignes_redirige_vers_import(logged_client):
    response = logged_client.get(url("integration_purchases"))

    assert response.status_code == 302
    assert response.url == reverse("edi:import_edi_invoices")
    # la validation de la période en cours a été créée au passage
    assert EdiValidation.objects.filter(final=False).exists()


def test_integration_purchases(logged_client, integration_data):
    response = logged_client.get(url("integration_purchases"))

    assert response.status_code == 200
    elements = response.context["integration_purchases"]
    assert len(elements) == 1
    assert elements[0]["third_party_num"] == "FOUR001"
    assert elements[0]["invoice_amount_without_tax"] == 30
    assert elements[0]["qty_invoices"] == 2
    assert elements[0]["have_control"] == 1
    assert response.context["uuid_validation"] == integration_data.validation.uuid_identification
    assert "janvier 2026" in response.context["titre_table"]
    assert "en_cours" not in response.context


@pytest.mark.usefixtures("integration_data")
def test_integration_purchases_en_cours(logged_client, monkeypatch):
    with patched_attrs(monkeypatch, views_etape_2_1, get_in_progress=lambda: True):
        response = logged_client.get(url("integration_purchases"))

    assert response.context["en_cours"] is True
    assert "EN COURS" in response.context["titre_table"]


def test_create_integration_control(logged_client, integration_data):
    response = logged_client.get(url("create_control", enc_param=integration_data.enc_param))

    assert response.status_code == 200
    assert response.context["third_party_num"] == "FOUR001"
    assert response.context["invoice_month"] == "janvier 2026"
    assert response.context["flow_name"] == "Widex"

    response = logged_client.post(
        url("create_control", enc_param=integration_data.enc_param),
        {"statement_without_tax": "30", "statement_with_tax": "36", "comment": "relevé"},
    )

    assert response.status_code == 302
    assert response.url == url("integration_purchases")
    control = EdiImportControl.objects.get(comment="relevé")
    assert control.modified_by == logged_client.user
    assert set(EdiImport.objects.values_list("uuid_control", flat=True)) == {
        control.uuid_identification
    }
    assert logged_client.session["level"] == 20


def test_update_integration_control(logged_client, integration_data):
    control = integration_data.control
    kwargs = {"enc_param": integration_data.enc_param, "pk": control.pk}

    response = logged_client.get(url("update_control", **kwargs))

    assert response.status_code == 200
    assert response.context["supplier"] == "WIDEX"

    response = logged_client.post(
        url("update_control", **kwargs),
        {"statement_without_tax": "31", "statement_with_tax": "37", "comment": "corrigé"},
    )

    assert response.status_code == 302
    control.refresh_from_db()
    assert control.statement_without_tax == 31
    assert control.modified_by == logged_client.user
    assert ChangesTrace.objects.filter(model_name="ediimportcontrol").exists()


@pytest.mark.parametrize(
    "name",
    [
        "integration_supplier_validation",
        "delete_supplier_edi_import",
        "integration_validation",
        "delete_invoice_purchase",
        "delete_line_details_purchase",
        "purchase_without_suppliers_update",
        "cct_change",
        "big_category_change",
    ],
)
def test_vues_ajax_refusent_get_et_non_ajax(logged_client, ajax_client, name):
    """GET ajax ou POST non ajax : redirection vers l'accueil"""
    assert ajax_client.get(url(name)).url == HOME
    assert logged_client.post(url(name), {}).url == HOME


def test_integration_supplier_validation(ajax_client, integration_data):
    control = integration_data.control
    response = ajax_client.post(
        url("integration_supplier_validation"),
        {"uuid_identification": str(control.uuid_identification), "valid": "on"},
    )

    assert response.json() == {
        "success": "ok",
        "inputCheck": False,
        "message": "Le Fournisseur à bien été validé",
    }
    control.refresh_from_db()
    assert control.valid is True

    response = ajax_client.post(
        url("integration_supplier_validation"),
        {"uuid_identification": str(control.uuid_identification)},
    )
    control.refresh_from_db()
    assert response.json()["success"] == "ok"
    assert control.valid is False


def test_integration_supplier_validation_erreurs(ajax_client, caplog):
    with caplog.at_level(logging.ERROR, logger="error_views"):
        unknown = ajax_client.post(
            url("integration_supplier_validation"),
            {"uuid_identification": str(uuid.uuid4()), "valid": "on"},
        )
        invalid = ajax_client.post(url("integration_supplier_validation"), {"valid": "on"})

    assert unknown.json()["success"] == "ko"
    assert invalid.json()["success"] == "ko"
    assert "uuid not exists" in caplog.text
    assert "form invalid" in caplog.text


@pytest.mark.usefixtures("integration_data")
def test_delete_supplier_edi_import(ajax_client):
    response = ajax_client.post(
        url("delete_supplier_edi_import"),
        {
            "third_party_num": "FOUR001",
            "supplier": "WIDEX",
            "invoice_month": "2026-01-01",
            "delete": "false",
        },
    )

    assert response.json() == {"success": "success"}
    assert not EdiImport.objects.exists()
    assert not EdiImportControl.objects.exists(), "le contrôle orphelin est supprimé"
    assert ChangesTrace.objects.filter(model_name="ediimport").exists()


def test_delete_supplier_edi_import_formulaire_invalide(ajax_client, caplog):
    with caplog.at_level(logging.ERROR, logger="error_views"):
        response = ajax_client.post(url("delete_supplier_edi_import"), {"supplier": "WIDEX"})

    assert response.json() == {"success": "ko"}
    assert "form invalid" in caplog.text


@pytest.mark.usefixtures("integration_data")
def test_integration_purchases_export(logged_client, stub_excel):
    calls = stub_excel(views_etape_2_1, "excel_integration_purchases")

    response = logged_client.get(url("integration_purchases_export"))

    assert response["Content-Disposition"].startswith(
        "attachment; filename=RELEVES_VS_FACTURES_INTEGREES_"
    )
    assert len(calls) == 1

    stub_excel(views_etape_2_1, "excel_integration_purchases", error=RuntimeError("boom"))
    response = logged_client.get(url("integration_purchases_export"))

    assert response.status_code == 302
    assert response.url == url("integration_purchases")


def test_alls_details_purchases_export(logged_client, integration_data, stub_excel, caplog):
    calls = stub_excel(views_etape_2_1, "excel_invoice_details")

    response = logged_client.get(
        url("alls_details_purchases_export", enc_param=integration_data.enc_param)
    )

    assert response["Content-Disposition"].startswith("attachment; filename=FOUR001_WIDEX_")
    assert calls[0][1] == (
        {
            "third_party_num": "FOUR001",
            "supplier": "WIDEX",
            "invoice_month": "2026-01-01",
            "flow_name": "Widex",
        },
    )

    with caplog.at_level(logging.ERROR, logger="error_views"):
        response = logged_client.get(
            url("alls_details_purchases_export", enc_param=encode("trop", "court"))
        )

    assert response.status_code == 302
    assert response.url == url("integration_purchases")
    assert "alls_details_purchases_export" in caplog.text


def test_integration_validation(ajax_client, integration_data, caplog):
    validation = integration_data.validation
    identification = str(validation.uuid_identification)

    response = ajax_client.post(
        url("integration_validation"), {"uuid_identification": identification, "integration": "on"}
    )
    assert response.json() == {
        "success": "ok",
        "message": "Les Intégration sont maintenant validées",
    }
    validation.refresh_from_db()
    assert validation.integration is True

    response = ajax_client.post(
        url("integration_validation"), {"uuid_identification": identification}
    )
    assert response.json() == {
        "success": "ko",
        "message": "Les Intégration sont maintenant dé-validées",
    }

    with caplog.at_level(logging.ERROR, logger="error_views"):
        unknown = ajax_client.post(
            url("integration_validation"),
            {"uuid_identification": str(uuid.uuid4()), "integration": "on"},
        )
        invalid = ajax_client.post(url("integration_validation"), {"integration": "on"})

    assert unknown.json()["success"] == "ko"
    assert invalid.json()["success"] == "ko"
    assert "integration_validation error" in caplog.text
    assert "form invalid" in caplog.text


# 2.1.A - LISTING FACTURES =========================================================================
def test_integration_supplier_purchases(logged_client, integration_data):
    response = logged_client.get(
        url("integration_supplier_purchases", enc_param=integration_data.enc_param)
    )

    assert response.status_code == 200
    invoices = response.context["controles_exports"]
    assert [row["invoice_number"] for row in invoices] == ["F001", "F002"]
    assert invoices[0]["axe_cct"] == "AF0001"
    assert invoices[0]["clickable"] is True
    assert "Janvier 2026" in response.context["titre_table"]


@pytest.mark.usefixtures("integration_data")
def test_integration_supplier_purchases_vide_redirige(logged_client):
    response = logged_client.get(
        url(
            "integration_supplier_purchases",
            enc_param=encode("INCONNU", "X", "2026-01-01", "Widex"),
        )
    )

    assert response.status_code == 302
    assert response.url == url("integration_purchases")


@pytest.mark.usefixtures("integration_data")
def test_delete_invoice_purchase(ajax_client, caplog):
    response = ajax_client.post(
        url("delete_invoice_purchase"),
        {
            "third_party_num": "FOUR001",
            "invoice_number": "F001",
            "invoice_month": "2026-01-01",
            "delete": "false",
        },
    )

    assert response.json() == {"success": "success"}
    assert list(EdiImport.objects.values_list("invoice_number", flat=True)) == ["F002"]

    with caplog.at_level(logging.ERROR, logger="error_views"):
        response = ajax_client.post(url("delete_invoice_purchase"), {"invoice_number": "F002"})

    assert response.json() == {"success": "ko"}
    assert "form invalid" in caplog.text


@pytest.mark.parametrize(
    ("supplier", "function_name"),
    [("WIDEX", "excel_supplier_purchases"), ("COSIUM TRANSFERTS", "excel_transfers_cosium")],
)
@pytest.mark.usefixtures("integration_data")
def test_integration_supplier_purchases_export(logged_client, stub_excel, supplier, function_name):
    calls = stub_excel(views_etape_2_1_A, function_name)
    enc_param = encode("FOUR001", supplier, "2026-01-01", "Widex")

    response = logged_client.get(
        url("integration_supplier_purchases_export", flow_name="Widex", enc_param=enc_param)
    )

    assert response["Content-Disposition"].startswith("attachment; filename=FOUR001_2026-01-01_")
    assert calls[0][1][0]["supplier"] == supplier


def test_integration_supplier_purchases_export_erreur(logged_client, caplog):
    with caplog.at_level(logging.ERROR, logger="error_views"):
        response = logged_client.get(
            url("integration_supplier_purchases_export", flow_name="Widex", enc_param="%%%")
        )

    assert response.status_code == 302
    assert response.url == url("integration_purchases")
    assert "integration_supplier_purchases_export" in caplog.text


# 2.1.B - DETAILS FACTURES =========================================================================
def test_details_purchase(logged_client, integration_data):
    response = logged_client.get(
        url("details_purchase", flow_name="Widex", enc_param=integration_data.enc_invoice)
    )

    assert response.status_code == 200
    assert [row.invoice_number for row in response.context["invoices"]] == ["F001"]
    assert response.context["chevron_retour"] == url(
        "integration_supplier_purchases", enc_param=integration_data.enc_param
    )


def test_delete_line_details_purchase(ajax_client, integration_data, caplog):
    row = integration_data.rows[0]

    response = ajax_client.post(url("delete_line_details_purchase"), {"pk[pk]": row.pk})

    assert response.json() == {"success": "success"}
    assert not EdiImport.objects.filter(pk=row.pk).exists()

    with caplog.at_level(logging.ERROR, logger="error_views"):
        response = ajax_client.post(url("delete_line_details_purchase"), {"pk[pk]": "abc"})

    assert response.json() == {"success": "ko"}
    assert "form invalid" in caplog.text


def test_details_purchases_export(logged_client, integration_data, stub_excel, caplog):
    calls = stub_excel(views_etape_2_1_B, "excel_invoice_number")

    response = logged_client.get(
        url("details_purchases_export", enc_param=integration_data.enc_invoice)
    )

    assert response["Content-Disposition"].startswith("attachment; filename=FOUR001_F001_")
    assert calls[0][1][0]["invoice_number"] == "F001"

    stub_excel(views_etape_2_1_B, "excel_invoice_number", error=RuntimeError("boom"))
    with caplog.at_level(logging.ERROR, logger="error_views"):
        response = logged_client.get(
            url("details_purchases_export", enc_param=integration_data.enc_invoice)
        )

    assert response.status_code == 302
    assert response.url == url("integration_purchases")
    assert "details_purchases_export" in caplog.text


# 2.2 - FACTURES SANS CCT ==========================================================================
def test_without_cct_purchases(logged_client, make_edi_import):
    make_edi_import(invoice_number="SANS")
    make_edi_import(invoice_number="SUPPR", delete=True)

    response = logged_client.get(url("without_cct_purchases"))

    assert response.status_code == 200
    assert [row["invoice_number"] for row in response.context["invoices_without_cct"]] == ["SANS"]


def test_without_cct_purchases_export(logged_client, stub_excel, caplog):
    stub_excel(views_etape_2_2, "excel_integration_without_cct")

    response = logged_client.get(url("without_cct_purchases_export"))
    assert response["Content-Disposition"].startswith(
        "attachment; filename=FACTURES_INTEGREES_SANS_CCT_"
    )

    stub_excel(views_etape_2_2, "excel_integration_without_cct", error=RuntimeError("boom"))
    with caplog.at_level(logging.ERROR, logger="error_views"):
        response = logged_client.get(url("without_cct_purchases_export"))

    assert response.status_code == 302
    assert response.url == url("without_cct_purchases")


# INTEGRATIONS SANS TIERS ==========================================================================
@pytest.fixture
def orphan_rows(make_edi_import, make_society, make_big_category):
    """Deux imports sans tiers (flux Widex et Lmc) et le fournisseur FOUR001 disponible"""
    make_society(
        "FOUR001",
        is_supplier=True,
        is_client=False,
        name="WIDEX SAS",
        centers_suppliers_indentifier="",
    )
    make_big_category("Marchandises")
    widex = make_edi_import(
        third_party_num="", supplier="WIDEX", supplier_ident="widex", flow_name="Widex"
    )
    lmc = make_edi_import(
        third_party_num="",
        supplier="LMC",
        supplier_ident="lmc",
        flow_name="Lmc",
        reference_article="L1",
    )
    return widex, lmc


@pytest.mark.usefixtures("orphan_rows")
def test_purchase_without_suppliers(logged_client, monkeypatch):
    response = logged_client.get(url("purchase_without_suppliers"))

    assert response.status_code == 200
    assert sorted(row["flow_name"] for row in response.context["elements_list"]) == ["Lmc", "Widex"]

    with patched_attrs(monkeypatch, views_without_third_party_num, get_in_progress=lambda: True):
        response = logged_client.get(url("purchase_without_suppliers"))

    assert response.context["en_cours"] is True


def post_data(row, **extra):
    return {
        "flow_name": row.flow_name,
        "supplier": row.supplier,
        "supplier_ident": row.supplier_ident,
        "third_party_num": "FOUR001",
        "uuid_identification": str(row.uuid_identification),
        **extra,
    }


def test_purchase_without_suppliers_update(ajax_client, orphan_rows):
    """Le tiers est posé sur l'import et l'identifiant ajouté au tiers ; il reste un import orphelin"""
    widex, _ = orphan_rows

    response = ajax_client.post(url("purchase_without_suppliers_update"), post_data(widex))

    assert response.json() == {"success": "success"}
    widex.refresh_from_db()
    assert widex.third_party_num == "FOUR001"
    assert widex.supplier == "WIDEX SAS"
    assert widex.big_category.slug_name == "marchandises"
    from apps.book.models import Society  # pylint: disable=C0415

    assert Society.objects.get(third_party_num="FOUR001").centers_suppliers_indentifier == "widex|"
    assert any("nouveau tiers : FOUR001" in message for message in messages_of(response))


@pytest.mark.usefixtures("make_society")
def test_purchase_without_suppliers_update_dernier_orphelin(ajax_client, orphan_rows):
    """Quand plus aucun import n'est orphelin, l'url de l'écran 2.1 est renvoyée"""
    widex, lmc = orphan_rows
    EdiImport.objects.filter(pk=lmc.pk).delete()
    from apps.book.models import Society  # pylint: disable=C0415

    Society.objects.filter(third_party_num="FOUR001").update(centers_suppliers_indentifier="autre|")

    response = ajax_client.post(url("purchase_without_suppliers_update"), post_data(widex))

    assert response.json() == {"success": url("integration_purchases")}
    from apps.book.models import Society  # pylint: disable=C0415

    assert (
        Society.objects.get(third_party_num="FOUR001").centers_suppliers_indentifier
        == "autre|widex|"
    )


def test_purchase_without_suppliers_update_identifiant_deja_present(ajax_client, orphan_rows):
    """Identifiant déjà connu du tiers : pas de doublon, l'import est tout de même rattaché"""
    widex, _ = orphan_rows
    from apps.book.models import Society  # pylint: disable=C0415

    Society.objects.filter(third_party_num="FOUR001").update(
        centers_suppliers_indentifier="autre|widex|"
    )

    response = ajax_client.post(url("purchase_without_suppliers_update"), post_data(widex))

    assert response.json() == {"success": "success"}
    assert any("nouveau tiers : FOUR001" in message for message in messages_of(response))
    widex.refresh_from_db()
    assert widex.third_party_num == "FOUR001"
    assert (
        Society.objects.get(third_party_num="FOUR001").centers_suppliers_indentifier
        == "autre|widex|"
    )


def test_purchase_without_suppliers_update_import_inchange(ajax_client, orphan_rows, monkeypatch):
    """Second trace_change sans changement : message d'erreur remonté, la réponse n'est pas un succès"""
    widex, _ = orphan_rows
    results = iter([(True, "tiers ok. "), (False, "rien sur l'import")])

    with patched_attrs(
        monkeypatch, views_without_third_party_num, trace_change=lambda *a, **k: next(results)
    ):
        response = ajax_client.post(url("purchase_without_suppliers_update"), post_data(widex))

    assert response.json() == {"success": "ko"}
    assert "tiers ok. rien sur l'import" in messages_of(response)


def test_purchase_without_suppliers_update_atomique(ajax_client, orphan_rows, monkeypatch):
    """L'import ne peut pas être mis à jour : l'identifiant ajouté au tiers est annulé"""
    from apps.book.models import Society  # pylint: disable=C0415
    from apps.core.bin.change_traces import trace_change as real_trace_change  # pylint: disable=C0415

    widex, _ = orphan_rows

    def trace_change(request, model, before_kwargs, update_kwargs):
        if model is Society:
            return real_trace_change(request, model, before_kwargs, update_kwargs)

        raise RuntimeError("import verrouillé")

    with patched_attrs(monkeypatch, views_without_third_party_num, trace_change=trace_change):
        response = ajax_client.post(url("purchase_without_suppliers_update"), post_data(widex))

    assert response.json() == {"success": "ko"}
    assert Society.objects.get(third_party_num="FOUR001").centers_suppliers_indentifier == ""
    widex.refresh_from_db()
    assert widex.third_party_num == ""


def test_purchase_without_suppliers_update_exception(ajax_client, orphan_rows, monkeypatch, caplog):
    widex, _ = orphan_rows

    def boom(*args, **kwargs):
        raise RuntimeError("boom")

    with (
        patched_attrs(monkeypatch, views_without_third_party_num, trace_change=boom),
        caplog.at_level(logging.ERROR, logger="error_views"),
    ):
        response = ajax_client.post(url("purchase_without_suppliers_update"), post_data(widex))

    assert response.json() == {"success": "ko"}
    assert "consulter les logs" in messages_of(response)[0]
    assert "purchase_without_suppliers_update" in caplog.text


@pytest.mark.usefixtures("orphan_rows")
def test_purchase_without_suppliers_update_formulaire_invalide(ajax_client, caplog):
    with caplog.at_level(logging.ERROR, logger="error_views"):
        response = ajax_client.post(
            url("purchase_without_suppliers_update"),
            {"flow_name": "Widex", "third_party_num": "INCONNU"},
        )

    assert response.json() == {"success": "ko"}
    message = messages_of(response)[0]
    assert message.startswith("Une erreur c'est produite : Erreur sur le champ third_party_num")
    assert "uuid_identification" in message
    assert "form invalid" in caplog.text


def test_purchase_without_suppliers_update_categorie_par_defaut_du_tiers(
    ajax_client, orphan_rows, make_big_category
):
    """La catégorie par défaut du tiers prime sur la catégorie Marchandises"""
    widex, _ = orphan_rows
    formation = make_big_category("Formation")
    from apps.book.models import Society  # pylint: disable=C0415

    Society.objects.filter(third_party_num="FOUR001").update(big_category_default=formation)

    response = ajax_client.post(url("purchase_without_suppliers_update"), post_data(widex))

    assert response.json() == {"success": "success"}
    widex.refresh_from_db()
    assert widex.big_category == formation


def test_purchase_without_suppliers_update_sans_categorie(ajax_client, orphan_rows):
    """Sans catégorie Marchandises ni défaut du tiers, seul le tiers est posé"""
    widex, _ = orphan_rows
    from apps.parameters.models import Category  # pylint: disable=C0415

    Category.objects.all().delete()

    response = ajax_client.post(url("purchase_without_suppliers_update"), post_data(widex))

    assert response.json() == {"success": "success"}
    widex.refresh_from_db()
    assert widex.third_party_num == "FOUR001"
    assert widex.big_category is None


EXPORT_URLS = [
    ("integration_purchases_export", {}, "integration_purchases", {}),
    ("alls_details_purchases_export", {"enc_param": "x"}, "integration_purchases", {}),
    (
        "integration_supplier_purchases_export",
        {"flow_name": "Widex", "enc_param": "x"},
        "integration_purchases",
        {},
    ),
    ("details_purchases_export", {"enc_param": "x"}, "integration_purchases", {}),
    ("without_cct_purchases_export", {}, "without_cct_purchases", {}),
    ("families_invoices_purchases_export", {}, "families_invoices_purchases", {}),
    (
        "supplier_details_invoices_purchases_export",
        {"third_party_num": "FOUR001"},
        "families_invoices_purchases",
        {},
    ),
    ("cct_franchiseurs_purchases_export", {}, "cct_franchiseurs_purchases", {}),
    ("clients_news_purchases_export", {}, "clients_news_purchases", {}),
    ("subscriptions_purchases_export", {}, "subscriptions_purchases", {}),
    ("control_rfa_period_export", {}, "control_rfa_period", {}),
    ("refac_cct_purchases_export", {}, "refac_cct_purchases", {}),
    (
        "suppliers_m_purchases_export",
        {"client": "AF0001"},
        "suppliers_m_purchases",
        {"client": "AF0001"},
    ),
    (
        "third_suppliers_m_purchases_export",
        {"client": "AF0001", "third_party_num": "FOUR001"},
        "third_suppliers_m_purchases",
        {"client": "AF0001", "third_party_num": "FOUR001"},
    ),
    ("balance_suppliers_purchases_export", {}, "balance_suppliers_purchases", {}),
    ("ca_cct_export", {}, "ca_cct", {}),
    ("ca_familly_cct_export", {"client": "AF0001"}, "ca_familly_cct", {"client": "AF0001"}),
]


@pytest.mark.parametrize(("name", "kwargs", "back", "back_kwargs"), EXPORT_URLS)
def test_exports_refusent_post(logged_client, name, kwargs, back, back_kwargs):
    """Les exports ne répondent qu'en GET : un POST redirige vers l'écran d'origine"""
    response = logged_client.post(url(name, **kwargs), {})

    assert response.status_code == 302
    assert response.url == url(back, **back_kwargs)
