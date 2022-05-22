# pylint: disable=E0401,R0903
"""
Views des Maisons
"""
from pathlib import Path
import pickle

import pendulum
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.core.files import File
from django.views.generic import ListView, CreateView, UpdateView

from heron.loggers import ERROR_VIEWS_LOGGER
from heron.settings import PICKLERS_DIR
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.core.models import PicklerFiles
from apps.centers_clients.excel_outputs.centers_clients_excel_maisons_list import (
    excel_liste_maisons,
)
from apps.accountancy.models import CctSage
from apps.book.models import Society
from apps.centers_clients.models import Maison, MaisonBi
from apps.centers_clients.forms import MaisonForm, ImportMaisonBiForm


# ECRANS DES CLIENTS ===============================================================================


def clients(request):
    """Vue en table d'une société"""

    context = {}

    return render(request, "centers_clients/clients_home.html", context=context)


# ECRANS DES MAISONS ===============================================================================
class MaisonsList(ListView):
    """View de la liste des Maisons"""

    model = Maison
    context_object_name = "maisons"
    template_name = "centers_clients/clients_list.html"
    extra_context = {"titre_table": "Clients"}


def import_bi(request):
    """
    View pour importer depuis la B.I et ainsi récupérer les principaux éléments,
    en vue de la création d'un Client
    """

    form = ImportMaisonBiForm(request.POST or None)

    if request.method == "POST":

        if form.is_valid():
            society = Society.objects.get(third_party_num=form.cleaned_data.get("tiers"))
            maison_bi = MaisonBi.objects.get(code_maison=form.cleaned_data.get("maison_bi"))
            cct = CctSage.objects.get(cct=form.cleaned_data.get("cct"))
            if Maison.objects.filter(cct=cct, tiers=society).exists():
                messages.error(
                    request,
                    f'Le couple "CCT : {cct.cct} / Tiers : {society.third_party_num}" existe déjà!',
                )
            else:
                initials = {
                    "cct": cct,
                    "tiers": society,
                    "code_maison": maison_bi.code_maison,
                    "intitule": maison_bi.intitule,
                    "intitule_court": maison_bi.intitule_court,
                    "code_cosium": maison_bi.code_cosium,
                    "code_bbgr": maison_bi.code_bbgr,
                    "opening_date": maison_bi.opening_date,
                    "closing_date": maison_bi.closing_date,
                    "immeuble": maison_bi.immeuble,
                    "adresse": maison_bi.adresse,
                    "code_postal": maison_bi.code_postal,
                    "ville": maison_bi.ville,
                    "pays": maison_bi.pays,
                    "telephone": maison_bi.telephone,
                    "email": maison_bi.email,
                }

                pickle_file = Path(PICKLERS_DIR) / "import_bi.pick"

                with open(pickle_file, "wb") as file:
                    pickler = pickle.Pickler(file)
                    pickler.dump(initials)

                with open(pickle_file, "rb") as file:
                    pickler_object = PicklerFiles.objects.create(
                        pickle_file=File(file, name=pickle_file)
                    )
                    uuid_pickler = pickler_object.uuid_identification

                return redirect("centers_clients:maisons_create", initials=str(uuid_pickler))

        else:
            ERROR_VIEWS_LOGGER.exception(f"erreur form : {str(form.data)!r}")

    context = {
        "titre_table": "Création d'un Client avec import depuis la B.I",
        "form": form,
        "chevron_retour": reverse("centers_clients:maisons_list"),
    }
    return render(request, "centers_clients/import_client_bi.html", context=context)


def filter_list_maisons_api(request):
    """View de filtrage pour les menus des maisons"""

    context = {}
    return render(request, "centers_clients/maisons_list_to_pick.html", context=context)


class MaisonCreate(SuccessMessageMixin, CreateView):
    """CreateView de création des Maisons"""

    model = Maison
    form_class = MaisonForm
    form_class.use_required_attribute = False
    template_name = "centers_clients/client_update.html"
    success_message = "Le CLient %(cct)s a été créé avec success"
    error_message = "Le CLient %(cct)s n'a pu être créé, une erreur c'est produite"

    def get_initial(self):
        """Return the initial data to use for forms on this view."""
        initial = self.initial.copy()
        uuid_identification = self.kwargs["initials"]

        if uuid_identification == "*":
            return initial

        self.pickler_object = get_object_or_404(
            PicklerFiles, uuid_identification=uuid_identification
        )

        with open(self.pickler_object.pickle_file.path, "rb") as file:
            unpickler = pickle.Unpickler(file)
            initial.update(unpickler.load())

        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["create"] = True
        context["chevron_retour"] = reverse("centers_clients:maisons_list")
        context["titre_table"] = "Création d'un nouveau Client"
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.modified_by = self.request.user
        self.request.session["level"] = 20
        Path(self.pickler_object.pickle_file.path).unlink()
        pickle_file = Path(PICKLERS_DIR) / "import_bi.pick"
        pickle_file.unlink()
        self.pickler_object.delete()
        return super().form_valid(form)

    def form_invalid(self, form):
        self.request.session["level"] = 50
        return super().form_invalid(form)


class MaisonUpdate(SuccessMessageMixin, UpdateView):
    """UpdateView pour modification des identifiants pour les fournisseurs EDI"""

    model = Maison
    form_class = MaisonForm
    form_class.use_required_attribute = False
    template_name = "centers_clients/client_update.html"
    success_message = "Le CLient %(cct)s a été modifiée avec success"
    error_message = "Le CLient %(cct)s n'a pu être modifiée, une erreur c'est produite"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["chevron_retour"] = reverse("centers_clients:maisons_list")
        context["titre_table"] = (
            f"Mise à jour du Client : "
            f"{context.get('object').cct} - "
            f"{context.get('object').intitule}"
        )
        return context

    def form_valid(self, form):
        form.instance.modified_by = self.request.user
        self.request.session["level"] = 20
        return super().form_valid(form)

    def form_invalid(self, form):
        self.request.session["level"] = 50
        return super().form_invalid(form)


def maisons_export_list(request):
    """
    Export Excel de la liste des Sociétés
    :param request: Request Django
    :return: response_file
    """
    try:

        today = pendulum.now()
        file_name = (
            f"LISTING_DES_CLIENTS_{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"
        )

        return response_file(excel_liste_maisons, file_name, CONTENT_TYPE_EXCEL)

    except:
        ERROR_VIEWS_LOGGER.exception("view : maisons_export_list")

    return redirect(reverse("centers_clients:maisons_list"))
