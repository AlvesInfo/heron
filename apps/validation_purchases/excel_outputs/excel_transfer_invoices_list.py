# pylint: disable=W0702,W1203
"""Module d'export du fichier excel pour les factures du tiers pas mois

Commentaire:

created at: 2022-05-12
created by: Paulo ALVES

modified at: 2022-05-12
modified by: Paulo ALVES
"""
import io
from typing import Dict
from pathlib import Path

import pendulum
from django.db import connection
from heron.settings.base import APPS_DIR
from heron.loggers import LOGGER_EXPORT_EXCEL
from apps.core.functions.functions_excel import GenericExcel
from apps.core.excel_outputs.excel_writer import (
    f_entetes,
    f_ligne,
    titre_page_writer,
    output_day_writer,
    columns_headers_writer,
    sheet_formatting,
    rows_writer,
)

COLUMNS = [
    {
        "entete": "Tiers X3",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "center",
            },
        },
        "width": 8,
    },
    {
        "entete": "Fournisseur",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "left",
            },
        },
        "width": 40,
    },
    {
        "entete": "CCT\nSage X3",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "center",
            },
        },
        "width": 8,
    },
    {
        "entete": "Référence\nCosium",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "center",
            },
        },
        "width": 15,
    },
    {
        "entete": "Maison",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "left",
            },
        },
        "width": 31,
    },
    {
        "entete": "Type\nPièce",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "center",
            },
        },
        "width": 10,
    },
    {
        "entete": "N° Facture",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "center",
            },
        },
        "width": 15,
    },
    {
        "entete": "Date\nfactue",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{"align": "center", "num_format": "dd/mm/yyyy"},
        },
        "width": 10,
    },
    {
        "entete": "Net\nHT",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "right",
                "num_format": "#,##0.00",
            },
        },
        "width": 10.6,
    },
    {
        "entete": "Mois des\nFactues",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{"align": "center", "num_format": "mmmm yyyy"},
        },
        "width": 13,
    },
]


def get_rows(parmas_dict: Dict = None):
    """Renvoie les résultats de la requête nécessaire à l'export excel
    :param parmas_dict: paramètre de la requête
    :return: resultats de la requête
    """
    parmas_dict = parmas_dict or {}

    with connection.cursor() as cursor:
        query = """
        select 
            ee.third_party_num, 
            bs."name", 
            ccm.cct, 
            hbm.reference_cosium, 
            ccm.intitule, 
            case 
                when ee.invoice_type = '380' 
                then 'FAF'
                else 'AVO'
            end as type_piece,
            ee.invoice_number, 
            invoice_date, 
            sum(net_amount) as montant, 
            invoice_month 
        from edi_ediimport ee
        left join centers_clients_maison ccm 
        on ee.cct_uuid_identification = ccm.uuid_identification 
        left join heron_bi_maisons hbm 
        on ccm.code_maison = hbm.code_maison 
        left join book_society bs 
        on ee.third_party_num = bs.third_party_num 
        where ee.third_party_num = %(third_party_num)s
          and supplier = %(supplier)s
          and date_trunc('month', invoice_date)::date = %(invoice_month)s
          and (ee."delete" = false or ee."delete" isnull)
          and ee."valid" = true
        group by ee.third_party_num, 
            bs."name", 
            ccm.cct, 
            ccm.intitule, 
            hbm.reference_cosium, 
            ee.invoice_number, 
            invoice_date, 
            invoice_month,
            ee.invoice_type
        order by hbm.reference_cosium, 
            invoice_date 
        """
        # print(cursor.mogrify(query, parmas_dict).decode())
        # print(query)
        cursor.execute(query, parmas_dict)
        return cursor.fetchall()


def excel_transfers_cosium(file_io: io.BytesIO, file_name: str, attr_dict: dict) -> dict:
    """Fonction de génération du fichier de liste des Tiers, Fournisseurs, Clients"""
    third_party_num = attr_dict.get("third_party_num")
    supplier = attr_dict.get("supplier")
    invoice_month = attr_dict.get("invoice_month")
    month = pendulum.parse(invoice_month).format("MMMM YYYY", locale="fr")
    titre = f"Factures : {third_party_num} - {supplier} - pour {month}"

    list_excel = [file_io, [f"{third_party_num}_{month}"]]
    excel = GenericExcel(list_excel)
    get_clean_rows = [line[:len(COLUMNS)] for line in get_rows(attr_dict)]

    try:
        titre_page_writer(excel, 1, 0, 0, COLUMNS, titre)
        output_day_writer(excel, 1, 1, 0)
        columns_headers_writer(excel, 1, 3, 0, COLUMNS)
        f_lignes = [dict_row.get("f_ligne") for dict_row in COLUMNS]
        f_lignes_odd = [
            {**dict_row.get("f_ligne"), **{"bg_color": "#D9D9D9"}} for dict_row in COLUMNS
        ]
        rows_writer(excel, 1, 4, 0, get_clean_rows, f_lignes, f_lignes_odd)
        sheet_formatting(
            excel, 1, COLUMNS, {"sens": "portrait", "repeat_row": (0, 5), "fit_page": (1, 0)}
        )

    except:
        LOGGER_EXPORT_EXCEL.exception(f"{file_name!r}")
        return {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}

    finally:
        excel.excel_close()

    return {"OK": f"GENERATION DU FICHIER {file_name} TERMINEE AVEC SUCCES"}
