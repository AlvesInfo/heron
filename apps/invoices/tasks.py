# pylint: disable=E0401,W0718,E0633,W1203,W1201,C0411
"""
FR : Module de génération des factures pdf de ventes sous task Celery
EN : Module for generating pdf sales invoices under task Celery

Commentaire:

created at: 2022-06-07
created by: Paulo ALVES

modified at: 2023-06-07
modified by: Paulo ALVES
"""

import time
from typing import AnyStr, Dict
import smtplib

from celery import group
from django.db import transaction

from heron.loggers import LOGGER_INVOICES, LOGGER_X3
from heron import celery_app
from apps.core.functions.functions_utilitaires import iter_slice
from apps.core.exceptions import EmailException
from apps.core.models import SSEProgress
from apps.invoices.bin.generate_invoices_pdf import invoices_pdf_generation, Maison
from apps.invoices.bin.invoices_insertions import invoices_insertion
from apps.invoices.bin.send_invoices_emails import invoices_send_by_email
from apps.invoices.bin.send_emails_essais import essais_send_by_email
from apps.invoices.loops.mise_a_jour_loop import process_update
from apps.parameters.models import ActionInProgress
from apps.invoices.bin.export_x3 import export_files_x3
from apps.core.utils.progress_bar import update_progress_threaded

# Import des tâches Gmail pour qu'elles soient découvertes par Celery
from apps.invoices.bin.api_gmail.tasks_gmail import *  # noqa: F401, F403


EMAIL_HOST = settings.EMAIL_HOST
EMAIL_PORT = settings.EMAIL_PORT
EMAIL_HOST_USER = settings.EMAIL_HOST_USER
EMAIL_HOST_PASSWORD = settings.EMAIL_HOST_PASSWORD


@shared_task(name="invoices_insertions_launch")
@clean_memory
def launch_invoices_insertions(
    user_uuid: User, invoice_date: pendulum.date, job_id: str = None
):
    """
    Insertion des factures définitives achats et ventes
    :param user_uuid: uuid de l'utilisateur qui a lancé le process
    :param invoice_date: date de la facture
    :param job_id: ID du job pour le suivi SSEProgress
    """
    start_initial = time.time()
    error = False
    trace = ""
    to_print = ""
    progress = None
    action = ActionInProgress.objects.get(action="insertion_invoices")
    action.in_progress = True
    action.save()

    try:
        # Récupérer le SSEProgress créé dans la vue (si job_id fourni)
        if job_id:
            with transaction.atomic():
                progress = SSEProgress.objects.select_for_update().get(job_id=job_id)

                user = User.objects.get(uuid_identification=user_uuid)
                trace, to_print = invoices_insertion(user_uuid, invoice_date, job_id)
                trace.created_by = user

                # Marquer comme terminé
                if progress:
                    progress.refresh_from_db()
                    progress.mark_as_completed()

    except TypeError as except_error:
        error = True
        to_print += f"TypeError : {except_error}\n"
        LOGGER_INVOICES.exception(f"TypeError : {except_error!r}")

    except Exception as except_error:
        error = True
        LOGGER_INVOICES.exception(
            f"Exception Générale: launch_invoices_insertions\n{except_error!r}"
        )
        # Marquer comme échoué
        try:
            if job_id and not progress:
                progress = SSEProgress.objects.get(job_id=job_id)
            if progress:
                progress.mark_as_failed(str(except_error))
        except Exception as e:
            LOGGER_INVOICES.error(
                f"Impossible de marquer le SSEProgress comme failed: {e}"
            )

    finally:
        if error and trace:
            trace.errors = True
            trace.comment = (
                trace.comment
                + "\n. Une erreur c'est produite veuillez consulter les logs"
            )

        if trace is not None:
            trace.invoices = True
            trace.save()

        action.in_progress = False
        action.save()

    LOGGER_INVOICES.warning(
        to_print
        + f"launch_invoices_insertions : {time.time() - start_initial} s"
        + "\n\n======================================================================="
        "======================================================================="
    )

    return {"launch_invoices_insertions : ": f"{time.time() - start_initial} s"}


