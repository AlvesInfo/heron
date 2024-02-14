# pylint: disable=E0401,W1203,W0703
"""
Views des Abonnements
"""
import pendulum
from django.db import connection
from django.shortcuts import render, redirect, reverse
from django.contrib import messages

from heron.loggers import LOGGER_VIEWS
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.periods.forms import MonthForm
from apps.compta.excel_outputs.output_excel_sales_cosium import excel_sales_cosium
from apps.compta.excel_outputs.output_excel_ca_cosium import excel_ca_cosium
from apps.compta.models import CaClients
from apps.compta.models import VentesCosium
from apps.edi.models import EdiImport
from apps.compta.bin.generate_ca import set_ca
from apps.compta.imports.import_ventes_cosium import (
    force_update_sales,
    set_cct_ventes,
    update_exchange_rates,
)


def export_sales_cosium(request):
    """Export des ventes Cosium par périodes"""
    form = MonthForm(request.POST or None)

    try:
        if request.method == "POST" and form.is_valid():
            dte_d, dte_f = form.cleaned_data.get("periode").split("_")

            today = pendulum.now()
            file_name = (
                f"VENTES_COSIUM_{dte_d}_{dte_f}_"
                f"{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"
            )
            return response_file(excel_sales_cosium, file_name, CONTENT_TYPE_EXCEL, dte_d, dte_f)

        if form.errors:
            LOGGER_VIEWS.exception(f"erreur form : {str(form.data)!r}")

    except Exception as error:
        LOGGER_VIEWS.exception(f"erreur export_sales_cosium : {error!r}")

    context = {
        "titre_table": "VENTES COSIUM PAR PERIODE",
        "form": form,
        "state": (
            VentesCosium.objects.values("pk").filter(cct_uuid_identification__isnull=True).exists()
        ),
    }

    return render(request, "compta/export_sales_cosium.html", context=context)


def export_ca_cosium(request):
    """Export des ventes Cosium par périodes"""
    form = MonthForm(request.POST or None)
    message_ca = ""

    try:
        if request.method == "POST" and form.is_valid():
            dte_d, dte_f = form.cleaned_data.get("periode").split("_")
            ca_exists = CaClients.objects.filter(date_ca__range=(dte_d, dte_f)).exists()

            if ca_exists:
                today = pendulum.now()
                file_name = (
                    f"CA_PAR_MAISONS_FAMILLES_{dte_d}_{dte_f}_"
                    f"{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"
                )
                return response_file(excel_ca_cosium, file_name, CONTENT_TYPE_EXCEL, dte_d, dte_f)

            else:
                message_ca = "Le CA pour cette période, semble ne pas avoir été importé"

        if form.errors:
            LOGGER_VIEWS.exception(f"erreur form : {str(form.data)!r}")

    except Exception as error:
        LOGGER_VIEWS.exception(f"erreur export_ca_cosium : {error!r}")

    context = {
        "titre_table": "CA MAISONS/FAMILLES PAR PERIODE",
        "form": form,
        "state": (
            CaClients.objects.values("pk").filter(cct_uuid_identification__isnull=True).exists()
        ),
        "message_ca": message_ca
    }

    return render(request, "compta/export_ca_cosium.html", context=context)


def reset_clients_in_sales(request):
    """Mise à jour forcée des ctt manquants au cas où un cct a été ajouté"""
    try:
        with connection.cursor() as cursor:
            set_cct_ventes(cursor)

        request.session["level"] = 20
        messages.add_message(request, 20, "La mise à jour des cct a bien été effectuée!")

    except Exception as error:
        LOGGER_VIEWS.exception(f"erreur reset_clients_in_sales : {error!r}")

        request.session["level"] = 50
        messages.add_message(request, 50, "Une erreur c'est produite au reset des CCT !")

    return redirect(reverse("compta:export_sales_cosium"))


