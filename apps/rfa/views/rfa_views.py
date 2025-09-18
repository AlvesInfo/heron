# pylint: disable=E0401
"""
Views de lancement des RFA
"""

from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render, redirect, reverse

from apps.articles.models import Article
from apps.rfa.bin.rfa_controls import (
    supplier_control_validation,
    supplier_control_cct,
    have_rfa_to_be_invoiced,
)
from apps.rfa.forms import AxeRfaForm
from apps.rfa.loops.rfa_loop_pool import rfa_generation_launch
from apps.parameters.bin.core import get_actions_in_progress

# ECRANS DES GENERATION DES RFA ====================================================================


def redirect_validation(request):
    """Retourne le redirect uri si les validations ne passent pas"""

    error_level = 50

    message_control = supplier_control_validation()

    if message_control:
        request.session["level"] = error_level
        messages.add_message(request, error_level, message_control)
        return redirect(reverse("validation_purchases:integration_purchases"))

    message_cct = supplier_control_cct()

    if message_cct:
        request.session["level"] = error_level
        messages.add_message(request, error_level, message_cct)
        return redirect(reverse("validation_purchases:integration_purchases"))


def rfa_generation(request):
    """Vue de lancement des RFA"""
    # on va vérifier qu'il n'y a pas de nouveaux articles
    in_action = get_actions_in_progress()
    form = AxeRfaForm(request.POST or None)
    have_rfa = have_rfa_to_be_invoiced()

    new_articles = Article.objects.filter(
        Q(new_article=True)
        | Q(error_sub_category=True)
        | Q(axe_bu__isnull=True)
        | Q(axe_prj__isnull=True)
        | Q(axe_pro__isnull=True)
        | Q(axe_pys__isnull=True)
        | Q(axe_rfa__isnull=True)
        | Q(big_category__isnull=True)
    )

    if new_articles:
        if have_rfa:
            level = 50
            request.session["level"] = level
            messages.add_message(
                request,
                level,
                "Vous ne pouvez pas générer de RFA, car il y existe de nouveaux articles",
            )

        return redirect(reverse("articles:new_articles_list"))

    if not in_action and have_rfa:
        if request.method == "GET":
            redirect_validation(request)

        if request.method == "POST" and form.is_valid():
            period_rfa = form.cleaned_data.get("section")

            # lancement du process de génération des RFA
            erreur, info = rfa_generation_launch(request.user.pk, have_rfa, period_rfa)
            level = 50 if erreur else 20
            request.session["level"] = level
            messages.add_message(request, level, info)

            return redirect(reverse("rfa:rfa_generation"))

    context = {
        "en_cours": in_action,
        "titre_table": (
            "DES INTEGRATIONS SONT EN COURS, PATIENTEZ..."
            if in_action
            else "GENERATION DES RFA"
        ),
        "have_rfa": have_rfa,
        "form": form,
    }

    return render(request, "rfa/rfa_generation_list.html", context=context)