def launch_celery_pdf_launch(user_pk: AnyStr, job_id: str):
    """
    Main pour lancement de la génération des pdf avec Celery
    :param user_pk: uuid de l'utilisateur qui a lancé le process
    :param job_id: id du job à executer pour suivi SSEProgress
    """
    error = False
    progress = None

    # On récupère les factures à générer par cct
    cct_sales_list = (
        SaleInvoice.objects.filter(final=False, printed=False, type_x3__in=(1, 2))
        .values("cct", "global_invoice_file")
        .annotate(dcount=Count("cct"))
        .values_list("cct", "global_invoice_file")
        .order_by("cct")
    )

    try:
        tasks_list = []
        start_all = time.time()
        # Récupérer le SSEProgress créé dans la vue
        progress = SSEProgress.objects.get(job_id=job_id)

        update_progress_threaded(
            job_id,
            processed=1,
            message="Mise à jours des parties prenantes",
            item_name="Mise à jours des parties prenantes",
        )

        # on met à jour les parts invoices
        process_update()

        # On boucle sur les factures des cct pour générer les pdf avec celery tasks
        for cct, num_file in cct_sales_list:
            tasks_list.append(
                celery_app.signature(
                    "launch_generate_pdf_invoices",
                    kwargs={
                        "cct": str(cct),
                        "num_file": str(num_file),
                        "user_pk": str(user_pk),
                        "job_id": job_id,
                    },
                )
            )

        result = group(*tasks_list)().get(3600)
        LOGGER_INVOICES.warning(f"result : {result!r},\nin {time.time() - start_all} s")

        # Marquer comme terminé
        if progress:
            # Rafraîchir depuis la DB pour avoir les dernières valeurs
            progress.refresh_from_db()
            progress.mark_as_completed()

    except Exception as ex_error:
        error = True
        print("ex_error : ", ex_error)
        LOGGER_INVOICES.exception(
            "Erreur détectée dans apps.invoices.tasks.launch_celery_pdf_launch()"
        )
        # Marquer comme échoué en cas d'erreur
        try:
            if not progress:
                # Essayer de récupérer le SSEProgress si pas encore fait
                progress = SSEProgress.objects.get(job_id=job_id)
            progress.mark_as_failed(str(error))
        except Exception as e:
            LOGGER_INVOICES.error(f"Impossible de marquer le SSEProgress comme failed: {e}")

    finally:
        if error:
            update_progress_threaded(job_id=job_id, **{"mark_as_failed": True})
        else:
            update_progress_threaded(job_id=job_id, **{"mark_as_completed": True})


@shared_task(name="launch_generate_pdf_invoices")
@clean_memory
def launch_generate_pdf_invoices(cct: Maison.cct, num_file: AnyStr, user_pk: int, job_id: str):
    """
    Génération des pdf des factures de ventes pour un cct
    :param cct: maison de la facture pdf à générer
    :param num_file: numero du fichier full
    :param user_pk: uuid de l'utilisateur qui a lancé le process
    :param job_id: uuid du process
    """

    start_initial = time.time()

    error = False
    trace = None
    to_print = ""

    try:
        user = User.objects.get(pk=user_pk)
        update_progress_threaded(
            job_id,
            processed=1,
            message=f"Génération facture PDF : {num_file}",
            item_name=num_file,
        )
        trace, to_print = invoices_pdf_generation(cct, num_file)
        trace.created_by = user

    except TypeError as except_error:
        error = True
        to_print += f"TypeError : {except_error}\n"
        LOGGER_INVOICES.exception(f"TypeError : {except_error!r}")

    except Exception as except_error:
        error = True
        LOGGER_INVOICES.exception(
            f"Exception Générale: launch_generate_pdf_invoices : {cct}\n{except_error!r}"
        )

    finally:
        if error and trace:
            trace.errors = True
            trace.comment = (
                trace.comment
                + "\n. Une erreur c'est produite veuillez consulter les logs"
            )
            update_progress_threaded(
                job_id,
                processed=0,
                failed=1,
                message=f"Erreur sur {num_file}",
                item_name=num_file,
            )

        if trace is not None:
            trace.save()

    LOGGER_INVOICES.warning(
        to_print + f"Génération du pdf {cct} : {time.time() - start_initial} s "
    )

    return {
        "Generation facture pdf : ": f"cct : {str(cct)} - {time.time() - start_initial} s"
    }


