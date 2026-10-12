# pylint: disable=E0401,W0621,W0611
"""
FR : Tests des générateurs PDF WeasyPrint des factures de vente (une fonction par catégorie)
EN : Tests for WeasyPrint invoice PDF generators

created at: 2026-10-10
created by: Paulo ALVES
"""
import datetime
from decimal import Decimal

import pytest
from typing import ClassVar

from apps.invoices.bin import pdf_marchandises, pdf_sumary
from apps.invoices.bin.pdf_formation import invoice_formation_pdf
from apps.invoices.bin.pdf_marchandises import (
    invoice_marchandise_pdf,
    marchandise_details_invoice_pdf,
    marchandise_header_invoice_pdf,
    marchandise_sub_details_invoice_pdf,
    marchandise_suppliers_invoice_pdf,
)
from apps.invoices.bin.pdf_material import invoice_material_pdf
from apps.invoices.bin.pdf_prestation import invoice_prestation_pdf
from apps.invoices.bin.pdf_publicity import invoice_publicity_pdf
from apps.invoices.bin.pdf_rfa import rfa_invoice_pdf
from apps.invoices.bin.pdf_royalties import invoice_royalties_pdf
from apps.invoices.bin.pdf_staff import invoice_staff_pdf
from apps.invoices.bin.pdf_sumary import summary_invoice_pdf
from apps.invoices.bin.pdf_various import invoice_various_pdf
from apps.invoices.tests.helpers_pdf import ENTETES, page_count

pytestmark = pytest.mark.django_db

MARCHANDISES_LINES = [
    {"supplier": "FOUR001", "invoice_number": "FF-1", "axe": "OPT", "vat": "001", "net_amount": "100",
     "client_name": "Mme Dupont", "serial_number": "SN-1", "delivery_number": "BL1"},
    {"supplier": "FOUR001", "invoice_number": "FF-1", "axe": "VER", "vat": "002", "net_amount": "50",
     "grouping_goods": "VERRES", "delivery_number": ""},
    {"supplier": "FOUR002", "invoice_number": "FF-9", "axe": "AUD", "vat": "003", "net_amount": "30",
     "grouping_goods": "AIDES AUDITIVES", "base": "Audio", "ranking": 2, "invoice_entete": "Entête Four 2"},
]


@pytest.fixture
def sale_marchandises(make_sale_with_lines):
    return make_sale_with_lines(MARCHANDISES_LINES)


@pytest.mark.parametrize(
    ("function", "name"),
    [
        (marchandise_header_invoice_pdf, "header"),
        (marchandise_suppliers_invoice_pdf, "suppliers"),
        (marchandise_details_invoice_pdf, "details"),
        (marchandise_sub_details_invoice_pdf, "sub_details"),
    ],
)
@pytest.mark.usefixtures('pdf_domain')
def test_marchandises_parties(tmp_path, sale_marchandises, function, name):
    """Chaque partie de la facture de marchandises produit un PDF d'au moins une page"""
    pdf_path = tmp_path / f"{name}.pdf"

    function(uuid_invoice=sale_marchandises.uuid_identification, pdf_path=pdf_path)

    assert pdf_path.is_file()
    assert page_count(pdf_path) >= 1


@pytest.mark.usefixtures('pdf_domain')
def test_invoice_marchandise_pdf_fusionne_et_nettoie(tmp_path, sale_marchandises):
    """Les quatre parties sont fusionnées dans l'ordre et les intermédiaires supprimés"""
    pdf_path = tmp_path / "AF0001_marchandises_FV1.pdf"

    invoice_marchandise_pdf(uuid_invoice=sale_marchandises.uuid_identification, pdf_path=pdf_path)

    assert page_count(pdf_path) >= 4
    assert sorted(path.name for path in tmp_path.iterdir()) == ["AF0001_marchandises_FV1.pdf", "www"]


