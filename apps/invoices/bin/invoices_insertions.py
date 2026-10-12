"""FR : Module d'insertion provisoire.

EN : Provisional insert module.

Commentaire:

created at: 2023-03-11
created by: Paulo ALVES

modified at: 2023-03-11
modified by: Paulo ALVES
"""

import csv
import io
import os
import platform
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, NoReturn
from uuid import UUID

import django
from django.db.backends.utils import CursorWrapper

from apps.core.bin.typing_helpers import required

BASE_DIR = r"C:\SitesWeb\heron"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")

django.setup()

import pendulum
from django.conf import settings
from django.db.models import Count, Q
from django.utils import timezone

from apps.centers_purchasing.bin.update_account_article import update_axes_edi
from apps.core.bin.echeances import get_due_date, get_payment_method_elements
from apps.core.functions.functions_setups import connection, transaction
from apps.core.utils.progress_bar import update_progress_threaded
from apps.data_flux.models import Trace
from apps.data_flux.postgres_save import (
    PostgresDjangoUpsert,
    PostgresKeyError,
    PostgresTypeError,
)
from apps.data_flux.trace import get_trace
from apps.edi.bin.cct_update import update_cct_edi_import
from apps.edi.models import EdiImport, EdiValidation
from apps.invoices.bin.columns import COL_SALES_DICT, COLS_PURCHASE_DICT
from apps.invoices.bin.invoives_nums import get_invoice_num, get_purchase_num
from apps.invoices.bin.pre_controls import control_alls_missings
from apps.invoices.loops.mise_a_jour_loop import process_update
from apps.invoices.models import Invoice, SaleInvoice
from apps.invoices.sql_files.sql_invoices_insertions import (
    SQL_CLEAR_INVOICES_SIGNBOARDS,
    SQL_COMMON_DETAILS,
    SQL_CONTROL_PURCHASES_INSERTION,
    SQL_CONTROL_SALES_INSERTION,
    SQL_FIX_ARTICLES,
    SQL_FIX_IMPORT_UUID,
    SQL_PURCHASE_DETAILS_FOR_EXPORT_X3,
    SQL_PURCHASE_FOR_EXPORT_X3,
    SQL_PURCHASES_DETAILS,
    SQL_PURCHASES_INVOICES,
    SQL_SALES_DETAILS,
    SQL_SALES_FOR_EXPORT_X3,
    SQL_SALES_INVOICES,
)
from apps.parameters.bin.generic_nums import get_generic_cct_num
from apps.parameters.models import CounterNums
from apps.users.models import User
from heron.loggers import LOGGER_EDI, LOGGER_INVOICES


class InvoicesInsertionError(Exception):
    """Exception niveau module pour les erreurs d'insertion des factures."""


def set_fix_uuid(cursor: CursorWrapper) -> None:
    """Ajout de l'import_uuid_identification, au cas où il en manque.

    :param cursor: cursor django pour la db
    :return:
    """
    cursor.execute(SQL_FIX_IMPORT_UUID)


def set_common_details(cursor: CursorWrapper) -> None:
    """Ajout des détails de factures pour la partie commune.

    :param cursor: cursor django pour la db
    :return:
    """
    cursor.execute(SQL_COMMON_DETAILS)


def set_sales_details(cursor: CursorWrapper) -> None:
    """Ajout des détails de factures de vente.

    :param cursor: cursor django pour la db
    :return:
    """
    cursor.execute(SQL_SALES_DETAILS)


