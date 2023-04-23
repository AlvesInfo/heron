# pylint: disable=E0401,R0903,W0702
"""
Views des Types de pièces par centales filles
"""
from django.http import JsonResponse
from django.shortcuts import redirect, reverse
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import ListView, CreateView, UpdateView

from heron.loggers import LOGGER_VIEWS
from apps.core.bin.change_traces import ChangeTraceMixin, trace_mark_delete
from apps.centers_purchasing.models import TypeFacture
from apps.centers_purchasing.forms import TypeFactureForm, TypeFactureDeleteForm


# ECRANS DES CENTRALES FILLES / Types de Facture ===================================================

class TypeFactureList(ListView):
    """View de la liste des Types de Factures"""

    model = TypeFacture
    context_object_name = "type_factures"
    template_name = "centers_purchasing/type_facture_list.html"
    extra_context = {"titre_table": "Centrale / Type de Facture"}


class TypeFactureCreate(ChangeTraceMixin, SuccessMessageMixin, CreateView):
    """CreateView de création des Types de Facture"""

    model = TypeFacture
    form_class = TypeFactureForm
    form_class.use_required_attribute = False
    template_name = "centers_purchasing/type_facture_update.html"
    success_message = (
        "Le Type de Facture %(child_center)s - %(invoice_type)s,  a été créé avec success"
    )
    error_message = (
        "Le Type de Facture %(child_center)s - %(invoice_type)s, "
        "n'a pu être créé, une erreur c'est produite"
    )

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["create"] = True
        context["chevron_retour"] = reverse("centers_purchasing:type_facture_list")
        context["titre_table"] = "Création d'un nouveau type de Facture"
        return context

    def form_valid(self, form):
        """Ajout de l'user à la sauvegarde du formulaire"""
        self.request.session["level"] = 20

        return super().form_valid(form)


class TypeFactureUpdate(ChangeTraceMixin, SuccessMessageMixin, UpdateView):
    """UpdateView pour modification des Types de Facture"""

    model = TypeFacture
    form_class = TypeFactureForm
    form_class.use_required_attribute = False
    template_name = "centers_purchasing/type_facture_update.html"
    success_message = (
        "Le Type de Facture %(child_center)s - %(invoice_type)s, a été modifiée avec success"
    )
    error_message = (
        "Le Type de Facture %(child_center)s - %(invoice_type)s, "
        "n'a pu être modifiée, une erreur c'est produite"
    )

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["chevron_retour"] = reverse("centers_purchasing:type_facture_list")
        context["titre_table"] = (
            f"Mise à jour du Type de Facture : "
            f"{context.get('object').child_center} - "
            f"{context.get('object').invoice_type}"
        )
        return context

    def form_valid(self, form, **kwargs):
        """Ajout de l'user à la sauvegarde du formulaire"""
        self.request.session["level"] = 20

        return super().form_valid(form)


def type_facture_delete(request):
    """Vue ajax de suppresion d'une ligne de la table"""

    if not request.is_ajax() and request.method != "POST":
        return redirect("home")

    data = {"success": "ko"}
    id_pk = request.POST.get("pk")
    form = TypeFactureDeleteForm({"id": id_pk})

    if form.is_valid():
        trace_mark_delete(
            request=request,
            django_model=TypeFacture,
            data_dict={"id": id_pk},
            force_delete=True,
        )
        data = {"success": "success"}

    else:
        LOGGER_VIEWS.exception(f"type_piece_delete, form invalid : {form.errors!r}")

    return JsonResponse(data)
