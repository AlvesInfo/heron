# pylint: disable=E0401,W0702,W1203
"""Module d'export du fichier excel du Contrôle des Abonnements

Commentaire:

created at: 2023-07-03
created by: Paulo ALVES

modified at: 2023-07-03
modified by: Paulo ALVES
"""
import io
from typing import Dict, List, Generator

import pendulum
from django.db import connection
from heron.loggers import LOGGER_EXPORT_EXCEL
from apps.core.functions.functions_excel import GenericExcel
from apps.core.excel_outputs.excel_writer import (
    f_entetes,
    f_ligne,
    titre_page_writer,
    output_day_writer,
    columns_headers_writer,
    sheet_formatting,
)

COLUMNS = [
    {
        "entete": "CCT X3",
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
        "width": 51,
    },
    {
        "entete": "Enseigne",
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
        "width": 15,
    },
    {
        "entete": "Date\nfermeture",
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
                "num_format": "dd/mm/yy",
            },
        },
        "width": 10,
    },
    {
        "entete": "M-11",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "num_format": "#,##0.00",
            },
        },
        "width": 10,
    },
    {
        "entete": "M-10",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "num_format": "#,##0.00",
            },
        },
        "width": 10,
    },
    {
        "entete": "M-9",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "num_format": "#,##0.00",
            },
        },
        "width": 10,
    },
    {
        "entete": "M-8",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "num_format": "#,##0.00",
            },
        },
        "width": 10,
    },
    {
        "entete": "M-7",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "num_format": "#,##0.00",
            },
        },
        "width": 10,
    },
    {
        "entete": "M-6",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "num_format": "#,##0.00",
            },
        },
        "width": 10,
    },
    {
        "entete": "M-5",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "num_format": "#,##0.00",
            },
        },
        "width": 10,
    },
    {
        "entete": "M-4",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "num_format": "#,##0.00",
            },
        },
        "width": 10,
    },
    {
        "entete": "M-3",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "num_format": "#,##0.00",
            },
        },
        "width": 10,
    },
    {
        "entete": "M-2",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "num_format": "#,##0.00",
            },
        },
        "width": 10,
    },
    {
        "entete": "M-1",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "num_format": "#,##0.00",
            },
        },
        "width": 10,
    },
    {
        "entete": "M",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "num_format": "#,##0.00",
            },
        },
        "width": 10,
    },
    {
        "entete": "Total des 6\nderniers mois",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "num_format": "#,##0.00",
            },
        },
        "width": 14,
    },
    {
        "entete": "Commentaires",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{},
        },
        "width": 50,
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
        with "maisons" as (
            select 
                "cct",
                "intitule",
                "closing_date",
                "uuid_identification",
                "sb"."name" as "signboard"
            from "centers_clients_maison" "cm"
            join "centers_purchasing_signboard" "sb"
            on "cm"."sign_board" = "sb"."code"
        ),
        "edi_details" as (
            select 
                (
                    "ee"."third_party_num" 
                    || ' - ' || 
                    "ee"."flow_name" 
                    || ' - ' || 
                    "ee"."reference_article"
                ) as "tiers",
                "cc"."cct" || ' - ' || "cc"."intitule" as "cct_name",
                "cc"."signboard",
                "cc"."closing_date",
                "ee"."net_amount" as "M_00",
                0 as "M_01",
                0 as "M_02",
                0 as "M_03",
                0 as "M_04",
                0 as "M_05",
                0 as "M_06",
                0 as "M_07",
                0 as "M_08",
                0 as "M_09",
                0 as "M_10",
                0 as "M_11"
            from "maisons" "cc"
            join "edi_ediimport" "ee"
            on "ee"."cct_uuid_identification" = "cc"."uuid_identification"
            where "ee"."sale_invoice"
            and "ee"."net_amount" <> 0
            and "ee"."flow_name" in  (
                select 
                    "function"
                from "centers_clients_maisonsubcription" "cs"
                group by "function"
            )
        ),
        "invoices_details" as (
            select 
                (
                    "ic"."third_party_num" 
                    || ' - ' || 
                    "ic"."flow_name" 
                    || ' - ' || 
                    "ic"."reference_article"
                )as "tiers",
                "cc"."cct" || ' - ' || "cc"."intitule" as "cct_name",
                "cc"."signboard",
                "cc"."closing_date",
                0 as "M_00",
                case
                    when (
                        "si"."invoice_month"
                        =
                        (date_trunc('month', now()) - interval '2 month')::date
                    )
                    then "iv"."net_amount" 
                    else 0
                end as "M_01",
                case
                    when (
                        "si"."invoice_month"
                        =
                        (date_trunc('month', now()) - interval '3 month')::date
                    )
                    then "iv"."net_amount" 
                    else 0
                end as "M_02",
                case
                    when (
                        "si"."invoice_month"
                        =
                        (date_trunc('month', now()) - interval '4 month')::date
                    )
                    then "iv"."net_amount" 
                    else 0
                end as "M_03",
                case
                    when (
                        "si"."invoice_month"
                        =
                        (date_trunc('month', now()) - interval '5 month')::date
                    )
                    then "iv"."net_amount" 
                    else 0
                end as "M_04",
                case
                    when (
                        "si"."invoice_month"
                        =
                        (date_trunc('month', now()) - interval '6 month')::date
                    )
                    then "iv"."net_amount" 
                    else 0
                end as "M_05",
                case
                    when (
                        "si"."invoice_month"
                        =
                        (date_trunc('month', now()) - interval '7 month')::date
                    )
                    then "iv"."net_amount" 
                    else 0
                end as "M_06",
                case
                    when (
                        "si"."invoice_month"
                        =
                        (date_trunc('month', now()) - interval '8 month')::date
                    )
                    then "iv"."net_amount" 
                    else 0
                end as "M_07",
                case
                    when (
                        "si"."invoice_month"
                        =
                        (date_trunc('month', now()) - interval '9 month')::date
                    )
                    then "iv"."net_amount" 
                    else 0
                end as "M_08",
                case
                    when (
                        "si"."invoice_month"
                        =
                        (date_trunc('month', now()) - interval '10 month')::date
                    )
                    then "iv"."net_amount" 
                    else 0
                end as "M_09",
                case
                    when (
                        "si"."invoice_month"
                        =
                        (date_trunc('month', now()) - interval '11 month')::date
                    )
                    then "iv"."net_amount" 
                    else 0
                end as "M_10",
                case
                    when (
                        "si"."invoice_month"
                        =
                        (date_trunc('month', now()) - interval '12 month')::date
                    )
                    then "iv"."net_amount" 
                    else 0
                end as "M_11"
            from "book_society" "bs" 
            join "invoices_invoicecommondetails" "ic" 
            on "bs"."third_party_num" = "ic"."third_party_num"
            join "invoices_saleinvoicedetail" "iv" 
            on "iv"."import_uuid_identification" = "ic"."import_uuid_identification" 
            join "invoices_saleinvoice" "si"
            on "iv"."uuid_invoice" = "si"."uuid_identification"
            join "maisons" "cc"
            on "si"."cct" = "cc"."cct" 
            where (
                "si"."invoice_month" 
                > 
                (
                    date_trunc('month', now()) - interval '13 month' + interval '1 month - 1 day'
                )::date
            )            
            and "ic"."flow_name" in  (
                select 
                    "function"
                from "centers_clients_maisonsubcription" "cs"
                group by "function"
            )
            and "iv"."net_amount" <> 0
            and "si"."final"
        ), 
        "alls" as (
            select 
                "tiers", "cct_name", "signboard", 
                coalesce("closing_date"::varchar, '') as "closing_date",
                "M_00", "M_01", "M_02", "M_03", "M_04", "M_05", 
                "M_06", "M_07", "M_08", "M_09", "M_10", "M_11", 
                ("M_00" + "M_01" + "M_02" + "M_03" + "M_04" + "M_05")::numeric as "M6_MONTH"
            from "edi_details"
            union all
            select 
                "tiers", "cct_name", "signboard", 
                coalesce("closing_date"::varchar, '') as "closing_date",
                "M_00", "M_01", "M_02", "M_03", "M_04", "M_05", 
                "M_06", "M_07", "M_08", "M_09", "M_10", "M_11", 
                ("M_00" + "M_01" + "M_02" + "M_03" + "M_04" + "M_05")::numeric as "M6_MONTH"
            from "invoices_details"
        ),
        "group_alls" as (
            select 
                "tiers",
                "cct_name", 
                "closing_date",
                sum("M_11") as "M_11",
                sum("M_10") as "M_10",
                sum("M_09") as "M_09",
                sum("M_08") as "M_08",
                sum("M_07") as "M_07",
                sum("M_06") as "M_06",
                sum("M_05") as "M_05",
                sum("M_04") as "M_04",
                sum("M_03") as "M_03",
                sum("M_02") as "M_02",
                sum("M_01") as "M_01",
                sum("M_00") as "M_00",
                SUM("M_00" + "M_01" + "M_02" + "M_03" + "M_04" + "M_05")::numeric as "M6_MONTH",
                '' as "comment"
            from "alls" 
            group by "tiers", 
                     "cct_name",
                     "closing_date"
        ),
        "maisons_alls" as (
            select 
                "tiers",
                "cct" || ' - ' || "intitule" as "cct_name",
                "signboard",
                coalesce("closing_date"::varchar, '') as "closing_date"
            from "maisons" , (
                select 
                    "tiers"
                from "group_alls"
                group by "tiers"
            ) "rr"
        )
        select 
            "ma"."tiers", "ma"."cct_name", "ma"."signboard", "ma"."closing_date", 
            "M_11", "M_10", "M_09", "M_08", "M_07", "M_06", "M_05", 
            "M_04", "M_03", "M_02", "M_01", "M_00", "M6_MONTH", "comment"
        from "maisons_alls" "ma"
        left join "group_alls" "ga"
         on "ma"."tiers" = "ga"."tiers"
        and "ma"."cct_name" = "ga"."cct_name"
        order by "ma"."tiers", 
                 "ma"."cct_name" 
        """
        # print(cursor.mogrify(query, parmas_dict).decode())
        # print(query)
        cursor.execute(query, parmas_dict)
        return cursor.fetchall()


def write_rows(excel: GenericExcel, f_lignes: List, f_lignes_odd: List, get_clean_rows: Generator):
    """Ecritures de lignes d'entete des Fournisseurs"""
    row = 2
    row_format = 1
    col = 0
    current_subcription = ""
    page_breaks = []

    format_client = {
        "font_name": "calibri",
        "bg_color": "#dce7f5",
        "top": 2,
        "bottom": 1,
        "left": 2,
        "right": 2,
        "bold": True,
        "text_wrap": True,
        "align": "left",
        "valign": "vcenter",
    }

    for rows in get_clean_rows:
        subcription, *line = rows
        line = [value or "" for value in line]
        closing_date = line[2]
        mois = line[14]

        if closing_date:
            line[2] = pendulum.parse(closing_date).date()

        if closing_date and mois:
            f_lignes[2]["bg_color"] = "red"
            f_lignes_odd[2]["bg_color"] = "red"
            f_lignes[14]["bg_color"] = "red"
            f_lignes_odd[14]["bg_color"] = "red"
        else:
            f_lignes[2]["bg_color"] = "white"
            f_lignes_odd[2]["bg_color"] = "#D9D9D9"
            f_lignes[14]["bg_color"] = "white"
            f_lignes_odd[14]["bg_color"] = "#D9D9D9"

        if current_subcription != subcription:
            if row > 4:
                row += 1
                page_breaks.append(row)
            else:
                row += 1

            excel.write_row(1, row, col, subcription, format_client)
            row += 1
            columns_headers_writer(excel, 1, row, 0, COLUMNS)
            current_subcription = subcription
            row += 1
            row_format = 1

        excel.write_rows(1, row, col, line, f_lignes if row_format % 2 == 0 else f_lignes_odd)
        row += 1
        row_format += 1

    return page_breaks


