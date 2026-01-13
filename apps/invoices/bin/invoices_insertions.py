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
from django.db.models import Count, Q

from heron.loggers import LOGGER_EDI, LOGGER_INVOICES
from apps.core.models import SSEProgress
from apps.core.bin.echeances import get_payment_method_elements, get_due_date
from apps.core.functions.functions_setups import connection, transaction
from apps.core.utils.progress_bar import update_progress_threaded
from apps.data_flux.postgres_save import (
    PostgresKeyError,
    PostgresTypeError,
    PostgresDjangoUpsert,
)
from apps.data_flux.trace import get_trace
from apps.users.models import User
from apps.edi.models import EdiImport
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
from apps.edi.models import EdiValidation


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
    integration_month = (
        pendulum.parse(invoice_date_iso).date().start_of("month").isoformat()
    )
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
        csv_writer = csv.writer(
            file_io, delimiter=";", quotechar='"', quoting=csv.QUOTE_ALL
        )
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
                trace.comment
                + "\n. Une erreur c'est produite veuillez consulter les logs"
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
        csv_writer = csv.writer(
            file_io, delimiter=";", quotechar='"', quoting=csv.QUOTE_ALL
        )
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
                trace.comment
                + "\n. Une erreur c'est produite veuillez consulter les logs"
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
        if file[0]:
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
    num = (cursor.fetchone())[0]

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


def sanitaze_before(cursor):
    """
    Suppression et nettoyage des factures non finalisées
    :return: None
    """
    # On supprime les factures pdf dont les factures sont à "final" = false
    delete_pdf_files(cursor)

    # On supprime les éxistant non définitifs
    cursor.execute(
        "delete from invoices_invoicecommondetails "
        'where ("final" isnull or "final" = false)'
    )

    cursor.execute(
        'delete from invoices_invoicedetail where ("final" isnull or "final" = false)'
    )

    cursor.execute(
        'delete from invoices_invoice where ("final" isnull or "final" = false)'
    )

    cursor.execute(
        'delete from invoices_saleinvoicedetail where ("final" isnull or "final" = false)'
    )

    cursor.execute(
        'delete from invoices_saleinvoice where ("final" isnull or "final" = false)'
    )

    # On réinitialise les compteurs de numérotation, pour qu'il n'y ait pas de décalages
    reinitialize_purchase_invoices_nums(cursor)
    reinitialize_sales_invoices_nums(cursor)


def copy_edi_import(cursor):
    """
    On copie la table edi_import avec toutes ses données (si la table n'est pas vide),
    afin d'avoir une sauvegarde fraiche avant de faire les insertions
    :return: None
    """
    if EdiImport.objects.exists():
        sql_delete_copy = "DROP TABLE IF EXISTS edi_ediimport_copy"
        cursor.execute(sql_delete_copy)
        sql_copy = "CREATE TABLE edi_ediimport_copy AS TABLE edi_ediimport"
        cursor.execute(sql_copy)


