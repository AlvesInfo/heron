import pendulum
from django.contrib.messages.views import SuccessMessageMixin
from django.db import connection, transaction
from django.http import JsonResponse
from django.shortcuts import render, redirect, reverse
from django.views.generic import CreateView, UpdateView

from heron.loggers import LOGGER_VIEWS
from apps.core.bin.change_traces import ChangeTraceMixin, trace_mark_delete, trace_mark_bulk_delete
from apps.core.bin.encoders import get_base_64, set_base_64_list
from apps.core.functions.functions_dates import get_date_apostrophe
from apps.core.functions.functions_postgresql import query_file_dict_cursor
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.validation_purchases.excel_outputs import (
    excel_integration_purchases,
    excel_supplier_purchases,
)

from apps.parameters.models import Category
from apps.edi.models import EdiImport
from apps.edi.forms import (
    EdiImportValidationForm,
    DeleteEdiForm,
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
            "nature": "les factures du fournisseur",
            "addition": True
        }

    return render(request, "validation_purchases/integration_purchases.html", context=context)


class CreateIntegrationControl(ChangeTraceMixin, SuccessMessageMixin, CreateView):
    """View de création de la ligne de contrôle, saisie du relevé founisseur"""

    model = EdiImportControl
    form_class = EdiImportControlForm
    form_class.use_required_attribute = False
    template_name = "validation_purchases/statment_controls.html"
    success_message = (
        "La saisie du relevé pour le tiers %(third_party_num)s "
        f"pour le mois %(date_month)s, a été modifiée avec success"
    )
    error_message = (
        "La saisie du relevé pour le tiers N° %(third_party_num)s "
        "n'a pu être modifiée, une erreur c'est produite"
    )

    def get_attributes(self, kwargs):
        """Décode-les parammètres de la variable enc_param passés en base64"""
        enc_param = get_base_64(kwargs.get("enc_param"))
        self.big_category, self.third_party_num, self.supplier, date_month = enc_param
        self.date_month = pendulum.parse(date_month)
        self.month = self.date_month.format("MMMM YYYY", locale="fr")
        self.success_message = (
            "La saisie du relevé pour le tiers %(third_party_num)s "
            f"du mois {get_date_apostrophe(self.date_month)}"
            f"{self.month}, a été modifiée avec success"
        )

    def get(self, request, *args, **kwargs):
        """Onrécupère les attributs venant par la méthode get"""
        self.get_attributes(kwargs)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["chevron_retour"] = reverse("validation_purchases:integration_purchases")
        context["titre_table"] = (
            f"{self.big_category} - {self.third_party_num} - "
            f"{self.date_month.format('MMMM YYYY', locale='fr')}"
        )
        context["third_party_num"] = self.third_party_num
        context["big_category"] = self.big_category
        context["supplier"] = self.supplier
        context["date_month"] = self.date_month.format("MMMM YYYY", locale="fr")
        return context

    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        return reverse("validation_purchases:integration_purchases")

    def post(self, request, *args, **kwargs):
        """Methode post"""
        self.get_attributes(kwargs)
        return super().post(request, *args, **kwargs)

    @transaction.atomic
    def form_valid(self, form):
        form.instance.modified_by = self.request.user
        self.request.session["level"] = 20
        instance = form.save()
        EdiImport.objects.filter(
            big_category=Category.objects.get(name=self.big_category),
            third_party_num=self.third_party_num,
            supplier=self.supplier,
            date_month=self.date_month,
        ).update(uuid_control=instance.uuid_identification)
        return super().form_valid(form)

    def form_invalid(self, form):
        self.request.session["level"] = 50
        return super().form_invalid(form)


