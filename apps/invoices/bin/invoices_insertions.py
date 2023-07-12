# pylint: disable=E0401,C0413,W1203,R0914,W0718,R0915,W0719
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
from pathlib import Path
from uuid import UUID

import django

BASE_DIR = r"C:\SitesWeb\heron"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")

django.setup()

import pendulum
from django.conf import settings
from django.utils import timezone
from django.db.models import Count

from heron.loggers import LOGGER_EDI, LOGGER_INVOICES
from apps.core.bin.echeances import get_payment_method_elements, get_due_date
from apps.core.functions.functions_setups import connection, transaction
from apps.data_flux.postgres_save import PostgresKeyError, PostgresTypeError, PostgresDjangoUpsert
from apps.data_flux.trace import get_trace
from apps.users.models import User
from apps.edi.bin.cct_update import update_cct_edi_import
from apps.invoices.bin.pre_controls import control_alls_missings
from apps.invoices.models import Invoice, SaleInvoice
from apps.parameters.bin.generic_nums import get_generic_cct_num
from apps.data_flux.models import Trace
from apps.invoices.sql_files.sql_invoices_insertions import (
    SQL_FIX_ARTICLES,
    SQL_FIX_IMPORT_UUID,
    SQL_COMMON_DETAILS,
    SQL_PURCHASES_INVOICES,
    SQL_PURCHASE_FOR_EXPORT_X3,
    SQL_PURCHASES_DETAILS,
    SQL_PURCHASE_DETAILS_FOR_EXPORT_X3,
    SQL_CONTROL_PURCHASES_INSERTION,
    SQL_CLEAR_INVOICES_SIGNBOARDS,
    SQL_SALES_INVOICES,
    SQL_SALES_FOR_EXPORT_X3,
    SQL_SALES_DETAILS,
    SQL_CONTROL_SALES_INSERTION,
)
from apps.invoices.bin.columns import COLS_PURCHASE_DICT, COL_SALES_DICT
from apps.invoices.bin.invoives_nums import get_purchase_num, get_invoice_num
from apps.invoices.loops.mise_a_jour_loop import process_update
from apps.centers_purchasing.bin.update_account_article import update_axes_edi
from apps.parameters.models import CounterNums


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


