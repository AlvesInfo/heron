# pylint: disable=E0401,R0903,W0702,W0613,R0901,E1101,W0201
"""
Views des Abonnements
"""
import pendulum
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect, reverse
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import ListView, CreateView, UpdateView

from heron.loggers import LOGGER_VIEWS
from apps.core.bin.change_traces import ChangeTraceMixin
from apps.core.bin.change_traces import trace_mark_delete
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.centers_clients.excel_outputs.excel_maisons_excel_subscriptions import (
    excel_liste_subscriptions,
)
from apps.centers_clients.models import MaisonSubcription
from apps.centers_clients.forms import (
    MaisonSubcriptionForm,
    DeleteMaisonSubcriptionForm,
)


# ECRANS DES ABONNEMENTS ===========================================================================
class MaisonSubcriptionList(ListView):
    """View de la liste des Abonnements"""

    model = MaisonSubcription
    queryset = MaisonSubcription.objects.all().values(
        "pk",
        "maison",
        "maison__intitule",
        "article__reference",
        "qty",
        "unit_weight__unity",
        "net_unit_price",
        "function",
        "for_signboard",
    )
    context_object_name = "subscriptions"
    template_name = "centers_clients/subscriptions_list.html"
    extra_context = {"titre_table": "Abonnements"}


class MaisonSubcriptionCreate(ChangeTraceMixin, SuccessMessageMixin, CreateView):
    """CreateView de création des Abonnements"""

    model = MaisonSubcription
    form_class = MaisonSubcriptionForm
    form_class.use_required_attribute = False
    template_name = "centers_clients/subscription_update.html"
    success_message = "L'Abonnement %(maison)s - %(article)s a été créé avec success"
    error_message = (
        "L'Abonnement %(maison)s - %(article)s n'a pu être créé, une erreur c'est produite"
    )

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["create"] = True
        context["chevron_retour"] = reverse("centers_clients:subscriptions_list")
        context["titre_table"] = "Création d'un nouvel Abonnement"
        return context

    def form_valid(self, form):
        """Ajout de l'user à la sauvegarde du formulaire"""
        form.instance.created_by = self.request.user
        self.request.session["level"] = 20

        return super().form_valid(form)


class MaisonSubcriptionUpdate(ChangeTraceMixin, SuccessMessageMixin, UpdateView):
    """UpdateView pour modification des Abonnements"""

    model = MaisonSubcription
    form_class = MaisonSubcriptionForm
    form_class.use_required_attribute = False
    template_name = "centers_clients/subscription_update.html"
    success_message = "L'Abonnement %(maison)s - %(article)s a été modifiée avec success"
    error_message = (
        "L'Abonnement %(maison)s - %(article)s n'a pu être modifiée, une erreur c'est produite"
    )

    def get_context_data(self, **kwargs):
        """Insert the form into the context dict."""

        context = super().get_context_data(**kwargs)
        context["titre_table"] = "Mise à jour d'un Abonnement"
        context["chevron_retour"] = reverse("centers_clients:subscriptions_list")
        return super().get_context_data(**context)

    def form_valid(self, form, **kwargs):
        """Ajout de l'user à la sauvegarde du formulaire"""
        form.instance.modified_by = self.request.user
        self.request.session["level"] = 20

        return super().form_valid(form)


def subscriptions_export_list(_):
    """
    Export Excel de la liste des Abonnements
    :param _: Request Django
    :return: response_file
    """
    try:

        today = pendulum.now()
        file_name = f"LISTING_DES_ABONNEMENTS_{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"

        return response_file(excel_liste_subscriptions, file_name, CONTENT_TYPE_EXCEL)

    except:
        LOGGER_VIEWS.exception("view : subscriptions_export_list")

    return redirect(reverse("centers_clients:subscriptions_list"))


@transaction.atomic
def subscription_delete(request):
    """Suppression des fonctions
    :param request: Request Django
    :return: view
    """

    if not request.is_ajax() and request.method != "POST":
        return redirect("home")

    data = {"success": "ko"}
    id_pk = request.POST.get("pk")
    form = DeleteMaisonSubcriptionForm({"id": id_pk})

    if form.is_valid():
        trace_mark_delete(
            request=request,
            django_model=MaisonSubcription,
            data_dict={"id": id_pk},
            force_delete=True,
        )
        data = {"success": "success"}

    else:
        LOGGER_VIEWS.exception(f"subscription_delete, form invalid : {form.errors!r}")

    return JsonResponse(data)
