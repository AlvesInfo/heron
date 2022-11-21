import pendulum
from django.contrib.messages.views import SuccessMessageMixin
from django.db import connection, transaction
from django.http import JsonResponse
from django.shortcuts import render, redirect, reverse
from django.views.generic import CreateView, UpdateView, DeleteView

from heron.loggers import LOGGER_VIEWS
from apps.core.bin.change_traces import ChangeTraceMixin, trace_mark_delete
from apps.core.functions.functions_postgresql import query_file_dict_cursor
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.validation_purchases.excel_outputs import (
    excel_integration_purchases,
)
from apps.edi.models import EdiImport
from apps.edi.forms import (
    EdiImportValidationForm,
    DeleteInvoiceForm,
    DeletePkForm,
)
from apps.edi.models import EdiImportControl
from apps.edi.forms import EdiImportControlForm

# CONTROLES ETAPE 2 - CONTROLE INTEGRATION


def integration_purchases(request):
    """View de l'étape 2 des écrans de contrôles
    Visualisation pour la validation des montants par fournisseurs par mois, intégrés ou saisis
    :param request: Request Django
    :return: view
    """
    sql_context_file = "apps/validation_purchases/sql_files/sql_integration_purchases.sql"

    with connection.cursor() as cursor:
        elements = query_file_dict_cursor(cursor, file_path=sql_context_file)
        context = {
            "titre_table": "Contrôle des Intégrations - Achats",
            "integration_purchases": elements,
            "margin_table": 10,
            "nb_paging": 100,
        }

    return render(request, "validation_purchases/integration_purchases.html", context=context)


class CreateIntegrationControl(ChangeTraceMixin, SuccessMessageMixin, CreateView):
    """View de création de la ligne de contrôle, saisie du relevé founisseur"""

    model = EdiImportControl
    form_class = EdiImportControlForm
    form_class.use_required_attribute = False
    template_name = "validation_purchases/statment_controls.html"
    success_message = (
        "La saisie de contrôle pour le tiers %(third_party_num)s "
        "du mois : %(date_month)s, a été modifiée avec success"
    )
    error_message = (
        "La saisie de contrôle pour le tiers N° %(third_party_num)s "
        "n'a pu être modifiée, une erreur c'est produite"
    )

    def get(self, request, *args, **kwargs):
        """Onrécupère les attributs venant par la méthode get"""
        self.third_party_num = kwargs.get("third_party_num")
        self.big_category = kwargs.get("big_category")
        self.date_month = pendulum.parse(kwargs.get("date_month"))
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["chevron_retour"] = reverse("validation_purchases:integration_purchases")
        context["titre_table"] = (
            f"Mise à jour du relevé : "
            f"{self.big_category} - "
            f"{self.third_party_num} - "
            f"{self.date_month.format('MMMM YYYY', locale='fr')}"
        )
        context["third_party_num"] = self.third_party_num
        context["date_month"] = self.date_month.format('MMMM YYYY', locale='fr')
        return context

    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        return reverse("validation_purchases:integration_purchases")

    def form_valid(self, form):
        form.instance.modified_by = self.request.user
        print(form.is_valid(), form.cleaned_data)
        self.request.session["level"] = 20
        return super().form_valid(form)

    def form_invalid(self, form):
        self.request.session["level"] = 50
        return super().form_invalid(form)


class UpdateIntegrationControl(ChangeTraceMixin, SuccessMessageMixin, UpdateView):
    """UpdateView pour modification des factures founisseurs"""

    model = EdiImportControl
    form_class = EdiImportControlForm
    form_class.use_required_attribute = False
    template_name = "book/society_update.html"
    success_message = (
        "La saisie de contrôle pour le tiers %(third_party_num)s "
        "du mois : %(date_month)s, a été modifiée avec success"
    )
    error_message = (
        "La saisie de contrôle pour le tiers N° %(third_party_num)s "
        "n'a pu être modifiée, une erreur c'est produite"
    )


def integration_purchases_export(request):
    """Export Excel de la liste de la validation des montants par fournisseurs par mois,
    intégrés ou saisis.
    :param request: Request Django
    :return: response_file
    """

    try:
        if request.method == "GET":
            today = pendulum.now()
            file_name = (
                f"RELEVES_VS_FACTURES_INTEGREES_{today.format('Y_M_D')}{today.int_timestamp}.xlsx"
            )

            return response_file(
                excel_integration_purchases,
                file_name,
                CONTENT_TYPE_EXCEL,
            )

    except:
        LOGGER_VIEWS.exception("view : integration_purchases_export")

    return redirect(reverse("validation_purchases:integration_purchases"))


# CONTROLES ETAPE 2.A - LISTING FACTURES


