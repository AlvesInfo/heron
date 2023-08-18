# pylint: disable=E0401,C0413,W0718,W0719,W1203
"""
FR : Module d'export des fichier X3 à intégrer dans Sage
EN : X3 file export module to be integrated into Sage
Commentaire:

created at: 2023-08-17
created by: Paulo ALVES

modified at: 2023-08-17
modified by: Paulo ALVES
"""
import os
import sys
import platform
import time

import django

BASE_DIR = r"/"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")

django.setup()

from heron.loggers import LOGGER_X3
from apps.data_flux.trace import get_trace
from apps.invoices.bin.export_x3_odana_invoices import write_odana
from apps.invoices.bin.export_x3_sale_invoices import write_bicpar
from apps.invoices.bin.export_x3_purchase_invoices import write_bispar
from apps.invoices.bin.export_x3_purchase_gdaud_invoices import write_bispar_gdaud


def export_files_x3(export_type, centrale, file_name, nb_fac):
    """
    Export des fichiers X3, pour insertion de la facturation dans Sage
    :param export_type: type d'export odana, sale, purchase, gdaud
    :param file_name: nom du fichier à générer
    :param nb_fac: nombre de factures présentes dans le fichier
    :param centrale: centrale pour laquelle on lance l'export
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
        "purchase": write_bispar,
        "gdaud": write_bispar_gdaud,
    }

    try:
        if export_type not in functions_dict:
            raise Exception(f"la fonction {export_type!r}, n'existe pas !")

        function = functions_dict.get(export_type)
        LOGGER_X3.warning(f"{export_type} - {centrale} - {function}")
        function(centrale, file_name, nbfac)

    except Exception as except_error:
        error = True
        LOGGER_X3.exception(f"Exception Générale : {except_error!r}")

    finally:
        if error:
            trace.errors = True
            trace.comment += trace.comment + (
                f"\n. Une erreur c'est produite pour la fonction ({export_type}) "
                f"d'export du fichier X3 et la centrale {centrale}, "
                f"veuillez consulter les logs"
            )

        trace.time_to_process = start - time.time()
        trace.save()

    return trace, to_print
