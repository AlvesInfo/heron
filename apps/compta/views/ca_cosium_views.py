# pylint: disable=E0401,W1203,W0703
"""
Views des Abonnements
"""
import pendulum
from django.db import connection
from django.shortcuts import render, redirect, reverse

from heron.loggers import LOGGER_VIEWS
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.periods.forms import MonthForm
from apps.compta.excel_outputs.output_excel_sales_cosium import excel_sales_cosium
from apps.compta.excel_outputs.output_excel_ca_cosium import excel_ca_cosium
from apps.compta.models import CaClients
from apps.edi.models import EdiImport
from apps.compta.bin.generate_ca import set_ca
from apps.compta.imports.import_ventes_cosium import force_update_sales, set_cct_ventes
from apps.compta.models import VentesCosium


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

    except Exception as error:
        print(error)
        LOGGER_VIEWS.exception(f"erreur form : {str(form.data)!r}")

    context = {
        "titre_table": "VENTES COSIUM PAR PERIODE",
        "form": form,
        "state": VentesCosium.objects.filter(cct_uuid_identification__isnull=True).exists(),
    }

    return render(request, "compta/export_sales_cosium.html", context=context)


def export_ca_cosium(request):
    """Export des ventes Cosium par périodes"""
    form = MonthForm(request.POST or None)

    try:

        if request.method == "POST" and form.is_valid():
            dte_d, dte_f = form.cleaned_data.get("periode").split("_")

            today = pendulum.now()
            file_name = (
                f"CA_PAR_MAISONS_FAMILLES_{dte_d}_{dte_f}_"
                f"{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"
            )
            return response_file(excel_ca_cosium, file_name, CONTENT_TYPE_EXCEL, dte_d, dte_f)

    except Exception as error:
        print(error)
        LOGGER_VIEWS.exception(f"erreur form : {str(form.data)!r}")

    context = {
        "titre_table": "CA MAISONS/FAMILLES PAR PERIODE",
        "form": form,
        "state": VentesCosium.objects.filter(cct_uuid_identification__isnull=True).exists(),
    }

    return render(request, "compta/export_sales_cosium.html", context=context)


def reset_clients_in_sales(_):
    """Mise à jour forcée des ctt manquants au cas où un cct à été ajouté"""
    with connection.cursor() as cursor:
        set_cct_ventes(cursor)

    return redirect(reverse("compta:export_sales_cosium"))


def reset_exhange_rates_in_sales(_):
    """Mise à jour forcée des ctt manquants au cas où un cct à été ajouté"""
    with connection.cursor() as cursor:
        set_cct_ventes(cursor)

    return redirect(reverse("compta:export_sales_cosium"))


def reset_sales(request):
    """Mise à jour forcée des ventes, si erreur sur Ventes Cosium et après rectification"""
    form = MonthForm(request.POST or None)

    if request.method == "POST":

        if form.is_valid():
            dte_d, dte_f = form.cleaned_data.get("periode").split("_")
            force_update_sales(dte_d, dte_f)
            set_ca(dte_d, dte_f, request.user.uuid_identification)

        else:
            LOGGER_VIEWS.exception(f"erreur form reset_ca : {str(form.data)!r}")

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

        else:
            LOGGER_VIEWS.exception(f"erreur form reset_ca : {str(form.data)!r}")

    context = {
        "titre_table": "Reset du Chiffre d'affaires Cosium",
        "form": form,
        "avertissement": (
            "Attention, Tous les abonnements, Royalties, Meuleuse, Publicité et Prestations, "
            "seront également supprimé, vous devrez les regénérer manuellement !"
        ),
    }

    return render(request, "compta/update_sales_launch.html", context=context)
