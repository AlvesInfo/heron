"""
FR : Module de traitement des factures saisies à la main
EN : New article processing module for in articles table with new_article = true

Commentaire:

created at: 2023-03-18
created by: Paulo ALVES

modified at: 2023-03-18
modified by: Paulo ALVES
"""
from typing import AnyStr, Dict, List
from decimal import Decimal
from uuid import uuid4

import pendulum
from django.db import transaction
from django import forms

from heron.loggers import LOGGER_IMPORT
from apps.users.models import User
from apps.accountancy.bin.utilities import get_dict_vat_rates
from apps.articles.bin.articles_queries import get_article
from apps.edi.bin.data_edi_invoices_nums import get_invoices_manual_entries_nums
from apps.edi.bin.edi_utilites import (
    form_errors_message,
    get_sens,
    set_trace_hand_invoice,
    set_signboard,
)
from apps.edi.models import EdiImport
from apps.book.models import Society
from apps.parameters.models import UnitChoices


def _entered_amount(line_dict: Dict, key: AnyStr, qty: Decimal):
    """Montant saisi sur la ligne (virgule décimale acceptée), du signe de la quantité ;
    None si rien n'a été saisi ou si la saisie vaut "0"
    :param line_dict: ligne de la facture
    :param key: nom du montant ("vat_amount" ou "amount_with_vat")
    :param qty: quantité signée de la ligne
    """
    value = line_dict.get(key)

    if not value or value == "0":
        return None

    # Signe de la quantité, sans division : une quantité nulle garde le montant saisi positif
    sign = -1 if qty < 0 else 1

    return sign * Decimal(value.replace(",", "."))


def _line_amounts(line_dict: Dict, invoice_type: AnyStr, vat_dict: Dict) -> Dict:
    """Montants d'une ligne ; pour un avoir (type 381) le sens de la quantité est inversé,
    y compris dans la ligne reçue
    :param line_dict: ligne de la facture
    :param invoice_type: type de facture de l'entête
    :param vat_dict: taux et régimes de TVA à la date de la facture
    """
    qty = Decimal(line_dict["qty"])

    # Si c'est un avoir (type 381) alors on change le sens
    if invoice_type == "381":
        qty = -qty
        line_dict["qty"] = f"-{line_dict['qty']}"

    net_unit_price = Decimal(line_dict["net_unit_price"])
    vat_regime, vat_rate = vat_dict.get(line_dict["vat"] or "001")
    vat_rate = round(Decimal(vat_rate), 5)
    net_amount = round(qty * net_unit_price, 2)
    vat_amount = _entered_amount(line_dict, "vat_amount", qty)

    if vat_amount is None:
        vat_amount = round(net_amount * vat_rate, 2)

    amount_with_vat = _entered_amount(line_dict, "amount_with_vat", qty)

    if amount_with_vat is None:
        amount_with_vat = net_amount + vat_amount

    return {
        "gross_unit_price": net_unit_price,
        "net_amount": net_amount,
        "vat_rate": vat_rate,
        "vat_amount": vat_amount,
        "amount_with_vat": amount_with_vat,
        "vat_regime": vat_regime,
    }


def _validate_lines(
    category_form: forms.ModelForm,
    entete_dict: Dict,
    lignes_list: List,
    vat_dict: Dict,
    sens_dict: Dict,
    user_uuid_identification,
):
    """Valide les lignes de la facture et cumule les totaux
    :param category_form: Form django de la catégorie
    :param entete_dict: Dictionnaire de l'entête de la facture
    :param lignes_list: Liste des dictionnaires des lignes de la facture
    :param vat_dict: taux et régimes de TVA à la date de la facture
    :param sens_dict: sens de facturation (achat / vente)
    :param user_uuid_identification: uuid de l'utilisateur qui saisit
    :return: (lignes à créer, cct rencontrés, totaux de la facture, message d'erreur ou None)
    """
    invoice_date = entete_dict.get("invoice_date")
    lines_to_create = []
    multistore_set = set()
    cct_dict = {"cct_uuid_identification": None}
    totals = {
        "invoice_amount_without_tax": Decimal("0"),
        "invoice_amount_tax": Decimal("0"),
        "invoice_amount_with_tax": Decimal("0"),
    }

    for line_dict in lignes_list:
        # Si la ligne n'a pas de cct alors on reprend celui de la ligne précédente
        if line_dict.get("cct_uuid_identification"):
            cct_dict = {
                "cct_uuid_identification": line_dict.get("cct_uuid_identification"),
                "created_by": user_uuid_identification,
                "saisie_by": user_uuid_identification,
                "modified_by": user_uuid_identification,
                "origin": 4,
                "invoice_month": pendulum.parse(invoice_date.isoformat()).start_of("month"),
                "invoice_year": invoice_date.year,
                **sens_dict,
            }

        # on calcule les montants par ligne et additionne les montants pour le total facturé
        amounts = _line_amounts(line_dict, entete_dict.get("invoice_type"), vat_dict)
        totals["invoice_amount_without_tax"] += amounts["net_amount"]
        totals["invoice_amount_tax"] += amounts["vat_amount"]
        totals["invoice_amount_with_tax"] += amounts["amount_with_vat"]
        cct_dict.update(amounts)

        # On récupère les axes et catégories des articles dans la base article
        articles_dict = get_article(line_dict.get("reference_article"))
        # On va valider le formulaire
        form = category_form({**entete_dict, **line_dict, **cct_dict, **articles_dict})

        if not form.is_valid():
            return lines_to_create, multistore_set, totals, form_errors_message(form)

        maison = form.cleaned_data.get("cct_uuid_identification")
        multistore_set.add(maison.cct)
        line_to_insert = {
            **form.cleaned_data,
            "code_fournisseur": maison.cct.cct,
            "code_maison": maison.cct.cct,
            "maison": maison.intitule,
            "import_uuid_identification": uuid4(),
        }
        # la référence article saisie doit être l'identifiant (entier) de l'article
        int(line_dict.get("reference_article", 0))
        lines_to_create.append(line_to_insert)

    return lines_to_create, multistore_set, totals, None