class UpdateIntegrationControl(ChangeTraceMixin, SuccessMessageMixin, UpdateView):
    """UpdateView pour modification des factures founisseurs"""

    model = EdiImportControl
    form_class = EdiImportControlForm
    form_class.use_required_attribute = False
    template_name = "validation_purchases/statment_controls.html"
    date_month = ""
    success_message = (
        "La saisie du relevé pour le tiers %(third_party_num)s "
        f"pour le mois %(date_month)s, a été modifiée avec success"
    )
    error_message = (
        "La saisie du relevé pour le tiers N° %(third_party_num)s "
        "n'a pu être modifiée, une erreur c'est produite"
    )

    def get_attributes(self, kwargs):
        """Décode-les parammètres de la variable enc_param passés en base64"""
        enc_param = get_base_64(kwargs.get("enc_param"))
        self.big_category, self.third_party_num, self.supplier, date_month = enc_param
        self.date_month = pendulum.parse(date_month)
        self.month = self.date_month.format("MMMM YYYY", locale="fr")
        self.success_message = (
            "La saisie du relevé pour le tiers %(third_party_num)s "
            f"pour le mois {get_date_apostrophe(self.date_month)}"
            f"{self.month}, a été modifiée avec success"
        )

    def get(self, request, *args, **kwargs):
        """On récupère les attributs venant par la méthode GET"""
        self.get_attributes(kwargs)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """On récupère les attributs venant par la méthode POST"""
        self.get_attributes(kwargs)
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["chevron_retour"] = reverse("validation_purchases:integration_purchases")
        context["titre_table"] = (
            f"{self.big_category} - {self.third_party_num} - "
            f"{self.date_month.format('MMMM YYYY', locale='fr')}"
        )
        context["third_party_num"] = self.third_party_num
        context["big_category"] = self.big_category
        context["supplier"] = self.supplier
        context["date_month"] = self.date_month.format("MMMM YYYY", locale="fr")

        return context

    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        return reverse("validation_purchases:integration_purchases")

    @transaction.atomic
    def form_valid(self, form):
        """Si le formulaire est valide"""
        form.instance.modified_by = self.request.user
        self.request.session["level"] = 20
        return super().form_valid(form)

    def form_invalid(self, form):
        """Si le formulaire est invalide"""
        self.request.session["level"] = 50
        return super().form_invalid(form)


@transaction.atomic
def delete_supplier_edi_import(request):
    """Suppression de toutes les factures en definitif selon uuid d'import
    :param request: Request Django
    :return: view
    """

    if not request.is_ajax() and request.method != "POST":
        return redirect("home")

    data = {"success": "ko"}
    third_party_num, supplier, big_category, date_month, delete = request.POST.values()
    instance_big_categorie = Category.objects.get(name=big_category)

    if instance_big_categorie:
        data_dict = {
            "third_party_num": third_party_num,
            "supplier": supplier,
            "big_category": instance_big_categorie.uuid_identification,
            "date_month": date_month,
            "delete": delete,
        }
        form = DeleteEdiForm(data_dict)

        if form.is_valid() and form.cleaned_data:
            trace_mark_bulk_delete(
                request=request,
                django_model=EdiImport,
                data_dict=form.cleaned_data,
                replacements=(("big_category", instance_big_categorie.name),),
            )
            data = {"success": "success"}

        else:
            LOGGER_VIEWS.exception(
                f"delete_supplier_edi_import error, form invalid : {form.errors!r}"
            )

    return JsonResponse(data)


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


