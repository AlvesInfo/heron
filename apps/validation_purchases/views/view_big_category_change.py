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

from apps.core.bin.change_traces import trace_change
from apps.core.functions.functions_http import is_ajax
from apps.edi.models import EdiImport
from apps.validation_purchases.forms import ChangeBigCategoryForm
from heron.loggers import LOGGER_VIEWS


def big_category_change(request):
    """Fonction de changement de la grande catégorie d'une ligne de facture."""
    if not is_ajax(request) or request.method != "POST":
        return redirect("home")

    data = {"success": "ko"}
    form = ChangeBigCategoryForm(request.POST)
    request.session["level"] = 50

    if form.is_valid() and form.cleaned_data:
        data_dict = form.cleaned_data

        # id absent (None) ou 0 : la ligne n'est pas ciblée par sa clé primaire
        if not data_dict.get("id"):
            data_dict.pop("id")

        data_dict.pop("big_category_default")
        data_dict.pop("uuid_origin")
        new_big_category = data_dict.pop("big_category")

        changed, message = trace_change(
            request,
            model=EdiImport,
            before_kwargs=data_dict,
            # l'uuid, pas l'instance : trace_change compare à la valeur stockée
            update_kwargs={"big_category_id": new_big_category.uuid_identification},
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
        LOGGER_VIEWS.error("big_category_change, form invalid : %r", form.errors)

    return JsonResponse(data)
