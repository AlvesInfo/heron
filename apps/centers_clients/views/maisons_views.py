# pylint: disable=E0401,R0903,W0201,W0702,W0613,W1203
"""
Views des Clients/Maisons
"""
from pathlib import Path
import pickle

import pendulum
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.core.files import File
from django.views.generic import ListView, CreateView, UpdateView

from heron.loggers import LOGGER_VIEWS
from heron.settings import PICKLERS_DIR
from apps.core.bin.change_traces import ChangeTraceMixin
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.core.models import PicklerFiles
from apps.centers_clients.excel_outputs.centers_clients_excel_maisons_list import (
    excel_liste_maisons,
)
from apps.accountancy.models import CctSage
from apps.book.models import Society
from apps.centers_clients.models import Maison, MaisonBi
from apps.centers_clients.forms import MaisonForm, ImportMaisonBiForm
from apps.centers_purchasing.models import ChildCenterPurchase
from apps.centers_clients.bin.gestion_cct import update_supplier_cct_reference_cosium


# ECRANS DES MAISONS ===============================================================================
class MaisonsList(ListView):
    """View de la liste des Maisons"""

    model = Maison
    queryset = Maison.objects.all().values(
        "third_party_num",
        "pk",
        "cct",
        "intitule",
        "center_purchase",
        "sign_board",
        "currency",
        "language",
        "pays__country_name",
        "type_x3__name",
        "credit_account__account",
        "debit_account__account",
        "cct__active"
    )
    context_object_name = "maisons"
    template_name = "centers_clients/clients_list.html"
    extra_context = {"titre_table": "Clients", "nb_paging": 25}


class MaisonCreate(ChangeTraceMixin, SuccessMessageMixin, CreateView):
    """CreateView de création des Maisons"""

    model = Maison
    form_class = MaisonForm
    form_class.use_required_attribute = False
    template_name = "centers_clients/client_update.html"
    success_message = "Le Client %(cct)s a été créé avec success"
    error_message = "Le Client %(cct)s n'a pu être créé, une erreur c'est produite"

    def get_initial(self):
        """Return the initial data to use for forms on this view."""
        initial = self.initial.copy()
        uuid_identification = self.kwargs["initials"]

        if uuid_identification == "*":
            return initial

        # Si un uuid est passé en paramètre de l'uuid, alors on récupère le fichier pickle,
        # pour initialiser le formulaire avec les données venues de la B.I
        self.pickler_object = get_object_or_404(
            PicklerFiles, uuid_identification=uuid_identification
        )

        with open(self.pickler_object.pickle_file.path, "rb") as file:
            unpickler = pickle.Unpickler(file)
            initial.update(unpickler.load())

        return initial

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["create"] = True
        context["chevron_retour"] = reverse("centers_clients:maisons_list")
        context["titre_table"] = "Création d'un nouveau Client"

        return context

    def form_valid(self, form):
        """
        On surcharge la méthode form_valid, pour supprimer les fichiers picklers au success du form.
        """
        form.instance.created_by = self.request.user

        try:
            form.instance.center_purchase = ChildCenterPurchase.objects.get(code="ACF")
        except ChildCenterPurchase.DoesNotExist:
            pass

        self.request.session["level"] = 20

        try:
            Path(self.pickler_object.pickle_file.path).unlink()
            pickle_file = Path(PICKLERS_DIR) / "import_bi.pick"
            pickle_file.unlink()
            self.pickler_object.delete()
        except AttributeError:
            # Création sans passer par import BI
            pass

        if form.instance.reference_cosium:
            form.save()
            update_supplier_cct_reference_cosium(form.instance.reference_cosium)

        return super().form_valid(form)