def integration_supplier_purchases(request, enc_param):
    """View de l'étape 2.A des écrans de contrôles
    Visualisation des montants par Factures pour le fournisseur demandé
    :param request: Request Django
    :param enc_param: paramètres encodés en base 64
    :return: view
    """
    sql_context_file = "apps/validation_purchases/sql_files/sql_integration_supplier_purchases.sql"
    big_category, third_party_num, supplier, date_month = get_base_64(enc_param)

    with connection.cursor() as cursor:
        elements = query_file_dict_cursor(
            cursor,
            file_path=sql_context_file,
            parmas_dict={
                "third_party_num": third_party_num,
                "supplier": supplier,
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
            "titre_table": f"Contrôle : {supplier}  - {mois}",
            "controles_exports": elements,
            "chevron_retour": reverse("validation_purchases:integration_purchases"),
            "nature": "La facture n° ",
            "nb_paging": 100,
        }

    return render(request, "validation_purchases/listing_invoices_suppliers.html", context=context)


class UpdateSupplierPurchases(ChangeTraceMixin, SuccessMessageMixin, UpdateView):
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


@transaction.atomic
def delete_invoice_purchase(request):
    """Suppression des factures non souhaitées
    :param request: Request Django
    :return: view
    """

    if not request.is_ajax() and request.method != "POST":
        return redirect("home")

    data = {"success": "ko"}
    third_party_num, invoice_number, date_month, _ = request.POST.values()
    data_dict = {
        "third_party_num": third_party_num,
        "invoice_number": invoice_number,
        "date_month": date_month,
    }
    form = DeleteInvoiceForm(data_dict)

    if form.is_valid() and form.cleaned_data:
        trace_mark_delete(
            request=request,
            django_model=EdiImport,
            data_dict=form.cleaned_data,
        )
        data = {"success": "success"}

    else:
        LOGGER_VIEWS.exception(f"delete_invoice_purchase, form invalid : {form.errors!r}")

    return JsonResponse(data)


def integration_supplier_purchases_export(request, enc_param):
    """Export Excel de la liste des montants par Factures pour le fournisseur demandé
    :param request: Request Django
    :param enc_param: paramètres au format base64
    :return: response_file
    """
    try:
        if request.method == "GET":
            big_category, third_party_num, supplier, date_month, _ = get_base_64(enc_param)
            today = pendulum.now()
            file_name = (
                f"{big_category}_{third_party_num}_{date_month}_"
                f"{today.format('Y_M_D')}{today.int_timestamp}.xlsx"
            )
            attr_dict = {
                "big_category": big_category,
                "third_party_num": third_party_num,
                "supplier": supplier,
                "date_month": date_month,
            }
            return response_file(
                excel_supplier_purchases,
                file_name,
                CONTENT_TYPE_EXCEL,
                attr_dict,
            )

    except:
        LOGGER_VIEWS.exception("view : integration_purchases_export")

    return redirect(reverse("validation_purchases:integration_purchases"))


# CONTROLES ETAPE 2.B - DETAILS FACTURES


def details_purchase(request, enc_param):
    """View de l'étape 2.B des écrans de contrôles
    Visualisation des détails des lignes d'une facture pour un fournisseur
    :param request: Request Django
    :param enc_param: paramètres encodés en base 64
    :return: view
    """
    sql_context_file = "apps/validation_purchases/sql_files/sql_details_purchases.sql"
    big_category, third_party_num, supplier, date_month, invoice_number = get_base_64(enc_param)

    with connection.cursor() as cursor:
        elements = query_file_dict_cursor(
            cursor,
            file_path=sql_context_file,
            parmas_dict={
                "big_category": big_category,
                "third_party_num": third_party_num,
                "supplier": supplier,
                "date_month": date_month,
                "invoice_number": invoice_number,
            },
        )
        context = {
            "titre_table": f"Contrôle : {supplier} - " f"Facture N°: {invoice_number}",
            "controles_exports": elements,
            "chevron_retour": reverse(
                "validation_purchases:integration_supplier_purchases",
                kwargs={
                    "enc_param": set_base_64_list(
                        [big_category, third_party_num, supplier, date_month]
                    ),
                },
            ),
            "nature": "La ligne n° ",
            "nb_paging": 50,
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
    data_dict = {
        "pk": request.POST.get("pk[pk]"),
    }
    form = DeletePkForm(data_dict)

    if form.is_valid() and form.cleaned_data:
        trace_mark_delete(
            request=request,
            django_model=EdiImport,
            data_dict=form.cleaned_data,
        )
        data = {"success": "success"}

    else:
        LOGGER_VIEWS.exception(f"delete_line_details_purchase, form invalid : {form.errors!r}")

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
    context = {"titre_table": "Controle des familles - Achats"}
    return render(request, "validation_purchases/families_invoices_suppliers.html", context=context)


def families_invoices_purchases_export(request):
    """View de l'étape 3.1 des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(request, "validation_purchases/families_invoices_suppliers.html", context=context)


# CONTROLES ETAPE 3.1 A - CONTROLE ARTICLES/FAMILLES


def articles_families_invoices_purchases(request):
    """View de l'étape 3.1 A des écrans de contrôles"""
    context = {"titre_table": "Controle des familles par articles - Achats"}
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
    context = {"titre_table": "Controle des RFA par CCT- Achats"}
    return render(request, "validation_purchases/rfa_cct_invoices_suppliers.html", context=context)


def rfa_cct_invoices_purchases_export(request):
    """View de l'étape RFA PAR CCT des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(request, "validation_purchases/rfa_cct_invoices_suppliers.html", context=context)


# CONTROLES ETAPE RFA - CONTROLE RFA PAR PRJ


def rfa_prj_invoices_purchases(request):
    """View de l'étape RFA PAR PRJ des écrans de contrôles"""
    context = {"titre_table": "Controle des RFA par PRJ - Achats"}
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