@shared_task(name="celery_send_invoices_emails")
@clean_memory
def launch_celery_send_invoice_mails(
    user_pk: AnyStr, cct: AnyStr = None, period: AnyStr = None
):
    """
    Main pour lancement de l'enoi des factures par mails
    :param user_pk: uuid de l'utilisateur qui a lancé le process
    :param cct: cct de la fcture à envoyer
    :param period: période de la facturation
    """
    # récupération du texte du corps de mail et sujet
    email = Email.objects.get(name=0)
    context_dict = {
        "subject_email": str(email.subject),
        "email_html": str(email.email_body),
        "email_text": BeautifulSoup(str(email.email_body), "lxml").get_text(),
    }

    # Si l'on demande un cct on doit avoir la période pour filtrer et ne pas tout envoyer
    if cct and period:
        cct_invoices_list = (
            SaleInvoice.objects.filter(
                cct=cct,
                invoice_month=period,
                printed=True,
                type_x3__in=(1, 2),
            )
            .values("cct", "global_invoice_file", "invoice_month")
            .annotate(dcount=Count("cct"))
            .order_by("cct")
        )

    else:
        # envoi de toutes les factures imprimées en pdf et non finales, et non envoyées
        cct_invoices_list = (
            SaleInvoice.objects.filter(
                final=False,
                printed=True,
                type_x3__in=(1, 2),
                send_email=False,
            )
            .values("cct", "global_invoice_file", "invoice_month")
            .annotate(dcount=Count("cct"))
            .order_by("cct")
        )

    try:
        tasks_list = []
        for cct_dict in cct_invoices_list:
            tasks_list.append(
                celery_app.signature(
                    "send_invoice_email",
                    kwargs={
                        "context_dict": {**context_dict, **cct_dict},
                        "user_pk": str(user_pk),
                    },
                )
            )

        group(*tasks_list).apply_async()

    except (smtplib.SMTPException, ValueError) as error:
        raise EmailException(
            "Erreur envoi email launch_celery_send_invoice_mails"
        ) from error

    except Exception as error:
        print("Error : ", error)
        LOGGER_INVOICES.exception(
            "Erreur détectée dans apps.invoices.tasks.launch_celery_pdf_launch()"
        )


@shared_task(name="send_invoice_email")
@clean_memory
def send_invoice_email(context_dict: Dict, user_pk: int):
    """
    Envoi d'une facture par mail
    :param context_dict: dictionnaire des éléments pour l'envoi d'emails
    :param user_pk: uuid de l'utilisateur qui a lancé le process
    """

    start_initial = time.time()

    error = False
    trace = None
    to_print = ""

    try:
        user = User.objects.get(pk=user_pk)
        trace, to_print = invoices_send_by_email(context_dict)
        trace.created_by = user

    except TypeError as except_error:
        error = True
        to_print += f"TypeError : {except_error}\n"
        LOGGER_INVOICES.exception(f"TypeError : {except_error!r}")

    except Exception as except_error:
        error = True
        LOGGER_INVOICES.exception(
            f"Exception Générale: launch_generate_pdf_invoices : "
            f"{context_dict.get('cct')}\n{except_error!r}"
        )

    finally:
        if error and trace:
            trace.errors = True
            trace.comment = (
                trace.comment
                + "\n. Une erreur c'est produite veuillez consulter les logs"
            )

        if trace is not None:
            trace.save()

    LOGGER_INVOICES.warning(
        to_print
        + (
            f"Envoie de la facture par mail {context_dict.get('cct')} "
            f": {time.time() - start_initial} s "
        )
    )

    return {
        "Envoie de la facture par mail : ": (
            f"cct : {str(context_dict.get('cct'))} - {time.time() - start_initial} s"
        )
    }


