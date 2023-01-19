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

from django.shortcuts import render, reverse
from django.http import JsonResponse
from django.forms import modelformset_factory
from apps.edi.bin.edi_tools import get_sens
from apps.edi.models import EdiImport
from apps.edi.forms import INVOICES_CREATE_FIELDS, CreateInvoiceForm

# 1. MARCHANDISES


def get_edi_import_elements(requect_dict: Dict) -> Dict:
    """Ajoute les éléments manquants du formulaire"""


def create_invoice_marchandises(request):
    """Fonction de création de factures manuelle par saisie"""
    count_elements = 100
    nb_display = 2
    InvoiceMarchandiseFormset = modelformset_factory(
        EdiImport,
        form=CreateInvoiceForm,
        fields=INVOICES_CREATE_FIELDS,
        extra=nb_display,
        localized_fields="__all__",
    )
    context = {
        "titre_table": f"Saisie de Facture / Avoir",
        "nb_elements": range(count_elements),
        "count_elements": count_elements,
        "nb_display": nb_display,
        "chevron_retour": reverse("home"),
        "formset": InvoiceMarchandiseFormset(queryset=EdiImport.objects.none()),
        "border_color": "darkgray",
        "url_saisie": reverse("edi:create_invoice_marchandise"),
    }

    if request.method == "POST":
        print("request.POST : ", request.POST)
        formset = InvoiceMarchandiseFormset(request.POST)
        if formset.is_valid():
            print("formset : ", formset.is_valid())
            instances = formset.save(commit=False)
            print("instances : ", instances)

            for instance in instances:
                print(dir(instance))
                instance.save()

        else:
            print(formset.errors)

        data = {"success": "ko"}
        return JsonResponse(data)
        # if formset.is_valid():
        #     print("in formset valid")
        #     print("formset.is_valid() : ", formset.is_valid())
        #     formset.save(commit=False)
        #
        #     for form in formset.instance:
        #         print(form)
        #
        # else:
        #     print("in formset errors")
        #     print(formset.errors)
    print("to render")
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
