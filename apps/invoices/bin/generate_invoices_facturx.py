# pylint: disable=E0401,C0413,R0914,W0718,W1203
"""
FR : Module de génération des factures de ventes au format Factur-X (PDF/A-3 + XML CII)
     via le serveur facturx_server (API de la bibliothèque facturx-fr).
     Une facture Factur-X est produite par facture de vente (SaleInvoice), à partir du
     PDF individuel de la facture régénéré avec les générateurs PDF existants.
EN : Generates Factur-X sales invoices through the facturx_server HTTP API.

Commentaire:

created at: 2026-10-10
created by: Paulo ALVES

modified at: 2026-10-10
modified by: Paulo ALVES
"""
import os
import sys
import platform
import uuid
from pathlib import Path
from typing import AnyStr, Tuple

import django

BASE_DIR = r"/"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")

django.setup()


from django.conf import settings
from django.db.models import Count, Q, QuerySet
from django_celery_results.models import TaskResult

from heron.loggers import LOGGER_INVOICES
from apps.data_flux.trace import get_trace
from apps.invoices.bin.facturx_client import FacturXClient, FacturXClientError
from apps.invoices.bin.facturx_mapping import FacturXMappingError, build_facturx_invoice
from apps.invoices.bin.pdf_marchandises import invoice_marchandise_pdf
from apps.invoices.bin.pdf_rfa import rfa_invoice_pdf
from apps.invoices.bin.pdf_royalties import invoice_royalties_pdf
from apps.invoices.bin.pdf_publicity import invoice_publicity_pdf
from apps.invoices.bin.pdf_prestation import invoice_prestation_pdf
from apps.invoices.bin.pdf_formation import invoice_formation_pdf
from apps.invoices.bin.pdf_staff import invoice_staff_pdf
from apps.invoices.bin.pdf_material import invoice_material_pdf
from apps.invoices.bin.pdf_various import invoice_various_pdf
from apps.invoices.models import SaleInvoice

FACTURX_TASK_NAME = "launch_generate_facturx_invoices"

# Générateurs du PDF individuel de chaque facture, par grande catégorie
GENERATION_PDF_DICT = {
    "marchandises": invoice_marchandise_pdf,
    "rfa": rfa_invoice_pdf,
    "redevances": invoice_royalties_pdf,
    "redevances-de-publicite": invoice_publicity_pdf,
    "formation": invoice_formation_pdf,
    "personnel": invoice_staff_pdf,
    "materiel": invoice_material_pdf,
    "prestation": invoice_prestation_pdf,
    "divers": invoice_various_pdf,
}


def get_facturx_in_progress() -> bool:
    """Renvoi si une génération Factur-X est en cours"""
    return TaskResult.objects.filter(status="STARTED", task_name=FACTURX_TASK_NAME).exists()


def get_facturx_candidates() -> QuerySet:
    """
    Factures de ventes dont le PDF a été produit (printed) et sans Factur-X,
    pour la période de facturation en cours (non finalisée)
    """
    return SaleInvoice.objects.filter(
        final=False, printed=True, type_x3__in=(1, 2)
    ).filter(Q(facturx_file__isnull=True) | Q(facturx_file=""))


def get_facturx_groups():
    """Groupes (cct, fichier pdf global) des factures à produire en Factur-X"""
    return (
        get_facturx_candidates()
        .values("cct", "global_invoice_file")
        .annotate(dcount=Count("cct"))
        .values_list("cct", "global_invoice_file")
        .order_by("cct")
    )


def facturx_file_name(sale: SaleInvoice) -> str:
    """Nom du fichier Factur-X d'une facture"""
    return f"{sale.cct_id}_{sale.big_category_slug_name}_{sale.invoice_number}_facturx.pdf"


def generate_sale_facturx(sale: SaleInvoice, client: FacturXClient) -> Tuple[Path, list]:
    """
    Génère le Factur-X d'une facture de vente
    :param sale: facture de vente (printed=True)
    :param client: client du serveur Factur-X
    :return: (chemin du fichier Factur-X, avertissements)
    """
    generation_pdf = GENERATION_PDF_DICT.get(sale.big_category_slug_name)

    if generation_pdf is None:
        raise FacturXMappingError(
            f"Pas de générateur PDF pour la catégorie {sale.big_category_slug_name!r}"
        )

    invoice, warnings = build_facturx_invoice(sale)

    # PDF individuel de la facture (régénéré dans un fichier temporaire)
    tmp_pdf = Path(settings.PROCESSING_FACTURX_DIR) / f"{uuid.uuid4()}.pdf"

    try:
        generation_pdf(sale.uuid_identification, tmp_pdf)
        pdf_bytes = tmp_pdf.read_bytes()
    finally:
        tmp_pdf.unlink(missing_ok=True)

    facturx_bytes = client.generate(invoice, pdf_bytes, file_name=f"{sale.invoice_number}.pdf")

    file_name = facturx_file_name(sale)
    file_path = Path(settings.SALES_INVOICES_FACTURX_DIR) / file_name
    file_path.write_bytes(facturx_bytes)

    SaleInvoice.objects.filter(pk=sale.pk).update(facturx_file=file_name)

    return file_path, warnings


def invoices_facturx_generation(cct: AnyStr, num_file: AnyStr):
    """
    Génération des Factur-X des factures de ventes d'un cct / fichier pdf global
    :param cct: cct des factures
    :param num_file: nom du fichier pdf global (global_invoice_file)
    :return: (trace, to_print)
    """
    trace = get_trace(
        trace_name="Generate Factur-X invoices",
        file_name=f"Generate Factur-X : {num_file}",
        application_name="invoices_facturx_generation",
        flow_name="facturx_invoices",
        comment="",
    )
    to_print = ""
    errors = []
    warnings_list = []
    generated = 0

    sales_invoices = (
        get_facturx_candidates()
        .filter(cct=cct, global_invoice_file=num_file)
        .select_related("centers", "parties")
        .order_by("big_category_ranking", "invoice_number")
    )

    try:
        client = FacturXClient()

        for sale in sales_invoices:
            try:
                _, warnings = generate_sale_facturx(sale, client)
                generated += 1

                for warning in warnings:
                    warnings_list.append(f"{sale.invoice_number} : {warning}")

            except (FacturXMappingError, FacturXClientError) as error:
                errors.append(f"{sale.invoice_number} : {error}")
                LOGGER_INVOICES.error(
                    f"Factur-X non généré pour la facture {sale.invoice_number} : {error}"
                )

            except Exception as error:
                errors.append(f"{sale.invoice_number} : {error!r}")
                LOGGER_INVOICES.exception(
                    f"Exception Générale Factur-X facture {sale.invoice_number} : {error!r}"
                )

        to_print = f"have generate Factur-X : {num_file} ({generated} factures) - "

    except Exception as except_error:
        errors.append(repr(except_error))
        LOGGER_INVOICES.exception(f"Exception Générale : {except_error!r}")

    finally:
        comments = [f"{generated} Factur-X générés pour {cct} ({num_file})"]

        if warnings_list:
            comments.append("Avertissements :\n" + "\n".join(warnings_list))

        if errors:
            trace.errors = True
            comments.append("Erreurs :\n" + "\n".join(errors))
            comments.append("Une erreur c'est produite veuillez consulter les logs")

        trace.created_numbers_records = generated
        trace.errors_numbers_records = len(errors)
        trace.comment = "\n".join(comments)
        trace.save()

    return trace, to_print


if __name__ == "__main__":
    print(FacturXClient().health())
