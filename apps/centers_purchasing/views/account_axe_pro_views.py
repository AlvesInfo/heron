# pylint: disable=E0401,R0903
"""
FR : Module Dictionnaire des Comptes debit crédit pour la facturation
EN : Dictionary of Debit Credit Accounts for invoicing

Commentaire:

created at: 2023-01-21
created by: Paulo ALVES

modified at: 2023-01-21
modified by: Paulo ALVES
"""
import pendulum
from django.http import JsonResponse
from django.shortcuts import redirect, reverse
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import ListView, CreateView, UpdateView

from heron.loggers import LOGGER_VIEWS
from apps.core.bin.change_traces import ChangeTraceMixin, trace_mark_delete
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.centers_purchasing.excel_outputs.output_excel_account_axe_list import (
    excel_liste_account_axe,
)
from apps.centers_purchasing.models import AccountsAxeProCategory
from apps.centers_purchasing.forms import (
    AccountsAxeProCategoryForm,
    AccountsAxeProCategoryDeleteForm,
)

# Comptes par Centrale fille, Catégorie, Axe Pro, et TVA


class AccountAxeList(ListView):
    """View de la liste du Dictionnaire des Comptes debit crédit pour la facturation"""

    model = AccountsAxeProCategory
    context_object_name = "accounts_axes"
    template_name = "centers_purchasing/account_axe_list.html"
    extra_context = {"titre_table": "Dictionnaire des Comptes debit crédit"}


class AccountAxeCreate(ChangeTraceMixin, SuccessMessageMixin, CreateView):
    """CreateView de création du Dictionnaire des Comptes debit crédit pour la facturation"""

    model = AccountsAxeProCategory
    form_class = AccountsAxeProCategoryForm
    form_class.use_required_attribute = False
    template_name = "centers_purchasing/account_axe_update.html"
    success_message = (
        "Dictionnaire des Comptes debit crédit pour la facturation a été créé avec success"
    )
    error_message = (
        "Le Dictionnaire des Comptes debit crédit pour la facturation n'a pu être créé, "
        "une erreur c'est produite"
    )

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["chevron_retour"] = reverse("centers_purchasing:account_axe_list")
        context["titre_table"] = (
            "Création d'un nouveau Dictionnaire des Comptes debit crédit"
        )
        return context

    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        return reverse("centers_purchasing:account_axe_list")

    def form_valid(self, form):
        """Ajout de l'user à la sauvegarde du formulaire"""
        form.instance.created_by = self.request.user
        self.request.session["level"] = 20
        return super().form_valid(form)


class AccountAxeUpdate(ChangeTraceMixin, SuccessMessageMixin, UpdateView):
    """UpdateView d'update du Dictionnaire des Comptes debit crédit pour la facturation"""

    model = AccountsAxeProCategory
    form_class = AccountsAxeProCategoryForm
    form_class.use_required_attribute = False
    template_name = "centers_purchasing/account_axe_update.html"
    success_message = (
        "Le Dictionnaire des Comptes debit crédit pour la facturation a été modifié avec success"
    )
    error_message = (
        "Le Dictionnaire des Comptes debit crédit pour la facturation n'a pu être modifié, "
        "une erreur c'est produite"
    )

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["chevron_retour"] = reverse("centers_purchasing:account_axe_list")
        context["titre_table"] = (
            "Mise à jour d'un Dictionnaire des Comptes debit crédit"
        )
        return context

    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        return reverse("centers_purchasing:account_axe_list")

    def form_valid(self, form, **kwargs):
        """Ajout de l'user à la sauvegarde du formulaire"""
        form.instance.modified_by = self.request.user
        self.request.session["level"] = 20
        return super().form_valid(form)


def account_axe_delete(request):
    """Vue ajax de suppresion d'une ligne de la table"""

    if not request.is_ajax() and request.method != "POST":
        return redirect("home")

    data = {"success": "ko"}
    id_pk = request.POST.get("pk")
    form = AccountsAxeProCategoryDeleteForm({"id": id_pk})

    if form.is_valid():
        trace_mark_delete(
            request=request,
            django_model=AccountsAxeProCategory,
            data_dict={"id": id_pk},
            force_delete=True,
        )
        data = {"success": "success"}

    else:
        LOGGER_VIEWS.exception(f"axe_grouping_delete, form invalid : {form.errors!r}")

    return JsonResponse(data)


def account_axe_export_list(_):
    """
    Export Excel de la liste du Dictionnaire Axe Pro/Regroupement de facturation
    :return: response_file
    """
    try:

        today = pendulum.now()
        file_name = (
            f"LISTING_DES_AXE_PRO_VS_REGROUPEMENTS_DE_FACTURATION_"
            f"{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"
        )

        return response_file(excel_liste_account_axe, file_name, CONTENT_TYPE_EXCEL)

    except:
        LOGGER_VIEWS.exception("view : account_axe_export_list")

    return redirect(reverse("centers_purchasing:account_axe_list"))
