"""FR : Module des vues pour les saisies et visualisation des marchandises.

EN : Views module for entering and viewing goods.

Commentaire:

created at: 2023-01-04
created by: Paulo ALVES

modified at: 2023-01-04
modified by: Paulo ALVES
"""

import json
from typing import Any

from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect

from apps.accountancy.bin.utilities import get_youngests_vat_rate
from apps.core.functions.functions_http import is_ajax
from apps.edi.bin.duplicates_check import check_invoice_exists
from apps.edi.bin.edi_utilites import (
    data_dict_invoices_clean,
    form_errors_message,
    get_personal_profession_type,
    get_query_articles,
    set_trace_hand_invoice,
)
from apps.edi.bin.set_hand_invoices import set_hand_invoice
from apps.edi.forms import (
    CreateBaseFormationForm,
    CreateBaseMarchandiseForm,
    CreateBasePersonnelForm,
    CreateFormationInvoiceForm,
    CreateMarchandiseInvoiceForm,
    CreatePersonnelInvoiceForm,
    # CreateBaseRfaForm,
    # CreateRfaInvoiceForm,
)
from apps.invoices.bin.pre_controls import control_insertion
from heron.loggers import LOGGER_VIEWS

# 1. CREATION DE FACTURES DE MARCHANDISES

CATEGORIES_DICT: dict[str, dict[str, Any]] = {
    "marchandises": {
        "titre_table": "Saisie de Facture de Marchandises",
        "form": CreateBaseMarchandiseForm,
        "details_form": CreateMarchandiseInvoiceForm,
        "query_articles": False,
        "nb_display": 50,
    },
    "formation": {
        "titre_table": "Saisie de Facture de Formations",
        "form": CreateBaseFormationForm,
        "details_form": CreateFormationInvoiceForm,
        "query_articles": True,
        "nb_display": 1,
    },
    "personnel": {
        "titre_table": "Saisie de Facture de Personnel",
        "form": CreateBasePersonnelForm,
        "details_form": CreatePersonnelInvoiceForm,
        "query_articles": True,
        "nb_display": 30,
    },
}


def _add_message(request, level: int, message: str) -> None:
    """Pose le niveau du message en session et ajoute le message à afficher."""
    request.session["level"] = level
    messages.add_message(request, level, message)


def _save_hand_invoice(category, details_form, entete, lignes, user):
    """Crée la facture saisie si elle n'existe pas déjà.

    :param category: Catégorie de facturation
    :param details_form: formulaire des lignes de la catégorie
    :param entete: données validées de l'entête
    :param lignes: lignes saisies
    :param user: utilisateur qui saisit
    :return: (erreur, message).
    """
    third_party_num = entete.get("third_party_num")
    invoice_number = entete.get("invoice_number", "")
    invoice_date = entete.get("invoice_date")

    # On vérifie que cette facture n'existe pas
    if not check_invoice_exists(third_party_num, invoice_number, invoice_date.year):
        # Si l'entête est bon, on va essayer de créer la facture complète
        return set_hand_invoice(category, details_form, entete, lignes, user)

    # On trace l'erreur, car cela ne se fera pas sans appel à set_hand_invoice()
    set_trace_hand_invoice(
        invoice_category=category,
        invoice_number=invoice_number,
        user=user,
        errors=True,
    )

    return True, f"La facture N°{invoice_number}, de {third_party_num} existe déjà!"


