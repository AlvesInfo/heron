# pylint: disable=E0401,W1203
"""
Views des Abonnements
"""

from django.shortcuts import render
from django.contrib import messages

from heron.loggers import LOGGER_VIEWS
from apps.periods.forms import MonthForm
from apps.compta.bin.validations_subscriptions import (
    get_have_subscriptions,
    get_missing_cosium_familly,
)
from apps.parameters.bin.core import get_in_progress
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
        }
        return render(request, "compta/update_sales_launch.html", context=context)

    form = MonthForm(request.POST or None)
    in_action = get_in_progress()

    if request.method == "POST":

        if form.is_valid():
            dte_d, dte_f = form.cleaned_data.get("periode").split("_")
            text_error_familly = get_missing_cosium_familly(dte_d, dte_f)

            if text_error_familly:
                request.session["level"] = 50
                messages.add_message(request, 50, text_error_familly)

            elif get_have_subscriptions("ROYALTIES", dte_d, dte_f):
                message = (
                    "Les Royalties pour cette période ont déjà été générées!. "
                    "Si vous souhaitez en ajouter, "
                    "supprimez les Royalties et refaite la génération."
                )
                request.session["level"] = 50
                messages.add_message(request, 50, message)

            else:

                erreur, info = import_launch_subscriptions(
                    "ROYALTIES", dte_d, dte_f, request.user.uuid_identification
                )
                level = 50 if erreur else 20
                request.session["level"] = level
                messages.add_message(request, level, info)
        else:
            LOGGER_VIEWS.exception(f"erreur form royalties_launch : {str(form.data)!r}")

    context = {
        "en_cours": in_action,
        "titre_table": (
            "DES INTEGRATIONS SONT EN COURS, PATIENTEZ..."
            if in_action
            else "Génération des factures de Royalties"
        ),
        "form": form,
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
        }
        return render(request, "compta/update_sales_launch.html", context=context)

    form = MonthForm(request.POST or None)
    in_action = get_in_progress()

    if request.method == "POST":

        if form.is_valid():
            dte_d, dte_f = form.cleaned_data.get("periode").split("_")
            text_error_familly = get_missing_cosium_familly(dte_d, dte_f)

            if text_error_familly:
                request.session["level"] = 50
                messages.add_message(request, 50, text_error_familly)

            elif get_have_subscriptions("MEULEUSE", dte_d, dte_f):
                message = (
                    "Les redevances Meuleuses pour cette période ont déjà été générées!. "
                    "Si vous souhaitez en ajouter, "
                    "supprimez les redevances Meuleuses et refaite la génération."
                )
                request.session["level"] = 50
                messages.add_message(request, 50, message)

            else:
                erreur, info = import_launch_subscriptions(
                    "MEULEUSE", dte_d, dte_f, request.user.uuid_identification
                )
                level = 50 if erreur else 20
                request.session["level"] = level
                messages.add_message(request, level, info)

        else:
            LOGGER_VIEWS.exception(f"erreur form meuleuse_launch : {str(form.data)!r}")

    context = {
        "en_cours": in_action,
        "titre_table": (
            "DES INTEGRATIONS SONT EN COURS, PATIENTEZ..."
            if in_action
            else "Génération des factures de Meuleuses"
        ),
        "form": form,
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
        }
        return render(request, "compta/update_sales_launch.html", context=context)

    form = MonthForm(request.POST or None)
    in_action = get_in_progress()

    if request.method == "POST":

        if form.is_valid():
            dte_d, dte_f = form.cleaned_data.get("periode").split("_")
            text_error_familly = get_missing_cosium_familly(dte_d, dte_f)

            if text_error_familly:
                request.session["level"] = 50
                messages.add_message(request, 50, text_error_familly)

            elif get_have_subscriptions("PUBLICITE", dte_d, dte_f):
                message = (
                    "Les redevances de Publicité pour cette période ont déjà été générées!. "
                    "Si vous souhaitez en ajouter, "
                    "supprimez les redevances de Publicité et refaite la génération."
                )
                request.session["level"] = 50
                messages.add_message(request, 50, message)

            else:
                erreur, info = import_launch_subscriptions(
                    "PUBLICITE", dte_d, dte_f, request.user.uuid_identification
                )
                level = 50 if erreur else 20
                request.session["level"] = level
                messages.add_message(request, level, info)

        else:
            LOGGER_VIEWS.exception(f"erreur form publicity_launch : {str(form.data)!r}")

    context = {
        "en_cours": in_action,
        "titre_table": (
            "DES INTEGRATIONS SONT EN COURS, PATIENTEZ..."
            if in_action
            else "Génération des factures de Publicité"
        ),
        "form": form,
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
        }
        return render(request, "compta/update_sales_launch.html", context=context)

    form = MonthForm(request.POST or None)
    in_action = get_in_progress()

    if request.method == "POST":

        if form.is_valid():
            dte_d, dte_f = form.cleaned_data.get("periode").split("_")
            text_error_familly = get_missing_cosium_familly(dte_d, dte_f)

            if text_error_familly:
                request.session["level"] = 50
                messages.add_message(request, 50, text_error_familly)

            elif get_have_subscriptions("PRESTATIONS", dte_d, dte_f):
                message = (
                    "Les Abonnements de Prestations pour cette période ont déjà été générés!. "
                    "Si vous souhaitez en ajouter, "
                    "supprimez les Abonnements de Prestations et refaite la génération."
                )
                request.session["level"] = 50
                messages.add_message(request, 50, message)

            else:
                erreur, info = import_launch_subscriptions(
                    "PRESTATIONS", dte_d, dte_f, request.user.uuid_identification
                )
                level = 50 if erreur else 20
                request.session["level"] = level
                messages.add_message(request, level, info)

        else:
            LOGGER_VIEWS.exception(f"erreur form services_launch : {str(form.data)!r}")

    context = {
        "en_cours": in_action,
        "titre_table": (
            "DES INTEGRATIONS SONT EN COURS, PATIENTEZ..."
            if in_action
            else "Génération des factures de Prestations"
        ),
        "form": form,
    }

    return render(request, "compta/update_sales_launch.html", context=context)
