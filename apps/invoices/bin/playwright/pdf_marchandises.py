# pylint: disable=E0401,C0413
"""
FR : Module de génération des factures de marchandises en pdf (version Playwright)
EN : Module for generating invoices marchandises in pdf (Playwright version)

Commentaire:
    Remplacement de WeasyPrint par Playwright pour la génération de PDF.
    Le pattern est identique, seule la couche de rendu HTML -> PDF change.

created at: 2024-02-10
created by: Paulo ALVES

modified at: 2024-02-10
modified by: Paulo ALVES
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from uuid import UUID
from typing import AnyStr

from django.template.loader import render_to_string
from django.db import connection
from pdfrw import PdfReader, PdfWriter

from apps.invoices.bin.conf import DOMAIN
from apps.invoices.bin.playwright.pdf_utils import html_to_pdf
from apps.invoices.models import SaleInvoice, EnteteDetails
from apps.invoices.sql_files.sql_marchandises import (
    SQL_HEADER,
    SQL_RESUME_HEADER,
    SQL_RESUME_SUPPLIER,
    SQL_DETAILS,
    SQL_SUB_DETAILS,
)


# =========================================================================
# Fonctions de préparation HTML (DB + template) — thread-safe
# =========================================================================

def _prepare_header_html(uuid_invoice: UUID) -> str:
    """Requêtes DB + rendu template pour l'entête de facture."""
    with connection.cursor() as cursor:
        invoices = SaleInvoice.objects.filter(uuid_identification=uuid_invoice)

        cursor.execute(SQL_HEADER, {"uuid_invoice": uuid_invoice})
        columns_header = [col[0] for col in cursor.description]
        headers = [dict(zip(columns_header, row)) for row in cursor.fetchall()]

        cursor.execute(SQL_RESUME_HEADER, {"uuid_invoice": uuid_invoice})
        columns_resume = [col[0] for col in cursor.description]
        resume = [dict(zip(columns_resume, row)) for row in cursor.fetchall()][0]

        context = {
            "invoices": invoices,
            "headers": headers,
            "resume": resume,
            "domain": DOMAIN,
            "logo": str(invoices[0].signboard.logo_signboard).replace("logos/", ""),
        }
        return render_to_string("invoices/pdf_marchandises_header.html", context)


def _prepare_suppliers_html(uuid_invoice: UUID) -> str:
    """Requêtes DB + rendu template pour le récapitulatif fournisseurs."""
    with connection.cursor() as cursor:
        invoices = SaleInvoice.objects.filter(uuid_identification=uuid_invoice)

        cursor.execute(SQL_RESUME_SUPPLIER, {"uuid_invoice": uuid_invoice})
        columns_uppliers = [col[0] for col in cursor.description]
        suppliers = [dict(zip(columns_uppliers, row)) for row in cursor.fetchall()]

        context = {
            "invoices": invoices,
            "suppliers": suppliers,
            "domain": DOMAIN,
            "logo": str(invoices[0].signboard.logo_signboard).replace("logos/", ""),
        }
        return render_to_string("invoices/pdf_marchandises_suppliers.html", context)


def _prepare_details_html(uuid_invoice: UUID) -> str:
    """Requêtes DB + rendu template pour les détails par fournisseur."""
    with connection.cursor() as cursor:
        invoices = SaleInvoice.objects.filter(uuid_identification=uuid_invoice)

        cursor.execute(SQL_DETAILS, {"uuid_invoice": uuid_invoice})
        columns_details = [col[0] for col in cursor.description]
        suppliers = [dict(zip(columns_details, row)) for row in cursor.fetchall()]

        context = {
            "invoices": invoices,
            "entetes": EnteteDetails.objects.all().values("column_name"),
            "suppliers": suppliers,
            "domain": DOMAIN,
            "logo": str(invoices[0].signboard.logo_signboard).replace("logos/", ""),
        }
        return render_to_string("invoices/pdf_marchandises_details.html", context)


def _prepare_sub_details_html(uuid_invoice: UUID) -> str:
    """Requêtes DB + rendu template pour les sous-détails."""
    with connection.cursor() as cursor:
        invoices = SaleInvoice.objects.filter(uuid_identification=uuid_invoice)

        cursor.execute(SQL_SUB_DETAILS, {"uuid_invoice": uuid_invoice})
        columns_sub_details = [col[0] for col in cursor.description]
        sub_details = [dict(zip(columns_sub_details, row)) for row in cursor.fetchall()]

        context = {
            "invoices": invoices,
            "sub_details": sub_details,
            "domain": DOMAIN,
            "logo": str(invoices[0].signboard.logo_signboard).replace("logos/", ""),
        }
        return render_to_string("invoices/pdf_marchandises_sub_details.html", context)


# =========================================================================
# Fonctions publiques de génération PDF (DB + template + Playwright)
# =========================================================================

