# pylint: disable=E0401,C0413,W1203,R0914,W0718
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

import django

BASE_DIR = r"C:\SitesWeb\heron"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")

django.setup()

import pendulum
from django.utils import timezone
from celery import group
from heron import celery_app

from heron.loggers import LOGGER_EDI
from apps.core.functions.functions_setups import connection, transaction
from apps.data_flux.postgres_save import PostgresKeyError, PostgresTypeError, PostgresDjangoUpsert
from apps.data_flux.trace import get_trace
from apps.users.models import User
from apps.edi.bin.cct_update import update_cct_edi_import
from apps.invoices.bin.pre_controls import control_alls_missings
from apps.invoices.models import SaleInvoice
from apps.invoices.sql_files.sql_invoices_insertions import (
    SQL_FIX_IMPORT_UUID,
    SQL_COMMON_DETAILS,
    SQL_SALES_INVOICES,
    SQL_SALES_DETAILS,
    SQL_CONTROL_SALES_INSERTION,
)
from apps.invoices.bin.columns import COL_SALES_DICT
from apps.invoices.bin.invoives_nums import get_invoice_num
from apps.invoices.loops.mise_a_jour_loop import process_update


def set_fix_uuid(cursor: connection.cursor) -> None:
    """
    Ajout de l'import_uuid_identification, au cas où il en manque
    :param cursor: cursor django pour la db
    :return:
    """
    cursor.execute(SQL_FIX_IMPORT_UUID)


def set_common_details(cursor: connection.cursor) -> None:
    """
    Ajout des détails de factures pour la partie commune
    :param cursor: cursor django pour la db
    :return:
    """
    cursor.execute(SQL_COMMON_DETAILS)


def set_sales_details(cursor: connection.cursor) -> None:
    """
    Ajout des détails de factures de vente
    :param cursor: cursor django pour la db
    :return:
    """
    cursor.execute(SQL_SALES_DETAILS)


def set_file_io(
    file_io: io.StringIO, cursor: connection.cursor, user: User, invoice_date: pendulum.date
) -> None:
    """
    Remplissage du fichier io pour insertion en base des factures de vente
    :param file_io: File StringIo
    :param cursor: cursor django pour la db
    :param user: utilisateur qui a lancé la commande
    :param invoice_date: date de la facture
    :return:
    """
    csv_writer = csv.writer(file_io, delimiter=";", quotechar='"', quoting=csv.QUOTE_ALL)
    cursor.execute(SQL_SALES_INVOICES)

    for i, line in enumerate(cursor.fetchall(), 1):
        invoice_num = get_invoice_num(invoice_date)
        line_to_write = list(line)
        line_to_write[5] = invoice_num
        line_to_write[6] = invoice_num
        line_to_write[8] = invoice_date.isoformat()
        line_to_write[9] = invoice_date.start_of("month").isoformat()
        line_to_write[10] = invoice_date.year
        line_to_write[20] = user.uuid_identification
        line_to_write[21] = user.uuid_identification

        csv_writer.writerow(line_to_write)


def control_sales_insertion(cursor: connection.cursor) -> bool:
    """
    Controle des montants totaux des entêtes factures de ventes par rapport au montant du détail,
    sur les HT, TVA et TTC.
    :param cursor: cursor django pour la db
    :return: False if OK else True
    """
    cursor.execute(SQL_CONTROL_SALES_INSERTION)

    return cursor.fetchone() is not None


def sales_invoices_insertion(
    cursor: connection.cursor, user: User, invoice_date: pendulum.date
) -> AnyStr:
    """
    Inserion des factures en mode provisoire avant la validation définitive
    :param cursor: cursor django pour la db
    :param user: utilisateur qui a lancé la commande
    :param invoice_date: date de la facture
    :return: to_print
    """

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
    comment = (
        f"Facturation de Ventes pour la période : "
        f"{invoice_date.format('MMMM YYYY', locale='fr')}"
    )
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)

    error = False
    file_io = io.StringIO()
    to_print = ""

    try:
        # On met les import_uuid_identification au cas où il en manque
        set_fix_uuid(cursor)

        # On met à jour les éléments pour la facturation
        process_update()

        # On supprime les éxistant non définitifs

        cursor.execute(
            'delete from invoices_invoicecommondetails where ("final" isnull or "final" = false)'
        )

        cursor.execute(
            'delete from invoices_invoicedetail where ("final" isnull or "final" = false)'
        )

        cursor.execute('delete from invoices_invoice where ("final" isnull or "final" = false)')

        cursor.execute(
            'delete from invoices_saleinvoicedetail where ("final" isnull or "final" = false)'
        )

        cursor.execute('delete from invoices_saleinvoice where ("final" isnull or "final" = false)')

        # On insère l'ensemble des données commmunes aux achats et ventes d'edi_ediimport
        set_common_details(cursor)

        # On insère les entêtes de factures de vente
        set_file_io(file_io, cursor, user, invoice_date)

        file_io.seek(0)
        postgres_upsert = PostgresDjangoUpsert(
            model=model,
            fields_dict=COL_SALES_DICT,
            cnx=connection,
            exclude_update_fields={},
        )
        file_io.seek(0)
        postgres_upsert.insertion(
            file=file_io,
            insert_mode="do_nothing",
            delimiter=";",
            quote_character='"',
            kwargs_prepared={"trace": trace},
        )

        # On insère les détails des factures de vente
        set_sales_details(cursor)

        # TODO: PREVOIR DE REMPLIR LA DATE D'ECHEANCE EN FONCTION DU mode_reglement

        # On contrôle l'insertion
        if control_sales_insertion(cursor):
            to_print = (
                "Il y a eu une erreur à l'insertion des factures de vente, "
                "les totaux ne correspondent pas"
            )
            raise Exception("Il y a eu une erreur à l'insertion des factures de vente")

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
        print(trace.time_to_process)
        trace.save()

        try:
            if not file_io.closed:
                file_io.close()
            del file_io

        except (AttributeError, NameError):
            pass

    return to_print


if __name__ == "__main__":
    with connection.cursor() as cur, transaction.atomic():
        utilisateur = User.objects.get(last_name="ALVES")
        to_print_ = sales_invoices_insertion(cur, utilisateur, pendulum.date(2023, 2, 28))

        if to_print_:
            raise Exception("Il y a eu une erreur à l'insertion des factures de vente")
