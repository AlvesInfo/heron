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
from django.forms import formset_factory
from django.views.generic import CreateView, UpdateView

from heron.loggers import LOGGER_VIEWS
from apps.core.bin.change_traces import ChangeTraceMixin, trace_form_change
from apps.edi.models import EdiImport
from apps.parameters.models import Category
from apps.edi.forms import CreateInvoiceForm

# 1. MARCHANDISES


@transaction.atomic
def invoice_marchandise_create(request):
    """View de création des factures de marchandises"""
    context = {}

    try:
        # Ajout des cct par défaut pour les maisons existantes, pour éviter de les saisir
        count_elements = 50
        context = {
            "titre_table": f"Facture de {Category.objects.get(slug_name='marchandises').name}",
            "nb_elements": range(count_elements),
            "count_elements": count_elements,
            "nb_display": 10,
            "chevron_retour": reverse("home"),
            "form": CreateInvoiceForm(),
        }
        request.session["level"] = 20

        if request.method == "POST":
            print("après POST et avant formset_factory")
            InvoiceFormset = formset_factory(
                CreateInvoiceForm,
                extra=1,
            )
            print("après formset_factory")
            request.session["level"] = 50
            print("request.POST : ", request.POST)
            print("avant InvoiceFormset")
            formset = InvoiceFormset(request.POST)
            print("après InvoiceFormset")
            message = ""

            if formset.is_valid():
                print("form.changed_data : ", formset.changed_data)
                # for form in formset:
                #     if form.changed_data:
                #         print("form.clean_data : ", form.cleaned_data, form)
                #         trace_form_change(request, form)
                #         message = (
                #             "Les identifiants du cct "
                #             f"{form.cleaned_data.get('id').cct_uuid_identification.cct}, "
                #             "on bien été changés."
                #         )
                #         request.session["level"] = 20
                #         messages.add_message(request, 20, message)
                #
                # if not message:
                #     messages.add_message(request, 50, "Vous n'avez rien modifié !")

            else:
                messages.add_message(
                    request, 50, f"Une erreur c'est produite, veuillez consulter les logs"
                )

                LOGGER_VIEWS.exception(f"erreur form : {formset.errors!r}")

    except Exception as error:
        request.session["level"] = 50
        messages.add_message(request, 50, f"Une erreur c'est produite, veuillez consulter les logs")
        LOGGER_VIEWS.exception(f"erreur form : {str(error)!r}")

    return render(request, "edi/invoice_marchandise_update.html", context=context)


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
                "nb_display": 10,
                "chevron_retour": reverse("home"),
                "form": CreateInvoiceForm(),
            },
        }

        return context

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
