# pylint: disable=E0401,W0718,E0633,W1203,W1201
"""
FR : Module de génération des factures pdf de ventes sous task Celery
EN : Module for generating pdf sales invoices under task Celery

Commentaire:

created at: 2022-06-07
created by: Paulo ALVES

modified at: 2023-06-07
modified by: Paulo ALVES
"""
import os
import io
import smtplib
from pathlib import Path
import time
from typing import AnyStr

import dkim
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pendulum
from celery import shared_task
from celery import group
from django.db.models import Count

from heron.loggers import LOGGER_INVOICES
from heron import celery_app
from apps.users.models import User
from apps.invoices.bin.generate_invoices_pdf import invoices_pdf_generation, Maison
from apps.invoices.bin.invoices_insertions import invoices_insertion
from apps.parameters.bin.generic_nums import get_generic_cct_num
from apps.invoices.loops.mise_a_jour_loop import process_update
from apps.invoices.models import SaleInvoice
from apps.parameters.models import ActionInProgress


@shared_task(name="invoices_insertions_launch")
def launch_invoices_insertions(user_uuid: User, invoice_date: pendulum.date):
    """
    Insertion des factures définitives achats et ventes
    :param user_uuid: uuid de l'utilisateur qui a lancé le process
    :param invoice_date: date de la facture
    """
    start_initial = time.time()
    error = False
    trace = ""
    to_print = ""
    action = ActionInProgress.objects.get(action="insertion_invoices")
    action.in_progress = True
    action.save()

    try:
        user = User.objects.get(uuid_identification=user_uuid)
        trace, to_print = invoices_insertion(user_uuid, invoice_date)
        trace.created_by = user
    except TypeError as except_error:
        error = True
        to_print += f"TypeError : {except_error}\n"
        LOGGER_INVOICES.exception(f"TypeError : {except_error!r}")

    except Exception as except_error:
        error = True
        LOGGER_INVOICES.exception(
            f"Exception Générale: launch_invoices_insertions\n{except_error!r}"
        )

    finally:
        if error and trace:
            trace.errors = True
            trace.comment = (
                trace.comment + "\n. Une erreur c'est produite veuillez consulter les logs"
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


@shared_task(name="celery_pdf_launch")
def launch_celery_pdf_launch(user_pk: AnyStr):
    """
    Main pour lancement de la génération des pdf avec Celery
    :param user_pk: uuid de l'utilisateur qui a lancé le process
    """

    # On récupère les factures à générer par cct
    cct_sales_list = (
        SaleInvoice.objects.filter(final=False, printed=False, type_x3__in=(1, 2))
        .values("cct")
        .annotate(dcount=Count("cct"))
        .values_list("cct", flat=True)
        .order_by("cct")
    )
    # On récupère les numérotations gérnériques des factures à générer (A....full.pdf)
    num_file_list = [get_generic_cct_num(cct) for cct in cct_sales_list]

    try:
        tasks_list = []

        # on met à jour les parts invoices
        process_update()

        # On boucle sur les factures des cct pour générer les pdf avec celery tasks
        for cct, num_file in zip(cct_sales_list, num_file_list):
            tasks_list.append(
                celery_app.signature(
                    "launch_generate_pdf_invoices",
                    kwargs={"cct": str(cct), "num_file": str(num_file), "user_pk": str(user_pk)},
                )
            )

        group(*tasks_list).apply_async()

    except Exception as error:
        print("Error : ", error)
        LOGGER_INVOICES.exception(
           "Erreur détectée dans apps.invoices.tasks.launch_celery_pdf_launch()"
        )


@shared_task(name="launch_generate_pdf_invoices")
def launch_generate_pdf_invoices(cct: Maison.cct, num_file: AnyStr, user_pk: int):
    """
    Génération des pdf des factures de ventes pour un cct
    :param cct: cct de la facture pdf à générer
    :param num_file: numero du fichier full
    :param user_pk: uuid de l'utilisateur qui a lancé le process
    """

    start_initial = time.time()

    error = False
    trace = None
    to_print = ""

    try:
        user = User.objects.get(pk=user_pk)
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
                trace.comment + "\n. Une erreur c'est produite veuillez consulter les logs"
            )

        if trace is not None:
            trace.invoices = True
            trace.save()

    LOGGER_INVOICES.warning(
        to_print
        + f"Génération du pdf {cct} : {time.time() - start_initial} s "
    )

    return {"Generation facture pdf : ": f"cct : {str(cct)} - {time.time() - start_initial} s"}
