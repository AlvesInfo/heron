import pendulum
from django.contrib.messages.views import SuccessMessageMixin
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render, redirect, reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import UpdateView, DeleteView

from heron.loggers import LOGGER_VIEWS
from apps.core.bin.change_traces import ChangeTraceMixin
from apps.core.functions.functions_postgresql import query_file_dict_cursor
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.validation_purchases.excel_outputs import (
    excel_integration_purchases,
)
from apps.edi.models import EdiImport
from apps.edi.forms import EdiImportValidationForm, EdiImportDeleteForm
from apps.validation_purchases.models import EdiImportControl
from apps.validation_purchases.forms import EdiImportControlForm

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
                f"LISTING_DES_FACTURES_INTEGREES_{today.format('Y_M_D')}{today.int_timestamp}.xlsx"
            )

            return response_file(
                excel_integration_purchases,
                file_name,
                CONTENT_TYPE_EXCEL,
            )

    except:
        LOGGER_VIEWS.exception("view : integration_purchases_export")

    return redirect(reverse("validation_purchases:integration_purchases"))


class UpdateEdiControl(ChangeTraceMixin, SuccessMessageMixin, UpdateView):
    """UpdateView pour modification des factures founisseurs"""

    model = EdiImportControl
    form_class = EdiImportControlForm
    form_class.use_required_attribute = False
    template_name = "book/society_update.html"
    success_message = (
        "La saisie de contrôle pour le tiers %(third_party_num)s " "a été modifiée avec success"
    )
    error_message = (
        "La saisie de contrôle pour le tiers N° %(third_party_num)s "
        "n'a pu être modifiée, une erreur c'est produite"
    )


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
            "pk": titre_table.get("pk"),
        }

    return render(request, "validation_purchases/listing_invoices_suppliers.html", context=context)


class DeleteInvoicePurchase(ChangeTraceMixin, SuccessMessageMixin, DeleteView):
    """Suppression des factures non souhaitées"""

    model = EdiImport
    form_class = EdiImportDeleteForm
    success_message = "La facture N° %(invoice_number)s a été supprimée avec success"
    error_message = (
        "La facture N° %(invoice_number)s n'a pu être supprimée, une erreur c'est produite"
    )
    template_name = "validation_purchases/listing_invoices_suppliers.html"

    def __init__(self, *args, **kwargs):
        """Méthode init"""
        super().__init__(*args, **kwargs)
        self.third_party_num = None
        self.big_category = None
        self.date_month = None

    def get_success_url(self):
        """Retourne l'url en cas de success"""
        invoices = self.model.objects.filter(
            third_party_num=self.third_party_num,
            big_category=self.big_category,
            date_month=self.date_month,
            delete=False,
        )

        if not invoices:
            return reverse("validation_purchases:integration_purchases")

        return reverse(
                "validation_purchases:integration_supplier_purchases",
                kwargs={
                    "third_party_num": self.third_party_num,
                    "big_category": self.big_category,
                    "date_month": self.date_month,
                },
            )

    def form_valid(self, form):
        """Action en cas du formualire validé"""
        success_url = self.get_success_url()
        print("form.cleaned_data :", form.cleaned_data)
        return redirect(success_url)

    def form_invalid(self, form):
        print(form.errors)
        return self.render_to_response(self.get_context_data(form=form))


def delete_invoice_purchase(request):
    """Suppression des factures non souhaitées
    :param request: Request Django
    :return: view
    """

    if not request.is_ajax() and request.method != "POST":
        return redirect("home")

    data = {"success": "ko"}

    try:
        form = EdiImportDeleteForm(request.POST)
        if form.is_valid():
            edi = EdiImport.objects.get(pk=form.cleaned_data.get("pk"))
            edi_to_update = EdiImport.objects.filter(
                big_category=edi.big_category,
                third_party_num=edi.third_party_num,
                invoice_number=edi.invoice_number,
                date_month=edi.date_month,
            )
            if not edi_to_update:
                raise EdiImport.DoesNotExist

            edi_to_update.update(delete=True)
            data = {"success": "success"}

    except EdiImport.DoesNotExist:
        print("passer par EdiImport.DoesNotExist")
        pass

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

    try:
        form = EdiImportDeleteForm(request.POST)
        if form.is_valid():
            edi = EdiImport.objects.get(pk=form.cleaned_data.get("pk"))
            print(edi.__dict__)
            edi.delete = True
            edi.save()
            data = {"success": "success"}

    except EdiImport.DoesNotExist:
        pass

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
