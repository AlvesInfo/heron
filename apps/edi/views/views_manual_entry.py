# pylint: disable=E0401,W1203,W0718,R0914
"""
FR : Module des vues pour les saisies et visualisation des marchandises
EN : Views module for entering and viewing goods

Commentaire:

created at: 2023-01-04
created by: Paulo ALVES

modified at: 2023-01-04
modified by: Paulo ALVES
"""
import json

from django.contrib import messages
from django.shortcuts import render, reverse, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.db import transaction

from heron.loggers import LOGGER_VIEWS
from apps.accountancy.bin.utilities import get_youngests_vat_rate
from apps.edi.bin.duplicates_check import check_invoice_exists
from apps.edi.bin.edi_utilites import (
    set_trace_hand_invoice,
    data_dict_invoices_clean,
    get_query_articles,
    get_personal_profession_type,
)
from apps.edi.bin.set_hand_invoices import set_hand_invoice
from apps.edi.forms import (
    CreateBaseMarchandiseForm,
    CreateMarchandiseInvoiceForm,
    CreateBaseFormationForm,
    CreateFormationInvoiceForm,
    CreateBasePersonnelForm,
    CreatePersonnelInvoiceForm,
    # CreateBaseRfaForm,
    # CreateRfaInvoiceForm,
)
from apps.invoices.bin.pre_controls import control_insertion

# 1. CREATION DE FACTURES DE MARCHANDISES

CATEGORIES_DICT = {
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
    # "rfa": {
    #     "titre_table": "Saisie de Facture de Personnel",
    #     "form": CreateBaseRfaForm,
    #     "details_form": CreateRfaInvoiceForm,
    #     "query_articles": True,
    #     "nb_display": 50,
    # },
}


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

    level = 50
    titre_table, invoice_form, details_form, query_articles, nb_display = CATEGORIES_DICT.get(
        category
    ).values()
    data = {"success": "ko"}

    # On contrôle qu'il n'y ai pas des factures non finalisées, mais envoyées par mail
    not_finalize = control_insertion()

    if not_finalize:
        request.session["level"] = 50
        messages.add_message(
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

    if request.is_ajax() and request.method == "POST":
        user = request.user
        data_dict = json.loads(request.POST.get("data"))
        data_dict_invoices_clean(category, data_dict)

        # On vérifie s'il y a des lignes dans le POST, s'il n'y en a pas on renvoie un message
        # d'erreur pour ne pas insérer des factures vides, et on shortcut
        if not data_dict.get("lignes"):
            request.session["level"] = level
            messages.add_message(request, level, "Aucunes des lignes saisies n'avaient d'articles")

            return JsonResponse(data)

        try:
            form = invoice_form(data_dict.get("entete"))
            message = ""

            # On valide l'entête
            if form.is_valid():
                entete = form.cleaned_data
                third_party_num = entete.get("third_party_num")
                invoice_number = entete.get("invoice_number", "")
                invoice_date = entete.get("invoice_date")

                # On vérifie que cette facture n'existe pas
                if check_invoice_exists(
                    third_party_num,
                    invoice_number,
                    invoice_date.year,
                ):
                    error = True
                    message = f"La facture N°{invoice_number}, de {third_party_num} existe déjà!"

                    # On trace l'erreur, car cela ne se fera pas sans appel à set_hand_invoice()
                    set_trace_hand_invoice(
                        invoice_category=category,
                        invoice_number=invoice_number,
                        user=user,
                        errors=True,
                    )

                else:
                    # Si l'entête est bon, on va essayer de créer la facture complète
                    error, message = set_hand_invoice(
                        category, details_form, entete, data_dict.get("lignes"), user
                    )

                if not error:
                    level = 20

                request.session["level"] = level
                messages.add_message(request, level, message)

                return JsonResponse(data)

            # Si le formulaire d'entête est invalide, on génère le message à afficher
            for key, error_list in dict(form.errors).items():
                message += (
                    f" - {key} : {', '.join(list(error_list))}"
                    if message
                    else f"{key} : {', '.join(list(error_list))}"
                )

            # On trace l'erreur, car cela ne se fera pas sans appel à set_hand_invoice()
            set_trace_hand_invoice(
                invoice_category=category,
                invoice_number=data_dict.get("entete").get("invoice_number", ""),
                user=user,
                errors=True,
            )

            request.session["level"] = level
            messages.add_message(request, level, message)

            return JsonResponse(data)

        except Exception as error:
            request.session["level"] = level
            messages.add_message(
                request, level, "Une erreur c'est produite, veuillez consulter les logs"
            )
            LOGGER_VIEWS.exception(f"erreur form : {str(error)!r}")

            # On trace l'erreur, car cela ne se fera pas sans appel à set_hand_invoice()
            set_trace_hand_invoice(
                invoice_category=category,
                invoice_number=data_dict.get("entete").get("invoice_number", ""),
                user=user,
                errors=True,
            )

            return JsonResponse(data)

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
