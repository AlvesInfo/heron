# pylint: disable=E0401,W1203
"""
Views des Abonnements
"""

import uuid
import threading

from django.shortcuts import render
from django.contrib import messages
from django.http import JsonResponse

from heron.loggers import LOGGER_VIEWS
from apps.periods.forms import MonthForm
from apps.compta.bin.validations_subscriptions import (
    get_have_subscriptions,
    get_missing_cosium_familly,
)
from apps.parameters.bin.core import get_in_progress
from apps.core.models import SSEProgress
from apps.edi.loops.imports_loop_pool import import_launch_subscriptions
from apps.invoices.bin.pre_controls import control_insertion


def royalties_launch(request):
    """Lancement de la génération des Royalties
    :param request: Request Django
    :return:
    """
    # On contrôle qu'il n'y ait pas des factures non finalisées, mais envoyées par mail
    not_finalize = control_insertion()

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
        }
        return render(request, "compta/update_sales_launch.html", context=context)

    form = MonthForm(request.POST or None)
    in_action = get_in_progress()

    if request.method == "POST" and not in_action:

        if form.is_valid():
            dte_d, dte_f = form.cleaned_data.get("periode").split("_")
            text_error_familly = get_missing_cosium_familly(dte_d, dte_f)

            if text_error_familly:
                return JsonResponse(
                    {"success": False, "error": text_error_familly}
                )

            elif get_have_subscriptions("ROYALTIES", dte_d, dte_f):
                message = (
                    "Les Royalties pour cette période ont déjà été générées!. "
                    "Si vous souhaitez en ajouter, "
                    "supprimez les Royalties et refaite la génération."
                )
                return JsonResponse(
                    {"success": False, "error": message}
                )

            else:
                user_pk = request.user.id
                job_id = str(uuid.uuid4())  # Générer un job_id unique

                # Créer le SSEProgress AVANT de lancer la tâche
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

                # Lancement d'un thread séparé
                thread = threading.Thread(
                    target=import_launch_subscriptions,
                    args=("ROYALTIES", dte_d, dte_f, request.user.uuid_identification, job_id),
                    daemon=True,
                )
                thread.start()

                # Retourner JSON immédiatement
                return JsonResponse({"success": True, "job_id": job_id})

        else:
            LOGGER_VIEWS.exception(f"erreur form royalties_launch : {str(form.data)!r}")
            return JsonResponse(
                {"success": False, "error": "Erreur de validation du formulaire"}
            )

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

    return render(request, "compta/update_sales_launch.html", context=context)


def meuleuse_launch(request):
    """Lancement de la génération des Meuleuses
    :param request: Request Django
    :return:
    """
    # On contrôle qu'il n'y ait pas des factures non finalisées, mais envoyées par mail
    not_finalize = control_insertion()

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
        }
        return render(request, "compta/update_sales_launch.html", context=context)

    form = MonthForm(request.POST or None)
    in_action = get_in_progress()

    if request.method == "POST" and not in_action:

        if form.is_valid():
            dte_d, dte_f = form.cleaned_data.get("periode").split("_")
            text_error_familly = get_missing_cosium_familly(dte_d, dte_f)

            if text_error_familly:
                return JsonResponse(
                    {"success": False, "error": text_error_familly}
                )

            elif get_have_subscriptions("MEULEUSE", dte_d, dte_f):
                message = (
                    "Les redevances Meuleuses pour cette période ont déjà été générées!. "
                    "Si vous souhaitez en ajouter, "
                    "supprimez les redevances Meuleuses et refaite la génération."
                )
                return JsonResponse(
                    {"success": False, "error": message}
                )

            else:
                user_pk = request.user.id
                job_id = str(uuid.uuid4())  # Générer un job_id unique

                # Créer le SSEProgress AVANT de lancer la tâche
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

                # Lancement d'un thread séparé
                thread = threading.Thread(
                    target=import_launch_subscriptions,
                    args=("MEULEUSE", dte_d, dte_f, request.user.uuid_identification, job_id),
                    daemon=True,
                )
                thread.start()

                # Retourner JSON immédiatement
                return JsonResponse({"success": True, "job_id": job_id})

        else:
            LOGGER_VIEWS.exception(f"erreur form meuleuse_launch : {str(form.data)!r}")
            return JsonResponse(
                {"success": False, "error": "Erreur de validation du formulaire"}
            )

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

    return render(request, "compta/update_sales_launch.html", context=context)


