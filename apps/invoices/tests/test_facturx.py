# pylint: disable=E0401,W0621,W0611,W0212
"""Tests de la chaîne Factur-X : mapping heron -> facturx-fr, client HTTP, génération"""
import datetime
import logging
import types
from decimal import Decimal
from pathlib import Path

import pytest

from apps.invoices.bin import facturx_mapping, generate_invoices_facturx
from apps.invoices.bin.facturx_client import FacturXClient, FacturXClientError
from apps.invoices.bin.facturx_mapping import FacturXMappingError, build_facturx_invoice
from apps.invoices.tests.helpers_external import PDF_BYTES, FakeResponse, FakeSession, reload_with_node, unreachable

pytestmark = pytest.mark.django_db


# DONNÉES ==========================================================================================
@pytest.fixture
def facturx_sale(make_society, make_country, make_child_center, make_maison, make_sale_invoice, make_sale_detail_external, make_vat):
    """Facture de vente complète : centrale vendeuse avec Society, maison acheteuse, lignes"""
    make_vat("001", "FRA")
    make_vat("002", "CEE")
    seller = make_society(
        "ACF001", corporate_name="Acuitis Franchise SAS", siret_number="123 456 789 00012",
        vat_cee_number="fr 12 345678900", adresse="10 rue du Vendeur", immeuble="Bât A", ville="Paris",
        code_postal="75001", country=make_country("FR"), email="vendeur@heron.local", telephone="0102030405",
    )
    buyer = make_society("CLI001", siren_number="987654321")
    maison = make_maison(
        "AF0001", third_party_num=buyer, invoice_entete="Maison Paris Opéra", adresse="1 rue de la Paix",
        siret_number="98765432100011", email="maison@heron.local",
    )
    center = make_child_center("ACF")
    center.society = seller
    center.sending_email = "factures@heron.local"
    center.member_num = "ADH-1"
    center.save()

    def _factory(**kwargs):
        defaults = {
            "cct": "AF0001", "third_party_num": "CLI001", "code_center": "ACF", "invoice_type": "FAC",
            "mode_reglement": "VIR", "date_echeance": datetime.date(2026, 2, 28),
        }
        defaults.update(kwargs)
        sale = make_sale_invoice(**defaults)
        sale.centers.legal_notice_center = "<p>Pénalités de <b>retard</b></p>"
        sale.centers.save()
        return sale, maison, seller

    return _factory


# MAPPING ==========================================================================================
def test_build_facturx_invoice_complet(facturx_sale, make_sale_detail_external):
    sale, _, _ = facturx_sale()
    make_sale_detail_external(sale, qty=Decimal("2"), net_unit_price=Decimal("50"), net_amount=Decimal("100"), ranking=1)
    make_sale_detail_external(
        sale, common=False, ranking=2, vat="002", vat_rate=Decimal("0"), net_amount=Decimal("0.00"),
        sub_category="Verres", unit_weight=None,
    )

    invoice, warnings = build_facturx_invoice(sale)

    assert warnings == []
    assert invoice["number"] == sale.invoice_number
    assert invoice["type_code"] == "380"
    assert invoice["currency"] == "EUR"
    assert invoice["seller"]["name"] == "Acuitis Franchise SAS"
    assert invoice["seller"]["siren"] == "123456789"
    assert invoice["seller"]["siret"] == "12345678900012"
    assert invoice["seller"]["vat_number"] == "FR12345678900"
    assert invoice["seller"]["email"] == "factures@heron.local"
    assert invoice["seller"]["address"] == {
        "street": "10 rue du Vendeur", "additional_street": "Bât A", "city": "Paris",
        "postal_code": "75001", "country_code": "FR",
    }
    assert invoice["buyer"]["name"] == "Maison Paris Opéra"
    assert invoice["buyer"]["siret"] == "98765432100011"
    assert invoice["buyer"]["siren"] == "987654321"
    assert invoice["buyer"]["delivery_address"] is None
    assert invoice["buyer"]["email"] == "maison@heron.local"
    line_1, line_2 = invoice["lines"]
    assert line_1["description"] == "Monture Ray"
    assert (line_1["quantity"], line_1["unit_price"], line_1["vat_rate"], line_1["vat_category"]) == ("2.00000", "50.00000", "20.00", "S")
    assert line_1["item_reference"] == "ART-1"
    assert line_1["buyer_reference"] == "CDE-1"
    assert line_2["description"] == "Verres"
    assert (line_2["quantity"], line_2["unit"], line_2["vat_category"], line_2["vat_exemption_reason_code"]) == ("1", "C62", "K", "VATEX-EU-IC")
    assert invoice["operation_category"] == "delivery"
    assert invoice["buyer_accounting_reference"] == "AF0001"
    assert invoice["contract_reference"] == "ADH-1"
    assert invoice["payment_terms"] == {"description": "30 jours"}
    assert invoice["payment_means"] == {"code": "58", "bank_account": {"iban": "FR7600000000000000000000000", "bic": "SWIFTFRPP"}}
    assert (invoice["billing_period_start"], invoice["billing_period_end"]) == ("2026-01-01", "2026-01-31")
    assert invoice["due_date"] == "2026-02-28"
    assert invoice["note"] == "Facture Marchandises - CCT AF0001\nPénalités de retard"


