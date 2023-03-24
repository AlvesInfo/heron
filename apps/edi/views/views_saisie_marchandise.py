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

from django.contrib import messages
from django.shortcuts import render, reverse, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect

from heron.loggers import LOGGER_VIEWS
from apps.edi.bin.set_hand_invoices import check_invoice_exists, set_hand_invoice
from apps.edi.forms import CreateBaseInvoiceForm, CreateDetailsInvoiceForm

# 1. CREATION DE FACTURES DE MARCHANDISES


@csrf_protect
def create_hand_invoices(request, category):
    """Fonction de création de factures manuelle par saisie"""
    nb_display = 5

    categories_dict = {
        "marchandises": "marchandises",
        "formations": "formations",
        "personnel": "personnel",
    }

    context = {
        "titre_table": f"Saisie de Facture / Avoir",
        "nb_display": nb_display,
        "range_display": range(1, nb_display + 1),
        "chevron_retour": reverse("home"),
        "form_base": CreateBaseInvoiceForm(),
        "article": CreateDetailsInvoiceForm(),
        "url_saisie": reverse("edi:create_hand_invoices", kwargs={"category": category}),
    }
    data = {"success": "ko"}
    level = 50

    try:
        categorie_invoice = categories_dict.get(category)

        if categorie_invoice is None:
            return redirect("home")

        if request.is_ajax() and request.method == "POST":
            data_dict = json.loads(request.POST.get("data"))
            form = CreateBaseInvoiceForm(data_dict.get("entete"))
            message = ""

            if form.is_valid():
                entete = form.cleaned_data
                third_party_num = entete.get("third_party_num")
                invoice_number = entete.get("invoice_number", "")
                invoice_date = entete.get("invoice_date")

                if check_invoice_exists(
                    third_party_num,
                    invoice_number,
                    invoice_date.year,
                ):
                    error = True
                    message = f"La facture N°{invoice_number}, de {third_party_num} existe déjà!"

                else:
                    error, message = set_hand_invoice(
                        category, entete, data_dict.get("lignes"), request.user
                    )

                if not error:
                    level = 20

                request.session["level"] = level
                messages.add_message(request, level, message)

                return JsonResponse(data)

            else:
                for error_list in dict(form.errors).values():
                    message += (
                        f", {', '.join([error for error in error_list])}"
                        if message
                        else ", ".join([error for error in error_list])
                    )

            request.session["level"] = level
            messages.add_message(request, level, message)

            return JsonResponse(data)

    except Exception as error:
        request.session["level"] = level
        messages.add_message(
            request, level, "Une erreur c'est produite, veuillez consulter les logs"
        )
        LOGGER_VIEWS.exception(f"erreur form : {str(error)!r}")

        return JsonResponse(data)

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