def excel_subscriptions(file_io: io.BytesIO, file_name: str) -> dict:
    """Fonction de génération du fichier du Contrôle des Abonnements"""
    titre = "3.5 - Contrôle des Abonnements"
    list_excel = [file_io, ["ABONNEMENTS"]]
    excel = GenericExcel(list_excel)

    try:
        mois = 12

        for i, column_dict in enumerate(COLUMNS, 1):
            if 3 < i < 16:
                column_dict["entete"] = (
                    (
                        pendulum.now()
                        .subtract(months=mois)
                        .start_of("month")
                        .format("MMMM YYYY", locale="fr")
                    )
                    .capitalize()
                    .replace(" ", "\n")
                )
                mois -= 1

        titre_page_writer(excel, 1, 0, 0, COLUMNS, titre)
        output_day_writer(excel, 1, 1, 0)
        f_lignes = [dict_row.get("f_ligne") for dict_row in COLUMNS]
        f_lignes_odd = [
            {**dict_row.get("f_ligne"), **{"bg_color": "#D9D9D9"}} for dict_row in COLUMNS
        ]
        page_breaks = write_rows(excel, f_lignes, f_lignes_odd, get_rows())
        excel.excel_sheet(1).set_h_pagebreaks(page_breaks)
        excel.excel_sheet(1).set_footer("&R&P/&N", {"margin": 0.1})
        sheet_formatting(
            excel, 1, COLUMNS, {"sens": "landscape", "repeat_row": (0, 2), "fit_page": (1, 0)}
        )

    except:
        LOGGER_EXPORT_EXCEL.exception(f"{file_name!r}")
        return {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}

    finally:
        excel.excel_close()

    return {"OK": f"GENERATION DU FICHIER {file_name} TERMINEE AVEC SUCCES"}
