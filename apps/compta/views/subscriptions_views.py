# pylint: disable=E0401,W1203
"""
Views des Abonnements
"""

import uuid
import threading

from django.shortcuts import render, reverse
from django.http import JsonResponse

from apps.periods.forms import MonthForm
from apps.compta.bin.validations_subscriptions import (
    get_have_subscriptions,
    get_missing_cosium_familly,
)
from apps.parameters.bin.core import (
    have_action_in_progress,
    have_send_email_without_finalize,
    have_subscription,
    set_message,
)
from apps.core.models import SSEProgress
from apps.edi.loops.imports_loop_pool import (
    import_launch_subscriptions,
)
from heron.loggers import LOGGER_EDI

# Configuration du logger pour afficher dans la console sans duplication
logger = LOGGER_EDI

ROYALTIES_TEMPLATE = "compta/update_sales_launch.html"
EN_COURS = "Il y a des générations en cours, réessayez plus tard !"
ERROR_FORM = "Erreur de validation du formulaire"
GEN_PUBLICITE = "Génération des factures de Publicité"
ABONNEMENT = "Il n'y pas de Maison avec cet abonnement!"


def royalties_launch(request):
    """Lancement de la génération des Royalties
    :param request: Request Django
    :return:
    """
    TITRE_PRINICIPAL = "Génération des factures de Royalties"
    form = MonthForm(request.POST or None)
    task_type = "ROYALTIES"
    subscription_exists = have_subscription(subscription_name=task_type)
    context = {
        "en_cours": False,
        "margin_table": 50,
        "titre_table": TITRE_PRINICIPAL,
        "submit_url": "compta:royalties_launch",
        "progress_title": TITRE_PRINICIPAL,
        "progress_icon": "💰",
        "form": form,
        "subscription_exists": subscription_exists,
        "button_name": "royalties_launch",
        "url": reverse("compta:royalties_launch"),
        "display_button": True,
    }

    if not subscription_exists:
        set_message(request, 50, ABONNEMENT)
        context["display_button"] = False

        return render(request, ROYALTIES_TEMPLATE, context=context)

    in_action = have_action_in_progress()

    if in_action:
        set_message(request, 50, EN_COURS)
        context["display_button"] = False

        return render(request, ROYALTIES_TEMPLATE, context=context)

    not_finalize = have_send_email_without_finalize()

    if not_finalize:
        message = (
            "Vous ne pouvez pas générer de Royalties, "
            "car la facturation est déjà envoyée par mail, mais non finalisée"
        )
        set_message(request, 50, message)
        context.update(
            {
                "not_finalize": True,
            }
        )
        context["display_button"] = False

        return render(request, ROYALTIES_TEMPLATE, context=context)

    if request.method == "POST":
        if form.is_valid():
            dte_d, dte_f = form.cleaned_data.get("periode").split("_")
            text_error_familly = get_missing_cosium_familly(dte_d, dte_f)

            if text_error_familly:
                set_message(request, 50, text_error_familly)
                return JsonResponse({"success": False, "error": text_error_familly})

            have_subs = get_have_subscriptions("ROYALTIES", dte_d, dte_f)

            if have_subs:
                message = (
                    "Les Royalties pour cette période ont déjà été générées!. "
                    "Si vous souhaitez en ajouter, "
                    "supprimez les Royalties et refaite la génération."
                )
                set_message(request, 50, message)
                return JsonResponse({"success": False, "error": message})

            user_pk = request.user.id
            job_id = str(uuid.uuid4())  # Générer un job_id unique

            # Créer le SSEProgress AVANT de lancer la tâche
            total_files = 1

            progress = SSEProgress.objects.create(
                job_id=job_id,
                user_id=user_pk,
                total_items=total_files,
                task_type=task_type,
                custom_title=TITRE_PRINICIPAL,
                metadata={"success": [], "failed": []},
            )
            progress.mark_as_started()

            # Lancement d'un thread séparé
            thread = threading.Thread(
                target=import_launch_subscriptions,
                args=(
                    task_type,
                    dte_d,
                    dte_f,
                    request.user.uuid_identification,
                    job_id,
                ),
                daemon=True,
            )
            thread.start()

            # Retourner JSON immédiatement
            return JsonResponse({"success": True, "job_id": job_id})

        else:
            logger.exception(f"erreur form royalties_launch : {str(form.data)!r}")
            set_message(request, 50, ERROR_FORM)

            return JsonResponse({"success": False, "error": ERROR_FORM})

    return render(request, ROYALTIES_TEMPLATE, context=context)


