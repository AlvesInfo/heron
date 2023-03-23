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
import json

from django.shortcuts import render, reverse, redirect
from django.http import JsonResponse
from django.forms import modelformset_factory

from heron.loggers import LOGGER_VIEWS
from apps.edi.bin.edi_utilites import get_sens
from apps.edi.models import EdiImport
from apps.edi.forms import CreateBaseInvoiceForm, CreateDetailsInvoiceForm

# 1. MARCHANDISES


def get_edi_import_elements(requect_dict: Dict) -> Dict:
    """Ajoute les éléments manquants du formulaire"""


from django.shortcuts import render


def create_invoice_marchandises(request):
    """Fonction de création de factures manuelle par saisie"""
    nb_display = 10

    context = {
        "titre_table": f"Saisie de Facture / Avoir",
        "nb_display": nb_display,
        "range_display": range(1, nb_display + 1),
        "chevron_retour": reverse("home"),
        "form_base": CreateBaseInvoiceForm(),
        "article": CreateDetailsInvoiceForm(),
        "url_saisie": reverse("edi:create_post_invoices"),
    }

    if request.method == "POST":
        print("request.POST : ", request.POST)
        # formset = InvoiceMarchandiseFormset(request.POST)
        #
        # if formset.is_valid():
        #     print("formset : ", formset.is_valid())
        #     instances = formset.save(commit=False)
        #     print("instances : ", instances)
        #
        #     for instance in instances:
        #         print(dir(instance))
        #         instance.save()
        #
        #     return JsonResponse({"success": "ok"})
        #
        # else:
        #     print(formset.errors)

    print("to render")
    return render(request, "edi/invoice_marchandise_update.html", context=context)


def create_post_invoices(request):
    """View de validation et création des factures"""

    if not request.is_ajax() and request.method != "POST":
        return redirect("home")

    data = {"success": "ko"}
    data_dict = json.loads(request.POST.get("data"))

    print(type(data_dict), data_dict)
    # id_pk = request.POST.get("pk")
    # # form = DeleteSupplierFamilyAxesForm({"id": id_pk})
    # if id_pk == 1:
    #     s = 1
    #     # if form.is_valid():
    #     #
    #     #     data = {"success": "success"}
    #
    # else:
    #     LOGGER_VIEWS.exception(f"create_post_invoices, form invalid : ")

    return JsonResponse(data)


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