def integration_supplier_purchases(request, third_party_num, big_category, date_month):
    """View de l'étape 2.A des écrans de contrôles
    Visualisation des montants par Factures pour le fournisseur demandé
    :param request: Request Django
    :param third_party_num: id X3 du fournisseur
    :param big_category: Grande Catégory
    :param date_month: Mois de facturation
    :return: view
    """
    sql_context_file = "apps/validation_purchases/sql_files/sql_integration_supplier_purchases.sql"

    with connection.cursor() as cursor:
        elements = query_file_dict_cursor(
            cursor,
            file_path=sql_context_file,
            parmas_dict={
                "third_party_num": third_party_num,
                "big_category": big_category,
                "date_month": date_month,
            },
        )
        titre_table = elements[0]
        mois = (
            pendulum.parse(titre_table.get("date_month").isoformat())
            .format("MMMM YYYY", locale="fr")
            .capitalize()
        )
        context = {
            "titre_table": f"Contrôle : {titre_table.get('supplier')}  - {mois}",
            "controles_exports": elements,
            "chevron_retour": reverse("validation_purchases:integration_purchases"),
            "nature": "La facture n° ",
        }

    return render(request, "validation_purchases/listing_invoices_suppliers.html", context=context)


class DeleteInvoicePurchase(ChangeTraceMixin, SuccessMessageMixin, DeleteView):
    """Suppression des factures non souhaitées"""


@transaction.atomic
def delete_invoice_purchase(request):
    """Suppression des factures non souhaitées
    :param request: Request Django
    :return: view
    """

    if not request.is_ajax() and request.method != "POST":
        return redirect("home")

    data = {"success": "ko"}
    form = DeleteInvoiceForm(request.POST)

    if form.is_valid() and form.cleaned_data:
        trace_mark_delete(
            request=request,
            django_model=EdiImport,
            data_dict=form.cleaned_data,
        )
        data = {"success": "success"}

    else:
        LOGGER_VIEWS.exception(f"delete_invoice_purchase error : {form.errors!r}")

    return JsonResponse(data)


def integration_supplier_purchases_export(request):
    """Export Excel de la liste des montants par Factures pour le fournisseur demandé
    :param request: Request Django
    :return: response_file
    """
    context = {"titre_table": "Export Excel"}
    return render(request, "validation_purchases/listing_invoices_suppliers.html", context=context)


# CONTROLES ETAPE 2.B - DETAILS FACTURES


def details_purchase(request, third_party_num, invoice_number):
    """View de l'étape 2.B des écrans de contrôles
    Visualisation des détails des lignes d'une facture pour un fournisseur
    :param request: Request Django
    :param third_party_num: id X3 du fournisseur
    :param invoice_number: N° de facture
    :return: view
    """
    sql_context_file = "apps/validation_purchases/sql_files/sql_details_purchases.sql"
    with connection.cursor() as cursor:
        elements = query_file_dict_cursor(
            cursor,
            file_path=sql_context_file,
            parmas_dict={
                "third_party_num": third_party_num,
                "invoice_number": invoice_number,
            },
        )
        titre_table = elements[0]
        context = {
            "titre_table": (
                f"Contrôle : {titre_table.get('supplier')} - "
                f"Facture N°: {titre_table.get('invoice_number')}"
            ),
            "controles_exports": elements,
            "chevron_retour": reverse(
                "validation_purchases:integration_supplier_purchases",
                kwargs={
                    "third_party_num": third_party_num,
                    "big_category": titre_table.get("big_category"),
                    "date_month": titre_table.get("date_month"),
                },
            ),
            "nature": "La ligne n° ",
        }
    return render(request, "validation_purchases/details_invoices_suppliers.html", context=context)


def delete_line_details_purchase(request):
    """Suppression des lignes de factures non souhaitées
    :param request: Request Django
    :return: view
    """

    if not request.is_ajax() and request.method != "POST":
        return redirect("home")

    data = {"success": "ko"}
    form = DeletePkForm(request.POST)

    if form.is_valid() and form.cleaned_data:
        trace_mark_delete(
            request=request,
            django_model=EdiImport,
            data_dict=form.cleaned_data,
        )
        data = {"success": "success"}

    else:
        LOGGER_VIEWS.exception(f"delete_line_details_purchase error : {form.errors!r}")

    return JsonResponse(data)


def details_purchases_export(request):
    """Export Excel de
    :param request: Request Django
    :return: response_file
    """
    context = {"titre_table": "Export Excel"}
    return render(request, "validation_purchases/details_invoices_suppliers.html", context=context)


class UpdateDetaisPurchase(ChangeTraceMixin, SuccessMessageMixin, UpdateView):
    """UpdateView pour modification des factures founisseurs"""

    model = EdiImport
    form_class = EdiImportValidationForm
    form_class.use_required_attribute = False
    template_name = "book/society_update.html"
    success_message = "La facture N° %(invoice_number)s a été modifiée avec success"
    error_message = (
        "La facture N° %(invoice_number)s n'a pu être modifiée, une erreur c'est produite"
    )


# CONTROLES ETAPE 2.2 - FACTURES SANS CCT


