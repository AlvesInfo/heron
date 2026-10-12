"""FR : Module d'import des factures founisseurs EDI sous task Celery.

EN : Import module for EDI incoives suppliers by celery tasks.

Commentaire:

created at: 2022-04-08
created by: Paulo ALVES

modified at: 2023-02-23
modified by: Paulo ALVES
"""

import contextlib
import shutil
import time
from pathlib import Path
from uuid import UUID

from celery import shared_task
from django.db import transaction

from apps.core.bin.clean_celery import clean_memory
from apps.core.models import SSEProgress
from apps.edi.bin.edi_post_processing_pool import (
    edi_trace_supplier_insert,
    post_processing_all,
)
from apps.edi.bin.exclusions import set_exclusions
from apps.edi.imports.imports_suppliers_invoices_pool import (
    bbgr_bulk,
    bbgr_monthly,
    bbgr_receptions,
    bbgr_retours,
    bbgr_statment,
    cosium,
    cosium_achats,
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
    transfert_cosium,
    unitron,
    widex,
    widex_ga,
    wsau,
    z_bu_refac,
)
from apps.parameters.bin.core import get_object
from apps.users.models import User
from heron.loggers import LOGGER_EDI

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
    """Avance la jauge SSEProgress d'un élément, en succès ou en échec.

    :param job_id: identifiant du job suivi
    :param has_error: vrai si le traitement de l'élément a échoué
    :param item_name: nom de l'élément traité (fichier, fonction ou tâche).
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
    """Avance la jauge SSEProgress ; une jauge absente ou en erreur est journalisée sans.

    interrompre la tâche.
    """
    try:
        _update_progress(job_id, has_error, item_name)

    except SSEProgress.DoesNotExist:
        LOGGER_EDI.warning("SSEProgress non trouvé pour job_id: %s", job_id)
    except Exception:
        LOGGER_EDI.exception("Erreur mise à jour progression")


def _close_import_trace(trace, error):
    """Marque la trace d'un import en erreur si besoin, puis la rattache aux factures.

    :param trace: trace de l'import, None si elle n'a pas pu être créée
    :param error: vrai si une exception a été levée pendant l'import.
    """
    if error and trace:
        trace.errors = True
        trace.comment = trace.comment + "\n. Une erreur c'est produite veuillez consulter les logs"

    if trace is not None:
        trace.invoices = True
        trace.save()


def _require_function(function, message: str):
    """Renvoie la fonction d'import, LookupError (message donné) si aucune n'est associée."""
    if function is None:
        raise LookupError(message)

    return function


@shared_task(name="suppliers_import")
@clean_memory
def launch_suppliers_import(process_objects, user_pk, job_id=None):
    """Intégration des factures fournisseurs présentes.

    dans les répertoires de processing/suppliers_invoices_files.
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
    LOGGER_EDI.warning("TASK STARTED: flow=%r job_id=%r", str(processing_key).upper(), job_id)

    try:
        function = _require_function(
            function,
            f"Flux inconnu {processing_key!r} : aucun import n'est associé à ce répertoire",
        )

        user = User.objects.get(pk=user_pk)
        trace, to_print = function(file)
        trace.created_by = user
    except TypeError as except_error:
        error = True
        to_print += f"TypeError : {except_error}\n"
        LOGGER_EDI.exception("TypeError")

    except Exception:
        error = True
        LOGGER_EDI.exception("Exception Générale: %s", file.name)

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
        "%sValidation %s in : %s s\n\n%s",
        to_print,
        file.name,
        time.time() - start_initial,
        "=" * 142,
    )

    return {"import : ": f"edi - {processing_key} - {time.time() - start_initial} s"}


@shared_task(name="bbgr_bi")
@clean_memory
def launch_bbgr_bi_import(function_name, user_pk, job_id=None):
    """Intégration des factures bbgr issues de la BI.

    dans le répertoire de processing/suppliers_invoices_files.
    """
    start_initial = time.time()

    error = False
    trace = None
    to_print = ""
    function = bbgr_dict.get(function_name)

    try:
        function = _require_function(function, f"Import B.I inconnu {function_name!r}")

        user = User.objects.get(pk=user_pk)
        trace, to_print = function()
        trace.created_by = user

    except TypeError as except_error:
        error = True
        to_print += f"TypeError : {except_error}\n"
        LOGGER_EDI.exception("TypeError")

    except Exception:
        error = True
        LOGGER_EDI.exception("Exception Générale: %s", function_name)

    finally:
        _close_import_trace(trace, error)

        # Update progress if job_id is provided
        if job_id:
            _update_progress_logged(job_id, error, function_name)

    LOGGER_EDI.warning(
        "%sValidation %s in : %s s\n\n%s",
        to_print,
        function_name,
        time.time() - start_initial,
        "=" * 142,
    )

    time_to_process = trace.time_to_process if trace is not None else time.time() - start_initial

    return {"import : ": f"BBGR BI - {function_name} - {time_to_process} s"}


