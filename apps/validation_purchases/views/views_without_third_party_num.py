# pylint: disable=E1101,W1203
"""
FR : Module qui change les integration venues sans tiers identifés
EN : Module that changes integrations without identified third parties

Commentaire:

created at: 2021-12-30
created by: Paulo ALVES

modified at: 2021-12-30
modified by: Paulo ALVES
"""

from django.contrib import messages
from django.http import JsonResponse

from heron.loggers import LOGGER_VIEWS

from django.db.models import Q, Count
from django.shortcuts import render, redirect, reverse

from apps.parameters.bin.core import get_in_progress
from apps.core.bin.change_traces import trace_change
from apps.book.models import Society
from apps.parameters.models import Category
from apps.edi.models import EdiImport
from apps.validation_purchases.forms import UpdateThirdpartynumForm


def purchase_without_suppliers(request):
    """Visualisation des intégrations sans Tiers Identifiés"""

    context = {
        "titre_table": "Factures Intégrées sans Tiers X3",
        "elements_list": EdiImport.objects.filter(
            Q(third_party_num="") | Q(third_party_num__isnull=True)
        )
        .values("uuid_identification", "third_party_num", "flow_name", "supplier", "supplier_ident")
        .annotate(dcount=Count("uuid_identification")),
        "form": UpdateThirdpartynumForm(),
        "margin_table": 50,
    }

    if get_in_progress():
        context["en_cours"] = True
        context["titre_table"] = "INTEGRATION EN COURS, PATIENTEZ..."

    return render(
        request, "validation_purchases/integration_without_third_party_num.html", context=context
    )


def purchase_without_suppliers_update(request):
    """Fonction d'insertion d'un tiers dans une intégration sans tiers X3"""

    if not request.is_ajax() and request.method != "POST":
        return redirect("home")

    data = {"success": "success"}
    form = UpdateThirdpartynumForm(request.POST)
    request.session["level"] = 50

    if form.is_valid() and form.cleaned_data:
        try:
            data_dict = form.cleaned_data
            third_party_num = data_dict.pop("third_party_num")
            society = Society.objects.get(third_party_num=third_party_num)
            old_center = society.centers_suppliers_indentifier or "|"

            if old_center[-1] == "|":
                old_center = old_center[:-1]

            center_identifier = (
                f"{old_center if old_center else ''}"
                f"{'|' if old_center else ''}"
                f"{data_dict.get('supplier_ident', '')}{'|' if data_dict.get('supplier_ident') else '|'}"
            )

            if form.changed_data:
                changed, message = trace_change(
                    request,
                    model=Society,
                    before_kwargs={"third_party_num": society.third_party_num},
                    update_kwargs={"centers_suppliers_indentifier": center_identifier},
                )

                if not changed:
                    messages.add_message(request, 50, message)

                else:
                    data_dict.pop("supplier")
                    old_message = message
                    update_kwargs = {
                        "third_party_num": third_party_num,
                        "supplier": society.name,
                    }
                    big_category_object = society.big_category_default

                    if not big_category_object:
                        big_category_object = Category.objects.filter(
                            slug_name="marchandises"
                        ).first()

                    if big_category_object:
                        update_kwargs["big_category_id"] = big_category_object

                    changed, message = trace_change(
                        request,
                        model=EdiImport,
                        before_kwargs=data_dict,
                        update_kwargs=update_kwargs,
                    )
                    message = old_message + message

                    if not changed:
                        messages.add_message(request, 50, message)
                    else:
                        message = (
                            f"L'intégration pour le flow name : {data_dict.get('flow_name')}, "
                            f"a bien comme nouveau tiers : {third_party_num}"
                        )
                        messages.add_message(request, 20, message)

                edi_without_third_part_num = (
                    EdiImport.objects.filter(
                        Q(third_party_num="") | Q(third_party_num__isnull=True)
                    )
                    .values(
                        "uuid_identification",
                        "third_party_num",
                        "flow_name",
                        "supplier",
                        "supplier_ident",
                    )
                    .annotate(dcount=Count("uuid_identification"))
                )

                if not edi_without_third_part_num:
                    data = {"success": reverse("validation_purchases:integration_purchases")}
                else:
                    data = {"success": "success"}

            else:
                messages.add_message(request, 50, "Vous n'avez rien modifié")

        except:
            messages.add_message(
                request, 50, "Une erreur c'est produite veuillez consulter les logs"
            )
            LOGGER_VIEWS.exception("view : purchase_without_suppliers_update")
    else:
        errors_list = []

        for key, errors in form.errors.items():
            error = errors.as_text().replace("* ", "").replace("\n", ", ")
            text_error = f"Erreur{'s' if len(errors) > 1 else ''} sur le champ {key} : {error}"
            errors_list.append(text_error)

        messages.add_message(request, 50, f"Une erreur c'est produite : {', '.join(errors_list)}")
        LOGGER_VIEWS.exception(f"cct_change, form invalid : {form.errors!r}")

    return JsonResponse(data)
