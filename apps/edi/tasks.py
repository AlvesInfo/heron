"""
FR : Module d'import des factures founisseurs EDI sous task Celery
EN : Import module for EDI incoives suppliers by celery tasks

Commentaire:

created at: 2022-04-08
created by: Paulo ALVES

modified at: 2023-02-23
modified by: Paulo ALVES
"""

import shutil
from pathlib import Path
from typing import AnyStr
import time
from uuid import UUID

from celery import shared_task
from django.db import transaction

from heron.loggers import LOGGER_EDI
from apps.core.bin.clean_celery import clean_memory
from apps.core.models import SSEProgress
from apps.edi.imports.imports_suppliers_invoices_pool import (
    bbgr_bulk,
    bbgr_statment,
    bbgr_monthly,
    bbgr_retours,
    bbgr_receptions,
    cosium,
    cosium_achats,
    transfert_cosium,
    edi,
    eye_confort,
    generique,
    generique_internal,
    hansaton,
    hearing,
    interson,
    johnson,
    lmc,
    newson,
    phonak,
    prodition,
    signia,
    starkey,
    technidis,
    unitron,
    widex,
    wsau,
    widex_ga,
    z_bu_refac,
)
from apps.edi.bin.edi_post_processing_pool import (
    post_processing_all,
    edi_trace_supplier_insert,
)
from apps.edi.bin.exclusions import set_exclusions
from apps.users.models import User
from apps.parameters.bin.core import get_object

processing_dict = {
    "BBGR_BULK": bbgr_bulk,
    "COSIUM": cosium,
    "COSIUM_ACHATS": cosium_achats,
    "EDI": edi,
    "EYE_CONFORT": eye_confort,
    "GENERIQUE": generique,
    "GENERIQUE_INTERNAL": generique_internal,
    "HEARING": hearing,
    "HANSATON": hansaton,
    "INTERSON": interson,
    "JOHNSON": johnson,
    "LMC": lmc,
    "NEWSON": newson,
    "PHONAK": phonak,
    "PRODITION": prodition,
    "SIGNIA": signia,
    "STARKEY": starkey,
    "TECHNIDIS": technidis,
    "TRANSFERTS": transfert_cosium,
    "UNITRON": unitron,
    "WIDEX": widex,
    "WSAU": wsau,
    "WIDEX_GA": widex_ga,
    "SAGE_YOOZ_REFAC0": z_bu_refac,
}

bbgr_dict = {
    "bbgr_statment": bbgr_statment,
    "bbgr_monthly": bbgr_monthly,
    "bbgr_retours": bbgr_retours,
    "bbgr_receptions": bbgr_receptions,
}


def _update_progress(job_id, has_error, item_name):
    """Avance la jauge SSEProgress d'un élément, en succès ou en échec
    :param job_id: identifiant du job suivi
    :param has_error: vrai si le traitement de l'élément a échoué
    :param item_name: nom de l'élément traité (fichier, fonction ou tâche)
    """
    with transaction.atomic():
        progress = SSEProgress.objects.select_for_update().get(job_id=job_id)

        if has_error:
            progress.update_progress(
                processed=1,
                failed=1,
                message=f"Erreur sur {item_name}",
                item_name=item_name,
            )
        else:
            progress.update_progress(
                processed=1,
                message=f"{item_name} traité avec succès",
                item_name=item_name,
            )


def _update_progress_logged(job_id, has_error, item_name):
    """Avance la jauge SSEProgress ; une jauge absente ou en erreur est journalisée sans
    interrompre la tâche
    """
    try:
        _update_progress(job_id, has_error, item_name)

    except SSEProgress.DoesNotExist:
        LOGGER_EDI.warning(f"SSEProgress non trouvé pour job_id: {job_id}")
    except Exception as progress_error:
        LOGGER_EDI.exception(
            f"Erreur mise à jour progression: {progress_error}"
        )


def _close_import_trace(trace, error):
    """Marque la trace d'un import en erreur si besoin, puis la rattache aux factures
    :param trace: trace de l'import, None si elle n'a pas pu être créée
    :param error: vrai si une exception a été levée pendant l'import
    """
    if error and trace:
        trace.errors = True
        trace.comment = (
            trace.comment
            + "\n. Une erreur c'est produite veuillez consulter les logs"
        )

    if trace is not None:
        trace.invoices = True
        trace.save()


