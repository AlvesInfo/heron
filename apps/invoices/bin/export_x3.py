"""FR : Module d'export des fichier X3 à intégrer dans Sage.

EN : X3 file export module to be integrated into Sage
Commentaire:

created at: 2023-08-17
created by: Paulo ALVES

modified at: 2023-08-17
modified by: Paulo ALVES
"""

import os
import platform
import sys
import time

import django

BASE_DIR = r"/"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")

django.setup()

from apps.data_flux.trace import get_trace
from apps.invoices.bin.export_x3_odana_invoices import write_odana
from apps.invoices.bin.export_x3_purchase_do_invoices import write_bispar_do
from apps.invoices.bin.export_x3_purchase_gdaud_invoices import write_bispar_gdaud
from apps.invoices.bin.export_x3_purchase_invoices import write_bispard
from apps.invoices.bin.export_x3_purchase_sdoa_invoices import write_bispar_sdoa
from apps.invoices.bin.export_x3_sale_invoices import write_bicpar
from heron.loggers import LOGGER_X3


class ExportX3Error(Exception):
    """Type d'export X3 inconnu."""


def _check_export_type(export_type: str, functions_dict: dict) -> None:
    """ExportX3Error si le type d'export demandé n'a pas de fonction associée."""
    if export_type not in functions_dict:
        raise ExportX3Error(f"la fonction {export_type!r}, n'existe pas !")


def export_files_x3(export_type, centrale, file_name, nb_fac):
    """Export des fichiers X3, pour insertion de la facturation dans Sage.

    :param export_type: type d'export odana, sale, purchase, gdaud
    :param file_name: nom du fichier à générer
    :param nb_fac: nombre de factures présentes dans le fichier
    :param centrale: centrale pour laquelle on lance l'export.
    """
    start = time.time()
    error = False
    trace = get_trace(
        trace_name="Export file X3",
        file_name=file_name,
        application_name="export_files_x3",
        flow_name="export_files_x3",
        comment="",
    )
    to_print = ""

    functions_dict = {
        "odana": write_odana,
        "sale": write_bicpar,
        "purchase": write_bispard,
        "gdaud": write_bispar_gdaud,
        "sdoa": write_bispar_sdoa,
        "do": write_bispar_do,
    }

    try:
        _check_export_type(export_type, functions_dict)

        fonction = functions_dict[export_type]
        fonction(centrale, file_name, nb_fac)

    except Exception:
        error = True
        LOGGER_X3.exception("Exception Générale")

    finally:
        if error:
            trace.errors = True
            trace.comment = (trace.comment or "") + (
                f"\n. Une erreur c'est produite pour la fonction ({export_type}) "
                f"d'export du fichier X3 et la centrale {centrale}, "
                f"veuillez consulter les logs"
            )

        trace.time_to_process = time.time() - start
        trace.save()

    return trace, to_print