def meuleuse_launch(request):
    """Lancement de la génération des Meuleuses
    :param request: Request Django
    :return:
    """
    TITRE_PRINICIPAL = "Génération des factures de Meuleuses"
    form = MonthForm(request.POST or None)
    task_type = "MEULEUSE"
    subscription_exists = have_subscription(subscription_name=task_type)
    context = {
        "en_cours": False,
        "margin_table": 50,
        "titre_table": TITRE_PRINICIPAL,
        "submit_url": "compta:meuleuse_launch",
        "progress_icon": "💰",
        "progress_title": TITRE_PRINICIPAL,
        "form": form,
        "subscription_exists": subscription_exists,
        "button_name": "meuleuse_launch",
        "url": reverse("compta:meuleuse_launch"),
        "display_button": True,
    }

    if not subscription_exists:
        set_message(request, 50, ABONNEMENT)
        context["display_button"] = False

        return render(request, ROYALTIES_TEMPLATE, context=context)

    in_action = have_action_in_progress()

    if in_action:
        set_message(request, 50, EN_COURS)

        context["display_button"] = False
        return render(request, ROYALTIES_TEMPLATE, context=context)

    not_finalize = have_send_email_without_finalize()

    if not_finalize:
        message = (
            "Vous ne pouvez pas générer de factures de Meuleuses, "
            "car la facturation est déjà envoyée par mail, mais non finalisée"
        )
        set_message(request, 50, message)
        context.update(
            {
                "not_finalize": True,
            }
        )
        context["display_button"] = False

        return render(request, ROYALTIES_TEMPLATE, context=context)

    if request.method == "POST":
        if form.is_valid():
            dte_d, dte_f = form.cleaned_data.get("periode").split("_")
            text_error_familly = get_missing_cosium_familly(dte_d, dte_f)

            if text_error_familly:
                set_message(request, 50, text_error_familly)
                return JsonResponse({"success": False, "error": text_error_familly})

            have_subs = get_have_subscriptions("MEULEUSE", dte_d, dte_f)

            if have_subs:
                message = (
                    "Les redevances Meuleuses pour cette période ont déjà été générées!. "
                    "Si vous souhaitez en ajouter, "
                    "supprimez les redevances Meuleuses et refaite la génération."
                )
                set_message(request, 50, message)

                return JsonResponse({"success": False, "error": message})

            user_pk = request.user.id
            job_id = str(uuid.uuid4())  # Générer un job_id unique

            # Créer le SSEProgress AVANT de lancer la tâche
            total_files = 1

            progress = SSEProgress.objects.create(
                job_id=job_id,
                user_id=user_pk,
                total_items=total_files,
                task_type=task_type,
                custom_title=TITRE_PRINICIPAL,
                metadata={"success": [], "failed": []},
            )
            progress.mark_as_started()

            # Lancement d'un thread séparé
            thread = threading.Thread(
                target=import_launch_subscriptions,
                args=(
                    task_type,
                    dte_d,
                    dte_f,
                    request.user.uuid_identification,
                    job_id,
                ),
                daemon=True,
            )
            thread.start()

            # Retourner JSON immédiatement
            return JsonResponse({"success": True, "job_id": job_id})

        else:
            logger.exception(f"erreur form meuleuse_launch : {str(form.data)!r}")
            return JsonResponse({"success": False, "error": ERROR_FORM})

    return render(request, ROYALTIES_TEMPLATE, context=context)


def publicity_launch(request):
    """Lancement de la génération des Publicités
    :param request: Request Django
    :return:
    """
    TITRE_PRINICIPAL = GEN_PUBLICITE
    form = MonthForm(request.POST or None)
    task_type = "PUBLICITE"
    subscription_exists = have_subscription(subscription_name=task_type)
    context = {
        "en_cours": False,
        "margin_table": 50,
        "titre_table": TITRE_PRINICIPAL,
        "submit_url": "compta:publicity_launch",
        "progress_title": TITRE_PRINICIPAL,
        "progress_icon": "💰",
        "form": form,
        "subscription_exists": subscription_exists,
        "button_name": "publicity_launch",
        "url": reverse("compta:publicity_launch"),
        "display_button": True,
    }

    if not subscription_exists:
        set_message(request, 50, ABONNEMENT)
        context["display_button"] = False

        return render(request, ROYALTIES_TEMPLATE, context=context)

    in_action = have_action_in_progress()

    if in_action:
        set_message(request, 50, EN_COURS)
        context["display_button"] = False

        return render(request, ROYALTIES_TEMPLATE, context=context)

    not_finalize = have_send_email_without_finalize()

    if not_finalize:
        message = (
            "Vous ne pouvez pas générer de factures de Publicité, "
            "car la facturation est déjà envoyée par mail, mais non finalisée"
        )
        set_message(request, 50, message)
        context.update(
            {
                "not_finalize": True,
            }
        )
        context["display_button"] = False

        return render(request, ROYALTIES_TEMPLATE, context=context)

    if request.method == "POST":
        if form.is_valid():
            dte_d, dte_f = form.cleaned_data.get("periode").split("_")
            text_error_familly = get_missing_cosium_familly(dte_d, dte_f)

            if text_error_familly:
                set_message(request, 50, text_error_familly)

                return JsonResponse({"success": False, "error": text_error_familly})

            have_subs = get_have_subscriptions("PUBLICITE", dte_d, dte_f)

            if have_subs:
                message = (
                    "Les redevances de Publicité pour cette période ont déjà été générées!. "
                    "Si vous souhaitez en ajouter, "
                    "supprimez les redevances de Publicité et refaite la génération."
                )
                set_message(request, 50, message)

                return JsonResponse({"success": False, "error": message})

            user_pk = request.user.id
            job_id = str(uuid.uuid4())  # Générer un job_id unique

            # Créer le SSEProgress AVANT de lancer la tâche

            total_files = 1

            progress = SSEProgress.objects.create(
                job_id=job_id,
                user_id=user_pk,
                total_items=total_files,
                task_type=task_type,
                custom_title=TITRE_PRINICIPAL,
                metadata={"success": [], "failed": []},
            )
            progress.mark_as_started()

            # Lancement d'un thread séparé
            thread = threading.Thread(
                target=import_launch_subscriptions,
                args=(
                    task_type,
                    dte_d,
                    dte_f,
                    request.user.uuid_identification,
                    job_id,
                ),
                daemon=True,
            )
            thread.start()

            # Retourner JSON immédiatement
            return JsonResponse({"success": True, "job_id": job_id})

        else:
            logger.exception(f"erreur form publicity_launch : {str(form.data)!r}")
            return JsonResponse({"success": False, "error": ERROR_FORM})

    return render(request, ROYALTIES_TEMPLATE, context=context)


