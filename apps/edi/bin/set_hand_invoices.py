# pylint: disable=E0401,E1101,C0303,R0914,R1735,R0915,R0912,R0913,W0150,W0718,W0212
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
    get_sens,
    set_trace_hand_invoice,
    set_signboard,
    set_hand_sales_prices,
)
from apps.edi.models import EdiImport
from apps.book.models import Society


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
    edi_imports = None

    # si l'on n'a pas de N° de Facture on en met un par défaut, avec la numérotation automatique
    # à aprtir du compteur des saisies manuelles
    if invoice_number == "":
        invoice_number = get_invoices_manual_entries_nums(entete_dict.get("third_party_num"))
        entete_dict["invoice_number"] = invoice_number

    try:
        # On récupère le dictionnaire des taux de TVA en fonction de la date de la facture
        vat_dict = get_dict_vat_rates(invoice_date)

        lines_to_create = []
        multistore_set = set()
        articles_pk_list = []
        message = ""
        cct_dict = {"cct_uuid_identification": None}
        invoice_amount_without_tax = Decimal("0")
        invoice_amount_tax = Decimal("0")
        invoice_amount_with_tax = Decimal("0")
        user_uuid_identification = user.uuid_identification

        # On itère sur les lignes pour les valider
        for line_dict in lignes_list:
            line_to_insert = dict()

            # Si la ligne n'a pas de cct alors on reprend celui de la ligne précédente
            if line_dict.get("cct_uuid_identification"):
                cct_uuid_identification = line_dict.get("cct_uuid_identification")
                cct_dict = {
                    "cct_uuid_identification": cct_uuid_identification,
                    "created_by": user_uuid_identification,
                    "saisie_by": user_uuid_identification,
                    "modified_by": user_uuid_identification,
                    "origin": 4,
                    "invoice_month": pendulum.parse(invoice_date.isoformat()).start_of("month"),
                    "invoice_year": invoice_date.year,
                    **sens_dict,
                }

            # on calcule les montants par ligne et additionne les montants pour le total facturé
            qty = Decimal(line_dict["qty"])

            # Si c'est un avoir (type 381) alors on change le sens
            if entete_dict.get("invoice_type") == "381":
                qty = -qty
                line_dict["qty"] = f"-{line_dict['qty']}"

            net_unit_price = Decimal(line_dict["net_unit_price"])
            vat = line_dict["vat"] or "001"
            vat_regime, vat_rate = vat_dict.get(vat)
            vat_rate = round(Decimal(vat_rate), 5)
            net_amount = round(qty * net_unit_price, 2)

            if line_dict.get("vat_amount") and line_dict.get("vat_amount", "0") != "0":
                vat_amount = (qty / abs(qty)) * Decimal(
                    line_dict.get("vat_amount").replace(",", ".")
                )
            else:
                vat_amount = round(net_amount * vat_rate, 2)

            if line_dict.get("amount_with_vat") and line_dict.get("amount_with_vat", "0") != "0":
                amount_with_vat = (qty / abs(qty)) * Decimal(
                    line_dict.get("amount_with_vat").replace(",", ".")
                )
            else:
                amount_with_vat = net_amount + vat_amount

            invoice_amount_without_tax += net_amount
            invoice_amount_tax += vat_amount
            invoice_amount_with_tax += amount_with_vat

            cct_dict.update(
                {
                    "gross_unit_price": net_unit_price,
                    "net_amount": net_amount,
                    "vat_rate": vat_rate,
                    "vat_amount": vat_amount,
                    "amount_with_vat": amount_with_vat,
                    "vat_regime": vat_regime,
                }
            )

            # On récupère les axes et catégories des articles dans la base article
            articles_dict = get_article(line_dict.get("reference_article"))
            # On va valider le formulaire
            form = category_form({**entete_dict, **line_dict, **cct_dict, **articles_dict})

            if form.is_valid():
                line_to_insert.update(form.cleaned_data)
                vat_regime, _ = vat_dict.get(vat)
                maison = form.cleaned_data.get("cct_uuid_identification")
                multistore_set.add(maison.cct)
                line_to_insert.update(
                    {
                        "code_fournisseur": maison.cct.cct,
                        "code_maison": maison.cct.cct,
                        "maison": maison.intitule,
                        "import_uuid_identification": uuid4(),
                    }
                )

                articles_pk_list.append(int(line_dict.get("reference_article", 0)))
                lines_to_create.append(line_to_insert)

            else:
                # S'il y a une erreur ont on génère le message
                for key, error_list in dict(form.errors).items():
                    message += (
                        f" - {key} : {', '.join(list(error_list))}"
                        if message
                        else f"{key} : {', '.join(list(error_list))}"
                    )

                # On trace l'erreur
                set_trace_hand_invoice(
                    invoice_category=invoice_category,
                    invoice_number=invoice_number,
                    user=user,
                    errors=True,
                )

                return True, message

        # On crée une liste de dictionnaire pour l'import en base
        edi_import_list = []
        uuid_identification = uuid4()
        society = Society.objects.get(third_party_num=third_party_num)

        for line_dict in lines_to_create:
            results_dict = dict()
            results_dict.update(entete_dict)
            results_dict.update(line_dict)

            # On ajoute les éléments manquants
            results_dict.update(
                {
                    "uuid_identification": uuid_identification,
                    "supplier": str(society.short_name)[:35],
                    "supplier_ident": third_party_num,
                    "supplier_name": str(society.name)[:80],
                    "valid": True,
                    "saisie": True,
                    "is_multi_store": len(multistore_set) > 1,
                    "manual_entry": True,
                    "invoice_amount_without_tax": invoice_amount_without_tax,
                    "invoice_amount_tax": invoice_amount_tax,
                    "invoice_amount_with_tax": invoice_amount_with_tax,
                }
            )

            edi_import_list.append(results_dict)

        # On crée les Factures dans edi_ediimport
        edi_imports = EdiImport.objects.bulk_create(
            [EdiImport(**row_dict) for row_dict in edi_import_list]
        )
        nbre = len(edi_imports)

        # TODO: Renforcer la fonction pour que cela ne créé pas la ligne malgré
        #  même si erreur avec les deux fonction ci après

        # On va mettre à jour la centrale fille et l'enseigne
        set_signboard(edi_imports)

        # On va mettre à jour les prix de ventes
        # TODO : A changer lors des multiprix
        set_hand_sales_prices(edi_imports)

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

    finally:
        return error, message
