# pylint: disable=E1101,W1203
"""
FR : Module qui change les CCT dans les écrans ou l'on peut modifier le CCT par double click
EN : Module that changes the CCTs in the screens where you can modify the CCT by double click

Commentaire:

created at: 2021-12-30
created by: Paulo ALVES

modified at: 2021-12-30
modified by: Paulo ALVES
"""

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect

from heron.loggers import LOGGER_VIEWS
from apps.core.bin.change_traces import trace_change
from apps.centers_clients.models import Maison
from apps.validation_purchases.forms import ChangeCttForm
from apps.edi.models import EdiImport


def cct_change(request):
    """Fonction de changement du cct d'une facture"""

    if not request.is_ajax() and request.method != "POST":
        return redirect("home")

    data = {"success": "ko"}
    form = ChangeCttForm(request.POST)
    request.session["level"] = 50

    if form.is_valid() and form.cleaned_data:
        data_dict = form.cleaned_data
        cct = Maison.objects.get(cct=data_dict.pop("cct"))

        if form.changed_data:
            changed, message = trace_change(
                request,
                EdiImport,
                data_dict,
                {"cct_uuid_identification_id": cct.uuid_identification},
            )

            if not changed:
                messages.add_message(request, 50, message)

            else:
                message = (
                    f"La Facture n° {data_dict.get('invoice_number')}, a bien comme nouveau CCT :"
                    f"{cct}."
                )
                messages.add_message(request, 20, message)

        data = {"success": "success"}

    else:
        messages.add_message(request, 50, f"Une erreur c'est produite : {form.errors}")
        LOGGER_VIEWS.exception(f"cct_change, form invalid : {form.errors!r}")

    return JsonResponse(data)