def publicity_launch(request):
    """Lancement de la génération des Publicités
    :param request: Request Django
    :return:
    """
    # On contrôle qu'il n'y ait pas des factures non finalisées, mais envoyées par mail
    not_finalize = control_insertion()

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
        }
        return render(request, "compta/update_sales_launch.html", context=context)

    form = MonthForm(request.POST or None)
    in_action = get_in_progress()

    if request.method == "POST" and not in_action:

        if form.is_valid():
            dte_d, dte_f = form.cleaned_data.get("periode").split("_")
            text_error_familly = get_missing_cosium_familly(dte_d, dte_f)

            if text_error_familly:
                return JsonResponse(
                    {"success": False, "error": text_error_familly}
                )

            elif get_have_subscriptions("PUBLICITE", dte_d, dte_f):
                message = (
                    "Les redevances de Publicité pour cette période ont déjà été générées!. "
                    "Si vous souhaitez en ajouter, "
                    "supprimez les redevances de Publicité et refaite la génération."
                )
                return JsonResponse(
                    {"success": False, "error": message}
                )

            else:
                user_pk = request.user.id
                job_id = str(uuid.uuid4())  # Générer un job_id unique

                # Créer le SSEProgress AVANT de lancer la tâche
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

                # Lancement d'un thread séparé
                thread = threading.Thread(
                    target=import_launch_subscriptions,
                    args=("PUBLICITE", dte_d, dte_f, request.user.uuid_identification, job_id),
                    daemon=True,
                )
                thread.start()

                # Retourner JSON immédiatement
                return JsonResponse({"success": True, "job_id": job_id})

        else:
            LOGGER_VIEWS.exception(f"erreur form publicity_launch : {str(form.data)!r}")
            return JsonResponse(
                {"success": False, "error": "Erreur de validation du formulaire"}
            )

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

    return render(request, "compta/update_sales_launch.html", context=context)


def services_launch(request):
    """Lancement de la génération des Prestations
    :param request: Request Django
    :return:
    """
    # On contrôle qu'il n'y ait pas des factures non finalisées, mais envoyées par mail
    not_finalize = control_insertion()

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
        }
        return render(request, "compta/update_sales_launch.html", context=context)

    form = MonthForm(request.POST or None)
    in_action = get_in_progress()

    if request.method == "POST" and not in_action:

        if form.is_valid():
            dte_d, dte_f = form.cleaned_data.get("periode").split("_")
            text_error_familly = get_missing_cosium_familly(dte_d, dte_f)

            if text_error_familly:
                return JsonResponse(
                    {"success": False, "error": text_error_familly}
                )

            elif get_have_subscriptions("PRESTATIONS", dte_d, dte_f):
                message = (
                    "Les Abonnements de Prestations pour cette période ont déjà été générés!. "
                    "Si vous souhaitez en ajouter, "
                    "supprimez les Abonnements de Prestations et refaite la génération."
                )
                return JsonResponse(
                    {"success": False, "error": message}
                )

            else:
                user_pk = request.user.id
                job_id = str(uuid.uuid4())  # Générer un job_id unique

                # Créer le SSEProgress AVANT de lancer la tâche
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

                # Lancement d'un thread séparé
                thread = threading.Thread(
                    target=import_launch_subscriptions,
                    args=("PRESTATIONS", dte_d, dte_f, request.user.uuid_identification, job_id),
                    daemon=True,
                )
                thread.start()

                # Retourner JSON immédiatement
                return JsonResponse({"success": True, "job_id": job_id})

        else:
            LOGGER_VIEWS.exception(f"erreur form services_launch : {str(form.data)!r}")
            return JsonResponse(
                {"success": False, "error": "Erreur de validation du formulaire"}
            )

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

    return render(request, "compta/update_sales_launch.html", context=context)