def invoices_insertion(
    user_uuid: User, invoice_date: pendulum.date, job_id: str
) -> (Trace.objects, AnyStr):
    """
    Inserion des factures en mode provisoire avant la validation définitive
    :param user_uuid: utilisateur qui a lancé la commande
    :param invoice_date: date de la facture
    :param job_id: pour affichage de la progession des tâches
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
    # On met à jour la billing date dans la table edi_edivalidation
    edi_validations = (
        EdiValidation.objects.filter(Q(final=False) | Q(final__isnull=True))
        .order_by("-id")
        .first()
    )
    edi_validations.billing_date = invoice_date
    edi_validations.save()

    # On update dabord les cct puis les centrales et enseignes
    update_cct_edi_import()
    update_progress_threaded(
        job_id,
        processed=1,
        message="Mise à jour Centrales et Enseignes",
        item_name="update_cct_edi_import",
    )
    print(f"update_cct_edi_import :{time.time() - start} s")
    start = time.time()

    # Pré-contrôle des données avant insertion
    controls = control_alls_missings()
    update_progress_threaded(
        job_id,
        processed=1,
        message="Pré-contrôle",
        item_name="control_alls_missings",
    )
    print(f"control_alls_missings :{time.time() - start} s")
    start = time.time()

    if controls:
        # TODO : FAIRE LE PRE CONTROLE QUAND TOUS LE PROCESS EST TERMINE
        # Renvoyer une erreur si le pré-contrôle n'est pas vide
        ...

    alls_print = ""
    error = False

    try:
        with connection.cursor() as cursor:
            user = User.objects.get(uuid_identification=user_uuid)

            # Étape 1 : Nettoyages et suppressions
            LOGGER_INVOICES.warning(r"Nettoyages et suppressions")
            with transaction.atomic():
                sanitaze_before(cursor)

            update_progress_threaded(
                job_id,
                processed=1,
                message="Suppression des factures non finalisées",
                item_name="sanitaze_before",
            )
            print(f"suppression :{time.time() - start} s")
            start = time.time()

            # Étape 2 : Copie de sécurité
            LOGGER_INVOICES.warning(r"Copie de la table edi_ediimport")
            with transaction.atomic():
                copy_edi_import(cursor)

            update_progress_threaded(
                job_id,
                processed=1,
                message="Copie de sécurité de la table edi_ediimport",
                item_name="copy_edi_import",
            )
            print(f"Copie :{time.time() - start} s")
            start = time.time()

            # Étape 3 : Préparatifs
            LOGGER_INVOICES.warning(r"Prépartifs insertion des factures")
            with transaction.atomic():
                set_fix_uuid(cursor)

            update_progress_threaded(
                job_id,
                processed=1,
                message="Insertion des import_uuid_identification",
                item_name="set_fix_uuid",
            )
            print(f"set_fix_uuid :{time.time() - start} s")
            start = time.time()

            # Étape 4 : Mise à jour des articles
            with transaction.atomic():
                cursor.execute(SQL_FIX_ARTICLES)

            update_progress_threaded(
                job_id,
                processed=1,
                message="Mise à jour des articles",
                item_name="sql_fix_articles",
            )

            # Étape 5 : Mise à jour des centres, enseignes et parties
            with transaction.atomic():
                process_update()

            update_progress_threaded(
                job_id,
                processed=1,
                message=(
                    "Mise à jour des CentersInvoices, SignboardsInvoices et PartiesInvoices "
                    "avant insertion"
                ),
                item_name="process_update",
            )
            print(f"process_update :{time.time() - start} s")
            start = time.time()

            # Étape 6 : Mise à jour des axes articles
            with transaction.atomic():
                update_axes_edi()

            update_progress_threaded(
                job_id,
                processed=1,
                message="Mise à jour des axes articles",
                item_name="update_axes_edi",
            )
            print(f"update_axes_edi :{time.time() - start} s")
            start = time.time()

            # Étape 7 : Insertion des données communes - TRANSACTION CRITIQUE
            with transaction.atomic():
                set_common_details(cursor)

            update_progress_threaded(
                job_id,
                processed=1,
                message="Insertion des données commmunes, achats et ventes",
                item_name="set_common_details",
            )
            print(f"set_common_details :{time.time() - start} s")
            start = time.time()

            # Étape 8 : Insertion des factures d'achats - TRANSACTION CRITIQUE
            LOGGER_INVOICES.warning(r"Insertion des factures d'achat")
            with transaction.atomic():
                error, to_print = set_purchases_invoices(cursor, user, invoice_date)

                if error:
                    raise Exception

                alls_print += to_print
                cursor.execute(SQL_PURCHASE_FOR_EXPORT_X3)
                cursor.execute(SQL_PURCHASES_DETAILS)
                cursor.execute(SQL_PURCHASE_DETAILS_FOR_EXPORT_X3)

            update_progress_threaded(
                job_id,
                processed=1,
                message="Insertion des factures d'achat",
                item_name="set_purchases_invoices",
            )
            print(f"set_purchases_invoices :{time.time() - start} s")
            start = time.time()

            # Étape 9 : Contrôle des achats
            LOGGER_INVOICES.warning(r"Contrôle des factures d'achat")
            if control_sales_insertion(cursor):
                alls_print = (
                    "Il y a eu une erreur à l'insertion des factures d'achat, "
                    "les totaux ne correspondent pas"
                )
                update_progress_threaded(
                    job_id,
                    processed=1,
                    failed=1,
                    message="Erreur sur les factures d'achat",
                    item_name="control_sales_insertion",
                )
                raise Exception(
                    "Il y a eu une erreur à l'insertion des factures de vente"
                )

            update_progress_threaded(
                job_id,
                processed=1,
                message="Contrôle des factures d'achat",
                item_name="control_sales_insertion",
            )
            print(f"control_sales_insertion :{time.time() - start} s")
            start = time.time()

            # Étape 10 : Insertion des factures de vente - TRANSACTION CRITIQUE
            LOGGER_INVOICES.warning(r"Insertion des factures de vente")
            with transaction.atomic():
                error, to_print = set_sales_invoices(cursor, user, invoice_date)
                alls_print += to_print
                cursor.execute(SQL_SALES_FOR_EXPORT_X3)

            if error:
                update_progress_threaded(
                    job_id,
                    processed=1,
                    failed=1,
                    message="Erreur sur les factures de vente",
                    item_name="set_sales_invoices",
                )
                raise Exception

            update_progress_threaded(
                job_id,
                processed=1,
                message="Insertion entêtes de factures de vente",
                item_name="set_sales_invoices",
            )
            print(f"set_sales_invoices :{time.time() - start} s")
            start = time.time()

            # Étape 11 : Insertion des détails des factures de vente
            LOGGER_INVOICES.warning(r"Insertion des détails des factures de vente")
            with transaction.atomic():
                set_sales_details(cursor)

            update_progress_threaded(
                job_id,
                processed=1,
                message="Insertion des détails des factures de vente",
                item_name="set_sales_details",
            )
            print(f"set_sales_details :{time.time() - start} s")
            start = time.time()

            # Étape 12 : Contrôle final des factures de vente
            LOGGER_INVOICES.warning(r"Contrôle des factures de vente")
            if control_sales_insertion(cursor):
                update_progress_threaded(
                    job_id,
                    processed=1,
                    failed=1,
                    message="Erreur sur le contrôle des factures de vente",
                    item_name="control_sales_insertion",
                )
                alls_print = (
                    "Il y a eu une erreur à l'insertion des factures de vente, "
                    "les totaux ne correspondent pas"
                )
                raise Exception(
                    "Il y a eu une erreur à l'insertion des factures de vente"
                )

            update_progress_threaded(
                job_id,
                processed=1,
                message="Contrôle des factures de vente réussi",
                item_name="control_sales_insertion",
            )
            print(f"control_sales_insertion :{time.time() - start} s")
            start = time.time()

            # TODO: FAIRE LE CONTROLE SUR TOUS LES CHAMPS EVENTUELLEMENT MANQUANTS
            #  EX.: TVA, REGIME DE TVA, COLLECTIF....

        # Étape 13 : Numérotation des factures globales
        LOGGER_INVOICES.warning(r"insertion numérotation globale")
        update_progress_threaded(
            job_id,
            processed=1,
            message="Numérotation des factures globales",
            item_name="num_full_sales_invoices",
        )

        with transaction.atomic():
            num_full_sales_invoices()

        print(f"num_full_sales_invoices :{time.time() - start} s")

    # Exceptions PostgresDjangoUpsert ==========================================================
    except PostgresKeyError as except_error:
        print("ERREUR - PostgresKeyError : ", except_error)
        LOGGER_EDI.exception(f"PostgresKeyError : {except_error!r}")
        error = True

    except PostgresTypeError as except_error:
        print("ERREUR - PostgresTypeError : ", except_error)
        LOGGER_EDI.exception(f"PostgresTypeError : {except_error!r}")
        error = True

    # Exception Générale =======================================================================
    except Exception as except_error:
        print("ERREUR - Exception : ", except_error)
        LOGGER_EDI.exception(f"Exception Générale : {except_error!r}")
        error = True

    finally:
        if error:
            update_progress_threaded(job_id=job_id, **{"mark_as_failed": True})
        else:
            update_progress_threaded(job_id=job_id, **{"mark_as_completed": True})

        # Fermeture explicite de la connexion Django pour éviter les fuites de connexions
        # dans les threads (CRITICAL: sans cela, chaque thread garde sa connexion ouverte)
        connection.close()

    return trace, alls_print


if __name__ == "__main__":
    utilisateur = User.objects.get(email="paulo@alves.ovh")
    to_print_ = invoices_insertion(utilisateur.uuid_identification, "2025-10-31")
    # set_purchases_invoices (cur, utilisateur)
    # if to_print_:
    #     print(to_print_)
    #     raise Exception("Il y a eu une erreur à l'insertion des factures de vente")
    # with connection.cursor() as cur:
    #     delete_pdf_files(cur)