def _post_hand_invoices(request, category, invoice_form, details_form):
    """Traite la saisie postée en ajax : validation de l'entête puis création de la facture.

    :param request: Request au sens Django
    :param category: Catégorie de facturation
    :param invoice_form: formulaire d'entête de la catégorie
    :param details_form: formulaire des lignes de la catégorie
    :return: JsonResponse, le résultat est porté par les messages.
    """
    level = 50
    data = {"success": "ko"}
    user = request.user
    data_dict = json.loads(request.POST.get("data"))
    data_dict_invoices_clean(category, data_dict)

    # On vérifie s'il y a des lignes dans le POST, s'il n'y en a pas on renvoie un message
    # d'erreur pour ne pas insérer des factures vides, et on shortcut
    if not data_dict.get("lignes"):
        _add_message(request, level, "Aucunes des lignes saisies n'avaient d'articles")

        return JsonResponse(data)

    try:
        form = invoice_form(data_dict.get("entete"))

        # On valide l'entête
        if form.is_valid():
            error, message = _save_hand_invoice(
                category, details_form, form.cleaned_data, data_dict.get("lignes"), user
            )

            if not error:
                level = 20

        else:
            # Si le formulaire d'entête est invalide, on génère le message à afficher
            message = form_errors_message(form)

            # On trace l'erreur, car cela ne se fera pas sans appel à set_hand_invoice()
            set_trace_hand_invoice(
                invoice_category=category,
                invoice_number=data_dict.get("entete").get("invoice_number", ""),
                user=user,
                errors=True,
            )

        _add_message(request, level, message)

    except Exception as error:
        _add_message(request, level, "Une erreur c'est produite, veuillez consulter les logs")
        LOGGER_VIEWS.exception("erreur form")

        # On trace l'erreur, car cela ne se fera pas sans appel à set_hand_invoice()
        set_trace_hand_invoice(
            invoice_category=category,
            invoice_number=data_dict.get("entete").get("invoice_number", ""),
            user=user,
            errors=True,
        )

    return JsonResponse(data)


@csrf_protect
@transaction.atomic
def create_hand_invoices(request, category):
    """View de création des factures par saisie manuelle.

    Dans le template il y aura des affichages en fonction des catégories. Si une catégorie
    est ajoutée ou enlevée, il faudra procéder au nettoyage du template aussi.

    Dans le template :
        - les Articles ont un data-models="articles"
        - les CCT ont un data-models="maisons"

    Les data-models servent à ce que l'appel de l'api renvoyant les données,
    sache quelle est la fonction à appliquer.

    L'url appelée est "api_models_query/<str:models>/<str:query>/",
    ou models est ce qu'il y a dans data-models.

    La view endpoint apps/core/views/api_models_query, va remplir les champs avec les fonctions
    du dictionnaire MODEL_DICT, ou la key est le data-models et sa fonction correspondante,
    qui est dans apps/core/bin/api_get_models.py

    :param request:  Request au sens Django
    :param category:  Catégorie de facturation
    """
    if category not in CATEGORIES_DICT:
        return redirect("home")

    titre_table, invoice_form, details_form, query_articles, nb_display = CATEGORIES_DICT[
        category
    ].values()

    # On contrôle qu'il n'y ai pas des factures non finalisées, mais envoyées par mail
    not_finalize = control_insertion()

    if not_finalize:
        _add_message(
            request,
            50,
            (
                "Vous ne pouvez pas saisir de factures, "
                "car la facturation est déjà envoyée par mail, mais non finalisée"
            ),
        )
        context = {
            "margin_table": 50,
            "titre_table": titre_table,
            "not_finalize": True,
            "nb_display": nb_display,
            "range_display": range(1, nb_display + 1),
            "chevron_retour": reverse("home"),
        }
        return render(request, "edi/invoice_hand_update.html", context=context)

    if is_ajax(request) and request.method == "POST":
        return _post_hand_invoices(request, category, invoice_form, details_form)

    context = {
        "titre_table": titre_table,
        "nb_display": nb_display,
        "range_display": range(1, nb_display + 1),
        "chevron_retour": reverse("home"),
        "form_base": invoice_form(),
        "url_saisie": reverse("edi:create_hand_invoices", kwargs={"category": category}),
        "category": category,
        "query_articles": get_query_articles(category) if query_articles else "",
        "form_detail": details_form(),
        "vat_list": get_youngests_vat_rate(),
    }

    if category == "personnel":
        context.update({"query_profession_type": get_personal_profession_type()})

    return render(request, "edi/invoice_hand_update.html", context=context)
