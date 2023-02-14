# pylint: disable=R0903,E0401,C0103,W0702,W0613,E1101,W1309,W1203
"""
Views des identifiants des Tiers X3
"""
import pendulum
from django.contrib import messages
from django.shortcuts import render, reverse, redirect
from django.db import transaction
from django.http import JsonResponse
from django.forms import modelformset_factory

from heron.loggers import LOGGER_VIEWS
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.core.bin.change_traces import trace_form_change, trace_change
from apps.core.bin.encoders import get_base_64
from apps.book.bin.checks import check_cct_identifier
from apps.edi.bin.set_suppliers_cct import (
    add_news_cct_sage,
    update_edi_import_cct_uui_identifiaction,
)
from apps.book.models import Society, SupplierCct
from apps.book.forms import SupplierCctForm, SupplierCctUnitForm
from apps.book.excel_outputs.book_excel_supplier_cct import excel_liste_supplier_cct

# Identifiants des tiers pour l'import des factures


@transaction.atomic
def supplier_cct_identifier(request, third_party_num, url_retour_supplier_cct):
    """UpdateView pour modification des couples Tiers/Code Maisons"""
    context = {}

    try:
        # Ajout des cct par défaut pour les maisons existantes, pour éviter de les saisir
        add_news_cct_sage(third_party_num=third_party_num, force_add=True)

        SupplierCctFormset = modelformset_factory(
            SupplierCct,
            fields=("id", "cct_identifier"),
            form=SupplierCctForm,
            extra=0,
        )
        queryset = (
            SupplierCct.objects.filter(third_party_num=third_party_num)
            .order_by("cct_uuid_identification__cct")
            .values(
                "id",
                "third_party_num",
                "cct_uuid_identification",
                "cct_uuid_identification__cct",
                "cct_uuid_identification__maison_cct__cct",
                "cct_uuid_identification__name",
                "cct_identifier",
                "cct_uuid_identification__maison_cct__immeuble",
                "cct_uuid_identification__maison_cct__adresse",
                "cct_uuid_identification__maison_cct__code_postal",
                "cct_uuid_identification__maison_cct__ville",
            )
        )
        context = {
            "titre_table": f"Identifiants des CCT pour le tiers {third_party_num}",
            "queryset": queryset,
            "count": queryset.count(),
            "chevron_retour": get_base_64(url_retour_supplier_cct)[0],
            "third_party_num": third_party_num,
        }
        request.session["level"] = 20

        if request.method == "POST":
            request.session["level"] = 50
            formset = SupplierCctFormset(request.POST, initial=queryset)
            message = ""

            if formset.is_valid():

                for form in formset:
                    if form.changed_data:
                        changed, message = check_cct_identifier(form.cleaned_data)

                        if changed is None:
                            messages.add_message(request, 50, message)
                        elif not changed:
                            messages.add_message(request, 50, message)
                        elif changed:
                            print("form.clean_data : ", form.cleaned_data, form)
                            trace_form_change(request, form)
                            message = (
                                "Les identifiants du cct "
                                f"{form.cleaned_data.get('id').cct_uuid_identification.cct}, "
                                "on bien été changés."
                            )
                            request.session["level"] = 20
                            messages.add_message(request, 20, message)

                            # Mise à jour du champ cct_uuid_identification
                            # dans edi_import quand il est null
                            update_edi_import_cct_uui_identifiaction()

                if not message:
                    messages.add_message(request, 50, "Vous n'avez rien modifié !")

            else:
                messages.add_message(
                    request, 50, f"Une erreur c'est produite, veuillez consulter les logs"
                )

                LOGGER_VIEWS.exception(f"erreur form : {formset.errors!r}")

    except Exception as error:
        request.session["level"] = 50
        messages.add_message(request, 50, f"Une erreur c'est produite, veuillez consulter les logs")
        LOGGER_VIEWS.exception(f"erreur form : {str(error)!r}")

    return render(request, "book/supplier_cct.html", context=context)


@transaction.atomic
def change_supplier_cct_unit(request):
    """Changement 1 à 1 des identifiants par fournisseurs"""

    if not request.is_ajax() and request.method != "POST":
        return redirect("home")

    data = {"success": "success"}
    form = SupplierCctUnitForm(request.POST)
    request.session["level"] = 50

    if form.is_valid() and form.cleaned_data:
        cct_identifier = form.cleaned_data.get("cct_identifier")

        if cct_identifier[-1] != "|":
            cct_identifier = f"{cct_identifier}|"

        get_supplier_cct = SupplierCct.objects.get(id=request.POST.get("pk"))

        changed, message = check_cct_identifier(
            {
                "id": get_supplier_cct,
                "cct_identifier": cct_identifier,
            }
        )

        if changed is None:
            messages.add_message(request, 50, message)

        elif not changed:
            messages.add_message(request, 50, message)

        elif changed:
            changed, message = trace_change(
                request,
                model=SupplierCct,
                before_kwargs={"id": get_supplier_cct.pk},
                update_kwargs={"cct_identifier": cct_identifier},
            )

            if not changed:
                messages.add_message(request, 50, message)

            else:
                message = (
                    "Les identifiants du cct "
                    f"{get_supplier_cct.cct_uuid_identification.cct}, "
                    "on bien été changés."
                )
                request.session["level"] = 20
                messages.add_message(request, 20, message)

                # Mise à jour du champ cct_uuid_identification dans edi_import quand il est null
                update_edi_import_cct_uui_identifiaction(
                    third_party_num=get_supplier_cct.third_party_num.third_party_num
                )

    else:
        messages.add_message(request, 50, f"Une erreur c'est produite : {form.errors}")
        LOGGER_VIEWS.exception(f"cct_change, form invalid : {form.errors!r}")

    return JsonResponse(data)


def export_list_supplier_cct(request, third_party_num):
    """
    Export Excel de la liste des Sociétés
    :param request: Request Django
    :param third_party_num: identification du tiers
    :return: response_file
    """
    try:
        if request.method == "GET":
            today = pendulum.now()
            file_name = (
                f"Identifiants_cct_{third_party_num}_"
                f"{today.format('Y_M_D')}{today.int_timestamp}.xlsx"
            )
            attr_dict = {
                "third_party_num": third_party_num,
            }
            return response_file(
                excel_liste_supplier_cct,
                file_name,
                CONTENT_TYPE_EXCEL,
                attr_dict,
            )

    except:
        request.session["level"] = 50
        messages.add_message(
            request,
            50,
            f"Une erreur c'est produite, lors de l'export du listing Excel des indentifiants CCT, "
            f"veuillez consulter les logs",
        )
        LOGGER_VIEWS.exception("view : export_list_supplier_cct")

    id_third_party_num = Society.objects.get(third_party_num=third_party_num)

    return redirect(reverse("book:society_update", kwargs={"pk": id_third_party_num.pk}))
