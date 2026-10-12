"""Vues de l'étape 6.0 de la validation des achats : exports des imports EDI fournisseurs."""

from pathlib import Path

import pendulum
from django.conf import settings
from django.http import FileResponse
from django.shortcuts import render

from apps.core.functions.functions_http_response import (
    CONTENT_TYPE_CSV,
    CONTENT_TYPE_EXCEL,
    response_file,
)
from apps.validation_purchases.excel_outputs.output_excel_purchases_edi_import import (
    csv_heron_purchases_edi_import,
    excel_heron_purchases_edi_import,
)
from heron.loggers import LOGGER_VIEWS

# CONTROLES ETAPE 6.0 - Contrôles des achats importés


def suppliers_edi_purchases(request):
    """View de l'étape 6.0 - Contrôle des achats fournisseurs intégrés."""
    context = {
        "titre_table": "6.0 - Export des achats fichiers fournisseurs intégrés",
    }

    return render(request, "validation_purchases/heron_purchases_edi.html", context=context)


def edi_import_purchases_export(request):
    """View de l'étape 6.0 Héron dans edi imports.

    Export Excel des achats Héron dans edi imports
    :param request: Request Django
    :return: response_file
    """
    try:
        today = pendulum.now()
        file_name = f"FACTURES FOURNISSEURS_{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"

        return response_file(excel_heron_purchases_edi_import, file_name, CONTENT_TYPE_EXCEL)

    except Exception:
        LOGGER_VIEWS.exception("view : edi_import_purchases_export")

    context = {"titre_table": "6.0 - Export des achats fichiers fournisseurs intégrés"}

    return render(request, "validation_purchases/heron_purchases_edi.html", context=context)


def edi_import_purchases_export_csv(request):
    """View de l'étape 6.0 Héron dans edi imports.

    Export Excel des achats Héron dans edi imports
    :param request: Request Django
    :return: response_file
    """
    try:
        file_name = "FACTURES FOURNISSEURS.csv"
        emplacement = Path(settings.MEDIA_EXCEL_FILES_DIR) / file_name
        csv_heron_purchases_edi_import(emplacement)

        return FileResponse(
            emplacement.open("rb"),
            filename=emplacement.name,
            as_attachment=True,
            content_type=CONTENT_TYPE_CSV,
        )

    except Exception:
        LOGGER_VIEWS.exception("view : edi_import_purchases_export")

    context = {"titre_table": "6.0 - Export des achats fichiers fournisseurs intégrés"}

    return render(request, "validation_purchases/heron_purchases_edi.html", context=context)