def without_cct_purchases(request):
    """View de l'étape 2.2 des écrans de contrôles
    Visualisation des factures sans CCT
    :param request: Request Django
    :return: view
    """
    context = {"titre_table": "Listing Factures sans CCT - Achats"}
    return render(
        request, "validation_purchases/without_cct_invoices_suppliers.html", context=context
    )


def without_cct_purchases_export(request):
    """Export Excel de
    :param request: Request Django
    :return: response_file"""
    context = {"titre_table": "Export Excel"}
    return render(
        request, "validation_purchases/without_cct_invoices_suppliers.html", context=context
    )


# CONTROLES ETAPE 3.1 - CONTROLE FAMILLES


def families_invoices_purchases(request):
    """View de l'étape 3.1 des écrans de contrôles"""
    context = {"titre_table": f"Controle des familles - Achats"}
    return render(request, "validation_purchases/families_invoices_suppliers.html", context=context)


def families_invoices_purchases_export(request):
    """View de l'étape 3.1 des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(request, "validation_purchases/families_invoices_suppliers.html", context=context)


# CONTROLES ETAPE 3.1 A - CONTROLE ARTICLES/FAMILLES


def articles_families_invoices_purchases(request):
    """View de l'étape 3.1 A des écrans de contrôles"""
    context = {"titre_table": f"Controle des familles par articles - Achats"}
    return render(
        request, "validation_purchases/articles_families_invoices_suppliers.html", context=context
    )


def articles_families_invoices_purchases_export(request):
    """View de l'étape 3.1 A des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(
        request, "validation_purchases/articles_families_invoices_suppliers.html", context=context
    )


# CONTROLES ETAPE RFA - CONTROLE RFA PAR CCT


def rfa_cct_invoices_purchases(request):
    """View de l'étape RFA PAR CCT des écrans de contrôles"""
    context = {"titre_table": f"Controle des RFA par CCT- Achats"}
    return render(request, "validation_purchases/rfa_cct_invoices_suppliers.html", context=context)


def rfa_cct_invoices_purchases_export(request):
    """View de l'étape RFA PAR CCT des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(request, "validation_purchases/rfa_cct_invoices_suppliers.html", context=context)


# CONTROLES ETAPE RFA - CONTROLE RFA PAR PRJ


def rfa_prj_invoices_purchases(request):
    """View de l'étape RFA PAR PRJ des écrans de contrôles"""
    context = {"titre_table": f"Controle des RFA par PRJ - Achats"}
    return render(request, "validation_purchases/rfa_prj_invoices_suppliers.html", context=context)


def rfa_prj_invoices_purchases_export(request):
    """View de l'étape RFA PAR PRJ des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(request, "validation_purchases/rfa_prj_invoices_suppliers.html", context=context)


# CONTROLES ETAPE 5.1


def balance_suppliers_purchases(request):
    """View de l'étape 5.5 des écrans de contrôles"""
    context = {"titre_table": "Contrôle Soldes Fournisseurs - Achats"}
    return render(request, "validation_purchases/balance_suppliers.html", context=context)


def balance_suppliers_purchases_export(request):
    """View de l'étape 5.5 des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(request, "validation_purchases/balance_suppliers.html", context=context)


def invoices_suppliers_purchases(request):
    """View de l'étape 5.5 B des écrans de contrôles"""
    context = {"titre_table": "Contrôle Factures Fournisseurs - Achats"}
    return render(request, "validation_purchases/invoices_suppliers.html", context=context)


def invoices_suppliers_purchases_export(request):
    """View de l'étape 5.5 B des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(request, "validation_purchases/invoices_suppliers.html", context=context)


# CONTROLES ETAPE 5.5


def sage_controls_globals_purchases(request):
    """View de l'étape 5.5 des écrans de contrôles"""
    context = {"titre_table": "Contrôle Intégration Sage X3 - Achats"}
    return render(request, "validation_purchases/sage_controls.html", context=context)


def validation_purchases_export_globals(request):
    """View de l'étape 5.5 des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(request, "validation_purchases/sage_controls.html", context=context)


def sage_controls_details_purchases(request):
    """View de l'étape 5.5 A des écrans de contrôles"""
    context = {"titre_table": "Contrôle Intégration Sage X3 - Achats", "details": True}
    return render(request, "validation_purchases/sage_controls.html", context=context)


def validation_purchases_export_details(request):
    """View de l'étape 5.5 A des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(request, "validation_purchases/sage_controls.html", context=context)


def sage_controls_familles_purchases(request):
    """View de l'étape 5.5 B des écrans de contrôles"""
    context = {
        "titre_table": "Contrôle Intégration Sage X3 - Détails Achats",
        "details_familles": True,
        "details": True,
    }
    return render(request, "validation_purchases/sage_controls.html", context=context)


def validation_purchases_export_familles(request):
    """View de l'étape 5.5 B des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(request, "validation_purchases/sage_controls.html", context=context)