def test_marchandises_header_contenu_html(monkeypatch, pdf_domain, sale_marchandises, tmp_path):
    """Le HTML rendu porte les rubriques, les totaux par taux et le fournisseur"""
    rendered: ClassVar = {}

    def fake_render(template, context):
        rendered["template"] = template
        rendered["context"] = context
        return "<html><body>vide</body></html>"

    monkeypatch.setattr(pdf_marchandises, "render_to_string", fake_render)
    marchandise_header_invoice_pdf(sale_marchandises.uuid_identification, tmp_path / "h.pdf")

    headers = rendered["context"]["headers"]
    resume = rendered["context"]["resume"]
    assert rendered["template"] == "invoices/pdf_marchandises_header.html"
    assert [row["base"] for row in headers] == ["Marchandises", "Marchandises", "Audio"]
    assert resume["net_amount"] == Decimal("180")
    assert resume["net_amount_02"] == Decimal("100")  # tva 001
    assert resume["net_amount_01"] == Decimal("50")  # tva 002
    assert resume["net_amount_00"] == Decimal("30")  # autre tva
    assert rendered["context"]["logo"] == ""
    assert rendered["context"]["domain"] == pdf_domain


@pytest.mark.usefixtures('pdf_domain')
def test_marchandises_details_regroupe_par_fournisseur(monkeypatch, sale_marchandises, tmp_path):
    rendered: ClassVar = {}
    monkeypatch.setattr(
        pdf_marchandises, "render_to_string", lambda template, context: rendered.update(context) or "<html></html>"
    )
    marchandise_details_invoice_pdf(sale_marchandises.uuid_identification, tmp_path / "d.pdf")

    suppliers = rendered["suppliers"]
    assert [row["supplier_name"] for row in suppliers] == ["Entête Four 2", "Société FOUR001"]
    four1 = suppliers[1]
    assert four1["MO"] == Decimal("100")
    assert four1["VE"] == Decimal("50")
    assert four1["total_ht"] == Decimal("150")
    assert set(ENTETES.values()) >= {row["column_name"] for row in rendered["entetes"]}


@pytest.mark.usefixtures('pdf_domain')
def test_marchandises_sub_details_lignes(monkeypatch, sale_marchandises, tmp_path):
    rendered: ClassVar = {}
    monkeypatch.setattr(
        pdf_marchandises, "render_to_string", lambda template, context: rendered.update(context) or "<html></html>"
    )
    marchandise_sub_details_invoice_pdf(sale_marchandises.uuid_identification, tmp_path / "s.pdf")

    lines = rendered["sub_details"]
    assert len(lines) == 3
    assert lines[0]["article"] == "ART-1 - Monture test"
    assert {line["grouping_goods"] for line in lines} == {"MONT. OPT.", "VERRES", "AIDES AUDITIVES"}


@pytest.mark.parametrize(
    ("function", "slug", "lines"),
    [
        (invoice_material_pdf, "materiel", [{"vat": "001"}, {"vat": "002"}, {"vat": "003"}]),
        (invoice_various_pdf, "divers", [{"vat": "001", "serial_number": "S1"}, {"vat": "003"}]),
        (invoice_prestation_pdf, "prestation", [{"sub_category": "Audit", "vat": "002"}, {"vat": "001"}]),
        (invoice_publicity_pdf, "redevances-de-publicite", [{"unit_weight": "%", "qty": "0.05"}, {"vat": "003"}]),
        (invoice_royalties_pdf, "redevances", [{"unit_weight": "%", "qty": "0.1"}, {"vat": "003"}]),
        (rfa_invoice_pdf, "rfa", [{"axe_prj": "SIEMENS", "axe_prj_name": "SIGNIA", "vat": "001"}, {"vat": "002"}, {"vat": "003"}]),
    ],
)
@pytest.mark.usefixtures('pdf_domain')
def test_factures_par_categorie(tmp_path, make_sale_with_lines, function, slug, lines):
    sale = make_sale_with_lines(lines, slug=slug)
    pdf_path = tmp_path / f"{slug}.pdf"

    function(uuid_invoice=sale.uuid_identification, pdf_path=pdf_path)

    assert page_count(pdf_path) >= 1


