# pylint: disable=E0401,W1203
"""
Views des Abonnements
"""

import uuid
import threading
import time
import logging
import sys
import os

from django.shortcuts import render
from django.contrib import messages
from django.http import JsonResponse

from apps.periods.forms import MonthForm
from apps.compta.bin.validations_subscriptions import (
    get_have_subscriptions,
    get_missing_cosium_familly,
)
from apps.parameters.bin.core import get_in_progress
from apps.core.models import SSEProgress
from apps.edi.loops.imports_loop_pool import import_launch_subscriptions
from apps.invoices.bin.pre_controls import control_insertion

# Configuration du logger pour afficher dans la console sans duplication
logger = logging.getLogger(__name__)
if os.environ.get('RUN_MAIN') == 'true':
    # Processus principal : configurer le logger pour afficher
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
else:
    # Processus reloader : désactiver complètement les logs
    logger.setLevel(logging.CRITICAL + 1)
    logger.propagate = False


def royalties_launch(request):
    """Lancement de la génération des Royalties
    :param request: Request Django
    :return:
    """
    start_total = time.perf_counter()

    # On contrôle qu'il n'y ai pas des factures non finalisées, mais envoyées par mail
    start = time.perf_counter()
    not_finalize = control_insertion()
    time_control_insertion = time.perf_counter() - start
    logger.info(f"[ROYALTIES_LAUNCH] control_insertion: {time_control_insertion:.4f}s")

    if not_finalize:
        request.session["level"] = 50
        messages.add_message(
            request,
            50,
            (
                "Vous ne pouvez pas générer de Royalties, "
                "car la facturation est déjà envoyée par mail, mais non finalisée"
            ),
        )
        context = {
            "titre_table": "Génération des factures de Royalties",
            "not_finalize": True,
            "submit_url": "compta:royalties_launch",
            "progress_title": "Génération des factures de Royalties",
            "progress_icon": "💰",
        }
        time_total = time.perf_counter() - start_total
        logger.info(f"[ROYALTIES_LAUNCH] TOTAL (not_finalize): {time_total:.4f}s")
        return render(request, "compta/update_sales_launch.html", context=context)

    start = time.perf_counter()
    form = MonthForm(request.POST or None)
    in_action = get_in_progress()
    time_form_init = time.perf_counter() - start
    logger.info(f"[ROYALTIES_LAUNCH] form_init + get_in_progress: {time_form_init:.4f}s")

    if request.method == "POST" and not in_action:

        if form.is_valid():
            start = time.perf_counter()
            dte_d, dte_f = form.cleaned_data.get("periode").split("_")
            time_form_valid = time.perf_counter() - start
            logger.info(f"[ROYALTIES_LAUNCH] form_validation: {time_form_valid:.4f}s")

            start = time.perf_counter()
            text_error_familly = get_missing_cosium_familly(dte_d, dte_f)
            time_check_family = time.perf_counter() - start
            logger.info(f"[ROYALTIES_LAUNCH] get_missing_cosium_familly: {time_check_family:.4f}s")

            if text_error_familly:
                time_total = time.perf_counter() - start_total
                logger.info(f"[ROYALTIES_LAUNCH] TOTAL (error_family): {time_total:.4f}s")
                return JsonResponse(
                    {"success": False, "error": text_error_familly}
                )

            start = time.perf_counter()
            have_subs = get_have_subscriptions("ROYALTIES", dte_d, dte_f)
            time_check_subs = time.perf_counter() - start
            logger.info(f"[ROYALTIES_LAUNCH] get_have_subscriptions: {time_check_subs:.4f}s")

            if have_subs:
                message = (
                    "Les Royalties pour cette période ont déjà été générées!. "
                    "Si vous souhaitez en ajouter, "
                    "supprimez les Royalties et refaite la génération."
                )
                time_total = time.perf_counter() - start_total
                logger.info(f"[ROYALTIES_LAUNCH] TOTAL (already_exists): {time_total:.4f}s")
                return JsonResponse(
                    {"success": False, "error": message}
                )

            else:
                user_pk = request.user.id
                job_id = str(uuid.uuid4())  # Générer un job_id unique

                # Créer le SSEProgress AVANT de lancer la tâche
                start = time.perf_counter()
                total_files = 1
                task_type = "royalties_import"
                custom_title = "Génération des factures de Royalties"

                progress = SSEProgress.objects.create(
                    job_id=job_id,
                    user_id=user_pk,
                    total_items=total_files,
                    task_type=task_type,
                    custom_title=custom_title,
                    metadata={"success": [], "failed": []},
                )
                progress.mark_as_started()
                time_create_progress = time.perf_counter() - start
                logger.info(f"[ROYALTIES_LAUNCH] create_SSEProgress: {time_create_progress:.4f}s")

                # Lancement d'un thread séparé
                start = time.perf_counter()
                thread = threading.Thread(
                    target=import_launch_subscriptions,
                    args=("ROYALTIES", dte_d, dte_f, request.user.uuid_identification, job_id),
                    daemon=True,
                )
                thread.start()
                time_thread_start = time.perf_counter() - start
                logger.info(f"[ROYALTIES_LAUNCH] thread_start: {time_thread_start:.4f}s")

                time_total = time.perf_counter() - start_total
                logger.info(f"[ROYALTIES_LAUNCH] TOTAL (success): {time_total:.4f}s")

                # Retourner JSON immédiatement
                return JsonResponse({"success": True, "job_id": job_id})

        else:
            time_total = time.perf_counter() - start_total
            logger.info(f"[ROYALTIES_LAUNCH] TOTAL (form_invalid): {time_total:.4f}s")
            logger.info(f"erreur form royalties_launch : {str(form.data)!r}")
            return JsonResponse(
                {"success": False, "error": "Erreur de validation du formulaire"}
            )

    start = time.perf_counter()
    context = {
        "en_cours": in_action,
        "titre_table": (
            "DES INTEGRATIONS SONT EN COURS, PATIENTEZ..."
            if in_action
            else "Génération des factures de Royalties"
        ),
        "form": form,
        "submit_url": "compta:royalties_launch",
        "progress_title": "Génération des factures de Royalties",
        "progress_icon": "💰",
        "task_type": "ROYALTIES",
    }
    time_context = time.perf_counter() - start
    logger.info(f"[ROYALTIES_LAUNCH] context_creation: {time_context:.4f}s")

    start = time.perf_counter()
    response = render(request, "compta/update_sales_launch.html", context=context)
    time_render = time.perf_counter() - start
    logger.info(f"[ROYALTIES_LAUNCH] render: {time_render:.4f}s")

    time_total = time.perf_counter() - start_total
    logger.info(f"[ROYALTIES_LAUNCH] TOTAL (GET): {time_total:.4f}s")
    return response


