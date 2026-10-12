"""Views des Abonnements."""

import threading
import uuid

from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse

from apps.compta.bin.validations_subscriptions import (
    get_have_subscriptions,
    get_missing_cosium_familly,
)
from apps.core.models import SSEProgress
from apps.edi.loops.imports_loop_pool import (
    import_launch_subscriptions,
)
from apps.parameters.bin.core import (
    have_action_in_progress,
    have_send_email_without_finalize,
    have_subscription,
    set_message,
)
from apps.periods.forms import MonthForm
from heron.loggers import LOGGER_EDI

# Configuration du logger pour afficher dans la console sans duplication
logger = LOGGER_EDI

ROYALTIES_TEMPLATE = "compta/update_sales_launch.html"
EN_COURS = "Il y a des générations en cours, réessayez plus tard !"
ERROR_FORM = "Erreur de validation du formulaire"
GEN_PUBLICITE = "Génération des factures de Publicité"
ABONNEMENT = "Il n'y pas de Maison avec cet abonnement!"


def _launch_post(
    request, form, task_type, titre_principal, deja_message, view_name, *, session_form_error=False
):
    """Traite le POST des vues de génération : contrôles, création de la jauge puis tâche en thread.

    :param deja_message: message renvoyé si la génération de la période existe déjà
    :param session_form_error: dépose aussi le message d'erreur du formulaire en session
    """
    if form.is_valid():
        dte_d, dte_f = form.cleaned_data.get("periode").split("_")
        text_error_familly = get_missing_cosium_familly(dte_d, dte_f)

        if text_error_familly:
            set_message(request, 50, text_error_familly)
            return JsonResponse({"success": False, "error": text_error_familly})

        if get_have_subscriptions(task_type, dte_d, dte_f):
            set_message(request, 50, deja_message)
            return JsonResponse({"success": False, "error": deja_message})

        user_pk = request.user.id
        job_id = str(uuid.uuid4())  # Générer un job_id unique

        # Créer le SSEProgress AVANT de lancer la tâche
        progress = SSEProgress.objects.create(
            job_id=job_id,
            user_id=user_pk,
            total_items=1,
            task_type=task_type,
            custom_title=titre_principal,
            metadata={"success": [], "failed": []},
        )
        progress.mark_as_started()

        # Lancement d'un thread séparé
        thread = threading.Thread(
            target=import_launch_subscriptions,
            args=(task_type, dte_d, dte_f, request.user.uuid_identification, job_id),
            daemon=True,
        )
        thread.start()

        # Retourner JSON immédiatement
        return JsonResponse({"success": True, "job_id": job_id})

    logger.error("erreur form %s : %r", view_name, str(form.data))

    if session_form_error:
        set_message(request, 50, ERROR_FORM)

    return JsonResponse({"success": False, "error": ERROR_FORM})


def royalties_launch(request):
    """Lancement de la génération des Royalties.

    :param request: Request Django
    :return:
    """
    titre_principal = "Génération des factures de Royalties"
    form = MonthForm(request.POST or None)
    task_type = "ROYALTIES"
    subscription_exists = have_subscription(subscription_name=task_type)
    context = {
        "en_cours": False,
        "margin_table": 50,
        "titre_table": titre_principal,
        "submit_url": "compta:royalties_launch",
        "progress_title": titre_principal,
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
        return _launch_post(
            request,
            form,
            task_type,
            titre_principal,
            (
                "Les Royalties pour cette période ont déjà été générées!. "
                "Si vous souhaitez en ajouter, "
                "supprimez les Royalties et refaite la génération."
            ),
            "royalties_launch",
            session_form_error=True,
        )

    return render(request, ROYALTIES_TEMPLATE, context=context)


def meuleuse_launch(request):
    """Lancement de la génération des Meuleuses.

    :param request: Request Django
    :return:
    """
    titre_principal = "Génération des factures de Meuleuses"
    form = MonthForm(request.POST or None)
    task_type = "MEULEUSE"
    subscription_exists = have_subscription(subscription_name=task_type)
    context = {
        "en_cours": False,
        "margin_table": 50,
        "titre_table": titre_principal,
        "submit_url": "compta:meuleuse_launch",
        "progress_icon": "💰",
        "progress_title": titre_principal,
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
        return _launch_post(
            request,
            form,
            task_type,
            titre_principal,
            (
                "Les redevances Meuleuses pour cette période ont déjà été générées!. "
                "Si vous souhaitez en ajouter, "
                "supprimez les redevances Meuleuses et refaite la génération."
            ),
            "meuleuse_launch",
        )

    return render(request, ROYALTIES_TEMPLATE, context=context)


def publicity_launch(request):
    """Lancement de la génération des Publicités.

    :param request: Request Django
    :return:
    """
    titre_principal = GEN_PUBLICITE
    form = MonthForm(request.POST or None)
    task_type = "PUBLICITE"
    subscription_exists = have_subscription(subscription_name=task_type)
    context = {
        "en_cours": False,
        "margin_table": 50,
        "titre_table": titre_principal,
        "submit_url": "compta:publicity_launch",
        "progress_title": titre_principal,
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
        return _launch_post(
            request,
            form,
            task_type,
            titre_principal,
            (
                "Les redevances de Publicité pour cette période ont déjà été générées!. "
                "Si vous souhaitez en ajouter, "
                "supprimez les redevances de Publicité et refaite la génération."
            ),
            "publicity_launch",
        )

    return render(request, ROYALTIES_TEMPLATE, context=context)


def services_launch(request):
    """Lancement de la génération des Prestations.

    :param request: Request Django
    :return:
    """
    titre_principal = "Génération des factures de Prestations"
    form = MonthForm(request.POST or None)
    task_type = "PRESTATIONS"
    subscription_exists = have_subscription(subscription_name=task_type)
    context = {
        "en_cours": False,
        "margin_table": 50,
        "titre_table": titre_principal,
        "submit_url": "compta:services_launch",
        "progress_title": titre_principal,
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
        return _launch_post(
            request,
            form,
            task_type,
            titre_principal,
            (
                "Les Abonnements de Prestations pour cette période ont déjà été générés!. "
                "Si vous souhaitez en ajouter, "
                "supprimez les Abonnements de Prestations et refaite la génération."
            ),
            "services_launch",
        )

    return render(request, ROYALTIES_TEMPLATE, context=context)
