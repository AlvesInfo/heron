"""Tests de la vue de saisie manuelle des factures (edi:create_hand_invoices)"""

import json
import logging

import pytest
from django.urls import reverse

from apps.edi.models import EdiImport
from apps.edi.tests.helpers_saisie import make_vat_rate
from apps.edi.views import views_manual_entry
from conftest import patched_attrs


def url(category="marchandises"):
    return reverse("edi:create_hand_invoices", kwargs={"category": category})


@pytest.fixture
def referentiel(
    make_society, make_vat, make_country_currency, make_nature, make_article, make_big_category
):
    make_society("FOUR001", is_client=False)
    make_vat_rate(make_vat, "001", "20")
    make_country_currency("EUR")
    make_nature("Opticien", for_personnel=True, for_contact=False, to_display="OPT")
    make_article(
        reference="FORM-1",
        society=make_society("ZFORM", is_client=False),
        big_category=make_big_category("Formation"),
    )


def post_data(entete=None, lignes=None):
    return {
        "data": json.dumps(
            {
                "entete": entete
                if entete is not None
                else {
                    "third_party_num": "FOUR001",
                    "invoice_number": "FA-1",
                    "invoice_date": "2026-01-15",
                    "invoice_type": "380",
                    "devise": "EUR",
                    "sens": "2",
                },
                "lignes": lignes if lignes is not None else [{"num": 1, "reference_article": "12"}],
            }
        )
    }


def test_unknown_category_redirects_home(logged_client):
    response = logged_client.get(url("inconnue"))

    assert response.status_code == 302
    assert response.url == reverse("home")


@pytest.mark.usefixtures("referentiel")
def test_not_finalized_invoicing_blocks_entry(logged_client, monkeypatch):
    with patched_attrs(monkeypatch, views_manual_entry, control_insertion=lambda: True):
        response = logged_client.get(url())

    assert response.status_code == 200
    assert response.context["not_finalize"] is True
    assert response.context["nb_display"] == 50
    assert logged_client.session["level"] == 50
    assert "déjà envoyée par mail" in str(next(iter(response.context["messages"])))


@pytest.mark.parametrize(
    ("category", "nb_display", "has_articles"),
    [("marchandises", 50, False), ("formation", 1, True), ("personnel", 30, True)],
)
@pytest.mark.usefixtures("referentiel")
def test_get_renders_entry_form(logged_client, category, nb_display, has_articles):
    response = logged_client.get(url(category))

    assert response.status_code == 200
    context = response.context
    assert context["category"] == category
    assert context["nb_display"] == nb_display
    assert list(context["range_display"]) == list(range(1, nb_display + 1))
    assert context["url_saisie"] == url(category)
    assert [vat for vat, _, _ in context["vat_list"]] == ["001"]
    assert bool(context["query_articles"]) is has_articles

    if category == "personnel":
        assert context["query_profession_type"][1]["to_display"] == "OPT"
    else:
        assert "query_profession_type" not in context


@pytest.mark.usefixtures("referentiel")
def test_post_without_ajax_renders_form(logged_client):
    response = logged_client.post(url(), post_data())

    assert response.status_code == 200
    assert response.context["category"] == "marchandises"


@pytest.mark.usefixtures("referentiel")
def test_post_without_lines(ajax_client):
    response = ajax_client.post(url(), post_data(lignes=[{"num": 1, "reference_article": ""}]))

    assert response.json() == {"success": "ko"}
    assert ajax_client.session["level"] == 50
    assert EdiImport.objects.count() == 0


@pytest.mark.usefixtures("referentiel", "make_trace")
def test_post_invalid_header(ajax_client):
    response = ajax_client.post(url(), post_data(entete={"invoice_number": "FA-1", "sens": "2"}))

    assert response.json() == {"success": "ko"}
    assert ajax_client.session["level"] == 50
    from apps.data_flux.models import Trace  # pylint: disable=C0415

    trace = Trace.objects.get()
    assert trace.errors is True
    assert "FA-1" in trace.comment


@pytest.mark.usefixtures("referentiel")
def test_post_existing_invoice(ajax_client, make_edi_import, monkeypatch):
    make_edi_import(third_party_num="FOUR001", invoice_number="FA-1", invoice_year=2026)
    calls = []

    with patched_attrs(
        monkeypatch,
        views_manual_entry,
        set_hand_invoice=lambda *args: calls.append(args) or (False, ""),
    ):
        response = ajax_client.post(url(), post_data())

    assert response.json() == {"success": "ko"}
    assert calls == []
    assert ajax_client.session["level"] == 50
    from apps.data_flux.models import Trace  # pylint: disable=C0415

    assert Trace.objects.get().errors is True


@pytest.mark.parametrize(("result", "level"), [((False, "créée"), 20), ((True, "refusée"), 50)])
@pytest.mark.usefixtures("referentiel")
def test_post_delegates_to_set_hand_invoice(ajax_client, monkeypatch, result, level):
    seen = {}

    def _set_hand_invoice(category, details_form, entete, lignes, user):
        seen.update(category=category, form=details_form, entete=entete, lignes=lignes, user=user)
        return result

    with patched_attrs(monkeypatch, views_manual_entry, set_hand_invoice=_set_hand_invoice):
        response = ajax_client.post(url(), post_data())

    assert response.json() == {"success": "ko"}
    assert ajax_client.session["level"] == level
    assert seen["category"] == "marchandises"
    assert seen["form"] is views_manual_entry.CreateMarchandiseInvoiceForm
    assert seen["entete"]["third_party_num"] == "FOUR001"
    assert seen["lignes"] == [{"num": 1, "reference_article": "12"}]
    assert seen["user"] == ajax_client.user


@pytest.mark.usefixtures("referentiel")
def test_post_general_exception(ajax_client, monkeypatch, caplog):
    def _boom(*_args):
        raise RuntimeError("explosion")

    with (
        patched_attrs(monkeypatch, views_manual_entry, check_invoice_exists=_boom),
        caplog.at_level(logging.ERROR, logger="error_views"),
    ):
        response = ajax_client.post(url(), post_data())

    assert response.json() == {"success": "ko"}
    assert ajax_client.session["level"] == 50
    assert "explosion" in caplog.text
    from apps.data_flux.models import Trace  # pylint: disable=C0415

    assert Trace.objects.get().errors is True
