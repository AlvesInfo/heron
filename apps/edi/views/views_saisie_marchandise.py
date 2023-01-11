# pylint: disable=
"""
FR : Module des vues pour les saisies et visualisation des marchandises
EN : Views module for entering and viewing goods

Commentaire:

created at: 2023-01-04
created by: Paulo ALVES

modified at: 2023-01-04
modified by: Paulo ALVES
"""
from django.shortcuts import render, redirect, reverse
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.forms import formset_factory, modelformset_factory
from django.views.generic import CreateView, UpdateView

from heron.loggers import LOGGER_VIEWS
from apps.core.bin.assembly_formset import get_request_formset
from apps.core.bin.change_traces import ChangeTraceMixin, trace_form_change
from apps.edi.models import EdiImport
from apps.parameters.models import Category
from apps.edi.forms import INVOICES_CREATE_FIELDS, CreateInvoiceForm

# 1. MARCHANDISES
InvoiceMarchandiseFormset = modelformset_factory(EdiImport, fields=INVOICES_CREATE_FIELDS)


class InvoiceMarchandiseCreate(ChangeTraceMixin, SuccessMessageMixin, CreateView):
    """View de création des factures de marchandises"""

    model = EdiImport
    form_class = CreateInvoiceForm
    form_class.use_required_attribute = False
    template_name = "edi/invoice_marchandise_update.html"
    success_message = "La Facture N° %(invoice_number)s a été créé avec success"
    error_message = "La facture %(invoice_number)s n'a pu être créé, une erreur c'est produite"

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        count_elements = 50
        context = {
            **super().get_context_data(**kwargs),
            **{
                "titre_table": f"Facture de {Category.objects.get(slug_name='marchandises').name}",
                "nb_elements": range(count_elements),
                "count_elements": count_elements,
                "nb_display": 5,
                "chevron_retour": reverse("home"),
                "formset": InvoiceMarchandiseFormset(queryset=EdiImport.objects.none()),
            },
        }

        return context

    def post(self, request, *args, **kwargs):
        """On adapte la méthode post pour inclure les données générale telles que,
        third_party_num, delivery_number, delivery_date, ...
        """
        request_dict = request.POST.dict()
        base_data = {
            "big_category": request_dict.get("big_category"),
            "manual_entry": request_dict.get("manual_entry"),
            "cct_uuid_identification": request_dict.get("cct_uuid_identification"),
            "third_party_num": request_dict.get("third_party_num"),
            "invoice_number": request_dict.get("invoice_number"),
            "invoice_type": request_dict.get("invoice_type"),
            "invoice_date": request_dict.get("invoice_date"),
            "devise_choices": request_dict.get("devise_choices")
        }
        sens = request_dict.get("sens")

        if sens == "2":
            base_data["purchase_invoice"] = "on"
            base_data["sale_invoice"] = "on"
        elif sens == "1":
            base_data["purchase_invoice"] = "off"
            base_data["sale_invoice"] = "on"
        else:
            base_data["purchase_invoice"] = "on"
            base_data["sale_invoice"] = "off"

        data_dict = get_request_formset(request_dict, base_data)

        print(data_dict)

        formset = CreateInvoiceForm(request.POST)
        if formset.is_valid():
            return self.form_valid(formset)
        else:
            print(formset.errors)

    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        return reverse("home")

    @transaction.atomic
    def form_valid(self, form):
        form.instance.modified_by = self.request.user
        if not form.instance.libelle_heron:
            form.instance.libelle_heron = form.instance.libelle
        self.request.session["level"] = 20
        return super().form_valid(form)

    def form_invalid(self, form):
        self.request.session["level"] = 50
        return super().form_invalid(form)


# class InvoiceMarchandiseUpdate(ChangeTraceMixin, SuccessMessageMixin, UpdateView):
#     """UpdateView pour modification des identifiants pour les fournisseurs EDI"""
#
#     model = Article
#     form_class = ArticleForm
#     form_class.use_required_attribute = False
#     pk_url_kwarg = "pk"
#     template_name = "articles/article_update.html"
#     success_message = "L'Article %(reference)s a été modifié avec success"
#     error_message = "L'Article %(reference)s n'a pu être modifié, une erreur c'est produite"
#
#     def get(self, request, *args, **kwargs):
#         """Handle GET requests: instantiate a blank version of the form."""
#         self.third_party_num = self.kwargs.get("third_party_num", "")
#         self.object = self.get_object()
#         return super().get(request, *args, **kwargs)
#
#     def get_context_data(self, **kwargs):
#         """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
#         context = super().get_context_data(**kwargs)
#         context["chevron_retour"] = reverse(
#             "articles:articles_list",
#             args=(
#                 self.object.third_party_num.third_party_num,
#                 self.object.big_category.slug_name,
#             ),
#         )
#         context["titre_table"] = f"Mise à jour Article {str(self.object)}"
#         context["article"] = f"Article Référence : {self.object.reference}"
#         context["third_party_num"] = self.object.third_party_num.third_party_num
#         return context
#
#     def get_success_url(self):
#         """Return the URL to redirect to after processing a valid form."""
#         return reverse(
#             "articles:articles_list",
#             args=(
#                 self.object.third_party_num.third_party_num,
#                 self.object.big_category.slug_name,
#             ),
#         )
#
#     @transaction.atomic
#     def form_valid(self, form):
#         """Si le formulaire est valide"""
#         form.instance.modified_by = self.request.user
#         self.request.session["level"] = 20
#         return super().form_valid(form)
#
#     def form_invalid(self, form):
#         """On élève le niveau d'alerte en cas de formulaire invalide"""
#         self.request.session["level"] = 50
#         return super().form_invalid(form)
