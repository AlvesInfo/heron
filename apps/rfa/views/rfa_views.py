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
from apps.rfa.bin.rfa_controls import supplier_control_validation
from apps.core.bin.change_traces import ChangeTraceMixin
from apps.core.bin.change_traces import trace_mark_delete
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.rfa.models import ClientExclusion
from apps.rfa.excel_outputs.rfa_clients_exclusion import excel_list_rfa_clients_exclusion
from apps.rfa.forms import ClientExclusionForm, DeleteClientExclusionForm


# ECRANS DES GENERATION DES RFA ====================================================================

def rfa_generation(request):
    """Vue de lancement des RFA"""
    context = {
        "titre_table": "GENERATION DES RFA",
    }
    if request.method == "GET":
        message_control = supplier_control_validation()

        if message_control:
            level = 50
            request.session["level"] = level
            messages.add_message(request, level, message_control)
            return redirect(reverse("validation_purchases:integration_purchases"))

    else:
        return render(request, "articles/articles_without_account.html", context=context)
