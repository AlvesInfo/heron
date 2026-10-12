"""
Tests des formulaires de saisie manuelle des factures (marchandises, formation, personnel)
"""
import datetime

import pytest

from apps.edi import forms as edi_forms
from apps.edi.forms.forms_django.saisie_marchandise_forms import (
    CreateBaseFormationForm,
    CreateBaseMarchandiseForm,
    CreateBasePersonnelForm,
    CreateFormationInvoiceForm,
    CreateMarchandiseInvoiceForm,
    CreatePersonnelInvoiceForm,
    initialed_date,
)


@pytest.mark.usefixtures('db')
def test_initialed_date_without_validation():
    assert initialed_date() == "2000-01-01"


def test_initialed_date_is_end_of_billing_month(make_edi_validation):
    make_edi_validation(billing_period=datetime.date(2026, 2, 1), final=True)
    make_edi_validation(billing_period=datetime.date(2026, 3, 1))

    assert initialed_date() == "2026-03-31"


def test_forms_package_exports_saisie_forms():
    assert edi_forms.CreateBaseMarchandiseForm is CreateBaseMarchandiseForm
    assert edi_forms.CreatePersonnelInvoiceForm is CreatePersonnelInvoiceForm


@pytest.fixture
def referentiel(make_society, make_country_currency, make_edi_validation):
    make_society("FOUR001", in_use=True)
    make_society("FOUR002", in_use=False)
    make_country_currency("EUR")
    make_country_currency("USD")
    make_edi_validation(billing_period=datetime.date(2026, 1, 1))


@pytest.mark.parametrize("form_class", [CreateBaseMarchandiseForm, CreateBasePersonnelForm])
@pytest.mark.usefixtures('referentiel')
def test_base_forms_choices(form_class):
    form = form_class()

    assert form.fields["third_party_num"].choices == [("", ""), ("FOUR001", "FOUR001 - Société FOUR001")]
    assert form.fields["invoice_type"].choices == [("380", "FAF"), ("381", "AVO")]
    assert form.fields["devise"].choices == [("EUR", "EUR"), ("USD", "USD")]
    assert form.fields["devise"].initial == "EUR"
    assert form.fields["invoice_number"].required is False
    assert form.fields["invoice_date"].initial == "2026-01-31"
    assert form.fields["invoice_date"].error_messages["required"] == "Une date de facture est obligatoire"


@pytest.mark.usefixtures('referentiel')
def test_base_marchandise_form_valid():
    form = CreateBaseMarchandiseForm(
        {
            "third_party_num": "FOUR001",
            "invoice_number": "",
            "invoice_date": "2026-01-15",
            "invoice_type": "380",
            "devise": "EUR",
            "sens": "2",
        }
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["sens"] == "2"
    assert form.fields["sens"].choices == [(0, "AC"), (1, "VE"), (2, "AC/VE")]


@pytest.mark.usefixtures('referentiel')
def test_base_marchandise_form_requires_supplier():
    form = CreateBaseMarchandiseForm({"invoice_date": "2026-01-15", "invoice_type": "380", "devise": "EUR"})

    assert form.is_valid() is False
    assert form.errors["third_party_num"] == ["Le Fournisseur (TiersX3) est obligatoire"]


@pytest.mark.usefixtures('referentiel')
def test_base_formation_form():
    form = CreateBaseFormationForm()

    assert form.fields["third_party_num"].initial == "ZFORM"
    assert form.fields["third_party_num"].required is False
    assert form.fields["third_party_num"].widget.attrs["readonly"] == ""
    assert form.fields["sens"].initial == 1
    assert form.fields["devise"].choices == [("EUR", "EUR"), ("USD", "USD")]

    bound = CreateBaseFormationForm({"invoice_date": "2026-01-15", "invoice_type": "381", "devise": "USD"})

    assert bound.is_valid(), bound.errors
    assert bound.cleaned_data["third_party_num"] == ""


@pytest.mark.usefixtures('referentiel')
def test_base_personnel_form_sens_hidden():
    form = CreateBasePersonnelForm()

    assert form.fields["sens"].widget.attrs == {"style": "display: none;"}
    assert form.fields["sens"].initial == 1


@pytest.mark.usefixtures('db')
def test_detail_forms_optional_fields():
    marchandise = CreateMarchandiseInvoiceForm()
    formation = CreateFormationInvoiceForm()
    personnel = CreatePersonnelInvoiceForm()

    for name in ("sub_category", "delivery_number", "delivery_date", "unit_weight"):
        assert marchandise.fields[name].required is False

    assert formation.fields["sub_category"].required is False
    assert "heures_formation" in formation.fields

    for name in ("sub_category", "command_reference", "initial_date"):
        assert personnel.fields[name].required is False

    assert "personnel_type" in personnel.fields


@pytest.mark.parametrize(
    "form_class", [CreateMarchandiseInvoiceForm, CreateFormationInvoiceForm, CreatePersonnelInvoiceForm]
)
def test_detail_forms_have_no_duplicate_fields(form_class):
    fields = form_class.Meta.fields

    assert len(fields) == len(set(fields))
