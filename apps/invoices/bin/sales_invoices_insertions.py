# pylint: disable=E0401
"""
FR : Module d'insertion provisoire
EN : Provisional insert module

Commentaire:

created at: 2023-03-11
created by: Paulo ALVES

modified at: 2023-03-11
modified by: Paulo ALVES
"""
from typing import AnyStr
import io
import os
import platform
import sys
import csv
import time

import django
from django.db import connection
from django.utils import timezone
from celery import group
from heron import celery_app

BASE_DIR = r"C:\SitesWeb\heron"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")
django.setup()

from heron.loggers import LOGGER_EDI
from apps.core.functions.functions_setups import connection
from apps.data_flux.postgres_save import PostgresKeyError, PostgresTypeError, PostgresDjangoUpsert
from apps.data_flux.trace import get_trace
from apps.edi.bin.cct_update import update_cct_edi_import
from apps.invoices.bin.pre_controls import control_alls_missings
from apps.invoices.models import SaleInvoice
from apps.invoices.bin.columns import COL_SALES_DICT


def set_file_io(file_io: io.StringIO, cursor: connection.cursor):
    """
    Remplissage du fichier io pour insertion en base des factures de vente
    :param file_io: File StringIo
    :param cursor: cursor django pour la db
    :return:
    """

    csv_writer = csv.writer(
        file_io, delimiter=";", quotechar='"', quoting=csv.QUOTE_ALL
    )

    for i, line in enumerate(csv_reader, 1):

        csv_writer.writerow(line)


def sales_invoices_insertion():
    """Inserion des factures en mode provisoire avant la validation définitive"""

    with connection.cursor() as cursor:
        # On update dabord les cct puis les centre et enseignes
        update_cct_edi_import()

        # Pré-contrôle des données avant insertion
        controls = control_alls_missings()

        if controls:
            # TODO : FAIRE LE PRE CONTROLE QUAND TOUS LE PROCESS EST TERMINE
            # Renvoyer une erreur si le pré-cotrôle n'est pas vide
            ...

        model = SaleInvoice
        file_name = "select ..."
        trace_name = "Insertion des factures de vente"
        application_name = "sales_invoices_insertion"
        flow_name = "Sales_Inseertion"
        comment = ""
        trace = get_trace(trace_name, file_name, application_name, flow_name, comment)

        error = False
        valide_file_io = io.StringIO()
        to_print = ""

        try:
            postgres_upsert = PostgresDjangoUpsert(
                model=model,
                fields_dict=COL_SALES_DICT,
                cnx=connection,
                exclude_update_fields={},
            )
            valide_file_io.seek(0)
            postgres_upsert.insertion(
                file=valide_file_io,
                insert_mode="insert",
                delimiter=";",
                quote_character='"',
                kwargs_prepared={"trace": trace},
            )

        # Exceptions PostgresDjangoUpsert ==========================================================
        except PostgresKeyError as except_error:
            error = True
            LOGGER_EDI.exception(f"PostgresKeyError : {except_error!r}")

        except PostgresTypeError as except_error:
            error = True
            LOGGER_EDI.exception(f"PostgresTypeError : {except_error!r}")

        # Exception Générale =======================================================================
        except Exception as except_error:
            error = True
            LOGGER_EDI.exception(f"Exception Générale : {except_error!r}")

        finally:
            if error:
                trace.errors = True
                trace.comment = (
                    trace.comment + "\n. Une erreur c'est produite veuillez consulter les logs"
                )

            trace.time_to_process = (timezone.now() - trace.created_at).total_seconds()
            trace.save()

            try:
                if not valide_file_io.closed:
                    valide_file_io.close()
                del valide_file_io

            except (AttributeError, NameError):
                pass

        return to_print
