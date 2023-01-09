# pylint: disable=R0903,E0401,C0103,W0702,W0613,E1101,W1309,W1203
"""
Views des Tiers X3
"""
from pathlib import Path

import pendulum
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import render, reverse, redirect
from django.views.generic import ListView, UpdateView
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.forms import modelformset_factory

from heron.settings import MEDIA_EXCEL_FILES_DIR
from heron.loggers import LOGGER_VIEWS
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.core.bin.change_traces import ChangeTraceMixin, trace_form_change, trace_change
from apps.core.bin.encoders import get_base_64, set_base_64_str
from apps.core.functions.functions_http_response import x_accel_exists_file_response
from apps.book.bin.checks import check_cct_identifier
from apps.edi.bin.set_suppliers_cct import (
    add_news_cct_sage,
    update_edi_import_cct_uui_identifiaction,
)
from apps.book.models import Society, SupplierCct
from apps.book.forms import SocietyForm, SupplierCctForm, SupplierCctUnitForm
from apps.book.excel_outputs.book_excel_supplier_cct import excel_liste_supplier_cct


# ECRANS DES FOURNISSEURS ==========================================================================
class SocietiesList(ListView):
    """View de la liste des Tiers X3"""

    model = Society
    context_object_name = "societies"
    template_name = "book/societies_list.html"
    extra_context = {"titre_table": "Tiers X3", "in_use": "alls"}
    queryset = Society.objects.filter(Q(is_client=True) | Q(is_supplier=True)).values(
        "third_party_num",
        "pk",
        "third_party_num",
        "name",
        "is_supplier",
        "is_client",
        "centers_suppliers_indentifier",
    )


class SocietiesInUseList(ListView):
    """View de la liste des Tiers X3, qui ont été utilisés dans les imports ou factures fournisseurs
    ou ceux qui ont été cochés en utilisation
    """

    model = Society
    context_object_name = "societies"
    template_name = "book/societies_list.html"
    extra_context = {
        "titre_table": "Tiers X3",
        "in_use": "in_use",
        "nb_paging": 50,
    }
    queryset = (
        Society.objects.filter(Q(is_client=True) | Q(is_supplier=True))
        .filter(in_use=True)
        .values(
            "third_party_num",
            "pk",
            "third_party_num",
            "name",
            "is_supplier",
            "is_client",
            "centers_suppliers_indentifier",
        )
    )


class SocietyUpdate(ChangeTraceMixin, SuccessMessageMixin, UpdateView):
    """UpdateView pour modification des Centrales Filles"""

    model = Society
    form_class = SocietyForm
    form_class.use_required_attribute = False
    template_name = "book/society_update.html"
    success_message = "Le Tiers %(third_party_num)s a été modifiée avec success"
    error_message = "Le Tiers %(third_party_num)s n'a pu être modifiée, une erreur c'est produite"
    extra_context = {}

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context_dict = super().get_context_data(**kwargs)
        pk = self.kwargs.get("pk")
        in_use = self.kwargs.get("in_use")
        context = {
            **context_dict,
            **{
                "chevron_retour": (
                    reverse("book:societies_list")
                    if in_use == "alls"
                    else reverse("book:societies_list_in_use")
                ),
                "titre_table": (
                    f"Mise à jour du Tiers : "
                    f"{context_dict.get('object').third_party_num} - "
                    f"{context_dict.get('object').name}"
                ),
                "adresse_principale_sage": (
                    context_dict.get("object").society_society.filter(default_adress=True).first()
                ),
                "compte_banque": (
                    context_dict.get("object").bank_society.filter(is_default=True).first()
                ),
                "third_party_num": context_dict.get("object").third_party_num,
                "pk": context_dict.get("object").pk,
                "url_retour_supplier_cct": set_base_64_str(
                    reverse("book:society_update", args=[pk, in_use])
                ),
            },
        }
        return context

    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        in_use = self.kwargs.get("in_use")
        return (
            reverse("book:societies_list")
            if in_use == "alls"
            else reverse("book:societies_list_in_use")
        )

    def form_valid(self, form, **kwargs):
        """
        On surcharge la méthode form_valid, pour ajouter les données, à la vollée,
        de l'adresse par défaut si la checkbox adresse_principale_sage est à true.
        """
        form.instance.modified_by = self.request.user
        self.request.session["level"] = 20
        copy_default_address = form.cleaned_data.get("copy_default_address")

        if copy_default_address:
            adress = self.get_context_data().get("adresse_principale_sage")
            if adress:
                self.object.immeuble = adress.line_01
                self.object.adresse = adress.line_02
                self.object.code_postal = adress.postal_code
                self.object.ville = adress.city
                self.object.pays = adress.country
                self.object.telephone = adress.phone_number_01
                self.object.mobile = adress.mobile_number
                self.object.email = adress.email_01
                self.object.save()

        form.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        self.request.session["level"] = 50
        return super().form_invalid(form)


def export_list_societies(request, file_name: str):
    """
    Export Excel de la liste des Sociétés
    :param request: Request Django
    :param file_name: Nom du fichier à downloader
    :return: response_file
    """
    file_dict = {
        "export_list_societies": "LISTING_DES_TIERS.xlsx",
        "export_list_clients": "LISTING_DES_CLIENTS.xlsx",
        "export_list_suppliers": "LISTING_DES_FOURNISSEURS.xlsx",
    }
    file = Path(MEDIA_EXCEL_FILES_DIR) / file_dict.get(file_name)
    response = x_accel_exists_file_response(file)

    return response


@transaction.atomic
def supplier_cct_identifier(request, third_party_num, url_retour_supplier_cct):
    """UpdateView pour modification des couples Tiers/Code Maisons"""
    context = {}

    try:
        # Ajout des cct par défaut pour les maisons existantes, pour éviter de les saisir
        add_news_cct_sage(third_party_num=third_party_num)
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