def test_build_facturx_invoice_avoir_et_ecarts(facturx_sale, make_sale_detail_external):
    """Avoir en montants négatifs -> signe inversé, écart qty x PU absorbé en remise / majoration"""
    sale, _, _ = facturx_sale(invoice_type="AVC", invoice_amount_without_tax=Decimal("-100"), mode_reglement="")
    make_sale_detail_external(sale, qty=Decimal("3"), net_unit_price=Decimal("-30"), net_amount=Decimal("-100"))  # 3 x 30 = 90 < 100 -> charge
    make_sale_detail_external(sale, qty=Decimal("3"), net_unit_price=Decimal("-40"), net_amount=Decimal("-100"), ranking=2)  # 120 > 100 -> discount

    invoice, warnings = build_facturx_invoice(sale)

    assert invoice["type_code"] == "381"
    assert invoice["lines"][0]["quantity"] == "-3.00000"
    assert invoice["lines"][0]["unit_price"] == "-30.00000"
    assert invoice["lines"][0]["charge_amount"] == "10.00"
    assert invoice["lines"][0]["discount_amount"] is None
    assert invoice["lines"][1]["discount_amount"] == "20.00"
    assert invoice["lines"][1]["charge_amount"] is None
    assert invoice["payment_means"]["code"] == "58"
    assert warnings == ["Total HT des lignes (200.00) différent du total HT heron (100.00)"]


def test_build_facturx_invoice_sans_quantite_et_tiers_fallback(facturx_sale, make_sale_detail_external, make_country):
    """Pas de ligne commune (qty 0 -> 1 x montant), acheteur sans maison, pays étranger"""
    sale, maison, _ = facturx_sale(cct="AF0002", mode_reglement="PRLV SEPA", invoice_amount_without_tax=Decimal("80"))
    make_sale_detail_external(sale, common=False, net_amount=Decimal("80"), big_category="Divers", sub_category="")
    buyer = sale.third_party_num
    buyer.country = make_country("BE", "Belgique")
    buyer.siret_number = "ignoré hors FR"
    buyer.corporate_name = ""
    buyer.name = ""
    buyer.short_name = "CLI"
    buyer.save()

    invoice, warnings = build_facturx_invoice(sale)

    line = invoice["lines"][0]
    assert (line["quantity"], line["unit_price"]) == ("1", "80.00")
    assert line["description"] == "Divers"
    assert invoice["buyer"]["name"] == "CLI"
    assert invoice["buyer"]["address"]["country_code"] == "BE"
    assert invoice["buyer"]["address"]["street"] == "CLI"  # repli sur le nom
    assert invoice["buyer"]["siren"] is None
    assert invoice["payment_means"]["code"] == "59"
    assert warnings == []