def reset_exhange_rates_in_sales(request):
    """Mise à jour forcée des taux de change"""
    form = MonthForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            dte_d, dte_f = form.cleaned_data.get("periode").split("_")
            update_exchange_rates(dte_d, dte_f)
            set_ca(dte_d, dte_f, request.user.uuid_identification)

            # Reset des Abonnements
            date_debut = pendulum.parse(dte_d)
            date_fin = pendulum.parse(dte_f)
            EdiImport.objects.filter(
                invoice_date__range=(date_debut, date_fin),
                flow_name__in=[
                    "ROYALTIES",
                    "MEULEUSE",
                    "PUBLICITE",
                    "PRESTATIONS",
                ],
            ).delete()
            message = (
                "Attention, Tous les abonnements, Royalties, Meuleuse, Publicité et Prestations, "
                "ont été supprimés, vous devez les regénérer manuellement !"
            )
            request.session["level"] = 20
            messages.add_message(request, 20, message)
            return redirect(reverse("compta:export_sales_cosium"))

        LOGGER_VIEWS.exception(f"erreur form reset_exhange_rates_in_sales : {str(form.data)!r}")
        request.session["level"] = 50
        messages.add_message(request, 50, "Une erreur c'est produite au reset des Ventes !")

    context = {
        "titre_table": "Mise à jour des taux de change dans les ventes",
        "form": form,
    }

    return render(request, "compta/reset_rates.html", context=context)


def reset_sales(request):
    """Mise à jour forcée des ventes, si erreur sur Ventes Cosium et après rectification"""
    form = MonthForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            dte_d, dte_f = form.cleaned_data.get("periode").split("_")
            force_update_sales(dte_d, dte_f)
            set_ca(dte_d, dte_f, request.user.uuid_identification)

            # Reset des Abonnements
            date_debut = pendulum.parse(dte_d)
            date_fin = pendulum.parse(dte_f)
            EdiImport.objects.filter(
                invoice_date__range=(date_debut, date_fin),
                flow_name__in=[
                    "ROYALTIES",
                    "MEULEUSE",
                    "PUBLICITE",
                    "PRESTATIONS",
                ],
            ).delete()

            return redirect("compta:export_sales_cosium")

        LOGGER_VIEWS.exception(f"erreur form reset_sales : {str(form.data)!r}")
        request.session["level"] = 50
        messages.add_message(request, 50, "Une erreur c'est produite au reset des Ventes !")

    context = {
        "titre_table": "Reset des ventes Cosium",
        "form": form,
        "avertissement": (
            "Attention, Tous les abonnements, Royalties, Meuleuse, Publicité et Prestations, "
            "seront également supprimé, vous devrez les regénérer manuellement !"
        ),
    }

    return render(request, "compta/update_sales_launch.html", context=context)


def reset_ca(request):
    """Reset du CA, si erreur sur Ventes Cosium et après rectification"""
    form = MonthForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            dte_d, dte_f = form.cleaned_data.get("periode").split("_")

            # Update des taux de change dans les ventes
            update_exchange_rates(dte_d, dte_f)

            # Reset des Abonnements
            date_debut = pendulum.parse(dte_d)
            date_fin = pendulum.parse(dte_f)
            CaClients.objects.filter(date_ca__range=(date_debut, date_fin)).delete()
            EdiImport.objects.filter(
                invoice_date__range=(date_debut, date_fin),
                flow_name__in=[
                    "ROYALTIES",
                    "MEULEUSE",
                    "PUBLICITE",
                    "PRESTATIONS",
                ],
            ).delete()
            set_ca(dte_d, dte_f, request.user.uuid_identification)

            return redirect("compta:export_ca_cosium")

        LOGGER_VIEWS.exception(f"erreur form reset_ca : {str(form.data)!r}")
        request.session["level"] = 50
        messages.add_message(request, 50, "Une erreur c'est produite au reset du CA !")

    context = {
        "titre_table": "Reset du Chiffre d'affaires Cosium",
        "form": form,
        "avertissement": (
            "Attention, Tous les abonnements, Royalties, Meuleuse, Publicité et Prestations, "
            "seront également supprimé, vous devrez les regénérer manuellement !"
        ),
    }

    return render(request, "compta/update_sales_launch.html", context=context)
