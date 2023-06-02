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
from apps.validation_purchases.forms import ChangeBigCategoryForm
from apps.edi.models import EdiImport


def big_category_change(request):
    """Fonction de changement du cct d'une facture"""

    if not request.is_ajax() and request.method != "POST":
        return redirect("home")

    data = {"success": "ko"}
    form = ChangeBigCategoryForm(request.POST)
    request.session["level"] = 50

    if form.is_valid() and form.cleaned_data:
        data_dict = form.cleaned_data

        if data_dict.get("id") == 0:
            data_dict.pop("id")

        data_dict.pop("big_category_default")
        data_dict.pop("uuid_origin")
        new_big_category = data_dict.pop("big_category")

        if form.changed_data:
            changed, message = trace_change(
                request,
                model=EdiImport,
                before_kwargs=data_dict,
                update_kwargs={"big_category_id": new_big_category},
            )

            if not changed:
                messages.add_message(request, 50, message)

            else:
                message = (
                    f"Les factures du tiers : {data_dict.get('third_party_num')}, "
                    f"ont bien comme nouvelle catégorie : {new_big_category.name}."
                )
                messages.add_message(request, 20, message)

        data = {"success": "success"}

    else:
        messages.add_message(request, 50, f"Une erreur c'est produite : {form.errors}")
        LOGGER_VIEWS.exception(f"cct_change, form invalid : {form.errors!r}")

    return JsonResponse(data)
