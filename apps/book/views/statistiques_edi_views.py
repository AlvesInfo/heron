"""Views des Statistiques par défault lors de nouveaux articles venant de l'edi."""

import pendulum
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import CreateView, ListView, UpdateView

from apps.book.excel_outputs.book_excel_statistiques_list import excel_liste_statistiques
from apps.book.forms import (
    DeleteSupplierFamilyAxesForm,
    StatFamillyAxesForm,
    SupplierFamilyAxesForm,
)
from apps.book.models.supplier_identifiers_models import StatFamillyAxes, SupplierFamilyAxes
from apps.core.bin.change_traces import ChangeTraceMixin, trace_mark_delete
from apps.core.functions.functions_http import is_ajax
from apps.core.functions.functions_http_response import CONTENT_TYPE_EXCEL, response_file
from heron.loggers import LOGGER_VIEWS


# ECRANS DES STATISTIQUES AXES FAMILLES ============================================================
class StatistiquesList(ListView):
    """View de la liste des Statistiques."""

    model = StatFamillyAxes
    context_object_name = "statistiques"
    template_name = "book/statistiques_list.html"
    extra_context = {"titre_table": "Familles Statistiques/Axes"}


class StatistiqueCreate(ChangeTraceMixin, SuccessMessageMixin, CreateView):
    """CreateView de création des Statistiques."""

    model = StatFamillyAxes
    form_class = StatFamillyAxesForm
    template_name = "book/statistique_update.html"
    success_message = "La Famille Statistiques/Axes %(name)s a été créé avec success"
    error_message = (
        "La Famille Statistiques/Axes %(name)s n'a pu être créé, une erreur c'est produite"
    )

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template."""
        context = super().get_context_data(**kwargs)
        context["create"] = True
        context["chevron_retour"] = reverse("book:statistiques_list")
        context["titre_table"] = "Création d'une nouvelle Famille Statistiques/Axes"
        return context

    def form_valid(self, form):
        """Ajout de l'user à la sauvegarde du formulaire."""
        form.instance.created_by = self.request.user
        self.request.session["level"] = 20
        return super().form_valid(form)


class StatistiqueUpdate(ChangeTraceMixin, SuccessMessageMixin, UpdateView):
    """UpdateView pour modification des identifiants pour les fournisseurs EDI."""

    model = StatFamillyAxes
    form_class = StatFamillyAxesForm
    slug_field = "name"
    slug_url_kwarg = "name"
    template_name = "book/statistique_update.html"
    success_message = "La Famille Statistiques/Axes %(name)s a été modifiée avec success"
    error_message = (
        "La Famille Statistiques/Axes %(name)s n'a pu être modifiée, une erreur c'est produite"
    )

    def get_context_data(self, **kwargs):
        """Insert the form into the context dict."""
        context = super().get_context_data(**kwargs)
        context["titre_table"] = "Mise à jour Famille Statistiques/Axes"
        context["chevron_retour"] = reverse("book:statistiques_list")
        return context

    def form_valid(self, form):
        """Ajout de l'user à la sauvegarde du formulaire."""
        form.instance.modified_by = self.request.user
        self.request.session["level"] = 20
        return super().form_valid(form)


def statistiques_export_list(_):
    """Export Excel de la liste des Sociétés.

    :param _: Request Django
    :return: response_file.
    """
    try:
        today = pendulum.now()
        file_name = (
            f"LISTING_DES_FAMILLES_STATISTIQUES_AXES_{today.format('Y_M_D')}"
            f"_{today.int_timestamp}.xlsx"
        )

        return response_file(excel_liste_statistiques, file_name, CONTENT_TYPE_EXCEL)

    except Exception:
        LOGGER_VIEWS.exception("view : statistiques_export_list")

    return redirect(reverse("book:statistiques_list"))


# ECRANS DES STATISTIQUES FAMILLES/AXES ============================================================