def meuleuse_launch(request):
    """Lancement de la génération des Meuleuses
    :param request: Request Django
    :return:
    """
    start_total = time.perf_counter()

    # On contrôle qu'il n'y ai pas des factures non finalisées, mais envoyées par mail
    start = time.perf_counter()
    not_finalize = control_insertion()
    time_control_insertion = time.perf_counter() - start
    logger.info(f"[MEULEUSE_LAUNCH] control_insertion: {time_control_insertion:.4f}s")

    if not_finalize:
        request.session["level"] = 50
        messages.add_message(
            request,
            50,
            (
                "Vous ne pouvez pas générer de factures de Meuleuses, "
                "car la facturation est déjà envoyée par mail, mais non finalisée"
            ),
        )
        context = {
            "titre_table": "Génération des factures de Meuleuses",
            "not_finalize": True,
            "submit_url": "compta:meuleuse_launch",
            "progress_title": "Génération des factures de Meuleuses",
            "progress_icon": "⚙️",
        }
        time_total = time.perf_counter() - start_total
        logger.info(f"[MEULEUSE_LAUNCH] TOTAL (not_finalize): {time_total:.4f}s")
        return render(request, "compta/update_sales_launch.html", context=context)

    start = time.perf_counter()
    form = MonthForm(request.POST or None)
    in_action = get_in_progress()
    time_form_init = time.perf_counter() - start
    logger.info(f"[MEULEUSE_LAUNCH] form_init + get_in_progress: {time_form_init:.4f}s")

    if request.method == "POST" and not in_action:

        if form.is_valid():
            start = time.perf_counter()
            dte_d, dte_f = form.cleaned_data.get("periode").split("_")
            time_form_valid = time.perf_counter() - start
            logger.info(f"[MEULEUSE_LAUNCH] form_validation: {time_form_valid:.4f}s")

            start = time.perf_counter()
            text_error_familly = get_missing_cosium_familly(dte_d, dte_f)
            time_check_family = time.perf_counter() - start
            logger.info(f"[MEULEUSE_LAUNCH] get_missing_cosium_familly: {time_check_family:.4f}s")

            if text_error_familly:
                time_total = time.perf_counter() - start_total
                logger.info(f"[MEULEUSE_LAUNCH] TOTAL (error_family): {time_total:.4f}s")
                return JsonResponse(
                    {"success": False, "error": text_error_familly}
                )

            start = time.perf_counter()
            have_subs = get_have_subscriptions("MEULEUSE", dte_d, dte_f)
            time_check_subs = time.perf_counter() - start
            logger.info(f"[MEULEUSE_LAUNCH] get_have_subscriptions: {time_check_subs:.4f}s")

            if have_subs:
                message = (
                    "Les redevances Meuleuses pour cette période ont déjà été générées!. "
                    "Si vous souhaitez en ajouter, "
                    "supprimez les redevances Meuleuses et refaite la génération."
                )
                time_total = time.perf_counter() - start_total
                logger.info(f"[MEULEUSE_LAUNCH] TOTAL (already_exists): {time_total:.4f}s")
                return JsonResponse(
                    {"success": False, "error": message}
                )

            else:
                user_pk = request.user.id
                job_id = str(uuid.uuid4())  # Générer un job_id unique

                # Créer le SSEProgress AVANT de lancer la tâche
                start = time.perf_counter()
                total_files = 1
                task_type = "meuleuse_import"
                custom_title = "Génération des factures de Meuleuses"

                progress = SSEProgress.objects.create(
                    job_id=job_id,
                    user_id=user_pk,
                    total_items=total_files,
                    task_type=task_type,
                    custom_title=custom_title,
                    metadata={"success": [], "failed": []},
                )
                progress.mark_as_started()
                time_create_progress = time.perf_counter() - start
                logger.info(f"[MEULEUSE_LAUNCH] create_SSEProgress: {time_create_progress:.4f}s")

                # Lancement d'un thread séparé
                start = time.perf_counter()
                thread = threading.Thread(
                    target=import_launch_subscriptions,
                    args=("MEULEUSE", dte_d, dte_f, request.user.uuid_identification, job_id),
                    daemon=True,
                )
                thread.start()
                time_thread_start = time.perf_counter() - start
                logger.info(f"[MEULEUSE_LAUNCH] thread_start: {time_thread_start:.4f}s")

                time_total = time.perf_counter() - start_total
                logger.info(f"[MEULEUSE_LAUNCH] TOTAL (success): {time_total:.4f}s")

                # Retourner JSON immédiatement
                return JsonResponse({"success": True, "job_id": job_id})

        else:
            time_total = time.perf_counter() - start_total
            logger.info(f"[MEULEUSE_LAUNCH] TOTAL (form_invalid): {time_total:.4f}s")
            logger.info(f"erreur form meuleuse_launch : {str(form.data)!r}")
            return JsonResponse(
                {"success": False, "error": "Erreur de validation du formulaire"}
            )

    start = time.perf_counter()
    context = {
        "en_cours": in_action,
        "titre_table": (
            "DES INTEGRATIONS SONT EN COURS, PATIENTEZ..."
            if in_action
            else "Génération des factures de Meuleuses"
        ),
        "form": form,
        "submit_url": "compta:meuleuse_launch",
        "progress_title": "Génération des factures de Meuleuses",
        "progress_icon": "⚙️",
        "task_type": "MEULEUSE",
    }
    time_context = time.perf_counter() - start
    logger.info(f"[MEULEUSE_LAUNCH] context_creation: {time_context:.4f}s")

    start = time.perf_counter()
    response = render(request, "compta/update_sales_launch.html", context=context)
    time_render = time.perf_counter() - start
    logger.info(f"[MEULEUSE_LAUNCH] render: {time_render:.4f}s")

    time_total = time.perf_counter() - start_total
    logger.info(f"[MEULEUSE_LAUNCH] TOTAL (GET): {time_total:.4f}s")
    return response


