"""FR : Module qui change les CCT dans les écrans ou l'on peut modifier le CCT par double click.

EN : Module that changes the CCTs in the screens where you can modify the CCT by double click.

Commentaire:

created at: 2021-12-30
created by: Paulo ALVES

modified at: 2021-12-30
modified by: Paulo ALVES
"""

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect

from apps.centers_clients.models import Maison
from apps.core.bin.change_traces import trace_change
from apps.core.functions.functions_http import is_ajax
from apps.edi.models import EdiImport
from apps.validation_purchases.bin.validations_utilities import set_is_multi_store
from apps.validation_purchases.forms import ChangeCttForm
from heron.loggers import LOGGER_VIEWS


def cct_change(request):
    """Fonction de changement du cct d'une facture."""
    if not is_ajax(request) or request.method != "POST":
        return redirect("home")

    data = {"success": "ko"}
    form = ChangeCttForm(request.POST)
    request.session["level"] = 50

    if form.is_valid() and form.cleaned_data:
        data_dict = form.cleaned_data

        # id absent (None) ou 0 : la ligne n'est pas ciblée par sa clé primaire
        if not data_dict.get("id"):
            data_dict.pop("id")

        cct = Maison.objects.get(cct=data_dict.pop("cct"))

        changed, message = trace_change(
            request,
            EdiImport,
            data_dict,
            {"cct_uuid_identification_id": cct.uuid_identification},
        )

        if not changed:
            messages.add_message(request, 50, message)

        else:
            # On va updater si la facture est multi sociétés
            set_is_multi_store(
                data_dict["third_party_num"],
                data_dict["invoice_number"],
                data_dict["invoice_year"],
            )
            message = (
                f"La Facture n° {data_dict.get('invoice_number')}, a bien comme nouveau CCT :{cct}."
            )
            messages.add_message(request, 20, message)

        data = {"success": "success"}

    else:
        messages.add_message(request, 50, f"Une erreur c'est produite : {form.errors}")
        LOGGER_VIEWS.error("cct_change, form invalid : %r", form.errors)

    return JsonResponse(data)
