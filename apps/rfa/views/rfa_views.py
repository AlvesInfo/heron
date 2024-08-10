# pylint: disable=E0401
"""
Views de lancement des RFA
"""
import pendulum
from django.contrib import messages
from django.db import transaction, connection
from django.http import JsonResponse
from django.shortcuts import render, redirect, reverse
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import ListView, CreateView, UpdateView

from heron.loggers import LOGGER_VIEWS, LOGGER_EXPORT_EXCEL
from apps.rfa.bin.rfa_controls import (
    supplier_control_validation,
    supplier_control_cct,
    have_rfa_to_be_invoiced,
    get_rfa
)
from apps.rfa.forms import AxeRfaForm
from apps.rfa.loops.rfa_loop_pool import celery_rfa_generation_launch
from apps.core.bin.change_traces import ChangeTraceMixin
from apps.core.bin.change_traces import trace_mark_delete
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.rfa.models import ClientExclusion
from apps.rfa.excel_outputs.rfa_clients_exclusion import excel_list_rfa_clients_exclusion
from apps.rfa.forms import ClientExclusionForm, DeleteClientExclusionForm


# ECRANS DES GENERATION DES RFA ====================================================================


def rfa_generation(request):
    """Vue de lancement des RFA"""

    have_rfa = have_rfa_to_be_invoiced()
    form = AxeRfaForm(request.POST or None)

    if request.method == "GET":
        message_control = supplier_control_validation()

        if message_control:
            level = 50
            request.session["level"] = level
            messages.add_message(request, level, message_control)
            return redirect(reverse("validation_purchases:integration_purchases"))

        message_cct = supplier_control_cct()

        if message_cct:
            level = 50
            request.session["level"] = level
            messages.add_message(request, level, message_cct)
            return redirect(reverse("validation_purchases:integration_purchases"))

        if not have_rfa:
            level = 50
            request.session["level"] = level
            messages.add_message(request, level, "Il n'y a pas de RFA à générer")
            return redirect(reverse("validation_purchases:integration_purchases"))

    if request.method == "POST":
        if form.is_valid():
            section = form.cleaned_data.get("section")
            print("section : ", section, " - request.user.pk : ", request.user.pk)

            # placer un contrôle des taches en cours (rfa_generation)

            # lancer la tâche celery
            # celery_rfa_generation_launch(request.user.pk, )
    context = {
        "titre_table": "GENERATION DES RFA",
        "have_rfa": have_rfa,
        "form": form
    }
    for row in get_rfa():
        print(row)

    return render(request, "rfa/rfa_generation_list.html", context=context)
