from pathlib import Path
import pendulum
from django.shortcuts import render, HttpResponse

from heron.loggers import LOGGER_VIEWS
from heron.settings import MEDIA_EXCEL_FILES_DIR

from apps.core.functions.functions_http_response import (
    response_file,
    CONTENT_TYPE_EXCEL,
)
from apps.validation_purchases.excel_outputs.output_excel_purchases_edi_import import (
    excel_heron_purchases_edi_import,
    csv_heron_purchases_edi_import,
)

# CONTROLES ETAPE 6.0 - Contrôles des achats importés


def suppliers_edi_purchases(request):
    """View de l'étape 6.0 - Contrôle des achats fournisseurs intégrés"""
    context = {
        "titre_table": "6.0 - Export des achats fichiers fournisseurs intégrés",
    }

    return render(request, "validation_purchases/heron_purchases_edi.html", context=context)


def edi_import_purchases_export(request):
    """View de l'étape 6.0 Héron dans edi imports

    Export Excel des achats Héron dans edi imports
    :param request: Request Django
    :return: response_file
    """
    try:
        today = pendulum.now()
        file_name = f"FACTURES FOURNISSEURS_{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"

        return response_file(excel_heron_purchases_edi_import, file_name, CONTENT_TYPE_EXCEL)

    except:
        LOGGER_VIEWS.exception("view : edi_import_purchases_export")

    context = {"titre_table": "6.0 - Export des achats fichiers fournisseurs intégrés"}

    return render(request, "validation_purchases/heron_purchases_edi.html", context=context)


def edi_import_purchases_export_csv(request):
    """View de l'étape 6.0 Héron dans edi imports

    Export Excel des achats Héron dans edi imports
    :param request: Request Django
    :return: response_file
    """
    try:
        today = pendulum.now()
        file_name = f"FACTURES FOURNISSEURS_{today.format('Y_M_D')}_{today.int_timestamp}.csv"
        emplacement = Path(MEDIA_EXCEL_FILES_DIR) / file_name

        if emplacement.is_file():
            emplacement.unlink()

        with emplacement.open("w"):
            # creation du fichier
            ...

        csv_heron_purchases_edi_import(emplacement)

        with open(emplacement, 'r') as f:
            file_data = f.read()

            response = HttpResponse(file_data, content_type='application/vnd.ms-excel')
            response['Content-Disposition'] = f'attachment; filename="{emplacement.name}"'

        return response

    except:
        LOGGER_VIEWS.exception("view : edi_import_purchases_export")

    context = {"titre_table": "6.0 - Export des achats fichiers fournisseurs intégrés"}

    return render(request, "validation_purchases/heron_purchases_edi.html", context=context)