@pytest.mark.usefixtures('monkeypatch')
def test_build_facturx_invoice_maison_etrangere_sans_siren(facturx_sale, make_sale_detail_external, make_country):
    sale, maison, _ = facturx_sale()
    make_sale_detail_external(sale)
    maison.pays = make_country("DE", "Allemagne")
    maison.siret_number = ""
    maison.save()
    sale.third_party_num.siren_number = ""
    sale.third_party_num.vat_cee_number = "DE 123"
    sale.third_party_num.save()

    invoice, warnings = build_facturx_invoice(sale)

    assert invoice["buyer"]["delivery_address"]["country_code"] == "DE"
    assert invoice["buyer"]["vat_number"] == "DE123"
    assert warnings == []


def test_build_facturx_invoice_acheteur_francais_sans_siren(facturx_sale, make_sale_detail_external):
    sale, maison, _ = facturx_sale()
    make_sale_detail_external(sale)
    sale.centers.legal_notice_center = ""
    sale.centers.save()
    maison.siret_number = None
    maison.save()
    sale.third_party_num.siren_number = None
    sale.third_party_num.save()

    invoice, warnings = build_facturx_invoice(sale)

    assert warnings == ["Acheteur français 'Maison Paris Opéra' sans n° SIREN"]
    assert invoice["note"] == "Facture Marchandises - CCT AF0001"


@pytest.mark.parametrize("invoice_type", ["XXX", ""])
def test_build_facturx_invoice_type_inconnu(facturx_sale, invoice_type):
    sale, _, _ = facturx_sale(invoice_type=invoice_type)

    with pytest.raises(FacturXMappingError, match="Type de facture inconnu"):
        build_facturx_invoice(sale)


def test_get_seller_erreurs(facturx_sale, make_child_center):
    sale, _, seller = facturx_sale()

    sale.code_center = "ZZZ"
    with pytest.raises(FacturXMappingError, match="Centrale fille 'ZZZ' introuvable"):
        facturx_mapping.get_seller(sale)

    center = make_child_center("ACF")
    center.society = None
    center.save()
    sale.code_center = "ACF"
    with pytest.raises(FacturXMappingError, match="aucune Society"):
        facturx_mapping.get_seller(sale)

    center.society = seller
    center.save()
    seller.siret_number = ""
    seller.siren_number = ""
    seller.save()
    with pytest.raises(FacturXMappingError, match="pas de n° SIREN"):
        facturx_mapping.get_seller(sale)


def test_get_buyer_sans_maison_ni_tiers(facturx_sale):
    sale, _, _ = facturx_sale()
    sale.cct_id = "INCONNU"
    sale.third_party_num_id = "INCONNU"

    with pytest.raises(FacturXMappingError, match="Aucune Maison ni tiers"):
        facturx_mapping.get_buyer(sale)


def test_build_lines_sans_detail(facturx_sale):
    sale, _, _ = facturx_sale()

    with pytest.raises(FacturXMappingError, match="aucune ligne de détail"):
        build_facturx_invoice(sale)


@pytest.mark.parametrize(("regime", "expected"), [
    ("CEE", ("K", "VATEX-EU-IC")), ("EXP", ("G", "VATEX-EU-G")), ("DOM", ("E", None)), ("FRA", ("E", None)), ("", ("E", None)),
])
def test_vat_category_taux_zero(regime, expected):
    category, code, reason = facturx_mapping._vat_category("001", Decimal("0"), {"001": regime})

    assert expected == (category, code)
    assert reason
    assert facturx_mapping._vat_category("001", Decimal("20"), {}) == ("S", None, None)


@pytest.mark.usefixtures('db', 'make_vat')
def test_payment_means_code():
    from apps.accountancy.models import ModeReglement
    from uuid import uuid4

    ModeReglement.objects.create(code="LCR", name="Lettre de change", uuid_identification=uuid4(), auuid=uuid4()) if hasattr(ModeReglement, "auuid") else ModeReglement.objects.create(code="LCR", name="Lettre de change", uuid_identification=uuid4())

    assert facturx_mapping._payment_means_code("") == "58"
    assert facturx_mapping._payment_means_code("CHQ") == "20"
    assert facturx_mapping._payment_means_code("Carte bleue CB") == "48"
    assert facturx_mapping._payment_means_code("lcr") == "30"
    assert facturx_mapping._payment_means_code("inconnu") == "58"


