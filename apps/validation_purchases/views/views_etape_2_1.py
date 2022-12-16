import pendulum
from django.contrib.messages.views import SuccessMessageMixin
from django.db import connection, transaction
from django.http import JsonResponse
from django.shortcuts import render, redirect, reverse
from django.views.generic import CreateView, UpdateView

from heron.loggers import LOGGER_VIEWS
from apps.core.bin.change_traces import ChangeTraceMixin, trace_mark_bulk_delete
from apps.core.bin.encoders import get_base_64
from apps.core.functions.functions_dates import get_date_apostrophe
from apps.core.functions.functions_postgresql import query_file_dict_cursor
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.data_flux.models import Trace
from apps.parameters.models import ActionInProgress
from apps.validation_purchases.excel_outputs import (
    excel_integration_purchases,
)

from apps.parameters.models import Category
from apps.edi.models import EdiImport
from apps.edi.forms import (
    DeleteEdiForm,
)
from apps.edi.models import EdiImportControl
from apps.edi.forms import EdiImportControlForm

# CONTROLES ETAPE 2.1 - CONTROLE INTEGRATION


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
            "addition": True,
            "traces": Trace.objects.filter(
                uuid_identification__in=EdiImport.objects.all().values("uuid_identification")
            ).order_by("trace_name", "file_name"),
        }

    if ActionInProgress.objects.filter(in_progress=True):
        context["en_cours"] = True
        context["titre_table"] = "PATIENTEZ INTEGRATION EN COURS .... (Rafraîchissez la page)"

    return render(request, "validation_purchases/integration_purchases.html", context=context)


class CreateIntegrationControl(ChangeTraceMixin, SuccessMessageMixin, CreateView):
    """View de création de la ligne de contrôle, saisie du relevé founisseur"""

    model = EdiImportControl
    form_class = EdiImportControlForm
    form_class.use_required_attribute = False
    template_name = "validation_purchases/statment_controls.html"
    success_message = (
        "La saisie du relevé pour le tiers %(third_party_num)s "
        f"pour le mois %(invoice_month)s, a été modifiée avec success"
    )
    error_message = (
        "La saisie du relevé pour le tiers N° %(third_party_num)s "
        "n'a pu être modifiée, une erreur c'est produite"
    )

    def get_attributes(self, kwargs):
        """Décode-les parammètres de la variable enc_param passés en base64"""
        enc_param = get_base_64(kwargs.get("enc_param"))
        self.big_category, self.third_party_num, self.supplier, invoice_month = enc_param
        self.invoice_month = pendulum.parse(invoice_month)
        self.month = self.invoice_month.format("MMMM YYYY", locale="fr")
        self.success_message = (
            "La saisie du relevé pour le tiers %(third_party_num)s "
            f"du mois {get_date_apostrophe(self.invoice_month)}"
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
            f"{self.invoice_month.format('MMMM YYYY', locale='fr')}"
        )
        context["third_party_num"] = self.third_party_num
        context["big_category"] = self.big_category
        context["supplier"] = self.supplier
        context["invoice_month"] = self.invoice_month.format("MMMM YYYY", locale="fr")
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
            invoice_month=self.invoice_month,
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
    invoice_month = ""
    success_message = (
        "La saisie du relevé pour le tiers %(third_party_num)s "
        f"pour le mois %(invoice_month)s, a été modifiée avec success"
    )
    error_message = (
        "La saisie du relevé pour le tiers N° %(third_party_num)s "
        "n'a pu être modifiée, une erreur c'est produite"
    )

    def get_attributes(self, kwargs):
        """Décode-les parammètres de la variable enc_param passés en base64"""
        enc_param = get_base_64(kwargs.get("enc_param"))
        self.big_category, self.third_party_num, self.supplier, invoice_month = enc_param
        self.invoice_month = pendulum.parse(invoice_month)
        self.month = self.invoice_month.format("MMMM YYYY", locale="fr")
        self.success_message = (
            "La saisie du relevé pour le tiers %(third_party_num)s "
            f"pour le mois {get_date_apostrophe(self.invoice_month)}"
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
            f"{self.invoice_month.format('MMMM YYYY', locale='fr')}"
        )
        context["third_party_num"] = self.third_party_num
        context["big_category"] = self.big_category
        context["supplier"] = self.supplier
        context["invoice_month"] = self.invoice_month.format("MMMM YYYY", locale="fr")

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
    third_party_num, supplier, big_category, invoice_month, delete = request.POST.values()
    instance_big_categorie = Category.objects.get(name=big_category)

    if instance_big_categorie:
        data_dict = {
            "third_party_num": third_party_num,
            "supplier": supplier,
            "big_category": instance_big_categorie.uuid_identification,
            "invoice_month": invoice_month,
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