@shared_task(name="launch_export_x3")
@clean_memory
def launch_export_x3(export_type, centrale, file_name, user_pk: int, nb_fac=5000):
    """
    Envoi d'une facture par mail
    :param export_type: type d'export odana, sale, purchase, gdaud
    :param centrale: centrale pour laquelle on lance l'export
    :param file_name: nom du fichier à générer
    :param nb_fac: nombre de factures présentes dans le fichier
    :param user_pk: uuid de l'utilisateur qui a lancé le process
    """

    start_initial = time.time()

    error = False
    trace = None
    to_print = ""

    try:
        user = User.objects.get(pk=user_pk)
        trace, to_print = export_files_x3(export_type, centrale, file_name, nb_fac)
        trace.created_by = user

    except TypeError as except_error:
        error = True
        to_print += f"TypeError : {except_error}\n"
        LOGGER_X3.exception(f"TypeError : {except_error!r}")

    except Exception as except_error:
        error = True
        LOGGER_X3.exception(
            f"Exception Générale: launch_export_x3 : "
            f"{export_type} - {centrale} - user : {str(user_pk)}\n{except_error!r}"
        )

    finally:
        if error and trace:
            trace.errors = True
            trace.comment = (
                trace.comment
                + "\n. Une erreur c'est produite veuillez consulter les logs"
            )

        if trace is not None:
            trace.save()

    LOGGER_X3.warning(
        to_print
        + (
            f"Génération des fichiers  {export_type}, pour la société {centrale} "
            f": {time.time() - start_initial} s "
        )
    )

    return not trace.errors


def launch_celery_send_emails_essais(user_pk: AnyStr):
    """
    Essais d'envoi des factures par mails
    :param user_pk: uuid de l'utilisateur qui a lancé le process
    """
    # récupération du texte du corps de mail et sujet
    email = Email.objects.get(name=0)
    context_dict = {
        "subject_email": str(email.subject),
        "email_html": str(email.email_body),
        "email_text": BeautifulSoup(str(email.email_body), "lxml").get_text(),
        "cct": "cct général",
        "invoice_month": "2000-01-01",
        "global_invoice_file": "un.pdf",
    }
    mails_essis_dict = {
        1: "admin.bi@acuitis.com",
        2: "sav.acuitis@alves-info.fr",
    }
    nb_iter = 3
    nb_mails = nb_iter * len(mails_essis_dict)

    try:
        tasks_list = []

        for i, range_list in enumerate(iter_slice(range(nb_mails), nb_iter), 1):
            context_dict["email_list"] = mails_essis_dict.get(i)

            for _ in range_list:
                tasks_list.append(
                    celery_app.signature(
                        "send_invoice_email_essais",
                        kwargs={
                            "context_dict": {**context_dict},
                            "user_pk": str(user_pk),
                        },
                    )
                )

        group(*tasks_list).apply_async()

    except (smtplib.SMTPException, ValueError) as error:
        raise EmailException(
            "Erreur envoi email launch_celery_send_emails_essais"
        ) from error

    except Exception as error:
        print("Error : ", error)
        LOGGER_INVOICES.exception(
            "Erreur détectée dans apps.invoices.tasks.launch_celery_send_emails_essais()"
        )


@shared_task(name="send_invoice_email_essais")
@clean_memory
def send_invoice_email_essais(context_dict: Dict, user_pk: int):
    """
    Essais d'envoi d'une facture par mail
    :param context_dict: dictionnaire des éléments pour l'envoi d'emails
    :param user_pk: uuid de l'utilisateur qui a lancé le process
    """

    start_initial = time.time()

    error = False
    trace = None
    to_print = ""

    try:
        user = User.objects.get(pk=user_pk)
        trace, to_print = essais_send_by_email(context_dict)
        trace.created_by = user

    except TypeError as except_error:
        error = True
        to_print += f"TypeError : {except_error}\n"
        LOGGER_INVOICES.exception(f"TypeError : {except_error!r}")

    except Exception as except_error:
        error = True
        LOGGER_INVOICES.exception(
            f"Exception Générale: send_invoice_email_essais : "
            f"{context_dict.get('cct')}\n{except_error!r}"
        )

    finally:
        if error and trace:
            trace.errors = True
            trace.comment = (
                trace.comment
                + "\n. Une erreur c'est produite veuillez consulter les logs"
            )

        if trace is not None:
            trace.save()

    LOGGER_INVOICES.warning(
        to_print
        + (
            f"Envoie de la facture par mail {context_dict.get('cct')} "
            f": {time.time() - start_initial} s "
        )
    )

    return {
        "Envoie de la facture par mail : ": (
            f"cct : {str(context_dict.get('cct'))} - {time.time() - start_initial} s"
        )
    }
