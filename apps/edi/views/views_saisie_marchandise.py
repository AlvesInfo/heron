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
from typing import Dict
from copy import deepcopy
import html

from django.shortcuts import render, redirect, reverse
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.forms import formset_factory, modelformset_factory
from django.views.generic import CreateView, UpdateView

from heron.loggers import LOGGER_VIEWS
from apps.core.bin.assembly_formset import get_request_formset, get_request_formset_to_form
from apps.core.bin.change_traces import ChangeTraceMixin, trace_form_change
from apps.edi.bin.edi_tools import get_sens
from apps.edi.models import EdiImport
from apps.parameters.models import Category
from apps.edi.forms import INVOICES_CREATE_FIELDS, CreateInvoiceForm

# 1. MARCHANDISES


def get_edi_import_elements(requect_dict: Dict) -> Dict:
    """Ajoute les éléments manquants du formulaire"""


def create_invoice_marchandises(request):
    """Fonction de création de factures manuelle par saisie"""
    count_elements = 100
    nb_display = 1
    InvoiceMarchandiseFormset = modelformset_factory(
        EdiImport, form=CreateInvoiceForm, fields=INVOICES_CREATE_FIELDS, extra=nb_display
    )
    context = {
        "titre_table": f"Saisie de Facture / Avoir",
        "nb_elements": range(count_elements),
        "count_elements": count_elements,
        "nb_display": nb_display,
        "chevron_retour": reverse("home"),
        "formset": InvoiceMarchandiseFormset(queryset=EdiImport.objects.none()),
        "border_color": "darkgray",
    }

    if request.method == "POST":
        print(request.POST)
        # request_dict = deepcopy(request.POST.dict())
        # sens_dict = get_sens(request_dict.pop("form-__prefix__-sens"))
        # base_data = {
        #     **{
        #         "third_party_num": request_dict.pop("form-__prefix__-third_party_num"),
        #         "invoice_number": request_dict.pop("form-__prefix__-invoice_number"),
        #         "invoice_date": request_dict.pop("form-__prefix__-invoice_date"),
        #         "invoice_type": request_dict.pop("form-__prefix__-invoice_type"),
        #         "devise": request_dict.pop("form-__prefix__-devise"),
        #     },
        #     **sens_dict,
        # }
        #
        # for i in range(int(request_dict.get("form-TOTAL_FORMS"))):
        #     request_dict.pop(f"form-{i}-sens")
        #
        # print("base_data : ", base_data)
        # data_dict = get_request_formset_to_form(request_dict, base_data)
        #
        # print("formset data_dict : ", data_dict)
        # # print("request.POST : ", request.POST.dict())
        # # formset = CreateInvoiceForm(data_dict)
        # # print("formset.is_valid() : ", formset.is_valid())
        #
        # for _, values_dict in data_dict.items():
        #     values_dict["vat"] = [html.unescape(values_dict["vat"])]
        #     print(values_dict["cct_uuid_identification"], type(values_dict["cct_uuid_identification"]))
        #     values_dict["cct_uuid_identification"] = [values_dict["cct_uuid_identification"].replace("&#x27;", "")]
        #     print(values_dict)
        #     form = CreateInvoiceForm(values_dict)
        #     if form.is_valid():
        #         print(form.cleaned_data)
        #     else:
        #         print(form.errors)
        #     print("form.is_valid() : ", form.is_valid())

        formset = InvoiceMarchandiseFormset(request.POST)
        if formset.is_valid():
            print(formset.data)
        else:
            print(formset.errors)
        # for i, form in enumerate(formset):
        #     print(f"form ({i}) is valid : ", form.is_valid())
        #     if form.is_valid():
        #         print(form.cleaned_data)

    return render(request, "edi/invoice_marchandise_update.html", context=context)


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
