"""Views de lancement des RFA."""

from django.contrib import messages
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse

from apps.articles.models import Article
from apps.parameters.bin.core import get_actions_in_progress
from apps.rfa.bin.rfa_controls import (
    have_rfa_to_be_invoiced,
    supplier_control_cct,
    supplier_control_validation,
)
from apps.rfa.bin.rfa_insertions import get_open_period
from apps.rfa.forms import AxeRfaForm
from apps.rfa.loops.rfa_loop_pool import rfa_generation_launch

# ECRANS DES GENERATION DES RFA ====================================================================


def redirect_validation(request):
    """Retourne le redirect uri si les validations ne passent pas."""
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

    return None


def _have_new_articles():
    """Vrai s'il reste des articles nouveaux ou incomplets (axes, catégorie, rubrique)."""
    return Article.objects.filter(
        Q(new_article=True)
        | Q(error_sub_category=True)
        | Q(axe_bu__isnull=True)
        | Q(axe_prj__isnull=True)
        | Q(axe_pro__isnull=True)
        | Q(axe_pys__isnull=True)
        | Q(axe_rfa__isnull=True)
        | Q(big_category__isnull=True)
    ).exists()


def _set_message(request, level, message):
    """Pose le niveau de message en session et le message lui-même."""
    request.session["level"] = level
    messages.add_message(request, level, message)


def _launch_generation(request, have_rfa, period_rfa):
    """Lance la génération des RFA (si une période est ouverte) et revient à l'écran."""
    if get_open_period() is None:
        _set_message(
            request, 50, "Aucune période de facturation ouverte : génération des RFA impossible"
        )
    else:
        erreur, info = rfa_generation_launch(request.user.pk, have_rfa, period_rfa)
        _set_message(request, 50 if erreur else 20, info)

    return redirect(reverse("rfa:rfa_generation"))


def rfa_generation(request):
    """Vue de lancement des RFA."""
    in_action = get_actions_in_progress()
    form = AxeRfaForm(request.POST or None)
    have_rfa = have_rfa_to_be_invoiced()

    # on va vérifier qu'il n'y a pas de nouveaux articles
    if have_rfa and _have_new_articles():
        _set_message(
            request, 50, "Vous ne pouvez pas générer de RFA, car il y existe de nouveaux articles"
        )
        return redirect(reverse("articles:new_articles_list"))

    if not in_action and have_rfa:
        # Factures non validées ou sans CCT : on redirige vers l'écran de validation
        response = redirect_validation(request)

        if response is not None:
            return response

        if request.method == "POST" and form.is_valid():
            return _launch_generation(request, have_rfa, form.cleaned_data.get("section"))

    context = {
        "en_cours": in_action,
        "titre_table": (
            "DES INTEGRATIONS SONT EN COURS, PATIENTEZ..." if in_action else "GENERATION DES RFA"
        ),
        "have_rfa": have_rfa,
        "form": form,
    }

    return render(request, "rfa/rfa_generation_list.html", context=context)