@shared_task(name="sql_clean_general")
@clean_memory
def launch_sql_clean_general(start_all, job_id=None):
    """Realise les requêtes sql générale, pour le néttoyages des imports."""
    start_initial = time.time()

    try:
        # Update progress if job_id is provided
        if job_id:
            try:
                with transaction.atomic():
                    progress = SSEProgress.objects.select_for_update().get(job_id=job_id)
                    progress.update_progress(processed=0, message="Validation et mises à jour")

            except SSEProgress.DoesNotExist:
                LOGGER_EDI.warning("SSEProgress non trouvé pour job_id: %s", job_id)
            except Exception:
                LOGGER_EDI.exception("Erreur mise à jour progression")

        post_processing_all()
        LOGGER_EDI.warning("post_processing_all terminé")

        # Insertion du nom du fournisseur dans la trace
        edi_trace_supplier_insert()

        set_exclusions()
        LOGGER_EDI.warning("exclusions terminées")

        if job_id:
            with transaction.atomic():
                progress = SSEProgress.objects.select_for_update().get(job_id=job_id)
                progress.update_progress(processed=1, message="Validation et mises à jour")

        LOGGER_EDI.warning("All validations : %s s", time.time() - start_all)

    except Exception:
        LOGGER_EDI.exception("Exception Générale: sur tâche launch_sql_clean_general")

    return {
        "Clean Sql Général : ": f"{time.time() - start_initial} s",
        "Ensemble": f"All validations : {time.time() - start_all} s",
    }


def _subscription_result(to_print, error, trace, start_initial):
    """Texte du résultat d'une génération d'abonnements : succès avec sa durée, ou erreur avec.

    le commentaire de la trace
    :param to_print: texte renvoyé par la fonction de génération
    :param error: vrai si une exception a été levée
    :param trace: trace de la génération, None si elle n'a pas pu être créée
    :param start_initial: instant de démarrage de la tâche.
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
    task_to_launch: str, dte_d: str, dte_f: str, user: UUID, job_id: str | None = None
):
    """Génération des Royalties, Publicités et Prestations sous task Celery.

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

    try:
        trace, to_print = function(dte_d, dte_f, user)
        trace.created_by = User.objects.get(uuid_identification=UUID(str(user)))
    except TypeError as except_error:
        error = True
        to_print += f"TypeError : {except_error}\n"
        LOGGER_EDI.exception("TypeError")

    except Exception:
        error = True
        LOGGER_EDI.exception("Exception Générale: %s", task_to_launch)

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
            except Exception:
                LOGGER_EDI.exception("Erreur lors de la mise à jour du SSEProgress")

    LOGGER_EDI.warning(
        "%sGénération des abonnement - %s : %s s\n\n%s",
        to_print,
        task_to_launch,
        time.time() - start_initial,
        "=" * 142,
    )

    return {
        "Génération des abonnement : ": _subscription_result(to_print, error, trace, start_initial)
    }


@shared_task(name="test_import_jauge")
@clean_memory
def task_test_import_jauge(job_id, user_id):
    """Tâche de test pour la jauge avec polling AJAX.

    Simule un long traitement avec mise à jour en base de données.
    """
    LOGGER_EDI.info("Démarrage de la tâche test_import_jauge - job_id: %s", job_id)

    try:
        # Créer l'enregistrement SSEProgress
        progress = SSEProgress.objects.create(
            job_id=job_id, user_id=user_id, task_type="test_import", total_items=100
        )

        # Marquer comme démarré
        progress.mark_as_started()
        LOGGER_EDI.info("Progression démarrée - job_id: %s", job_id)

        # Traiter 100 items avec un délai pour simuler le travail
        for idx in range(1, 101):
            # Simuler un traitement
            time.sleep(0.1)  # 100ms par item = 10 secondes au total

            # Mettre à jour la progression en base
            progress.update_progress(processed=1)

            if idx % 10 == 0:
                LOGGER_EDI.debug("Progression: %s/100 - job_id: %s", idx, job_id)

        # Marquer comme terminé
        progress.mark_as_completed()
        LOGGER_EDI.info("Tâche test_import_jauge terminée - job_id: %s", job_id)

    except Exception as error:
        LOGGER_EDI.exception("Erreur dans test_import_jauge")
        # L'erreur d'origine est relancée, l'échec du marquage de la jauge n'est pas bloquant
        with contextlib.suppress(Exception):
            progress.mark_as_failed(str(error))
        raise

    return {"status": "success", "job_id": job_id}