def test_fonctions_utilitaires():
    assert facturx_mapping._clean(None) == ""
    assert facturx_mapping._digits(" 12 ab 3 ") == "123"
    assert facturx_mapping._identifiers("123456789", "12345678900012", country_code="FR") == ("123456789", "12345678900012")
    assert facturx_mapping._identifiers("", "12345678900012", country_code="FR") == ("123456789", "12345678900012")
    assert facturx_mapping._identifiers("123456789", country_code="BE") == (None, None)
    assert facturx_mapping._vat_number(" fr 12 ") == "FR12"
    assert facturx_mapping._vat_number("") is None
    assert facturx_mapping._country_code("f") == "FR"
    assert facturx_mapping._country_code(types.SimpleNamespace(country="de")) == "DE"
    assert facturx_mapping._html_to_text("") == ""
    assert facturx_mapping._html_to_text("<p>a</p><p>b</p>") == "a b"
    address = facturx_mapping._address("", "Bât B", "", "", None, fallback_street="Nom")
    assert address == {"street": "Bât B", "additional_street": None, "city": "-", "postal_code": "-", "country_code": "FR"}
    assert facturx_mapping._line_adjustments(Decimal("1"), Decimal("10"), Decimal("10")) == (None, None)
    assert facturx_mapping._billing_period(types.SimpleNamespace(invoice_month=None)) == (None, None)
    assert facturx_mapping._payment_terms(types.SimpleNamespace(parties=None)) is None
    payment = facturx_mapping._payment_means(types.SimpleNamespace(centers=None, mode_reglement=None))
    assert payment == {"code": "58"}


# CLIENT HTTP ======================================================================================
def test_facturx_client_error_str():
    assert str(FacturXClientError("boom")) == "boom"
    assert str(FacturXClientError("boom", status=422, details="détail")) == "[422] boom - détail"
    details = [{"loc": ["seller", "siren"], "msg": "manquant"}, "texte"] + ["x"] * 20
    text = str(FacturXClientError("boom", details=details))
    assert "seller.siren : manquant" in text
    assert "texte" in text
    assert "(2 erreurs supplémentaires)" in text


def test_facturx_client_parametres(settings):
    settings.FACTURX_API_KEY = ""
    client = FacturXClient()

    assert client.base_url == settings.FACTURX_SERVER_URL.rstrip("/")
    assert client.headers == {}
    assert client.validate is True
    assert client._url("/health/") == f"{client.base_url}/facturx/health/"

    client = FacturXClient(base_url="http://srv/", api_key="k", profile="BASIC", timeout=5, validate=False)
    assert client.headers == {"Authorization": "Bearer k"}
    assert (client.profile, client.timeout, client.validate) == ("BASIC", 5, False)


def test_facturx_client_health_et_disponibilite(caplog):
    client = FacturXClient(base_url="http://srv", api_key="k")
    client.session = FakeSession([FakeResponse(200, {"status": "ok"}), FakeResponse(500, {"error": "KO"}), unreachable()])

    assert client.health() == {"status": "ok"}
    assert client.session.calls[0][1] == "http://srv/facturx/health/"

    with caplog.at_level(logging.WARNING, logger="invoices_flux"):
        assert client.is_available() is False

    assert "[500] KO" in caplog.text

    with pytest.raises(FacturXClientError, match="injoignable"):
        client.health()