class FamillyAxeCreate(ChangeTraceMixin, SuccessMessageMixin, CreateView):
    """CreateView de création des définitions des Statistiques Familles/Axes."""

    model = SupplierFamilyAxes
    form_class = SupplierFamilyAxesForm
    template_name = "book/statistique_famille_axe_update.html"
    success_message = (
        "La Définition des Statistiques Familles/Axes Presta %(stat_name)s a été créé avec success"
    )
    error_message = (
        "La Définition des Statistiques Familles/Axes Presta %(stat_name)s n'a pu être créé, "
        "une erreur c'est produite"
    )

    def get(self, request, *args, **kwargs):  # noqa: ARG002 (signature Django)
        """Ajout de self.statistique a l'instance de la vue (404 si la statistique n'existe pas)."""
        self.statistique = get_object_or_404(StatFamillyAxes, pk=kwargs.get("statistique_pk"))
        return self.render_to_response(self.get_context_data())

    def post(self, request, *args, **kwargs):
        """Ajout de self.statistique a l'instance de la vue (404 si la statistique n'existe pas)."""
        self.object = None
        self.statistique = get_object_or_404(StatFamillyAxes, pk=kwargs.get("statistique_pk"))
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template."""
        context = super().get_context_data(**kwargs)
        context["create"] = True
        context["chevron_retour"] = reverse(
            "book:statistique_update", kwargs={"name": self.statistique.name}
        )
        context["titre_table"] = f"Création Statistique Familles/Axes : {self.statistique.name}"
        context["statistique"] = self.statistique
        return context

    def get_success_url(self):
        """Surcharge de l'url en case de succes pour revenir à la catégorie où l'on était."""
        return reverse("book:statistique_update", kwargs={"name": self.statistique.name})

    def form_valid(self, form):
        """Ajout de l'user à la sauvegarde du formulaire."""
        form.instance.created_by = self.request.user
        self.request.session["level"] = 20
        return super().form_valid(form)


class FamillyAxeUpdate(ChangeTraceMixin, SuccessMessageMixin, UpdateView):
    """UpdateView pour modification des définitions des Statistiques Familles/Axes."""

    model = SupplierFamilyAxes
    form_class = SupplierFamilyAxesForm
    template_name = "book/statistique_famille_axe_update.html"
    success_message = (
        "La Définition des Statistiques Familles/Axes Presta %(stat_name)s "
        "a été modifiée avec success"
    )
    error_message = (
        "La Définition des Statistiques Familles/Axes Presta %(stat_name)s n'a pu modifiée créé, "
        "une erreur c'est produite"
    )

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template."""
        context = super().get_context_data(**kwargs)
        context["create"] = True
        context["chevron_retour"] = reverse(
            "book:statistique_update", kwargs={"name": self.object.stat_name}
        )
        context["titre_table"] = "Modification de la Statistique Familles/Axes"
        context["statistique"] = self.object.stat_name
        return context

    def get_success_url(self):
        """Surcharge de l'url en case de succes pour revenir à la catégorie où l'on était."""
        return reverse("book:statistique_update", kwargs={"name": self.object.stat_name})

    def form_valid(self, form):
        """Ajout de l'user à la sauvegarde du formulaire."""
        form.instance.modified_by = self.request.user
        self.request.session["level"] = 20
        return super().form_valid(form)


@transaction.atomic
def delete_familly_axes(request):
    """Suppression des rubriques prestas.

    :param request: Request Django
    :return: view.
    """
    if not is_ajax(request) or request.method != "POST":
        return redirect("home")

    data = {"success": "ko"}
    id_pk = request.POST.get("pk")
    form = DeleteSupplierFamilyAxesForm({"id": id_pk})

    if form.is_valid():
        trace_mark_delete(
            request=request,
            django_model=SupplierFamilyAxes,
            data_dict={"id": id_pk},
            force_delete=True,
        )
        data = {"success": "success"}

    else:
        LOGGER_VIEWS.error("delete_familly_axes, form invalid : %r", form.errors)

    return JsonResponse(data)
