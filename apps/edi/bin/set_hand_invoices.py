# pylint: disable=E0401,C0303,E1101,R0914,R1735,R0915,W0150,W0718
"""
FR : Module de traitement des factures saisies à la main
EN : New article processing module for in articles table with new_article = true

Commentaire:

created at: 2023-03-18
created by: Paulo ALVES

modified at: 2023-03-18
modified by: Paulo ALVES
"""
from typing import AnyStr, Dict
from decimal import Decimal
from uuid import uuid4

import pendulum
from django.db import transaction, connection

from heron.loggers import LOGGER_IMPORT
from apps.users.models import User
from apps.articles.bin.articles_queries import get_article
from apps.edi.bin.data_edi_invoices_nums import get_invoices_manual_entries_nums
from apps.edi.bin.edi_utilites import get_sens
from apps.edi.forms import CreateEdiImportInvoiceForm
from apps.edi.models import EdiImport


def check_invoice_exists(third_party_num: AnyStr, invoice_number: AnyStr, invoice_year: int):
    """Vérification des doublons de factures dans la saisie des factures manuelles
    Doublons causés par le trouple third_party_num, invoice_number, invoice_year
    :param third_party_num: Tiers X3
    :param invoice_number: N° de la facture
    :param invoice_year: Année de la facture
    :return: True/False
    """
    with connection.cursor() as cursor:
        sql_check_invoice_exist = """
        select
            "nbre" 
        from (
            (
                select 
                    1 as "nbre"
                from "edi_ediimport" "ee" 
                where "ee"."third_party_num" = %(third_party_num)s
                and "ee"."invoice_number" = %(invoice_number)s
                and "ee"."invoice_year" = %(invoice_year)s
                limit 1
            )
            union all
            (
                select 
                    1 as "nbre"
                from "invoices_invoice" "ii" 
                where "ii"."third_party_num"= %(third_party_num)s
                and "ii"."invoice_number" = %(invoice_number)s
                and "ii"."invoice_year" = %(invoice_year)s
                limit 1
            )
        ) "doublons"
        """
        cursor.execute(
            sql_check_invoice_exist,
            {
                "third_party_num": third_party_num,
                "invoice_number": invoice_number,
                "invoice_year": invoice_year,
            },
        )

        if cursor.fetchall():
            return True

        return False


def get_vat_rate(invoice_date: AnyStr):
    """
    Retourne le taux de TVA
    :param invoice_date: date de la facture au format isoformat
    :return: vat_rat dict
    """

    with connection.cursor() as cursor:
        sql_vat_rate = """
        select distinct
            "vtr"."vat", "vtr"."vat_regime", ("vtr"."rate" / 100)::numeric as "vat_rate"
        from "accountancy_vatratsage" "vtr"
        join (
            select
                max("vat_start_date") as "vat_start_date",
                "vat",
                "vat_regime"
            from "accountancy_vatratsage"
            where "vat_start_date" <= %(invoice_date)s
            group by "vat", "vat_regime"
        ) "vd"
        on "vtr"."vat" = "vd"."vat"
        and "vtr"."vat_start_date" = "vd"."vat_start_date"
        """
        cursor.execute(sql_vat_rate, {"invoice_date": invoice_date})

        return {row[0]: row[1:] for row in cursor.fetchall()}


@transaction.atomic
def set_hand_invoice(
    category_invoice: AnyStr, entete_dict: Dict, lignes_dict: Dict, user: User.objects
):
    """
    Création dans edi_import des factures saisies manuellement
    :param category_invoice: catégorie ( marchandises, formations, personnel)
    :param entete_dict: dictionnaire de l'entête de la facture
    :param lignes_dict: dictionnaire des lignes de la facture
    :param user: user qui créer la facture
    :return: error (True/False), message ("" si pas d'erreur/"message" si erreur)
    """

    error = False
    message = ""

    try:
        third_party_num = entete_dict.get("third_party_num")
        invoice_number = entete_dict.get("invoice_number", "")
        invoice_date = entete_dict.get("invoice_date")
        sens_dict = get_sens(entete_dict.pop("sens"))

        if invoice_number == "":
            invoice_number = get_invoices_manual_entries_nums(entete_dict.get("third_party_num"))
            entete_dict["invoice_number"] = invoice_number

        vat_dict = get_vat_rate(invoice_date)
        lines_to_create = []
        form_list = [row for row in lignes_dict if row.get("reference_article")]
        form_list = sorted(form_list, key=lambda line_sort_dict: line_sort_dict.get("num"))
        multistore_set = set()
        articles_pk_list = []
        message = ""
        cct_dict = {"cct_uuid_identification": None}
        invoice_amount_without_tax = Decimal("0")
        invoice_amount_tax = Decimal("0")
        invoice_amount_with_tax = Decimal("0")
        user_uuid_identification = user.uuid_identification

        # On itère sur les lignes pour les valider
        for line_dict in form_list:
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
            qty = Decimal(line_dict["qty"])
            net_unit_price = Decimal(line_dict["net_unit_price"])
            vat_regime, vat_rate = vat_dict.get(line_dict["vat"])
            vat_rate = round(Decimal(vat_rate), 5)
            net_amount = round(qty * net_unit_price)
            vat_amount = round(net_amount * vat_rate, 2)
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
            articles_dict = get_article(line_dict.get("reference_article"))

            form = CreateEdiImportInvoiceForm(
                {**entete_dict, **line_dict, **cct_dict, **articles_dict}
            )

            if form.is_valid():
                line_to_insert.update(form.cleaned_data)
                vat_regime, _ = vat_dict.get(line_dict.get("vat"))
                maison = form.cleaned_data.get("cct_uuid_identification")
                multistore_set.add(maison.cct)
                line_to_insert.update(
                    {
                        "code_fournisseur": maison.cct.cct,
                        "code_maison": maison.cct.cct,
                        "maison": maison.intitule,
                    }
                )

                articles_pk_list.append(int(line_dict.get("reference_article", 0)))
                lines_to_create.append(line_to_insert)

            else:
                print(form.errors)
                for error_list in dict(form.errors).values():
                    message += (
                        f", {', '.join(list(error_list))}"
                        if message
                        else ", ".join(list(error_list))
                    )

                    return True, message

        edi_import_list = []
        uuid_identification = uuid4()

        # On créera une liste de dictionnaire pour l'import en base
        for line_dict in lines_to_create:
            results_dict = dict()
            results_dict.update(entete_dict)
            results_dict.update(line_dict)

            results_dict.update(
                {
                    "uuid_identification": uuid_identification,
                    "supplier": third_party_num,
                    "supplier_ident": third_party_num,
                    "supplier_name": third_party_num,
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

        edi_import = EdiImport.objects.bulk_create(
            [EdiImport(**row_dict) for row_dict in edi_import_list]
        )

        nbre = len(edi_import)
        error = False
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
        return error, message

    except Exception:
        LOGGER_IMPORT.exception("Erreur : set_hand_invoice")
        error = True
        message = "Une erreur c'est produite, veuillez consulter les logs"

    finally:
        return error, message