class MaisonUpdate(ChangeTraceMixin, SuccessMessageMixin, UpdateView):
    """UpdateView pour modification des identifiants pour les fournisseurs EDI"""

    model = Maison
    form_class = MaisonForm
    form_class.use_required_attribute = False
    template_name = "centers_clients/client_update.html"
    success_message = "Le Client %(cct)s a été modifiée avec success"
    error_message = "Le Client %(cct)s n'a pu être modifiée, une erreur c'est produite"

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template"""
        context = super().get_context_data(**kwargs)
        context["chevron_retour"] = reverse("centers_clients:maisons_list")
        context["titre_table"] = (
            f"Mise à jour du Client : "
            f"{context.get('object').cct} - "
            f"{context.get('object').intitule}"
        )
        context["adresse_principale_sage"] = (
            context.get("object")
            .third_party_num.society_society.filter(address_code="1").first()
        )
        context["cct__active"] = context.get("object").cct.active

        return context

    def form_valid(self, form, **kwargs):
        """Ajout de l'user à la sauvegarde du formulaire"""
        form.instance.modified_by = self.request.user
        form.instance.axe_bu = form.cleaned_data.get("axe_bu")

        try:
            form.instance.center_purchase = ChildCenterPurchase.objects.get(code="ACF")
        except ChildCenterPurchase.DoesNotExist:
            pass

        self.request.session["level"] = 20

        if form.instance.reference_cosium:
            form.save()
            update_supplier_cct_reference_cosium(form.instance.reference_cosium)

        return super().form_valid(form)


def maisons_export_list(_):
    """
    Export Excel de la liste des Sociétés
    :param _: Request Django
    :return: response_file
    """
    try:
        today = pendulum.now()
        file_name = f"LISTING_DES_CLIENTS_{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"

        return response_file(excel_liste_maisons, file_name, CONTENT_TYPE_EXCEL)

    except:
        LOGGER_VIEWS.exception("view : maisons_export_list")

    return redirect(reverse("centers_clients:maisons_list"))


def import_bi(request):
    """
    View pour importer depuis la B.I et ainsi récupérer les principaux éléments,
    en vue de la création d'un Client. Après avoir récupéré et validé le formulaire saisi, on crée
    un dictionnaire et on le pickle de façon à pouvoir le récupérer dans la CreateView de la Maison
    en  lui passant un uuid dans l'url
    """

    form = ImportMaisonBiForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            society = Society.objects.get(third_party_num=form.cleaned_data.get("tiers"))
            maison_bi = MaisonBi.objects.get(code_maison=form.cleaned_data.get("maison_bi"))
            cct = CctSage.objects.get(cct=form.cleaned_data.get("cct"))
            maison = Maison.objects.filter(cct=cct)

            if maison.exists():
                request.session["level"] = 50
                messages.error(
                    request,
                    f'Ce "CCT : {cct.cct}, est déjà utilisé!',
                )

            else:
                initials = {
                    "cct": cct,
                    "third_party_num": society,
                    "code_maison": maison_bi.code_maison,
                    "intitule": maison_bi.intitule,
                    "intitule_court": maison_bi.intitule_court,
                    "code_cosium": maison_bi.code_cosium,
                    "reference_cosium": maison_bi.reference_cosium,
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
                    "signature_franchise_date": maison_bi.opening_date,
                }

                pickle_file = Path(PICKLERS_DIR) / "import_bi.pick"

                with open(pickle_file, "wb") as file:
                    pickler = pickle.Pickler(file)
                    pickler.dump(initials)

                with open(pickle_file, "rb") as file:
                    pickler_object = PicklerFiles.objects.create(
                        pickle_file=File(file, name=pickle_file.name)
                    )
                    uuid_pickler = pickler_object.uuid_identification

                return redirect("centers_clients:maisons_create", initials=str(uuid_pickler))

        else:
            LOGGER_VIEWS.exception(f"erreur form : {str(form.data)!r}")

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


def emails_rest_api_query(request, query):
    """Views pour ramener les emails en cas de changement de tiers X3"""
    if request.is_ajax() and request.method == "GET":
        dic = {"success": "ko", "message": ""}

        try:
            if len(query) == 14:
                query = query[:13]

            articles = Maison.objects.annotate().values("id", "cct")

            if articles.count() > 30:
                dic = {"success": []}
            else:
                dic = {"success": [{**dic} for dic in articles]}

        except:
            LOGGER_VIEWS.exception("emails_rest_api_query")

        response = JsonResponse(dic)
        return HttpResponse(response)

    return redirect("home")