@shared_task(name="suppliers_import")
@clean_memory
def launch_suppliers_import(process_objects, user_pk, job_id=None):
    """
    Intégration des factures fournisseurs présentes
    dans les répertoires de processing/suppliers_invoices_files
    """

    start_initial = time.time()

    error = False
    trace = None
    to_print = ""
    str_file, str_backup_file, processing_key = process_objects
    file = Path(str_file)
    backup_file = Path(str_backup_file)
    function = processing_dict.get(processing_key)
    separator = "\n" + "=" * 142
    LOGGER_EDI.warning(separator)
    LOGGER_EDI.warning(f"TASK STARTED: flow={str(processing_key).upper()!r} job_id={job_id!r}")

    try:
        if function is None:
            raise LookupError(
                f"Flux inconnu {processing_key!r} : aucun import n'est associé à ce répertoire"
            )

        user = User.objects.get(pk=user_pk)
        trace, to_print = function(file)
        trace.created_by = user
    except TypeError as except_error:
        error = True
        to_print += f"TypeError : {except_error}\n"
        LOGGER_EDI.exception(f"TypeError : {except_error!r}")

    except Exception as except_error:
        error = True
        LOGGER_EDI.exception(f"Exception Générale: {file.name}\n{except_error!r}")

    finally:
        # Vérifier trace.errors car la fonction ne propage pas les exceptions
        has_error = error or (trace and trace.errors)

        _close_import_trace(trace, error)

        if file.is_file() and not backup_file.is_file():
            shutil.move(file.resolve(), backup_file.resolve())
        elif file.is_file():
            file.unlink()

        # Update progress if job_id is provided
        if job_id:
            _update_progress_logged(job_id, has_error, file.name)

    LOGGER_EDI.warning(
        to_print
        + f"Validation {file.name} in : {time.time() - start_initial} s"
        + "\n\n======================================================================="
        "======================================================================="
    )

    return {"import : ": f"edi - {processing_key} - {time.time() - start_initial} s"}


@shared_task(name="bbgr_bi")
@clean_memory
def launch_bbgr_bi_import(function_name, user_pk, job_id=None):
    """
    Intégration des factures bbgr issues de la BI
    dans le répertoire de processing/suppliers_invoices_files
    """

    start_initial = time.time()

    error = False
    trace = None
    to_print = ""
    function = bbgr_dict.get(function_name)

    try:
        if function is None:
            raise LookupError(f"Import B.I inconnu {function_name!r}")

        user = User.objects.get(pk=user_pk)
        trace, to_print = function()
        trace.created_by = user

    except TypeError as except_error:
        error = True
        to_print += f"TypeError : {except_error}\n"
        LOGGER_EDI.exception(f"TypeError : {except_error!r}")

    except Exception as except_error:
        error = True
        LOGGER_EDI.exception(f"Exception Générale: {function_name}\n{except_error!r}")

    finally:
        _close_import_trace(trace, error)

        # Update progress if job_id is provided
        if job_id:
            _update_progress_logged(job_id, error, function_name)

    LOGGER_EDI.warning(
        to_print
        + f"Validation {function_name} in : {time.time() - start_initial} s"
        + "\n\n======================================================================="
        "======================================================================="
    )

    time_to_process = trace.time_to_process if trace is not None else time.time() - start_initial

    return {"import : ": f"BBGR BI - {function_name} - {time_to_process} s"}


@shared_task(name="sql_clean_general")
@clean_memory
def launch_sql_clean_general(start_all, job_id=None):
    """Realise les requêtes sql générale, pour le néttoyages des imports"""
    start_initial = time.time()

    try:
        # Update progress if job_id is provided
        if job_id:
            try:
                with transaction.atomic():
                    progress = SSEProgress.objects.select_for_update().get(
                        job_id=job_id
                    )
                    progress.update_progress(
                        processed=0, message="Validation et mises à jour"
                    )

            except SSEProgress.DoesNotExist:
                LOGGER_EDI.warning(f"SSEProgress non trouvé pour job_id: {job_id}")
            except Exception as progress_error:
                LOGGER_EDI.exception(
                    f"Erreur mise à jour progression: {progress_error}"
                )

        post_processing_all()
        LOGGER_EDI.warning("post_processing_all terminé")

        # Insertion du nom du fournisseur dans la trace
        edi_trace_supplier_insert()

        # post_vacuum()
        # LOGGER_EDI.warning("post_vacuum terminé")

        set_exclusions()
        LOGGER_EDI.warning("exclusions terminées")

        if job_id:
            with transaction.atomic():
                progress = SSEProgress.objects.select_for_update().get(
                    job_id=job_id
                )
                progress.update_progress(
                    processed=1, message="Validation et mises à jour"
                )

        LOGGER_EDI.warning(f"All validations : {time.time() - start_all} s")

    except Exception as except_error:
        LOGGER_EDI.exception(
            f"Exception Générale: sur tâche launch_sql_clean_general\n{except_error!r}"
        )

    return {
        "Clean Sql Général : ": f"{time.time() - start_initial} s",
        "Ensemble": f"All validations : {time.time() - start_all} s",
    }