def services_launch(request):
    """Lancement de la génération des Prestations
    :param request: Request Django
    :return:
    """
    TITRE_PRINICIPAL = "Génération des factures de Prestations"
    form = MonthForm(request.POST or None)
    task_type = "PRESTATIONS"
    subscription_exists = have_subscription(subscription_name=task_type)
    context = {
        "en_cours": False,
        "margin_table": 50,
        "titre_table": TITRE_PRINICIPAL,
        "submit_url": "compta:services_launch",
        "progress_title": TITRE_PRINICIPAL,
        "progress_icon": "💰",
        "form": form,
        "subscription_exists": subscription_exists,
        "button_name": "services_launch",
        "url": reverse("compta:services_launch"),
        "display_button": True,
    }

    if not subscription_exists:
        set_message(request, 50, ABONNEMENT)
        context["display_button"] = False

        return render(request, ROYALTIES_TEMPLATE, context=context)

    in_action = have_action_in_progress()

    if in_action:
        set_message(request, 50, EN_COURS)
        context["display_button"] = False

        return render(request, ROYALTIES_TEMPLATE, context=context)

    not_finalize = have_send_email_without_finalize()

    if not_finalize:
        message = (
            "Vous ne pouvez pas générer de factures de Prestations, "
            "car la facturation est déjà envoyée par mail, mais non finalisée"
        )
        set_message(request, 50, message)
        context.update(
            {
                "not_finalize": True,
            }
        )
        context["display_button"] = False

        return render(request, ROYALTIES_TEMPLATE, context=context)

    if request.method == "POST":
        if form.is_valid():
            dte_d, dte_f = form.cleaned_data.get("periode").split("_")
            text_error_familly = get_missing_cosium_familly(dte_d, dte_f)

            if text_error_familly:
                set_message(request, 50, text_error_familly)

                return JsonResponse({"success": False, "error": text_error_familly})

            have_subs = get_have_subscriptions("PRESTATIONS", dte_d, dte_f)

            if have_subs:
                message = (
                    "Les Abonnements de Prestations pour cette période ont déjà été générés!. "
                    "Si vous souhaitez en ajouter, "
                    "supprimez les Abonnements de Prestations et refaite la génération."
                )
                set_message(request, 50, message)

                return JsonResponse({"success": False, "error": message})

            user_pk = request.user.id
            job_id = str(uuid.uuid4())  # Générer un job_id unique

            # Créer le SSEProgress AVANT de lancer la tâche

            total_files = 1

            progress = SSEProgress.objects.create(
                job_id=job_id,
                user_id=user_pk,
                total_items=total_files,
                task_type=task_type,
                custom_title=TITRE_PRINICIPAL,
                metadata={"success": [], "failed": []},
            )
            progress.mark_as_started()

            # Lancement d'un thread séparé

            thread = threading.Thread(
                target=import_launch_subscriptions,
                args=(
                    task_type,
                    dte_d,
                    dte_f,
                    request.user.uuid_identification,
                    job_id,
                ),
                daemon=True,
            )
            thread.start()

            # Retourner JSON immédiatement
            return JsonResponse({"success": True, "job_id": job_id})

        else:
            logger.exception(f"erreur form services_launch : {str(form.data)!r}")
            return JsonResponse({"success": False, "error": ERROR_FORM})

    return render(request, ROYALTIES_TEMPLATE, context=context)