def set_purchases_invoices(
    cursor: CursorWrapper, user: User, invoice_date_iso: str
) -> tuple[bool, str]:
    """Remplissage du fichier io pour insertion en base des factures de vente.

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
            # date_echeance
            line_to_write[17] = get_due_date(str(line_to_write[8]), auuid)
            # created_by
            line_to_write[25] = user.uuid_identification
            # modified by
            line_to_write[26] = user.uuid_identification
            # Mois d'intégration = période de facturation
            line_to_write[29] = integration_month

            csv_writer.writerow(line_to_write)

        file_io.seek(0)
        postgres_upsert = PostgresDjangoUpsert(
            model=model,
            fields_dict=COLS_PURCHASE_DICT,
            cnx=connection,
            exclude_update_fields=set(),
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
    except PostgresKeyError:
        error = True
        LOGGER_EDI.exception("PostgresKeyError")

    except PostgresTypeError:
        error = True
        LOGGER_EDI.exception("PostgresTypeError")

    # Exception Générale =======================================================================
    except Exception:
        error = True
        LOGGER_EDI.exception("Exception Générale")

    finally:
        if error:
            trace.errors = True
            trace.comment = (
                trace.comment + "\n. Une erreur c'est produite veuillez consulter les logs"
            )

        trace.time_to_process = (timezone.now() - trace.created_at).total_seconds()
        trace.save()

        try:
            if not file_io.closed:
                file_io.close()
            del file_io

        except (AttributeError, NameError):
            pass

    return error, to_print


def _sales_line(line: tuple, invoice_date, user: User) -> list:
    """Ligne de facture de vente à écrire : numéro, dates de période et utilisateur renseignés."""
    invoice_num = get_invoice_num(invoice_date)
    line_to_write = list(line)
    line_to_write[5] = invoice_num
    line_to_write[6] = f"{line[34]!s}{invoice_num}"
    line_to_write[8] = invoice_date.isoformat()
    line_to_write[9] = invoice_date.start_of("month").isoformat()
    line_to_write[10] = invoice_date.year
    line_to_write[20] = user.uuid_identification
    line_to_write[21] = user.uuid_identification

    return line_to_write


def set_sales_invoices(
    cursor: CursorWrapper, user: User, invoice_date_iso: str
) -> tuple[bool, str]:
    """Remplissage du fichier io pour insertion en base des factures de vente.

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
        f"Facturation de Ventes pour la période : {invoice_date.format('MMMM YYYY', locale='fr')}"
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
            csv_writer.writerow(_sales_line(line, invoice_date, user))

        file_io.seek(0)
        postgres_upsert = PostgresDjangoUpsert(
            model=model,
            fields_dict=COL_SALES_DICT,
            cnx=connection,
            exclude_update_fields=set(),
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
    except PostgresKeyError:
        error = True
        LOGGER_EDI.exception("PostgresKeyError")

    except PostgresTypeError:
        error = True
        LOGGER_EDI.exception("PostgresTypeError")

    # Exception Générale =======================================================================
    except Exception:
        error = True
        LOGGER_EDI.exception("Exception Générale")

    finally:
        if error:
            trace.errors = True
            trace.comment = (
                trace.comment + "\n. Une erreur c'est produite veuillez consulter les logs"
            )

        trace.time_to_process = (timezone.now() - trace.created_at).total_seconds()
        trace.save()

        try:
            if not file_io.closed:
                file_io.close()
            del file_io

        except (AttributeError, NameError):
            pass

    return error, to_print


def control_purchases_insertion(cursor: CursorWrapper) -> bool:
    """Controle des montants totaux des entêtes factures de ventes par rapport au montant du détail,.

    sur les HT, TVA et TTC.
    :param cursor: cursor django pour la db
    :return: False if OK else True.
    """
    cursor.execute(SQL_CONTROL_PURCHASES_INSERTION)

    return cursor.fetchone() is not None


def control_sales_insertion(cursor: CursorWrapper) -> bool:
    """Controle des montants totaux des entêtes factures de ventes par rapport au montant du détail,.

    sur les HT, TVA et TTC.
    :param cursor: cursor django pour la db
    :return: False if OK else True.
    """
    cursor.execute(SQL_CONTROL_SALES_INSERTION)

    return cursor.fetchone() is not None


def num_full_sales_invoices():
    """Insertion des numérotaions full par cct."""
    sales_list = (
        SaleInvoice.objects.filter(final=False, type_x3__in=(1, 2))
        .values("cct")
        .annotate(dcount=Count("cct"))
        .order_by()
    )

    if not sales_list:
        return

    cct = sales_list[0].get("cct")
    global_invoice_file = f"{get_generic_cct_num(str(cct))}_full.pdf"

    for line_dict in sales_list:
        cct_query = line_dict.get("cct")

        if cct_query != cct:
            cct = cct_query
            global_invoice_file = f"{get_generic_cct_num(str(cct))}_full.pdf"

        SaleInvoice.objects.filter(cct=cct, final=False, type_x3__in=(1, 2)).update(
            global_invoice_file=global_invoice_file
        )


def delete_pdf_files(cursor: CursorWrapper) -> None:
    """Supprime les fichiers pdf, des factures devant être supprimées.

    :param cursor: cursor django pour la db
    :return: False if OK else True.
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


def reinitialize_purchase_invoices_nums(cursor: CursorWrapper) -> None:
    """Réinitialise la numérotation des factures de d'achat après suppressions.

    :param cursor: cursor django pour la db
    :return: False if OK else True.
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
    # Plus aucune facture : le compteur repart à 1 (max(...) + 1 renvoie NULL)
    num = (cursor.fetchone())[0] or 1

    try:
        numerotation = CounterNums.objects.get(
            counter__uuid_identification=UUID("ad95c27f-9800-46d4-8e63-55191023f0a4")
        )
        numerotation.num = num
        numerotation.save()

    except CounterNums.DoesNotExist:
        pass


def reinitialize_sales_invoices_nums(cursor: CursorWrapper) -> None:
    """Réinitialise la numérotation des factures de ventes après suppressions.

    :param cursor: cursor django pour la db
    :return: False if OK else True.
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
    # Plus aucune facture : le compteur repart à 1 (max(...) + 1 renvoie NULL)
    num = (cursor.fetchone())[0] or 1

    try:
        numerotation = CounterNums.objects.get(
            counter__uuid_identification=UUID("8aad17a2-90a8-4a72-a8c6-caccdadf5a8b")
        )
        numerotation.num = num
        numerotation.save()

    except CounterNums.DoesNotExist:
        pass


def sanitaze_before(cursor):
    """Suppression et nettoyage des factures non finalisées.

    :return: None.
    """
    # On supprime les factures pdf dont les factures sont à "final" = false
    delete_pdf_files(cursor)

    # On supprime les éxistant non définitifs
    cursor.execute(
        'delete from invoices_invoicecommondetails where ("final" isnull or "final" = false)'
    )

    cursor.execute('delete from invoices_invoicedetail where ("final" isnull or "final" = false)')

    cursor.execute('delete from invoices_invoice where ("final" isnull or "final" = false)')

    cursor.execute(
        'delete from invoices_saleinvoicedetail where ("final" isnull or "final" = false)'
    )

    cursor.execute('delete from invoices_saleinvoice where ("final" isnull or "final" = false)')

    # On réinitialise les compteurs de numérotation, pour qu'il n'y ait pas de décalages
    reinitialize_purchase_invoices_nums(cursor)
    reinitialize_sales_invoices_nums(cursor)


def copy_edi_import(cursor):
    """On copie la table edi_import avec toutes ses données (si la table n'est pas vide),.

    afin d'avoir une sauvegarde fraiche avant de faire les insertions
    :return: None.
    """
    if EdiImport.objects.exists():
        sql_delete_copy = "DROP TABLE IF EXISTS edi_ediimport_copy"
        cursor.execute(sql_delete_copy)
        sql_copy = "CREATE TABLE edi_ediimport_copy AS TABLE edi_ediimport"
        cursor.execute(sql_copy)


class _InsertionSteps:
    """Enchaîne les étapes de l'insertion : journal, progression SSE, chronométrage et compte rendu."""

    def __init__(self, job_id: str) -> None:
        self.job_id = job_id
        self.start = time.time()
        self.report = ""

    def done(self, *, message: str, item_name: str, label: str | None = None) -> None:
        """Notifie la fin d'une étape dans la jauge et journalise sa durée si `label` est donné."""
        update_progress_threaded(self.job_id, processed=1, message=message, item_name=item_name)

        if label:
            LOGGER_INVOICES.info("%s :%s s", label, time.time() - self.start)
            self.start = time.time()

    def run(
        self,
        action: Callable[[], Any],
        *,
        message: str,
        item_name: str,
        title: str | None = None,
        label: str | None = None,
    ) -> Any:
        """Joue `action` dans une transaction puis notifie la progression."""
        if title:
            LOGGER_INVOICES.warning(title)

        with transaction.atomic():
            result = action()

        self.done(message=message, item_name=item_name, label=label)

        return result

    def fail(self, *, message: str, item_name: str, error: str) -> NoReturn:
        """Marque l'étape en échec dans la jauge puis lève InvoicesInsertionError."""
        update_progress_threaded(
            self.job_id, processed=1, failed=1, message=message, item_name=item_name
        )
        raise InvoicesInsertionError(error)


def _insert_purchases(cursor, user: User, invoice_date) -> str:
    """Insère les factures d'achat et leurs détails ; InvoicesInsertionError si les entêtes échouent."""
    error, to_print = set_purchases_invoices(cursor, user, invoice_date)

    if error:
        raise InvoicesInsertionError("Erreur à l'insertion des entêtes de factures d'achat")

    cursor.execute(SQL_PURCHASE_FOR_EXPORT_X3)
    cursor.execute(SQL_PURCHASES_DETAILS)
    cursor.execute(SQL_PURCHASE_DETAILS_FOR_EXPORT_X3)

    return to_print


def _insert_sales(cursor, user: User, invoice_date) -> tuple[bool, str]:
    """Insère les entêtes de factures de vente et prépare l'export X3 ; (erreur, compte rendu)."""
    error, to_print = set_sales_invoices(cursor, user, invoice_date)
    cursor.execute(SQL_SALES_FOR_EXPORT_X3)

    return error, to_print


def _prepare_insertion(invoice_date, job_id: str) -> Trace:
    """Trace, date de facturation, mise à jour des cct et pré-contrôle avant l'insertion."""
    start = time.time()
    trace = get_trace(
        f"Insertion de la facturation : {invoice_date}",
        "insertion par fonction",
        "invoices_insertion",
        "Invoices_Insertion",
        "",
    )
    # On met à jour la billing date dans la table edi_edivalidation
    edi_validations = required(
        EdiValidation.objects.filter(Q(final=False) | Q(final__isnull=True))
        .order_by("-id")
        .first(),
        "validation EDI en cours",
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
    LOGGER_INVOICES.info("update_cct_edi_import :%s s", time.time() - start)
    start = time.time()

    # Pré-contrôle des données avant insertion
    controls = control_alls_missings()
    update_progress_threaded(
        job_id,
        processed=1,
        message="Pré-contrôle",
        item_name="control_alls_missings",
    )
    LOGGER_INVOICES.info("control_alls_missings :%s s", time.time() - start)

    if controls:
        # Limitation connue : le pré-contrôle n'est pas joué ici (il le sera quand tout le
        # processus sera terminé) ; une erreur devrait être renvoyée s'il n'est pas vide
        ...

    return trace


def _run_insertion_steps(cursor, user: User, invoice_date, steps: _InsertionSteps) -> None:
    """Étapes 1 à 12 de l'insertion sur le curseur ouvert ; le compte rendu est dans `steps.report`."""
    # Étape 1 : Nettoyages et suppressions
    steps.run(
        lambda: sanitaze_before(cursor),
        title=r"Nettoyages et suppressions",
        message="Suppression des factures non finalisées",
        item_name="sanitaze_before",
        label="suppression",
    )
    # Étape 2 : Copie de sécurité
    steps.run(
        lambda: copy_edi_import(cursor),
        title=r"Copie de la table edi_ediimport",
        message="Copie de sécurité de la table edi_ediimport",
        item_name="copy_edi_import",
        label="Copie",
    )
    # Étape 3 : Préparatifs
    steps.run(
        lambda: set_fix_uuid(cursor),
        title=r"Prépartifs insertion des factures",
        message="Insertion des import_uuid_identification",
        item_name="set_fix_uuid",
        label="set_fix_uuid",
    )
    # Étape 4 : Mise à jour des articles
    steps.run(
        lambda: cursor.execute(SQL_FIX_ARTICLES),
        message="Mise à jour des articles",
        item_name="sql_fix_articles",
    )
    # Étape 5 : Mise à jour des centres, enseignes et parties
    steps.run(
        process_update,
        message=(
            "Mise à jour des CentersInvoices, SignboardsInvoices et PartiesInvoices avant insertion"
        ),
        item_name="process_update",
        label="process_update",
    )
    # Étape 6 : Mise à jour des axes articles
    steps.run(
        update_axes_edi,
        message="Mise à jour des axes articles",
        item_name="update_axes_edi",
        label="update_axes_edi",
    )
    # Étape 7 : Insertion des données communes - TRANSACTION CRITIQUE
    steps.run(
        lambda: set_common_details(cursor),
        message="Insertion des données commmunes, achats et ventes",
        item_name="set_common_details",
        label="set_common_details",
    )
    # Étape 8 : Insertion des factures d'achats - TRANSACTION CRITIQUE
    steps.report += steps.run(
        lambda: _insert_purchases(cursor, user, invoice_date),
        title=r"Insertion des factures d'achat",
        message="Insertion des factures d'achat",
        item_name="set_purchases_invoices",
        label="set_purchases_invoices",
    )
    # Étape 9 : Contrôle des achats
    LOGGER_INVOICES.warning(r"Contrôle des factures d'achat")
    if control_purchases_insertion(cursor):
        steps.report = (
            "Il y a eu une erreur à l'insertion des factures d'achat, "
            "les totaux ne correspondent pas"
        )
        steps.fail(
            message="Erreur sur les factures d'achat",
            item_name="control_purchases_insertion",
            error="Il y a eu une erreur à l'insertion des factures d'achat",
        )

    steps.done(
        message="Contrôle des factures d'achat",
        item_name="control_purchases_insertion",
        label="control_purchases_insertion",
    )
    # Étape 10 : Insertion des factures de vente - TRANSACTION CRITIQUE
    LOGGER_INVOICES.warning(r"Insertion des factures de vente")
    with transaction.atomic():
        error, to_print = _insert_sales(cursor, user, invoice_date)
        steps.report += to_print

    if error:
        steps.fail(
            message="Erreur sur les factures de vente",
            item_name="set_sales_invoices",
            error="Erreur à l'insertion des entêtes de factures de vente",
        )

    steps.done(
        message="Insertion entêtes de factures de vente",
        item_name="set_sales_invoices",
        label="set_sales_invoices",
    )
    # Étape 11 : Insertion des détails des factures de vente
    steps.run(
        lambda: set_sales_details(cursor),
        title=r"Insertion des détails des factures de vente",
        message="Insertion des détails des factures de vente",
        item_name="set_sales_details",
        label="set_sales_details",
    )
    # Étape 12 : Contrôle final des factures de vente
    LOGGER_INVOICES.warning(r"Contrôle des factures de vente")
    if control_sales_insertion(cursor):
        steps.report = (
            "Il y a eu une erreur à l'insertion des factures de vente, "
            "les totaux ne correspondent pas"
        )
        steps.fail(
            message="Erreur sur le contrôle des factures de vente",
            item_name="control_sales_insertion",
            error="Il y a eu une erreur à l'insertion des factures de vente",
        )

    steps.done(
        message="Contrôle des factures de vente réussi",
        item_name="control_sales_insertion",
        label="control_sales_insertion",
    )

    # Limitation connue : pas de contrôle des champs éventuellement manquants
    # (TVA, régime de TVA, collectif...)


def invoices_insertion(
    user_uuid: UUID | str, invoice_date: pendulum.date, job_id: str
) -> tuple[Trace, str]:
    """Inserion des factures en mode provisoire avant la validation définitive.

    :param user_uuid: utilisateur qui a lancé la commande
    :param invoice_date: date de la facture
    :param job_id: pour affichage de la progession des tâches
    :return: to_print.
    """
    trace = _prepare_insertion(invoice_date, job_id)
    steps = _InsertionSteps(job_id)
    error = False

    try:
        with connection.cursor() as cursor:
            user = User.objects.get(uuid_identification=user_uuid)
            _run_insertion_steps(cursor, user, invoice_date, steps)

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

        LOGGER_INVOICES.info("num_full_sales_invoices :%s s", time.time() - steps.start)

    # Exceptions PostgresDjangoUpsert ==========================================================
    except PostgresKeyError:
        LOGGER_EDI.exception("PostgresKeyError")
        error = True

    except PostgresTypeError:
        LOGGER_EDI.exception("PostgresTypeError")
        error = True

    # Exception Générale =======================================================================
    except Exception:
        LOGGER_EDI.exception("Exception Générale")
        error = True

    finally:
        if error:
            update_progress_threaded(job_id=job_id, mark_as_failed=True)
        else:
            update_progress_threaded(job_id=job_id, mark_as_completed=True)

        # Fermeture explicite de la connexion Django pour éviter les fuites de connexions
        # dans les threads (CRITICAL: sans cela, chaque thread garde sa connexion ouverte)
        connection.close()

    return trace, steps.report
