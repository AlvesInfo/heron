# pylint: disable=E0401,R0901,W0702,E1101,W0201,W1203
"""
Views des rfa à prendre sur l'axe RFA
"""
import pendulum
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect, reverse
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import ListView, CreateView, UpdateView

from heron.loggers import LOGGER_VIEWS, LOGGER_EXPORT_EXCEL
from apps.core.bin.change_traces import ChangeTraceMixin
from apps.core.bin.change_traces import trace_mark_delete
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.rfa.models import SectionRfa
from apps.rfa.excel_outputs.rfa_sections import excel_list_rfa_sections
from apps.rfa.forms import SectionRfaForm, DeleteSectionRfaForm


# ECRANS DES AXE RFA ===============================================================================
class SectionRfaList(ListView):
    """View de la liste des axes RFA à prendre"""

    model = SectionRfa
    context_object_name = "rfa_parameters"
    template_name = "rfa/sections_rfa_list.html"
    extra_context = {"titre_table": "Axe RFA à Prendre dans le calcul de RFA"}


class SectionRfaCreate(ChangeTraceMixin, SuccessMessageMixin, CreateView):
    """CreateView des axes RFA à prendre"""

    model = SectionRfa
    form_class = SectionRfaForm
    form_class.use_required_attribute = False
    template_name = "rfa/sections_rfa_update.html"
    success_message = "L'Axe RFA %(axe_rfa)s a été créé avec success"
    error_message = (
        "L'Axe RFA %(axe_rfa)s n'a pu être créé, une erreur c'est produite"
    )

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["create"] = True
        context["chevron_retour"] = reverse("rfa:sections_rfa_list")
        context["titre_table"] = "Création d'un Axe RFA à Prendre dans le calcul de RFA"
        return context

    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        return reverse("rfa:sections_rfa_list")

    def form_valid(self, form):
        """Ajout d'user à la sauvegarde du formulaire"""
        form.instance.created_by = self.request.user
        self.request.session["level"] = 20

        return super().form_valid(form)

    def form_invalid(self, form):
        """On surcharge la méthode form_invalid, pour ajouter le niveau de message et sa couleur."""
        # Si la view appelante souhaite faire quelque chose après une erreur dans le formulaire
        # On lance sa methode form_error
        if hasattr(self, "form_error"):
            form_error = getattr(self, "form_error")
            form_error()

        return super().form_invalid(form)


class SectionRfaUpdate(ChangeTraceMixin, SuccessMessageMixin, UpdateView):
    """UpdateView des axes RFA à prendre"""

    model = SectionRfa
    form_class = SectionRfaForm
    form_class.use_required_attribute = False
    template_name = "rfa/sections_rfa_update.html"
    success_message = "L'Axe RFA %(axe_rfa)s a été modifiée avec success"
    error_message = (
        "L'Axe RFA %(axe_rfa)s n'a pu être modifiée, une erreur c'est produite"
    )

    def get_context_data(self, **kwargs):
        """Insert the form into the context dict."""

        context = super().get_context_data(**kwargs)
        context["titre_table"] = "Mise à jour Axe RFA à Prendre dans le calcul de RFA"
        context["chevron_retour"] = reverse("rfa:sections_rfa_list")
        return super().get_context_data(**context)

    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        return reverse("rfa:sections_rfa_list")

    def form_valid(self, form, **kwargs):
        """Ajout d'user à la sauvegarde du formulaire"""
        form.instance.modified_by = self.request.user
        self.request.session["level"] = 20

        return super().form_valid(form)

    def form_invalid(self, form):
        """On surcharge la méthode form_invalid, pour ajouter le niveau de message et sa couleur."""
        # Si la view appelante souhaite faire quelque chose après une erreur dans le formulaire
        # On lance sa methode form_error
        if hasattr(self, "form_error"):
            form_error = getattr(self, "form_error")
            form_error()

        return super().form_invalid(form)


@transaction.atomic
def section_rfa_delete(request):
    """Suppression des exclusions des section_rfas pour les RFA
    :param request: Request Django
    :return: view
    """

    if not request.is_ajax() and request.method != "POST":
        return redirect("home")

    data = {"success": "ko"}
    id_pk = request.POST.get("pk")
    form = DeleteSectionRfaForm({"id": id_pk})

    if form.is_valid():
        trace_mark_delete(
            request=request,
            django_model=SectionRfa,
            data_dict={"id": id_pk},
            force_delete=True,
        )
        data = {"success": "success"}

    else:
        LOGGER_VIEWS.exception(f"section_rfa_delete, form invalid : {form.errors!r}")

    return JsonResponse(data)


def section_rfa_export_list(_):
    """
    Export Excel de la liste des Exclusions RFA des section_rfas
    :param _: Request Django
    :return: response_file
    """
    try:

        today = pendulum.now()
        file_name = (
            "LISTING_DES_AXES_RFA_A_PRENDRE_"
            f"{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"
        )

        return response_file(excel_list_rfa_sections, file_name, CONTENT_TYPE_EXCEL)

    except:
        LOGGER_EXPORT_EXCEL.exception("view : section_rfa_export_list")

    return redirect(reverse("rfa:sections_rfa_list"))