def set_purchases_invoices(
    cursor: connection.cursor, user: User, invoice_date_iso: AnyStr
) -> [bool, AnyStr]:
    """
    Remplissage du fichier io pour insertion en base des factures de vente
    :param cursor: cursor django pour la db
    :param user: utilisateur qui a lancé la commande
    :param invoice_date_iso: mois d'intégration de la facture au format isoformat
    :return:
    """
    integration_month = pendulum.parse(invoice_date_iso).date().start_of("month").isoformat()
    model = Invoice
    file_name = "select ..."
    trace_name = "Insertion des factures d'achat"
    application_name = "purchasess_invoices_insertion"
    flow_name = "Purchases_Insertion"
    comment = "Factures d'Achat"
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    error = False
    file_io = io.StringIO()
    to_print = ""

    # On initialise le cache de la fonction qui renvoie les modes de paiements
    get_payment_method_elements.cache_clear()

    try:
        csv_writer = csv.writer(file_io, delimiter=";", quotechar='"', quoting=csv.QUOTE_ALL)
        cursor.execute(SQL_PURCHASES_INVOICES)

        for line in cursor.fetchall():
            *line_to_write, auuid = list(line)
            # invoice_sage_number
            line_to_write[5] = (
                f"{line_to_write[15]}"
                f"{str(line_to_write[10])[-2:]}"
                f"{str(line_to_write[8].month).zfill(2)}"
                f"{get_purchase_num()}"
            )[-20:]
            # print(get_due_date(str(line_to_write[8]), auuid))
            # date_echeance
            line_to_write[17] = get_due_date(str(line_to_write[8]), auuid)
            # created_by
            line_to_write[25] = user.uuid_identification
            # modified by
            line_to_write[26] = user.uuid_identification
            # Mois d'intégration = période de facturation
            line_to_write[29] = integration_month
            # print(line_to_write)
            # print(dict(zip(COLS_PURCHASE_DICT, line_to_write)))

            csv_writer.writerow(line_to_write)

        file_io.seek(0)
        postgres_upsert = PostgresDjangoUpsert(
            model=model,
            fields_dict=COLS_PURCHASE_DICT,
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

    return error, to_print


def set_sales_invoices(
    cursor: connection.cursor, user: User, invoice_date_iso: AnyStr
) -> [bool, AnyStr]:
    """
    Remplissage du fichier io pour insertion en base des factures de vente
    :param cursor: cursor django pour la db
    :param user: utilisateur qui a lancé la commande
    :param invoice_date_iso: date de la facture au format isoformat
    :return:
    """
    invoice_date = pendulum.parse(invoice_date_iso).date()
    model = SaleInvoice
    file_name = "select ..."
    trace_name = "Insertion des factures de vente"
    application_name = "sales_invoices_insertion"
    flow_name = "Sales_Insertion"
    comment = (
        f"Facturation de Ventes pour la période : "
        f"{invoice_date.format('MMMM YYYY', locale='fr')}"
    )
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    error = False
    file_io = io.StringIO()
    to_print = ""

    try:
        csv_writer = csv.writer(file_io, delimiter=";", quotechar='"', quoting=csv.QUOTE_ALL)
        cursor.execute(SQL_CLEAR_INVOICES_SIGNBOARDS)
        cursor.execute(SQL_SALES_INVOICES)

        for line in cursor.fetchall():
            invoice_num = get_invoice_num(invoice_date)
            line_to_write = list(line)
            line_to_write[5] = invoice_num
            line_to_write[6] = f"{str(line[34])}{invoice_num}"
            line_to_write[8] = invoice_date.isoformat()
            line_to_write[9] = invoice_date.start_of("month").isoformat()
            line_to_write[10] = invoice_date.year
            line_to_write[20] = user.uuid_identification
            line_to_write[21] = user.uuid_identification

            csv_writer.writerow(line_to_write)

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

    return error, to_print


def control_purchases_insertion(cursor: connection.cursor) -> bool:
    """
    Controle des montants totaux des entêtes factures de ventes par rapport au montant du détail,
    sur les HT, TVA et TTC.
    :param cursor: cursor django pour la db
    :return: False if OK else True
    """
    cursor.execute(SQL_CONTROL_PURCHASES_INSERTION)

    return cursor.fetchone() is not None


def control_sales_insertion(cursor: connection.cursor) -> bool:
    """
    Controle des montants totaux des entêtes factures de ventes par rapport au montant du détail,
    sur les HT, TVA et TTC.
    :param cursor: cursor django pour la db
    :return: False if OK else True
    """
    cursor.execute(SQL_CONTROL_SALES_INSERTION)

    return cursor.fetchone() is not None


def num_full_sales_invoices():
    """Insertion des numérotaions full par cct"""

    sales_list = (
        SaleInvoice.objects.filter(final=False, type_x3__in=(1, 2))
        .values("cct")
        .annotate(dcount=Count("cct"))
        .order_by()
    )

    cct = sales_list[0].get("cct")
    global_invoice_file = f"{get_generic_cct_num(cct)}_full.pdf"

    for line_dict in sales_list:
        cct_query = line_dict.get("cct")

        if cct_query != cct:
            cct = cct_query
            global_invoice_file = f"{get_generic_cct_num(cct)}_full.pdf"

        SaleInvoice.objects.filter(cct=cct, final=False, type_x3__in=(1, 2)).update(
            global_invoice_file=global_invoice_file
        )


def delete_pdf_files(cursor: connection.cursor) -> bool:
    """
    Supprime les fichiers pdf, des factures devant être supprimées
    :param cursor: cursor django pour la db
    :return: False if OK else True
    """
    sql_pdf_delete = """
    select 
        global_invoice_file
    from invoices_saleinvoice
    where "final" = false
    group by global_invoice_file
    """
    cursor.execute(sql_pdf_delete)

    for file in cursor.fetchall():
        file_path = Path(settings.SALES_INVOICES_FILES_DIR) / file[0]

        if file_path.is_file():
            file_path.unlink()


def reinitialize_purchase_invoices_nums(cursor: connection.cursor) -> bool:
    """
    Réinitialise la numérotation des factures de d'achat après suppressions
    :param cursor: cursor django pour la db
    :return: False if OK else True
    """
    sql_initialize = """
    select 
        max(
            right(
                "invoice_sage_number",
                (
                    select 
                        "lpad_num" 
                    from "parameters_counter" "pc" 
                    where "uuid_identification" = 'ad95c27f-9800-46d4-8e63-55191023f0a4'::uuid
                )
            )::int
        ) + 1 as "nums"
    from "invoices_invoice"
    """
    cursor.execute(sql_initialize)
    LOGGER_INVOICES.warning(rf"{str([r for r in cursor.fetchall()])}")
    LOGGER_INVOICES.warning(rf"{cursor.mogrify(sql_initialize, {}).decode()}")
    num = (cursor.fetchone())[0]
    LOGGER_INVOICES.warning(rf"{str(num)}")
    try:
        numerotation = CounterNums.objects.get(
            counter__uuid_identification=UUID("ad95c27f-9800-46d4-8e63-55191023f0a4")
        )
        numerotation.num = num
        numerotation.save()

    except CounterNums.DoesNotExist:
        pass


def reinitialize_sales_invoices_nums(cursor: connection.cursor) -> bool:
    """
    Réinitialise la numérotation des factures de ventes après suppressions
    :param cursor: cursor django pour la db
    :return: False if OK else True
    """
    sql_initialize = """
    select 
        max(
            right(
                "invoice_number",
                (
                    select 
                        "lpad_num" 
                    from "parameters_counter" "pc" 
                    where "uuid_identification" = '8aad17a2-90a8-4a72-a8c6-caccdadf5a8b'::uuid
                )
            )::int
        ) + 1 as "nums"
    from "invoices_saleinvoice"
    """
    cursor.execute(sql_initialize)

    num = (cursor.fetchone())[0]

    try:
        numerotation = CounterNums.objects.get(
            counter__uuid_identification=UUID("8aad17a2-90a8-4a72-a8c6-caccdadf5a8b")
        )
        numerotation.num = num
        numerotation.save()

    except CounterNums.DoesNotExist:
        pass


def invoices_insertion(user_uuid: User, invoice_date: pendulum.date) -> (Trace.objects, AnyStr):
    """
    Inserion des factures en mode provisoire avant la validation définitive
    :param user_uuid: utilisateur qui a lancé la commande
    :param invoice_date: date de la facture
    :return: to_print
    """
    start = time.time()
    trace = get_trace(
        f"Insertion de la facturation : {invoice_date}",
        "insertion par fonction",
        "invoices_insertion",
        "Invoices_Insertion",
        "",
    )

    # On update dabord les cct puis les centrales et enseignes
    update_cct_edi_import()
    print(f"update_cct_edi_import :{time.time()-start} s")
    start = time.time()

    # Pré-contrôle des données avant insertion
    controls = control_alls_missings()
    print(f"control_alls_missings :{time.time()-start} s")
    start = time.time()

    if controls:
        # TODO : FAIRE LE PRE CONTROLE QUAND TOUS LE PROCESS EST TERMINE
        # Renvoyer une erreur si le pré-contrôle n'est pas vide
        ...

    alls_print = ""

    try:
        with connection.cursor() as cursor, transaction.atomic():
            LOGGER_INVOICES.warning(r"Prépartifs insertion des factures")
            # On met les import_uuid_identification au cas où il en manque
            set_fix_uuid(cursor)
            print(f"set_fix_uuid :{time.time()-start} s")
            start = time.time()

            # Mise à jour des articles
            cursor.execute(SQL_FIX_ARTICLES)

            # Mise à jour des CentersInvoices, SignboardsInvoices et PartiesInvoices avant insertion
            process_update()

            # On supprime les factures pdf dont les factures sont à "final" = false
            delete_pdf_files(cursor)

            print(f"process_update :{time.time()-start} s")
            start = time.time()

            # On supprime les éxistant non définitifs
            cursor.execute(
                "delete from invoices_invoicecommondetails "
                'where ("final" isnull or "final" = false)'
            )

            cursor.execute(
                'delete from invoices_invoicedetail where ("final" isnull or "final" = false)'
            )

            cursor.execute('delete from invoices_invoice where ("final" isnull or "final" = false)')

            cursor.execute(
                'delete from invoices_saleinvoicedetail where ("final" isnull or "final" = false)'
            )

            cursor.execute(
                'delete from invoices_saleinvoice where ("final" isnull or "final" = false)'
            )
            # On réinitialise les compteurs de numérotation, pour qu'il n'y ai pas de décalages
            reinitialize_purchase_invoices_nums(cursor)
            reinitialize_sales_invoices_nums(cursor)

            print(f"suppression :{time.time()-start} s")
            start = time.time()

            # Mise à jour des articles de la table edi_ediimport avec les axes de la table articles
            update_axes_edi()
            print(f"update_axes_edi :{time.time()-start} s")
            start = time.time()

            # On insère l'ensemble des données commmunes aux achats et ventes d'edi_ediimport
            set_common_details(cursor)
            print(f"set_common_details :{time.time()-start} s")
            start = time.time()

            user = User.objects.get(uuid_identification=user_uuid)

            # On insère les factures d'achats
            LOGGER_INVOICES.warning(r"Insertion des factures d'achat")
            error, to_print = set_purchases_invoices(cursor, user, invoice_date)
            print(f"set_purchases_invoices :{time.time()-start} s")
            start = time.time()

            if error:
                raise Exception

            alls_print += to_print
            cursor.execute(SQL_PURCHASE_FOR_EXPORT_X3)
            cursor.execute(SQL_PURCHASES_DETAILS)
            cursor.execute(SQL_PURCHASE_DETAILS_FOR_EXPORT_X3)

            # On contrôle l'insertion des achats
            LOGGER_INVOICES.warning(r"Contrôle des factures de vente")
            if control_sales_insertion(cursor):
                alls_print = (
                    "Il y a eu une erreur à l'insertion des factures d'achat, "
                    "les totaux ne correspondent pas"
                )
                raise Exception("Il y a eu une erreur à l'insertion des factures de vente")

            print(f"control_sales_insertion :{time.time()-start} s")
            start = time.time()

            # On insère les entêtes de factures de vente
            error, to_print = set_sales_invoices(cursor, user, invoice_date)

            if error:
                raise Exception

            print(f"set_sales_invoices :{time.time()-start} s")
            start = time.time()
            alls_print += to_print
            cursor.execute(SQL_SALES_FOR_EXPORT_X3)

            # On insère les détails des factures de vente
            LOGGER_INVOICES.warning(r"Insertion des détails des factures de vente")
            set_sales_details(cursor)

            print(f"set_sales_details :{time.time()-start} s")
            start = time.time()

            # TODO: PREVOIR DE REMPLIR LA DATE D'ECHEANCE EN FONCTION DU mode_reglement

            # On contrôle l'insertion
            LOGGER_INVOICES.warning(r"Contrôle des factures de vente")
            if control_sales_insertion(cursor):
                alls_print = (
                    "Il y a eu une erreur à l'insertion des factures de vente, "
                    "les totaux ne correspondent pas"
                )
                raise Exception("Il y a eu une erreur à l'insertion des factures de vente")

            print(f"control_sales_insertion :{time.time()-start} s")
            start = time.time()

        # On insère les numérotations des factures globales
        LOGGER_INVOICES.warning(r"insertion numérotation globale")
        num_full_sales_invoices()
        print(f"num_full_sales_invoices :{time.time()-start} s")

    # Exceptions PostgresDjangoUpsert ==========================================================
    except PostgresKeyError as except_error:
        print("ERREUR - PostgresKeyError : ", except_error)
        LOGGER_EDI.exception(f"PostgresKeyError : {except_error!r}")

    except PostgresTypeError as except_error:
        print("ERREUR - PostgresTypeError : ", except_error)
        LOGGER_EDI.exception(f"PostgresTypeError : {except_error!r}")

    # Exception Générale =======================================================================
    except Exception as except_error:
        print("ERREUR - Exception : ", except_error)
        LOGGER_EDI.exception(f"Exception Générale : {except_error!r}")

    finally:
        pass

    return trace, alls_print


if __name__ == "__main__":
    utilisateur = User.objects.get(last_name="ALVES")
    to_print_ = invoices_insertion(utilisateur.uuid_identification, "2023-06-30")
    # set_purchases_invoices (cur, utilisateur)
    # if to_print_:
    #     print(to_print_)
    #     raise Exception("Il y a eu une erreur à l'insertion des factures de vente")
    # with connection.cursor() as cur:
    #     delete_pdf_files(cur)