def publicity_launch(request):
    """Lancement de la génération des Publicités
    :param request: Request Django
    :return:
    """
    start_total = time.perf_counter()

    # On contrôle qu'il n'y ai pas des factures non finalisées, mais envoyées par mail
    start = time.perf_counter()
    not_finalize = control_insertion()
    time_control_insertion = time.perf_counter() - start
    logger.info(f"[PUBLICITY_LAUNCH] control_insertion: {time_control_insertion:.4f}s")

    if not_finalize:
        request.session["level"] = 50
        messages.add_message(
            request,
            50,
            (
                "Vous ne pouvez pas générer de factures de Publicité, "
                "car la facturation est déjà envoyée par mail, mais non finalisée"
            ),
        )
        context = {
            "titre_table": "Génération des factures de Publicité",
            "not_finalize": True,
            "submit_url": "compta:publicity_launch",
            "progress_title": "Génération des factures de Publicité",
            "progress_icon": "📣",
        }
        time_total = time.perf_counter() - start_total
        logger.info(f"[PUBLICITY_LAUNCH] TOTAL (not_finalize): {time_total:.4f}s")
        return render(request, "compta/update_sales_launch.html", context=context)

    start = time.perf_counter()
    form = MonthForm(request.POST or None)
    in_action = get_in_progress()
    time_form_init = time.perf_counter() - start
    logger.info(f"[PUBLICITY_LAUNCH] form_init + get_in_progress: {time_form_init:.4f}s")

    if request.method == "POST" and not in_action:

        if form.is_valid():
            start = time.perf_counter()
            dte_d, dte_f = form.cleaned_data.get("periode").split("_")
            time_form_valid = time.perf_counter() - start
            logger.info(f"[PUBLICITY_LAUNCH] form_validation: {time_form_valid:.4f}s")

            start = time.perf_counter()
            text_error_familly = get_missing_cosium_familly(dte_d, dte_f)
            time_check_family = time.perf_counter() - start
            logger.info(f"[PUBLICITY_LAUNCH] get_missing_cosium_familly: {time_check_family:.4f}s")

            if text_error_familly:
                time_total = time.perf_counter() - start_total
                logger.info(f"[PUBLICITY_LAUNCH] TOTAL (error_family): {time_total:.4f}s")
                return JsonResponse(
                    {"success": False, "error": text_error_familly}
                )

            start = time.perf_counter()
            have_subs = get_have_subscriptions("PUBLICITE", dte_d, dte_f)
            time_check_subs = time.perf_counter() - start
            logger.info(f"[PUBLICITY_LAUNCH] get_have_subscriptions: {time_check_subs:.4f}s")

            if have_subs:
                message = (
                    "Les redevances de Publicité pour cette période ont déjà été générées!. "
                    "Si vous souhaitez en ajouter, "
                    "supprimez les redevances de Publicité et refaite la génération."
                )
                time_total = time.perf_counter() - start_total
                logger.info(f"[PUBLICITY_LAUNCH] TOTAL (already_exists): {time_total:.4f}s")
                return JsonResponse(
                    {"success": False, "error": message}
                )

            else:
                user_pk = request.user.id
                job_id = str(uuid.uuid4())  # Générer un job_id unique

                # Créer le SSEProgress AVANT de lancer la tâche
                start = time.perf_counter()
                total_files = 1
                task_type = "publicite_import"
                custom_title = "Génération des factures de Publicité"

                progress = SSEProgress.objects.create(
                    job_id=job_id,
                    user_id=user_pk,
                    total_items=total_files,
                    task_type=task_type,
                    custom_title=custom_title,
                    metadata={"success": [], "failed": []},
                )
                progress.mark_as_started()
                time_create_progress = time.perf_counter() - start
                logger.info(f"[PUBLICITY_LAUNCH] create_SSEProgress: {time_create_progress:.4f}s")

                # Lancement d'un thread séparé
                start = time.perf_counter()
                thread = threading.Thread(
                    target=import_launch_subscriptions,
                    args=("PUBLICITE", dte_d, dte_f, request.user.uuid_identification, job_id),
                    daemon=True,
                )
                thread.start()
                time_thread_start = time.perf_counter() - start
                logger.info(f"[PUBLICITY_LAUNCH] thread_start: {time_thread_start:.4f}s")

                time_total = time.perf_counter() - start_total
                logger.info(f"[PUBLICITY_LAUNCH] TOTAL (success): {time_total:.4f}s")

                # Retourner JSON immédiatement
                return JsonResponse({"success": True, "job_id": job_id})

        else:
            time_total = time.perf_counter() - start_total
            logger.info(f"[PUBLICITY_LAUNCH] TOTAL (form_invalid): {time_total:.4f}s")
            logger.info(f"erreur form publicity_launch : {str(form.data)!r}")
            return JsonResponse(
                {"success": False, "error": "Erreur de validation du formulaire"}
            )

    start = time.perf_counter()
    context = {
        "en_cours": in_action,
        "titre_table": (
            "DES INTEGRATIONS SONT EN COURS, PATIENTEZ..."
            if in_action
            else "Génération des factures de Publicité"
        ),
        "form": form,
        "submit_url": "compta:publicity_launch",
        "progress_title": "Génération des factures de Publicité",
        "progress_icon": "📣",
        "task_type": "PUBLICITE",
    }
    time_context = time.perf_counter() - start
    logger.info(f"[PUBLICITY_LAUNCH] context_creation: {time_context:.4f}s")

    start = time.perf_counter()
    response = render(request, "compta/update_sales_launch.html", context=context)
    time_render = time.perf_counter() - start
    logger.info(f"[PUBLICITY_LAUNCH] render: {time_render:.4f}s")

    time_total = time.perf_counter() - start_total
    logger.info(f"[PUBLICITY_LAUNCH] TOTAL (GET): {time_total:.4f}s")
    return response


