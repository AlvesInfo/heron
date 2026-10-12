"""Tests des formulaires de validation des achats"""

import uuid

import pytest

from apps.validation_purchases.forms import (
    CaCctValidationForm,
    ChangeBigCategoryForm,
    ChangeCttForm,
    ClientsNewsValidationForm,
    ControlValidationForm,
    DeleteEdiForm,
    DeleteFieldForm,
    DeleteInvoiceForm,
    DeletePkForm,
    EdiImportControlForm,
    EdiImportGetForm,
    EdiImportValidationForm,
    FamiliesValidationForm,
    FranchiseursValidationForm,
    IntegrationValidationForm,
    RefacCctValidationForm,
    RfaValidationForm,
    SubscriptionsValidationForm,
    SuppliersValidationForm,
    UpdateSupplierPurchasesForm,
    UpdateThirdpartynumForm,
)

pytestmark = pytest.mark.django_db


def cleaned(form):
    """Valide le formulaire et renvoie ses données nettoyées"""
    assert form.is_valid(), form.errors
    return form.cleaned_data


VALIDATION_FORMS = [
    (ControlValidationForm, "valid"),
    (IntegrationValidationForm, "integration"),
    (FamiliesValidationForm, "families"),
    (FranchiseursValidationForm, "franchiseurs"),
    (ClientsNewsValidationForm, "clients_news"),
    (SubscriptionsValidationForm, "subscriptions"),
    (RfaValidationForm, "rfa"),
    (RefacCctValidationForm, "refac_cct"),
    (SuppliersValidationForm, "suppliers"),
    (CaCctValidationForm, "validation_ca"),
]


@pytest.mark.parametrize(("form_class", "flag"), VALIDATION_FORMS)
def test_validation_forms_flag_optionnel(form_class, flag):
    """Le booléen est facultatif (case décochée = False), l'uuid est obligatoire"""
    identification = uuid.uuid4()
    form = form_class({"uuid_identification": str(identification)})

    assert form.is_valid(), form.errors
    assert form.cleaned_data["uuid_identification"] == identification
    assert form.cleaned_data[flag] is False
    assert (
        cleaned(form_class({"uuid_identification": str(identification), flag: "on"}))[flag] is True
    )
    assert not form_class({flag: "on"}).is_valid()


def test_delete_forms(make_edi_import):
    make_edi_import(invoice_number="F1", invoice_month="2026-01-01", supplier="WIDEX")
    data = {
        "third_party_num": "FOUR001",
        "supplier": "WIDEX",
        "invoice_month": "2026-01-01",
        "invoice_number": "F1",
    }

    assert DeleteEdiForm(data).is_valid()
    assert DeleteInvoiceForm(data).is_valid()
    assert cleaned(DeletePkForm({"pk": "5"}))["pk"] == 5
    assert not DeletePkForm({"pk": "x"}).is_valid()
    assert DeleteFieldForm({**data, "id": 1, "purchase_invoice": True}).is_valid()


def test_edi_import_forms(make_edi_import, make_big_category):
    row = make_edi_import(invoice_month="2026-01-01")
    category = make_big_category("Marchandises")

    assert EdiImportGetForm({"id": row.pk}).is_valid()
    assert UpdateSupplierPurchasesForm(
        {"id": row.pk, "qty": "2", "net_unit_price": "3", "vat_rate": "0.2"}
    ).is_valid()
    validation = EdiImportValidationForm(
        {
            "third_party_num": "FOUR001",
            "big_category": category.uuid_identification,
            "invoice_month": "2026-01-01",
        }
    )
    assert validation.is_valid(), validation.errors


def test_edi_import_control_form():
    form = EdiImportControlForm(
        {
            "statement_without_tax": "100",
            "statement_with_tax": "120",
            "comment": "ok",
            "third_party_num": "FOUR001",
        }
    )

    assert form.is_valid(), form.errors
    assert set(form.fields) == {
        "statement_without_tax",
        "statement_with_tax",
        "comment",
        "third_party_num",
        "invoice_month",
    }


def test_update_third_party_num_form_choices(make_society):
    """Seuls les fournisseurs dont le code ne commence pas par un chiffre sont proposés"""
    make_society("FOUR001", is_supplier=True, is_client=False, name="Widex")
    make_society("CLI001", is_supplier=False)
    make_society("1234", is_supplier=True)
    form = UpdateThirdpartynumForm()

    assert form.third_party_num_choices == [("", ""), ("FOUR001", "FOUR001 - Widex")]
    bound = UpdateThirdpartynumForm(
        {
            "flow_name": "Widex",
            "supplier": "WIDEX",
            "supplier_ident": "widex",
            "third_party_num": "FOUR001",
            "uuid_identification": str(uuid.uuid4()),
        }
    )
    assert bound.is_valid(), bound.errors
    assert not UpdateThirdpartynumForm({"third_party_num": "CLI001", "flow_name": "x"}).is_valid()


def test_change_forms(make_big_category):
    category = make_big_category("Marchandises")
    form = ChangeBigCategoryForm(
        {
            "big_category": category.uuid_identification,
            "big_category_default": category.uuid_identification,
            "uuid_origin": str(uuid.uuid4()),
            "third_party_num": "FOUR001",
            "invoice_month": "2026-01-01",
        }
    )
    assert form.is_valid(), form.errors
    assert form.cleaned_data["id"] is None
    assert form.big_category_choices[0] == ("", "")

    cct_form = ChangeCttForm(
        {
            "cct": "AF0001",
            "uuid_identification": str(uuid.uuid4()),
            "third_party_num": "FOUR001",
            "invoice_number": "F1",
            "invoice_year": 2026,
            "id": 0,
        }
    )
    assert cct_form.is_valid(), cct_form.errors
    assert cct_form.cleaned_data["id"] == 0
