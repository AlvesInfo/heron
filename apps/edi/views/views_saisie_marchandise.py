# pylint: disable=E0401,W1203,W0718,R0914
"""
FR : Module des vues pour les saisies et visualisation des marchandises
EN : Views module for entering and viewing goods

Commentaire:

created at: 2023-01-04
created by: Paulo ALVES

modified at: 2023-01-04
modified by: Paulo ALVES
"""
import json

from django.contrib import messages
from django.shortcuts import render, reverse, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.db import transaction

from heron.loggers import LOGGER_VIEWS
from apps.accountancy.bin.utilities import get_youngests_vat_rate
from apps.edi.bin.duplicates_check import check_invoice_exists
from apps.edi.bin.edi_utilites import (
    set_trace_hand_invoice,
    data_dict_invoices_clean,
    get_query_articles,
)
from apps.edi.bin.set_hand_invoices import set_hand_invoice
from apps.edi.forms import (
    CreateBaseMarchandiseForm,
    CreateMarchandiseInvoiceForm,
    CreateBaseFormationForm,
    CreateFormationInvoiceForm,
    CreateBasePersonnelForm,
    CreatePersonnelInvoiceForm,
)

# 1. CREATION DE FACTURES DE MARCHANDISES

CATEGORIES_DICT = {
    "marchandises": {
        "titre_table": "Saisie de Facture de Marchandises",
        "form": CreateBaseMarchandiseForm,
        "details_form": CreateMarchandiseInvoiceForm,
        "query_articles": False,
    },
    "formation": {
        "titre_table": "Saisie de Facture de Formations",
        "form": CreateBaseFormationForm,
        "details_form": CreateFormationInvoiceForm,
        "query_articles": True,
    },
    "personnel": {
        "titre_table": "Saisie de Facture de Personnel",
        "form": CreateBasePersonnelForm,
        "details_form": CreatePersonnelInvoiceForm,
        "query_articles": True,
    },
}


@csrf_protect
@transaction.atomic
def create_hand_invoices(request, category):
    """View de création des factures par saisie manuelle.

    Dans le template il y aura des affichages en fonction des catégories. Si une catégorie
    est ajoutée ou enlevée, il faudra procéder au nettoyage du template aussi.

    Dans le template :
        - les Articles ont un data-models="articles"
        - les CCT ont un data-models="maisons"

    Les data-models servent à ce que l'appel de l'api renvoyant les données,
    sache quelle est la fonction à appliquer.

    L'url appelée est "api_models_query/<str:models>/<str:query>/",
    ou models est ce qu'il y a dans data-models.

    La view endpoint apps/core/views/api_models_query, va remplir les champs avec les fonctions
    du dictionnaire MODEL_DICT, ou la keys est le data-models et sa fonction correspondante,
    qui est dans apps/core/bin/api_get_models.py

    :param request:  Request au sens Django
    :param category:  Catégorie de facturation
    """

    if category not in CATEGORIES_DICT:
        return redirect("home")

    level = 50
    nb_display = 50
    titre_table, invoice_form, details_form, query_articles = CATEGORIES_DICT.get(category).values()
    data = {"success": "ko"}

    if request.is_ajax() and request.method == "POST":
        user = request.user
        data_dict = json.loads(request.POST.get("data"))
        data_dict_invoices_clean(category, data_dict)

        # On vérifie si il y a des lignes dans le POST, si il n'y en a pas on renvoie un message
        # d'erreur pour ne pas insérer des factures vides, et on shortcut
        if not data_dict.get("lignes"):
            request.session["level"] = level
            messages.add_message(request, level, "Aucunes des lignes saisies n'avaient d'articles")

            return JsonResponse(data)

        try:
            form = invoice_form(data_dict.get("entete"))
            message = ""

            # On valide l'entête
            if form.is_valid():
                entete = form.cleaned_data
                third_party_num = entete.get("third_party_num")
                invoice_number = entete.get("invoice_number", "")
                invoice_date = entete.get("invoice_date")

                # On vérifie que cette facture n'existe pas
                if check_invoice_exists(
                    third_party_num,
                    invoice_number,
                    invoice_date.year,
                ):
                    error = True
                    message = f"La facture N°{invoice_number}, de {third_party_num} existe déjà!"

                    # On trace l'erreur, car cela ne se fera pas sans appel à set_hand_invoice()
                    set_trace_hand_invoice(
                        invoice_category=category,
                        invoice_number=invoice_number,
                        user=user,
                        errors=True,
                    )

                else:
                    # Si l'entête est bon, on va essayer de créer la facture complète
                    error, message = set_hand_invoice(
                        category, details_form, entete, data_dict.get("lignes"), user
                    )

                if not error:
                    level = 20

                request.session["level"] = level
                messages.add_message(request, level, message)

                return JsonResponse(data)

            # Si le formulaire d'entête est invalide, on génère le message à afficher
            for error_list in dict(form.errors).values():
                message += (
                    f", {', '.join(list(error_list))}" if message else ", ".join(list(error_list))
                )

            # On trace l'erreur, car cela ne se fera pas sans appel à set_hand_invoice()
            set_trace_hand_invoice(
                invoice_category=category,
                invoice_number=data_dict.get("entete").get("invoice_number", ""),
                user=user,
                errors=True,
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

            # On trace l'erreur, car cela ne se fera pas sans appel à set_hand_invoice()
            set_trace_hand_invoice(
                invoice_category=category,
                invoice_number=data_dict.get("entete").get("invoice_number", ""),
                user=user,
                errors=True,
            )

            return JsonResponse(data)

    template = "edi/invoice_hand_update.html"

    context = {
        "titre_table": titre_table,
        "nb_display": nb_display,
        "range_display": range(1, nb_display + 1),
        "chevron_retour": reverse("home"),
        "form_base": invoice_form(),
        "url_saisie": reverse("edi:create_hand_invoices", kwargs={"category": category}),
        "category": category,
        "query_articles": get_query_articles(category) if query_articles else "",
        "form_detail": details_form(),
        "vat_list": get_youngests_vat_rate(),
    }

    return render(request, template, context=context)


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
