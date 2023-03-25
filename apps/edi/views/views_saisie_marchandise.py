# pylint: disable=E0401,W1203,W0718
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
from apps.edi.bin.duplicates_check import check_invoice_exists
from apps.edi.bin.set_hand_invoices import set_hand_invoice
from apps.edi.bin.edi_utilites import set_trace_hand_invoice
from apps.edi.forms import CreateBaseInvoiceForm

# 1. CREATION DE FACTURES DE MARCHANDISES

CATEGORIES_DICT = {
    "marchandises": "Saisie de Facture/Avoir de marchandises",
    "formations": "Saisie de Facture/Avoir de formations",
    "personnel": "Saisie de Facture/Avoir de personnel",
}


@csrf_protect
@transaction.atomic
def create_hand_invoices(request, category):
    """View de création des factures par saisie manuelle"""
    nb_display = 10

    if category not in CATEGORIES_DICT:
        return redirect("home")

    context = {
        "titre_table": CATEGORIES_DICT.get(category),
        "nb_display": nb_display,
        "range_display": range(1, nb_display + 1),
        "chevron_retour": reverse("home"),
        "form_base": CreateBaseInvoiceForm(),
        "url_saisie": reverse("edi:create_hand_invoices", kwargs={"category": category}),
        "category": category,
    }
    data = {"success": "ko"}
    level = 50

    if request.is_ajax() and request.method == "POST":
        user = request.user
        data_dict = json.loads(request.POST.get("data"))

        try:
            form = CreateBaseInvoiceForm(data_dict.get("entete"))
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
                    # Si l'entête est bonne, on va essayer de créer la facture complète
                    error, message = set_hand_invoice(
                        category, entete, data_dict.get("lignes"), user
                    )

                if not error:
                    level = 20

                request.session["level"] = level
                messages.add_message(request, level, message)

                return JsonResponse(data)

            else:
                # Si le formulaire d'entête est invalide, on génère le message à afficher
                for error_list in dict(form.errors).values():
                    message += (
                        f", {', '.join(list(error_list))}"
                        if message
                        else ", ".join(list(error_list))
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