def services_launch(request):
    """Lancement de la génération des Prestations
    :param request: Request Django
    :return:
    """
    start_total = time.perf_counter()

    # On contrôle qu'il n'y ai pas des factures non finalisées, mais envoyées par mail
    start = time.perf_counter()
    not_finalize = control_insertion()
    time_control_insertion = time.perf_counter() - start
    logger.info(f"[SERVICES_LAUNCH] control_insertion: {time_control_insertion:.4f}s")

    if not_finalize:
        request.session["level"] = 50
        messages.add_message(
            request,
            50,
            (
                "Vous ne pouvez pas générer de factures de Prestations, "
                "car la facturation est déjà envoyée par mail, mais non finalisée"
            ),
        )
        context = {
            "titre_table": "Génération des factures de Prestations",
            "not_finalize": True,
            "submit_url": "compta:services_launch",
            "progress_title": "Génération des factures de Prestations",
            "progress_icon": "🛠️",
        }
        time_total = time.perf_counter() - start_total
        logger.info(f"[SERVICES_LAUNCH] TOTAL (not_finalize): {time_total:.4f}s")
        return render(request, "compta/update_sales_launch.html", context=context)

    start = time.perf_counter()
    form = MonthForm(request.POST or None)
    in_action = get_in_progress()
    time_form_init = time.perf_counter() - start
    logger.info(f"[SERVICES_LAUNCH] form_init + get_in_progress: {time_form_init:.4f}s")

    if request.method == "POST" and not in_action:

        if form.is_valid():
            start = time.perf_counter()
            dte_d, dte_f = form.cleaned_data.get("periode").split("_")
            time_form_valid = time.perf_counter() - start
            logger.info(f"[SERVICES_LAUNCH] form_validation: {time_form_valid:.4f}s")

            start = time.perf_counter()
            text_error_familly = get_missing_cosium_familly(dte_d, dte_f)
            time_check_family = time.perf_counter() - start
            logger.info(f"[SERVICES_LAUNCH] get_missing_cosium_familly: {time_check_family:.4f}s")

            if text_error_familly:
                time_total = time.perf_counter() - start_total
                logger.info(f"[SERVICES_LAUNCH] TOTAL (error_family): {time_total:.4f}s")
                return JsonResponse(
                    {"success": False, "error": text_error_familly}
                )

            start = time.perf_counter()
            have_subs = get_have_subscriptions("PRESTATIONS", dte_d, dte_f)
            time_check_subs = time.perf_counter() - start
            logger.info(f"[SERVICES_LAUNCH] get_have_subscriptions: {time_check_subs:.4f}s")

            if have_subs:
                message = (
                    "Les Abonnements de Prestations pour cette période ont déjà été générés!. "
                    "Si vous souhaitez en ajouter, "
                    "supprimez les Abonnements de Prestations et refaite la génération."
                )
                time_total = time.perf_counter() - start_total
                logger.info(f"[SERVICES_LAUNCH] TOTAL (already_exists): {time_total:.4f}s")
                return JsonResponse(
                    {"success": False, "error": message}
                )

            else:
                user_pk = request.user.id
                job_id = str(uuid.uuid4())  # Générer un job_id unique

                # Créer le SSEProgress AVANT de lancer la tâche
                start = time.perf_counter()
                total_files = 1
                task_type = "prestations_import"
                custom_title = "Génération des factures de Prestations"

                progress = SSEProgress.objects.create(
                    job_id=job_id,
                    user_id=user_pk,
                    total_items=total_files,
                    task_type=task_type,
                    custom_title=custom_title,
                    metadata={"success": [], "failed": []},
                )
                progress.mark_as_started()
                time_create_progress = time.perf_counter() - start
                logger.info(f"[SERVICES_LAUNCH] create_SSEProgress: {time_create_progress:.4f}s")

                # Lancement d'un thread séparé
                start = time.perf_counter()
                thread = threading.Thread(
                    target=import_launch_subscriptions,
                    args=("PRESTATIONS", dte_d, dte_f, request.user.uuid_identification, job_id),
                    daemon=True,
                )
                thread.start()
                time_thread_start = time.perf_counter() - start
                logger.info(f"[SERVICES_LAUNCH] thread_start: {time_thread_start:.4f}s")

                time_total = time.perf_counter() - start_total
                logger.info(f"[SERVICES_LAUNCH] TOTAL (success): {time_total:.4f}s")

                # Retourner JSON immédiatement
                return JsonResponse({"success": True, "job_id": job_id})

        else:
            time_total = time.perf_counter() - start_total
            logger.info(f"[SERVICES_LAUNCH] TOTAL (form_invalid): {time_total:.4f}s")
            logger.info(f"erreur form services_launch : {str(form.data)!r}")
            return JsonResponse(
                {"success": False, "error": "Erreur de validation du formulaire"}
            )

    start = time.perf_counter()
    context = {
        "en_cours": in_action,
        "titre_table": (
            "DES INTEGRATIONS SONT EN COURS, PATIENTEZ..."
            if in_action
            else "Génération des factures de Prestations"
        ),
        "form": form,
        "submit_url": "compta:services_launch",
        "progress_title": "Génération des factures de Prestations",
        "progress_icon": "🛠️",
        "task_type": "PRESTATIONS",
    }
    time_context = time.perf_counter() - start
    logger.info(f"[SERVICES_LAUNCH] context_creation: {time_context:.4f}s")

    start = time.perf_counter()
    response = render(request, "compta/update_sales_launch.html", context=context)
    time_render = time.perf_counter() - start
    logger.info(f"[SERVICES_LAUNCH] render: {time_render:.4f}s")

    time_total = time.perf_counter() - start_total
    logger.info(f"[SERVICES_LAUNCH] TOTAL (GET): {time_total:.4f}s")
    return response
