# pylint: disable=E0401,W0621,C0415
"""
FR : Aides aux tests de génération PDF de l'app invoices (jeu de données facture + lignes,
     domaine statique local pour WeasyPrint, PDF minimal, lecture du nombre de pages)
EN : Helpers for invoices PDF tests

Importées explicitement par les modules de tests : `from apps.invoices.tests.helpers_pdf import *`
"""
import datetime
import shutil
from decimal import Decimal
from pathlib import Path
from typing import Any
from collections.abc import Callable
from uuid import uuid4

import pytest
from pdfrw import PdfReader
from weasyprint import HTML


STATIC_FILES = ["logo_heron_01.png", "ClanBook.otf", "ClanMedium.otf", "ClanThin.otf"]

# Entêtes de détails référencées par SQL_DETAILS (colonnes MO, MS, VE, ...)
ENTETES = {
    "OPT": "MONTURES OPTIQUES",
    "SOL": "MONTURES SOLAIRES",
    "VER": "VERRES",
    "COT": "CONTACTO - SOLUTIONS",
    "AUD": "AIDES AUDITIVES",
    "PIL": "PILES",
    "ACA": "ACCESSOIRES AUDIO",
    "ACO": "ACCESSOIRES OPTIQUE",
    "CON": "CONSOMMABLES",
    "POR": "PORT ET EMBALLAGE",
    "DIV": "DIVERS",
}


def page_count(pdf_path) -> int:
    """Nombre de pages d'un fichier PDF"""
    return len(PdfReader(str(pdf_path)).pages)


def write_minimal_pdf(path, text: str = "test") -> Path:
    """Écrit un PDF valide d'une page (sert de sortie aux générateurs simulés)"""
    HTML(string=f"<p>{text}</p>").write_pdf(str(path))
    return Path(path)


@pytest.fixture
def pdf_domain(tmp_path, settings) -> str:
    """
    Domaine local (file://) servant les statiques aux templates WeasyPrint : pas d'accès réseau,
    logos et polices résolus depuis une copie de files/static dans tmp_path.
    """
    static_dir = tmp_path / "www" / "static"
    static_dir.mkdir(parents=True)
    source = Path(settings.STATIC_ROOT)

    for name in STATIC_FILES:
        if (source / name).is_file():
            shutil.copy(source / name, static_dir / name)

    domain = (tmp_path / "www").as_uri()
    settings.PDF_STATIC_DOMAIN = domain
    return domain


@pytest.fixture
def sales_dir(invoices_dirs, settings):
    """Le répertoire des pdf de ventes lu par les modules via django.conf.settings -> tmp_path"""
    settings.SALES_INVOICES_FILES_DIR = invoices_dirs.sales
    return invoices_dirs.sales


@pytest.fixture
def make_sale_with_lines(
    make_sale_invoice, make_invoice_common_details, make_society,
    make_axes_details, make_child_center,
) -> Callable[..., Any]:
    """
    Fabrique une facture de vente et ses lignes : chaque ligne crée un couple
    SaleInvoiceDetail / InvoiceCommonDetails partageant import_uuid_identification.
    `lines` : liste de dicts, clés optionnelles : supplier (tiers), invoice_number (facture
    fournisseur), delivery_number, delivery_date, axe (code ENTETES), vat ("001"/"002"/"003"),
    vat_rate, net_amount, grouping_goods, base, reference, libelle, qty, client_name,
    serial_number, supplier_initial_libelle, personnel_type, command_reference, first_name,
    last_name, initial_date, final_date, heures_formation, unit_weight, sub_category, axe_prj,
    axe_prj_name, axe_rfa.
    """
    from apps.invoices.models import AxesDetails, SaleInvoiceDetail

    make_child_center("ACF")

    def _factory(lines=None, slug: str = "marchandises", **sale_kwargs):
        sale_defaults = {"big_category_slug_name": slug, "big_category": slug.capitalize()}
        sale_defaults.update(sale_kwargs)
        sale = make_sale_invoice(**sale_defaults)

        for line in lines or []:
            axe = line.get("axe", "OPT")

            if not AxesDetails.objects.filter(axe_pro__section=axe).exists():
                make_axes_details(section=axe, column_name=ENTETES.get(axe, axe))
            import_uuid = uuid4()
            supplier = line.get("supplier", "FOUR001")
            make_society(supplier, is_client=False, invoice_entete=line.get("invoice_entete"))
            common_kwargs = {
                "import_uuid_identification": import_uuid,
                "invoice_date": line.get("invoice_date", datetime.date(2026, 1, 10)),
                "delivery_number": line.get("delivery_number", "BL1"),
                "delivery_date": line.get("delivery_date", datetime.date(2026, 1, 8)),
                "reference_article": line.get("reference", "ART-1"),
                "libelle": line.get("libelle", "Monture test"),
                "supplier_initial_libelle": line.get("supplier_initial_libelle", "Libellé fournisseur"),
                "qty": line.get("qty", Decimal("1")),
                "client_name": line.get("client_name"),
                "serial_number": line.get("serial_number"),
                "command_reference": line.get("command_reference", "CMD1"),
                "first_name": line.get("first_name"),
                "last_name": line.get("last_name"),
                "initial_date": line.get("initial_date"),
                "final_date": line.get("final_date"),
                "heures_formation": line.get("heures_formation"),
                "unit_weight": line.get("unit_weight", "U"),
                "cct": sale.cct,
            }
            if line.get("personnel_type") is not None:
                common_kwargs["personnel_type"] = line["personnel_type"]
            make_invoice_common_details(
                third_party_num=supplier,
                invoice_number=line.get("invoice_number", "FF-1"),
                **common_kwargs,
            )
            vat = line.get("vat", "001")
            vat_rate = line.get("vat_rate", {"001": Decimal("0.2"), "002": Decimal("0.055")}.get(vat, Decimal("0")))
            net_amount = Decimal(str(line.get("net_amount", "100")))
            vat_amount = (net_amount * vat_rate).quantize(Decimal("0.01"))
            SaleInvoiceDetail.objects.create(
                uuid_invoice=sale,
                import_uuid_identification=import_uuid,
                axe_bu="CAHA",
                axe_pys="FR",
                axe_pro=axe,
                axe_prj=line.get("axe_prj", "NAF"),
                axe_prj_name=line.get("axe_prj_name"),
                axe_rfa=line.get("axe_rfa", "NAF"),
                vat=vat,
                vat_rate=vat_rate,
                vat_regime="FRA",
                big_category="Marchandises",
                sub_category=line.get("sub_category"),
                base=line.get("base", "Marchandises"),
                grouping_goods=line.get("grouping_goods", "MONTURES OPTIQUES"),
                ranking=line.get("ranking", 1),
                account="707000",
                account_od_600="607000",
                net_unit_price=net_amount,
                net_amount=net_amount,
                vat_amount=vat_amount,
                amount_with_vat=net_amount + vat_amount,
            )

        return sale

    return _factory

