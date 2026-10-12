"""Tests de la vue de recherche des factures pour réaffectation"""
import pytest
from django.urls import reverse

from apps.invoices.views import invoice_reassignment_views
from conftest import patched_attrs

pytestmark = pytest.mark.django_db
URL = "invoices:invoice_search_list"


def test_bloque_si_non_finalise(logged_client, monkeypatch):
    with patched_attrs(monkeypatch, invoice_reassignment_views, control_insertion=lambda: True):
        response = logged_client.get(reverse(URL))

    assert response.status_code == 200
    assert response.context["not_finalize"] is True
    assert logged_client.session["level"] == 50


def test_liste_vide(logged_client):
    response = logged_client.get(reverse(URL))

    assert response.status_code == 200
    assert response.context["num_items"] == 0
    assert "Facture trouv" not in response.context["titre_table"]


def test_liste_une_facture(logged_client, make_invoice_common_details):
    make_invoice_common_details("FOUR001", "FAC-1")
    response = logged_client.get(reverse(URL), {"page": "abc"})

    assert "(1 Facture trouvé)" in response.context["titre_table"]
    assert response.context["start_index"] == 0
    assert response.context["end_index"] == 1


def test_liste_plusieurs_et_filtres(logged_client, make_invoice_common_details):
    make_invoice_common_details("FOUR001", "FAC-1")
    make_invoice_common_details("FOUR001", "FAC-2")
    make_invoice_common_details("FOUR002", "AUTRE")

    response = logged_client.get(reverse(URL), {"page": "99"})
    assert "(3 Facture trouvés)" in response.context["titre_table"]

    response = logged_client.get(reverse(URL), {"invoice_number__icontains": "FAC"})
    assert response.context["num_items"] == 2
    assert response.context["attrs_filter"] == {"invoice_number__icontains": "FAC"}
    assert response.context["form"].fields["invoice_number__icontains"].required is False
