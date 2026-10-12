"""Tests des formulaires et du filtre de recherche des factures"""

import pytest

from apps.invoices.filters import InvoiceFilter
from apps.invoices.forms import (
    AxesDetailsDeleteForm,
    AxesDetailsForm,
    EnteteDetailsDeleteForm,
    EnteteDetailsForm,
    InvoiceSearchForm,
)

pytestmark = pytest.mark.django_db


def test_entete_details_form(make_entete_details):
    assert EnteteDetailsForm({"ranking": 3, "column_name": "Lentilles"}).is_valid()
    make_entete_details("Lentilles")
    form = EnteteDetailsForm({"ranking": 3, "column_name": "Lentilles"})

    assert not form.is_valid()
    assert "column_name" in form.errors


def test_delete_forms_exigent_un_id_existant(make_entete_details, make_axes_details):
    """Les formulaires de suppression n'étaient jamais invalides (champ id sans champ réel)"""
    entete = make_entete_details("Montures")
    axe = make_axes_details("OPT", "Montures")

    assert EnteteDetailsDeleteForm({"id": entete.pk}).is_valid()
    assert not EnteteDetailsDeleteForm({"id": entete.pk + 999}).is_valid()
    assert not EnteteDetailsDeleteForm({}).is_valid()
    assert AxesDetailsDeleteForm({"id": axe.pk}).is_valid()
    assert not AxesDetailsDeleteForm({"id": axe.pk + 999}).is_valid()


def test_axes_details_form(make_section, make_entete_details):
    section = make_section("PRO", "AUD")
    entete = make_entete_details("Audio")
    form = AxesDetailsForm(
        {"axe_pro": section.uuid_identification, "column_name": entete.column_name}
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["axe_pro"] == section


def test_invoice_search_form_et_filter(make_invoice_common_details, make_cct):
    make_invoice_common_details("FOUR001", "FAC-10")
    make_invoice_common_details("FOUR002", "AUTRE-1", cct=make_cct("AF0002"))
    form = InvoiceSearchForm({})

    assert form.is_valid()
    assert form.fields["invoice_number__icontains"].required is False

    filtered = InvoiceFilter(
        {"invoice_number__icontains": "FAC"}, queryset=InvoiceFilter.Meta.model.objects.all()
    )

    assert [row.invoice_number for row in filtered.qs] == ["FAC-10"]
    assert (
        InvoiceFilter(
            {"third_party_num": "FOUR002"}, queryset=InvoiceFilter.Meta.model.objects.all()
        ).qs.count()
        == 1
    )
