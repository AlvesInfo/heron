# pylint: disable=R0903,E0401,C0103,W0702,W0613
"""
Views des Tiers X3
"""
from pathlib import Path

from psycopg2 import sql
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import render, reverse
from django.views.generic import ListView, UpdateView
from django.db import connection
from django.db.models import Q
from django.forms import modelformset_factory, formsets

from heron.settings import MEDIA_EXCEL_FILES_DIR
from apps.core.bin.change_traces import ChangeTraceMixin
from apps.core.functions.functions_http_response import x_accel_exists_file_response
from apps.book.models import Society, SupplierCct
from apps.book.forms import SocietyForm, SupplierCctForm


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


def supplier_cct_identifier(request, third_party_num):
    """UpdateView pour modification des couples Tiers/Code Maisons"""
    sql_insert = sql.SQL(
        """
        insert into "book_suppliercct" as bb
        (
            "created_at",
            "modified_at",
            "third_party_num",
            "axe_cct",
            "cct_identifier"
        )
        select
            now() as "created_at",
            now() as "modified_at",
            %(third_party_num)s as "third_party_num",
            ac."uuid_identification" as "axe_cct",
            ac."cct" || '|' as "cct_identifier"
        from "accountancy_cctsage" ac
        left join book_suppliercct bs 
        on %(third_party_num)s = bs.third_party_num 
        and ac.uuid_identification = bs.axe_cct  
        where bs.axe_cct isnull
        on conflict do nothing
    """
    )

    with connection.cursor() as cursor:
        cursor.execute(sql_insert, {"third_party_num": third_party_num})

    SupplierCctFormset = modelformset_factory(
        SupplierCct,
        fields=("third_party_num", "axe_cct", "cct_identifier"),
        form=SupplierCctForm,
        extra=0,
    )
    queryset = SupplierCct.objects.filter(third_party_num=third_party_num).order_by("axe_cct")
    print(queryset)
    formset = SupplierCctFormset(request.POST or None)
    print("formset instancié")

    if request.method == "POST" and formset.is_valid():

        for form in formset:
            print(form.cleaned_data, form.changed_data)
        # if form.is_valid():
        #     return redirect("centers_clients:maisons_create", initials=str(uuid_pickler))
        #
        # else:
        #     LOGGER_VIEWS.exception(f"erreur form : {str(form.data)!r}")

    context = {
        "titre_table": "Création d'un Client avec import depuis la B.I",
        "formset": formset,
        "chevron_retour": reverse("centers_clients:maisons_list"),
    }
    return render(request, "book/test_formset.html", context=context)


# class SupplierCctIdentifier(ChangeTraceMixin, SuccessMessageMixin, UpdateView):
#     """UpdateView pour modification des couples Tiers/Code Maisons"""
#
#     model = SupplierCct
#     form_class = SupplierCctForm
#     formset_class = modelformset_factory(
#         SupplierCct,
#         fields=("third_party_num", "axe_cct", "cct_indentifier"),
#         formset=SupplierCctForm,
#     )
#     # formset = formsets(queryset=model.objects.filter(third_party_num=self.get('object').third_party_num))
#     form_class.use_required_attribute = False
#     template_name = "book/test_formset.html"
#     success_message = "Les CCT, pour le Tiers %(third_party_num)s ont été modifiés avec success"
#     error_message = (
#         "Les CCT, pour le Tiers %(third_party_num)s n'ont pu être modifiés, "
#         "une erreur c'est produite"
#     )
#     pk_url_kwarg = "third_party_num"
#
#     def get_context_data(self, **kwargs):
#         """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
#         print("get_context_data : ", kwargs)
#
#         sql_insert = sql.SQL(
#             """
#             insert into "book_suppliercct" as bb
#             (
#                 "created_at",
#                 "modified_at",
#                 "third_party_num",
#                 "axe_cct",
#                 "cct_indentifier"
#             )
#             select
#                 now() as "created_at",
#                 now() as "modified_at",
#                 'BAUS001' as "third_party_num",
#                 ac."uuid_identification" as "axe_cct",
#                 ac."cct" || '|' as "cct_indentifier"
#             from "accountancy_cctsage" ac
#             on conflict do nothing
#         """
#         )
#
#         with connection.cursor() as cursor:
#             cursor.execute(sql_insert)
#
#         context = super().get_context_data(**kwargs)
#         print(context)
#         context["chevron_retour"] = reverse("book:society_update", args=[963])
#         context["titre_table"] = (
#             f"Identifiants des CCT - " f"{context.get('object').third_party_num}"
#         )
#         return context
#
#     # def get_object(self, queryset=None):
#     #     """Renvoie l'objet que la vue affiche.
#     #     Requiert `self.queryset` et l'argument`third_party_num` dans l'URL.
#     #     """
#     #     print("get_object")
#     #     if queryset is None:
#     #         queryset = self.get_queryset()
#     #
#     #     pk = self.kwargs.get(self.pk_url_kwarg)
#     #
#     #     if pk is not None:
#     #         queryset = queryset.filter(third_party_num=pk)
#     #     else:
#     #         raise AttributeError(
#     #             "Generic detail view %s must be called with either an object "
#     #             "pk or a slug in the URLconf." % self.__class__.__name__
#     #         )
#     #
#     #     return queryset
#     #
#     # def get_queryset(self):
#     #     """
#     #     Retourne le queryset, en insérant les maison existantes par défaut,
#     #     si elle n'existent pas dans la table
#     #     """
#     #     print("get_queryset")
#     #     third_party_num = self.kwargs.get(self.pk_url_kwarg)
#     #     print("third_party_num : ", third_party_num)
#     #
#     #     sql_insert = sql.SQL(
#     #         """
#     #         insert into "book_suppliercct" as bb
#     #         (
#     #             "created_at",
#     #             "modified_at",
#     #             "third_party_num",
#     #             "axe_cct",
#     #             "cct_indentifier"
#     #         )
#     #         select
#     #             now() as "created_at",
#     #             now() as "modified_at",
#     #             'BAUS001' as "third_party_num",
#     #             ac."uuid_identification" as "axe_cct",
#     #             ac."cct" || '|' as "cct_indentifier"
#     #         from "accountancy_cctsage" ac
#     #         on conflict do nothing
#     #     """
#     #     )
#     #
#     #     with connection.cursor() as cursor:
#     #         cursor.execute(sql_insert)
#     #
#     #     self.queryset = self.model.objects.filter(third_party_num=third_party_num)
#     #
#     #     return self.queryset
#
#     def form_valid(self, form, **kwargs):
#         """
#         On surcharge la méthode form_valid
#         """
#         for unique_form in form:
#             unique_form.instance.modified_by = self.request.user
#             unique_form.save()
#
#         self.request.session["level"] = 20
#         return super().form_valid(form)
#
#     def form_invalid(self, form):
#         self.request.session["level"] = 50
#         return super().form_invalid(form)


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