@pytest.mark.usefixtures('settings')
def test_facturx_client_generate():
    client = FacturXClient(base_url="http://srv", api_key="k", validate=True)
    client.session = FakeSession([
        FakeResponse(200, content=b"%PDF-facturx"),
        FakeResponse(422, {"error": "invalide", "details": [{"loc": ["a"], "msg": "m"}]}),
        FakeResponse(502, json_error=True),
        FakeResponse(400, payload=["liste"]),
        FakeResponse(200, content=b"<html>"),
        unreachable(),
    ])

    assert client.generate({"number": "F1"}, b"%PDF", file_name="f1.pdf") == b"%PDF-facturx"
    data = client.session.calls[0][2]["data"]
    assert data["validate"] == "true"
    assert data["profile"] == client.profile
    assert '"F1"' in data["invoice"]

    with pytest.raises(FacturXClientError, match=r"\[422\] invalide - a : m"):
        client.generate({}, b"%PDF", validate=False)

    with pytest.raises(FacturXClientError, match=r"\[502\] Erreur HTTP 502"):
        client.generate({}, b"%PDF")

    with pytest.raises(FacturXClientError, match="liste"):
        client.generate({}, b"%PDF")

    with pytest.raises(FacturXClientError, match="pas un PDF"):
        client.generate({}, b"%PDF")

    with pytest.raises(FacturXClientError, match="injoignable"):
        client.generate({}, b"%PDF")


# GÉNÉRATION =======================================================================================
class FakeFacturXClient:
    """Client Factur-X simulé"""

    def __init__(self, error=None):
        self.error = error
        self.calls = []

    def generate(self, invoice, pdf_bytes, file_name="facture.pdf"):
        self.calls.append((invoice["number"], pdf_bytes, file_name))

        if self.error:
            raise self.error

        return b"%PDF-facturx-" + invoice["number"].encode()


@pytest.fixture
def pdf_generators(monkeypatch):
    """Générateurs PDF individuels remplacés par l'écriture d'un pdf factice"""
    calls = []

    def fake_pdf(uuid_identification, path):
        calls.append(uuid_identification)
        Path(path).write_bytes(PDF_BYTES)

    monkeypatch.setattr(generate_invoices_facturx, "GENERATION_PDF_DICT", {"marchandises": fake_pdf})
    return calls


@pytest.mark.usefixtures('make_sale_invoice')
def test_get_facturx_in_progress_et_candidats(facturx_sale):
    from django_celery_results.models import TaskResult

    assert generate_invoices_facturx.get_facturx_in_progress() is False
    TaskResult.objects.create(task_id="t1", status="STARTED", task_name=generate_invoices_facturx.FACTURX_TASK_NAME)
    assert generate_invoices_facturx.get_facturx_in_progress() is True

    sale, _, _ = facturx_sale(printed=True, global_invoice_file="g.pdf")
    facturx_sale(cct="AF0003", printed=True, global_invoice_file="g.pdf", facturx_file="deja.pdf")
    facturx_sale(cct="AF0004", printed=False)

    assert list(generate_invoices_facturx.get_facturx_candidates()) == [sale]
    assert list(generate_invoices_facturx.get_facturx_groups()) == [("AF0001", "g.pdf")]
    assert generate_invoices_facturx.facturx_file_name(sale) == f"AF0001_marchandises_{sale.invoice_number}_facturx.pdf"


def test_generate_sale_facturx(facturx_sale, make_sale_detail_external, email_dirs, pdf_generators):
    sale, _, _ = facturx_sale()
    make_sale_detail_external(sale)
    client = FakeFacturXClient()

    file_path, warnings = generate_invoices_facturx.generate_sale_facturx(sale, client)

    assert warnings == []
    assert file_path.parent == email_dirs.facturx
    assert file_path.read_bytes().startswith(b"%PDF-facturx-")
    assert client.calls[0][1] == PDF_BYTES
    assert client.calls[0][2] == f"{sale.invoice_number}.pdf"
    assert pdf_generators == [sale.uuid_identification]
    assert not list(email_dirs.processing_facturx.iterdir())
    sale.refresh_from_db()
    assert sale.facturx_file.name == file_path.name


@pytest.mark.usefixtures('pdf_generators')
def test_generate_sale_facturx_sans_generateur(facturx_sale):
    sale, _, _ = facturx_sale(big_category_slug_name="inconnu")
    client = FakeFacturXClient()

    with pytest.raises(FacturXMappingError, match="Pas de générateur PDF"):
        generate_invoices_facturx.generate_sale_facturx(sale, client)