def marchandise_header_invoice_pdf(uuid_invoice: UUID, pdf_path: Path) -> None:
    """Génération de l'entête de facture marchandises."""
    content = _prepare_header_html(uuid_invoice)
    html_to_pdf(content, pdf_path)


def marchandise_suppliers_invoice_pdf(uuid_invoice: UUID, pdf_path: Path) -> None:
    """Génération du récapitulatif par fournisseurs."""
    content = _prepare_suppliers_html(uuid_invoice)
    html_to_pdf(content, pdf_path)


def marchandise_details_invoice_pdf(uuid_invoice: UUID, pdf_path: Path) -> None:
    """Génération des détails par fournisseurs."""
    content = _prepare_details_html(uuid_invoice)
    html_to_pdf(content, pdf_path)


def marchandise_sub_details_invoice_pdf(uuid_invoice: UUID, pdf_path: Path) -> None:
    """Génération des sous-détails de marchandises."""
    content = _prepare_sub_details_html(uuid_invoice)
    html_to_pdf(content, pdf_path)


# =========================================================================
# Orchestrateur avec parallélisation
# =========================================================================

def _prepare_html_in_thread(name, prepare_func, uuid_invoice):
    """Exécute la préparation HTML dans un thread worker.

    Django utilise des connexions DB thread-local, chaque thread obtient
    automatiquement sa propre connexion. On force la fermeture en sortie
    pour éviter les connexions orphelines.
    """
    try:
        html_content = prepare_func(uuid_invoice)
    finally:
        connection.close()
    return name, html_content


def invoice_marchandise_pdf(uuid_invoice: UUID, pdf_path: AnyStr) -> None:
    """
    Génération des pages de marchandises avec parallélisation.

    L'API sync de Playwright utilise des greenlets liés au thread créateur :
    on ne peut pas appeler page.pdf() depuis un thread différent.

    Stratégie en 2 phases :
      Phase 1 — Threads : requêtes DB + render_to_string en parallèle (I/O bound)
      Phase 2 — Thread principal : génération PDF Playwright séquentielle

    :param uuid_invoice: uuid_identification de la facture
    :param pdf_path: Path du fichier pdf
    """
    prepare_steps = [
        ("header", _prepare_header_html),
        ("suppliers", _prepare_suppliers_html),
        ("details", _prepare_details_html),
        ("sub_details", _prepare_sub_details_html),
    ]

    # Phase 1 : Préparation HTML en parallèle (DB + templates)
    html_contents = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(
                _prepare_html_in_thread, name, func, uuid_invoice
            ): name
            for name, func in prepare_steps
        }
        for future in as_completed(futures):
            name, html_content = future.result()
            html_contents[name] = html_content

    # Phase 2 : Génération PDF séquentielle (Playwright, thread principal)
    files_list = []
    for name, _ in prepare_steps:
        pdf_path_name = Path(str(pdf_path)[:-4] + f"_{name}.pdf")
        html_to_pdf(html_contents[name], pdf_path_name)
        files_list.append(pdf_path_name)

    # Phase 3 : Fusion dans l'ordre (header → suppliers → details → sub_details)
    writer = PdfWriter()
    for pdf_file in files_list:
        reader = PdfReader(pdf_file)
        for page in reader.pages:
            writer.addpage(page)

    writer.write(pdf_path)

    for file in files_list:
        if file.is_file():
            file.unlink()


if __name__ == "__main__":
    from django.conf import settings

    uuid_invoice_to_pdf = UUID("8b4ac234-e03e-4ac6-bf9e-491a40cab635")
    sale = SaleInvoice.objects.get(uuid_identification=uuid_invoice_to_pdf)

    header_path = Path(settings.SALES_INVOICES_FILES_DIR) / f"{sale.cct}_header_marchandise.pdf"
    marchandise_header_invoice_pdf(uuid_invoice=uuid_invoice_to_pdf, pdf_path=header_path)

    supplier_path = (
        Path(settings.SALES_INVOICES_FILES_DIR) / f"{sale.cct}_supplier_marchandise.pdf"
    )
    marchandise_suppliers_invoice_pdf(uuid_invoice=uuid_invoice_to_pdf, pdf_path=supplier_path)

    details_path = (
        Path(settings.SALES_INVOICES_FILES_DIR) / f"{sale.cct}_details_marchandise.pdf"
    )
    marchandise_details_invoice_pdf(uuid_invoice=uuid_invoice_to_pdf, pdf_path=details_path)

    sub_path = Path(settings.SALES_INVOICES_FILES_DIR) / f"{sale.cct}_sub_marchandise.pdf"
    marchandise_sub_details_invoice_pdf(uuid_invoice=uuid_invoice_to_pdf, pdf_path=sub_path)

    sub_path = (
        Path(settings.SALES_INVOICES_FILES_DIR) / f"{sale.cct}_{sale.invoice_number}.pdf"
    )
    invoice_marchandise_pdf(uuid_invoice=uuid_invoice_to_pdf, pdf_path=sub_path)