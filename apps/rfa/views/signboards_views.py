"""Views des exclusions des rfa pour les enseignes."""

import pendulum
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import CreateView, ListView, UpdateView

from apps.core.bin.change_traces import ChangeTraceMixin, trace_mark_delete
from apps.core.functions.functions_http import is_ajax
from apps.core.functions.functions_http_response import CONTENT_TYPE_EXCEL, response_file
from apps.rfa.excel_outputs.rfa_signboards_exclusion import excel_list_rfa_signboards_exclusion
from apps.rfa.forms import DeleteSignboardExclusionForm, SignboardExclusionForm
from apps.rfa.models import SignboardExclusion
from heron.loggers import LOGGER_EXPORT_EXCEL, LOGGER_VIEWS


# ECRANS DES ENSEIGNES ============================================================================
class SignboardExclusionList(ListView):
    """View de la liste des Exclusions RFA des Enseignes."""

    model = SignboardExclusion
    context_object_name = "rfa_parameters"
    template_name = "rfa/signboards_exclusions_list.html"
    extra_context = {"titre_table": "ENSEIGNES A EXCLURE DU CALCUL DES RFA"}


class SignboardExclusionCreate(ChangeTraceMixin, SuccessMessageMixin, CreateView):
    """CreateView de création des exclusions rfa des Enseignes."""

    model = SignboardExclusion
    form_class = SignboardExclusionForm
    template_name = "rfa/signboards_exclusions_update.html"
    success_message = "L'Exclusion de l'Enseigne %(signboard)s a été créé avec success"
    error_message = (
        "L'Exclusion de l'Enseigne %(signboard)s n'a pu être créé, une erreur c'est produite"
    )

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template."""
        context = super().get_context_data(**kwargs)
        context["create"] = True
        context["chevron_retour"] = reverse("rfa:signboards_exclusion_list")
        context["titre_table"] = "Création d'une nouvelle Exclusion Enseigne pour les RFA"
        return context

    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        return reverse("rfa:signboards_exclusion_list")

    def form_valid(self, form):
        """Ajout de l'user à la sauvegarde du formulaire."""
        form.instance.created_by = self.request.user
        self.request.session["level"] = 20

        return super().form_valid(form)


class SignboardExclusionUpdate(ChangeTraceMixin, SuccessMessageMixin, UpdateView):
    """UpdateView des exclusions rfa des Enseignes."""

    model = SignboardExclusion
    form_class = SignboardExclusionForm
    template_name = "rfa/signboards_exclusions_update.html"
    success_message = "L'Exclusion de l'Enseigne %(signboard)s a été modifiée avec success"
    error_message = (
        "L'Exclusion de l'Enseigne %(signboard)s n'a pu être modifiée, une erreur c'est produite"
    )

    def get_context_data(self, **kwargs):
        """Insert the form into the context dict."""
        context = super().get_context_data(**kwargs)
        context["titre_table"] = "Mise à jour Exclusion Enseigne"
        context["chevron_retour"] = reverse("rfa:signboards_exclusion_list")
        return super().get_context_data(**context)

    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        return reverse("rfa:signboards_exclusion_list")

    def form_valid(self, form):
        """Ajout de l'user à la sauvegarde du formulaire."""
        form.instance.modified_by = self.request.user
        self.request.session["level"] = 20

        return super().form_valid(form)


@transaction.atomic
def signboard_exclusion_delete(request):
    """Suppression des exclusions d'Enseignes pour les RFA.

    :param request: Request Django
    :return: view.
    """
    if not is_ajax(request) or request.method != "POST":
        return redirect("home")

    data = {"success": "ko"}
    id_pk = request.POST.get("pk")
    form = DeleteSignboardExclusionForm({"id": id_pk})

    if form.is_valid():
        trace_mark_delete(
            request=request,
            django_model=SignboardExclusion,
            data_dict={"id": id_pk},
            force_delete=True,
        )
        data = {"success": "success"}

    else:
        LOGGER_VIEWS.error("delete_signboard_exclusion, form invalid : %r", form.errors)

    return JsonResponse(data)


def signboard_exclusion_export_list(_):
    """Export Excel de la liste des Exclusions RFA des Enseignes.

    :param _: Request Django
    :return: response_file.
    """
    try:
        today = pendulum.now()
        file_name = (
            "LISTING_DES_EXCLUSIONS_RFA_ENSEIGNES_"
            f"{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"
        )

        return response_file(excel_list_rfa_signboards_exclusion, file_name, CONTENT_TYPE_EXCEL)

    except Exception:
        LOGGER_EXPORT_EXCEL.exception("view : signboard_exclusion_export_list")

    return redirect(reverse("rfa:signboards_exclusion_list"))
