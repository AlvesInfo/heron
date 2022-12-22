# pylint: disable=R0903,E0401,C0103,W0702,W0613
"""
Views des Tiers X3
"""
from pathlib import Path

import pendulum
from psycopg2 import sql
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import render, reverse, redirect
from django.views.generic import ListView, UpdateView
from django.db import connection, transaction
from django.db.models import Q
from django.forms import modelformset_factory

from heron.settings import MEDIA_EXCEL_FILES_DIR
from heron.loggers import LOGGER_VIEWS
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.core.bin.change_traces import ChangeTraceMixin, trace_form_change
from apps.core.functions.functions_http_response import x_accel_exists_file_response
from apps.book.bin.checks import check_cct_identifier
from apps.book.models import Society, SupplierCct
from apps.book.forms import SocietyForm, SupplierCctForm
from apps.book.excel_outputs.book_excel_supplier_cct import excel_liste_supplier_cct


# ECRANS DES FOURNISSEURS ==========================================================================
class SocietiesList(ListView):
    """View de la liste des Tiers X3"""

    model = Society
    context_object_name = "societies"
    template_name = "book/societies_list.html"
    extra_context = {"titre_table": "Tiers X3"}
    queryset = Society.objects.filter(Q(is_client=True) | Q(is_supplier=True))


class SocietyUpdate(ChangeTraceMixin, SuccessMessageMixin, UpdateView):
    """UpdateView pour modification des Centrales Filles"""

    model = Society
    form_class = SocietyForm
    form_class.use_required_attribute = False
    template_name = "book/society_update.html"
    success_message = "Le Tiers %(third_party_num)s a été modifiée avec success"
    error_message = "Le Tiers %(third_party_num)s n'a pu être modifiée, une erreur c'est produite"

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["chevron_retour"] = reverse("book:societies_list")
        context["titre_table"] = (
            f"Mise à jour du Tiers : "
            f"{context.get('object').third_party_num} - "
            f"{context.get('object').name}"
        )
        context["adresse_principale_sage"] = (
            context.get("object").society_society.filter(default_adress=True).first()
        )
        context["compte_banque"] = (
            context.get("object").bank_society.filter(is_default=True).first()
        )
        context["third_party_num"] = context.get("object").third_party_num
        context["pk"] = context.get("object").pk
        return context

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

        return super().form_valid(form)

    def form_invalid(self, form):
        self.request.session["level"] = 50
        return super().form_invalid(form)


@transaction.atomic
def supplier_cct_identifier(request, third_party_num):
    """UpdateView pour modification des couples Tiers/Code Maisons"""
    context = {}

    try:

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
                "cct_uuid_identification__cct",
                "cct_uuid_identification__name",
                "cct_identifier",
            )
        )
        third_party_num_pk = Society.objects.get(third_party_num=third_party_num)

        context = {
            "titre_table": f"Identifiants des CCT pour le tiers {third_party_num}",
            "queryset": queryset,
            "count": queryset.count(),
            "chevron_retour": reverse("book:society_update", args=[third_party_num_pk.pk]),
            "third_party_num": third_party_num,
        }
        request.session["level"] = 20

        if request.method == "POST":
            formset = SupplierCctFormset(request.POST, initial=queryset)
            message = ""

            if formset.is_valid():
                for form in formset:
                    if form.changed_data:
                        changed, message = check_cct_identifier(form.cleaned_data)

                        if changed is None:
                            request.session["level"] = 50
                            messages.add_message(request, 50, message)
                        elif not changed:
                            request.session["level"] = 50
                            messages.add_message(request, 50, message)
                        elif changed:
                            trace_form_change(request, form)
                            message = (
                                "Les identifiants du cct "
                                f"{form.cleaned_data.get('id').cct_uuid_identification.cct}, "
                                "on bien été changés."
                            )
                            messages.add_message(request, 20, message)

                if not message:
                    request.session["level"] = 50
                    messages.add_message(request, 50, "Vous n'avez rien modifié !")

            elif formset.errors:
                request.session["level"] = 50
                messages.add_message(
                    request, 50, f"Une erreur c'est produite, veuillez consulter les logs"
                )
                LOGGER_VIEWS.exception(f"erreur form : {str(formset.data)!r}")

    except Exception as error:
        request.session["level"] = 50
        messages.add_message(request, 50, f"Une erreur c'est produite, veuillez consulter les logs")
        LOGGER_VIEWS.exception(f"erreur form : {str(error)!r}")

    return render(request, "book/supplier_cct.html", context=context)


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
        LOGGER_VIEWS.exception("view : export_list_supplier_cct")

    return redirect(
        reverse("book:supplier_cct_identifier", kwargs={"third_party_num": third_party_num})
    )