@pytest.mark.usefixtures('make_sale_invoice', 'email_dirs', 'pdf_generators')
def test_invoices_facturx_generation(facturx_sale, make_sale_detail_external, monkeypatch, caplog):
    """Une facture générée avec avertissement, une en erreur de mapping, une en erreur client"""
    sale_ok, _, _ = facturx_sale(printed=True, global_invoice_file="g.pdf", invoice_amount_without_tax=Decimal("90"))
    make_sale_detail_external(sale_ok)
    facturx_sale(cct="AF0001", printed=True, global_invoice_file="g.pdf", big_category_slug_name="inconnu")[0]
    sale_client = facturx_sale(cct="AF0001", printed=True, global_invoice_file="g.pdf")[0]
    make_sale_detail_external(sale_client)
    clients = iter([FakeFacturXClient()])
    monkeypatch.setattr(generate_invoices_facturx, "FacturXClient", lambda: next(clients))

    class _Client(FakeFacturXClient):
        def generate(self, invoice, pdf_bytes, file_name="f"):
            if invoice["number"] == sale_client.invoice_number:
                raise FacturXClientError("serveur", status=500)
            return super().generate(invoice, pdf_bytes, file_name)

    monkeypatch.setattr(generate_invoices_facturx, "FacturXClient", _Client)

    with caplog.at_level(logging.ERROR, logger="invoices_flux"):
        trace, to_print = generate_invoices_facturx.invoices_facturx_generation("AF0001", "g.pdf")

    assert to_print == "have generate Factur-X : g.pdf (1 factures) - "
    assert trace.errors is True
    assert trace.created_numbers_records == 1
    assert trace.errors_numbers_records == 2
    assert "1 Factur-X générés pour AF0001 (g.pdf)" in trace.comment
    assert "Avertissements :" in trace.comment
    assert "Total HT des lignes" in trace.comment
    assert "Pas de générateur PDF" in trace.comment
    assert "[500] serveur" in trace.comment


@pytest.mark.usefixtures('pdf_generators', 'email_dirs')
def test_invoices_facturx_generation_succes(facturx_sale, make_sale_detail_external, monkeypatch):
    sale, _, _ = facturx_sale(printed=True, global_invoice_file="g.pdf")
    make_sale_detail_external(sale)
    monkeypatch.setattr(generate_invoices_facturx, "FacturXClient", FakeFacturXClient)

    trace, to_print = generate_invoices_facturx.invoices_facturx_generation("AF0001", "g.pdf")

    assert to_print == "have generate Factur-X : g.pdf (1 factures) - "
    assert trace.errors is False
    assert trace.comment == "1 Factur-X générés pour AF0001 (g.pdf)"
    sale.refresh_from_db()
    assert sale.facturx_file.name.endswith("_facturx.pdf")


@pytest.mark.usefixtures('pdf_generators', 'email_dirs')
def test_invoices_facturx_generation_exceptions(facturx_sale, make_sale_detail_external, monkeypatch, caplog):
    sale, _, _ = facturx_sale(printed=True, global_invoice_file="g.pdf")
    make_sale_detail_external(sale)

    class _Client(FakeFacturXClient):
        def generate(self, *args, **kwargs):
            raise RuntimeError("inattendu")

    monkeypatch.setattr(generate_invoices_facturx, "FacturXClient", _Client)

    with caplog.at_level(logging.ERROR, logger="invoices_flux"):
        trace, _ = generate_invoices_facturx.invoices_facturx_generation("AF0001", "g.pdf")

    assert trace.errors is True
    assert "RuntimeError('inattendu')" in trace.comment

    def boom():
        raise RuntimeError("client indisponible")

    monkeypatch.setattr(generate_invoices_facturx, "FacturXClient", boom)
    trace, to_print = generate_invoices_facturx.invoices_facturx_generation("AF0001", "g.pdf")

    assert to_print == ""
    assert "client indisponible" in trace.comment


@pytest.mark.parametrize(("node", "expected"), [("MSI", "/"), ("serveur", "/home/paulo/heron")])
def test_base_dir_selon_la_machine(monkeypatch, node, expected):
    assert reload_with_node(monkeypatch, generate_invoices_facturx, node) == expected