@pytest.mark.usefixtures('pdf_domain')
def test_facture_personnel(tmp_path, make_sale_with_lines, make_nature):
    nature = make_nature("Opticien", for_personnel=True)
    sale = make_sale_with_lines(
        [{"personnel_type": nature, "libelle": "Mise à disposition", "command_reference": "Janvier"}],
        slug="personnel",
    )

    invoice_staff_pdf(uuid_invoice=sale.uuid_identification, pdf_path=tmp_path / "staff.pdf")

    assert page_count(tmp_path / "staff.pdf") >= 1


@pytest.mark.usefixtures('pdf_domain')
def test_facture_formation(tmp_path, make_sale_with_lines):
    sale = make_sale_with_lines(
        [{
            "first_name": "Jean", "last_name": "Dupont", "initial_date": datetime.date(2026, 1, 5),
            "final_date": datetime.date(2026, 1, 6), "heures_formation": Decimal("14"),
            "supplier_initial_libelle": "Formation vente",
        }],
        slug="formation",
    )

    invoice_formation_pdf(uuid_invoice=sale.uuid_identification, pdf_path=tmp_path / "formation.pdf")

    assert page_count(tmp_path / "formation.pdf") >= 1


# PAGE DE RÉSUMÉ ===================================================================================
@pytest.mark.usefixtures('pdf_domain')
def test_summary_invoice_pdf(tmp_path, make_sale_with_lines, monkeypatch):
    """Le résumé liste les factures non finalisées du cct et reprend la banque de la centrale"""
    sale = make_sale_with_lines([{"vat": "001"}])
    make_sale_with_lines([{"vat": "001"}], slug="rfa", big_category_ranking=2)
    rendered: ClassVar = {}
    original = pdf_sumary.render_to_string

    def spy(template, context):
        rendered.update(context)
        return original(template, context)

    monkeypatch.setattr(pdf_sumary, "render_to_string", spy)
    summary_invoice_pdf(sale.cct_id, tmp_path / "summary.pdf")

    assert page_count(tmp_path / "summary.pdf") >= 1
    assert [invoice.big_category_slug_name for invoice in rendered["invoices"]] == ["marchandises", "rfa"]
    assert rendered["center_puchase"].code == "ACF"
    assert rendered["logo"] == ""


@pytest.mark.usefixtures('pdf_domain')
def test_summary_invoice_pdf_sans_facture(tmp_path, make_cct):
    """Aucune facture à imprimer : la page est produite sans logo ni centrale (plus d'IndexError)"""
    make_cct("AF0002")

    summary_invoice_pdf("AF0002", tmp_path / "summary.pdf")

    assert page_count(tmp_path / "summary.pdf") >= 1


@pytest.mark.usefixtures('pdf_domain')
def test_summary_invoice_pdf_centrale_inconnue(tmp_path, make_sale_with_lines, make_signboards_invoices):
    """Enseigne sans centrale fille correspondante : plus de DoesNotExist"""
    sale = make_sale_with_lines([{"vat": "001"}], signboard=make_signboards_invoices("INCONNUE"))

    summary_invoice_pdf(sale.cct_id, tmp_path / "summary.pdf")

    assert page_count(tmp_path / "summary.pdf") >= 1


@pytest.mark.usefixtures('pdf_domain')
def test_invoice_marchandise_pdf_intermediaire_disparu(tmp_path, sale_marchandises, monkeypatch):
    """Un fichier intermédiaire déjà absent n'empêche pas le nettoyage final"""

    class Reader:
        pages: ClassVar[list] = []

        def __init__(self, path):
            pass

    class Writer:
        def addpage(self, page):
            pass

        def write(self, path):
            path.write_bytes(b"%PDF-1.4")

    monkeypatch.setattr(pdf_marchandises, "PdfReader", Reader)
    monkeypatch.setattr(pdf_marchandises, "PdfWriter", Writer)
    for name in ("marchandise_header_invoice_pdf", "marchandise_suppliers_invoice_pdf",
                 "marchandise_details_invoice_pdf", "marchandise_sub_details_invoice_pdf"):
        monkeypatch.setattr(pdf_marchandises, name, lambda uuid_invoice, pdf_path: None)

    invoice_marchandise_pdf(sale_marchandises.uuid_identification, tmp_path / "f.pdf")

    assert sorted(path.name for path in tmp_path.iterdir()) == ["f.pdf", "www"]