def _rows_to_insert(
    entete_dict: Dict, lines_to_create: List, third_party_num: AnyStr, totals: Dict, is_multi_store: bool
) -> List:
    """Dictionnaires des lignes à créer dans edi_ediimport, complétés des éléments de la facture
    :param entete_dict: Dictionnaire de l'entête de la facture
    :param lines_to_create: lignes validées
    :param third_party_num: Tiers X3 de la facture
    :param totals: totaux de la facture
    :param is_multi_store: True si la facture porte sur plusieurs cct
    """
    edi_import_list = []
    uuid_identification = uuid4()
    society = Society.objects.get(third_party_num=third_party_num)

    for line_dict in lines_to_create:
        results_dict = {**entete_dict, **line_dict}

        if not results_dict.get("unit_weight"):
            results_dict["unit_weight"] = UnitChoices.objects.get(unity="U")

        # On ajoute les éléments manquants
        results_dict.update(
            {
                "uuid_identification": uuid_identification,
                "supplier": str(society.short_name)[:35],
                "supplier_ident": third_party_num,
                "supplier_name": str(society.name)[:80],
                "valid": True,
                "saisie": True,
                "is_multi_store": is_multi_store,
                "manual_entry": True,
                **totals,
            }
        )
        edi_import_list.append(results_dict)

    return edi_import_list


@transaction.atomic
def set_hand_invoice(
    invoice_category: AnyStr,
    category_form: forms.ModelForm,
    entete_dict: Dict,
    lignes_list: List,
    user: User.objects,
):
    """
    Création dans edi_import des factures saisies manuellement
    :param invoice_category: Catégorie ( marchandises, formations, personnel)
    :param category_form: Form django de la catégorie
    :param entete_dict: Dictionnaire de l'entête de la facture
    :param lignes_list: Liste des dictionnaires des lignes de la facture
    :param user: user qui créer la facture
    :return: error (True/False), message ("" si pas d'erreur/"message" si erreur)
    """

    error = False
    message = ""
    third_party_num = entete_dict.get("third_party_num")
    invoice_number = entete_dict.get("invoice_number", "")
    invoice_date = entete_dict.get("invoice_date")
    sens_dict = get_sens(entete_dict.pop("sens"))

    # si l'on n'a pas de N° de Facture on en met un par défaut, avec la numérotation automatique
    # à aprtir du compteur des saisies manuelles
    if invoice_number == "":
        invoice_number = get_invoices_manual_entries_nums(entete_dict.get("third_party_num"))
        entete_dict["invoice_number"] = invoice_number

    try:
        # On récupère le dictionnaire des taux de TVA en fonction de la date de la facture
        vat_dict = get_dict_vat_rates(invoice_date)

        # On itère sur les lignes pour les valider
        lines_to_create, multistore_set, totals, errors_message = _validate_lines(
            category_form, entete_dict, lignes_list, vat_dict, sens_dict, user.uuid_identification
        )

        if errors_message is not None:
            # On trace l'erreur
            set_trace_hand_invoice(
                invoice_category=invoice_category,
                invoice_number=invoice_number,
                user=user,
                errors=True,
            )

            return True, errors_message

        # On crée les Factures dans edi_ediimport
        edi_imports = EdiImport.objects.bulk_create(
            [
                EdiImport(**row_dict)
                for row_dict in _rows_to_insert(
                    entete_dict, lines_to_create, third_party_num, totals, len(multistore_set) > 1
                )
            ]
        )
        nbre = len(edi_imports)

        # TODO: Renforcer la fonction pour que cela ne créé pas la ligne malgré
        #  même si erreur avec les deux fonction ci après

        # On va mettre à jour la centrale fille et l'enseigne
        set_signboard(edi_imports)

        # on va créer les traces et les changestrace
        set_trace_hand_invoice(
            invoice_category=invoice_category,
            invoice_number=invoice_number,
            user=user,
            edi_objects=edi_imports,
            numbers=nbre,
        )

        # On prépare le message
        message = (
            (
                f"La Facture N°{invoice_number}, "
                f"pour le Fournisseur {third_party_num}, a bien été crée"
            )
            if nbre == 1
            else (
                f"Les {nbre} lignes, de la Facture N°{invoice_number}, "
                f"pour le Fournisseur {third_party_num}, ont bien été crées"
            )
        )

    except Exception:
        LOGGER_IMPORT.exception("Erreur : set_hand_invoice")
        error = True
        message = "Une erreur c'est produite, veuillez consulter les logs"

        # On trace l'erreur
        set_trace_hand_invoice(
            invoice_category=invoice_category,
            invoice_number=invoice_number,
            user=user,
            errors=True,
        )

    return error, message