def _subscription_result(to_print, error, trace, start_initial):
    """Texte du résultat d'une génération d'abonnements : succès avec sa durée, ou erreur avec
    le commentaire de la trace
    :param to_print: texte renvoyé par la fonction de génération
    :param error: vrai si une exception a été levée
    :param trace: trace de la génération, None si elle n'a pas pu être créée
    :param start_initial: instant de démarrage de la tâche
    """
    comment = trace.comment if trace is not None else ""
    time_to_process = trace.time_to_process if trace is not None else time.time() - start_initial

    if error or "Erreur" in to_print:
        comment_prefix = ":" if comment else ""
        return f"Erreur - {to_print.replace('Erreur', '')} {comment_prefix} {comment!r}"

    return f"{to_print}, réalisée avec sucess, en {time_to_process} s"


@shared_task(name="subscription_launch_task")
@clean_memory
def subscription_launch_task(
    task_to_launch: AnyStr, dte_d: AnyStr, dte_f: AnyStr, user: UUID, job_id: str = None
):
    """Génération des Royalties, Publicités et Prestations sous task Celery
    :param task_to_launch: Tâche à lancer
    :param dte_d: Date de début de période au format texte isoformat
    :param dte_f: Date de fin de période au format texte isoformat
    :param user: Utilisateur lançant la génération
    :param job_id: ID du job pour le suivi SSEProgress
    :return:
    """
    start_initial = time.time()

    error = False
    trace = None
    to_print = ""
    function = get_object(task_to_launch)
    # print(function.__name__)

    try:
        trace, to_print = function(dte_d, dte_f, user)
        trace.created_by = User.objects.get(uuid_identification=UUID(user))
    except TypeError as except_error:
        error = True
        to_print += f"TypeError : {except_error}\n"
        LOGGER_EDI.exception(f"TypeError : {except_error!r}")

    except Exception as except_error:
        error = True
        LOGGER_EDI.exception(f"Exception Générale: {task_to_launch}\n{except_error!r}")

    finally:
        if error and trace:
            trace.errors = True
            trace.comment = (
                f"{trace.comment}\n" if trace.comment else ""
            ) + "Une erreur c'est produite veuillez consulter les logs"

        if trace is not None:
            trace.invoices = True
            trace.save()

        # Update progress if job_id is provided
        if job_id:
            try:
                _update_progress(job_id, error, task_to_launch)
            except Exception as e:
                LOGGER_EDI.error(f"Erreur lors de la mise à jour du SSEProgress: {e}")

    LOGGER_EDI.warning(
        to_print
        + f"Génération des abonnement - {task_to_launch} : {time.time() - start_initial} s"
        + "\n\n======================================================================="
        "======================================================================="
    )

    return {
        "Génération des abonnement : ": _subscription_result(to_print, error, trace, start_initial)
    }


@shared_task(name="test_import_jauge")
@clean_memory
def task_test_import_jauge(job_id, user_id):
    """
    Tâche de test pour la jauge avec polling AJAX
    Simule un long traitement avec mise à jour en base de données
    """
    LOGGER_EDI.info(f"Démarrage de la tâche test_import_jauge - job_id: {job_id}")

    try:
        # Créer l'enregistrement SSEProgress
        progress = SSEProgress.objects.create(
            job_id=job_id, user_id=user_id, task_type="test_import", total_items=100
        )

        # Marquer comme démarré
        progress.mark_as_started()
        LOGGER_EDI.info(f"Progression démarrée - job_id: {job_id}")

        # Traiter 100 items avec un délai pour simuler le travail
        for idx in range(1, 101):
            # Simuler un traitement
            time.sleep(0.1)  # 100ms par item = 10 secondes au total

            # Mettre à jour la progression en base
            progress.update_progress(processed=1)

            if idx % 10 == 0:
                LOGGER_EDI.debug(f"Progression: {idx}/100 - job_id: {job_id}")

        # Marquer comme terminé
        progress.mark_as_completed()
        LOGGER_EDI.info(f"Tâche test_import_jauge terminée - job_id: {job_id}")

        return {"status": "success", "job_id": job_id}

    except Exception as error:
        LOGGER_EDI.exception(f"Erreur dans test_import_jauge: {error}")
        try:
            progress.mark_as_failed(str(error))
        except Exception:
            pass
        raise
