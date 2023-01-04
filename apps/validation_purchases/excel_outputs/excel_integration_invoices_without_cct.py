# pylint: disable=E0401,W0702,W1203
"""Module d'export du fichier excel pour les facturs founisseurs intégrées sans CCT

Commentaire:

created at: 2022-05-12
created by: Paulo ALVES

modified at: 2022-05-12
modified by: Paulo ALVES
"""
import io

from django.db.models import Count

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
from apps.edi.models import EdiImport

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
        "width": 12,
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
        },
        "width": 18,
    },
    {
        "entete": "Mois facture",
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
    {
        "entete": "Code Fournisseur",
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
        "width": 24,
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
                "text_wrap": True,
            },
        },
        "width": 75,
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
        "width": 14,
    },
    {
        "entete": "Date Facture",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{"align": "center", "num_format": "dd/mm/yy"},
        },
        "width": 12,
    },
    {
        "entete": "Montant\nHT",
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
        "width": 11,
    },
    {
        "entete": "Montant\nTTC",
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
        "width": 11,
    },
]


def get_rows():
    """Renvoie les résultats de la requête nécessaire à l'export excel
    :return: resultats de la requête
    """
    rows_without_cct = (
        EdiImport.objects.filter(cct_uuid_identification__isnull=True, invoice_for=0)
        .exclude(delete=True)
        .values(
            "third_party_num",
            "supplier",
            "invoice_month",
            "code_maison",
            "maison",
            "invoice_number",
            "invoice_date",
            "invoice_amount_without_tax",
            "invoice_amount_with_tax",
        )
        .annotate(dcount=Count("third_party_num"))
        .order_by("third_party_num", "invoice_number")
    )

    return [
        (
            row.get("third_party_num"),
            row.get("supplier"),
            row.get("invoice_month"),
            row.get("code_maison"),
            row.get("maison"),
            row.get("invoice_number"),
            row.get("invoice_date"),
            row.get("invoice_amount_without_tax"),
            row.get("invoice_amount_with_tax"),
        )
        for row in rows_without_cct
    ]


def excel_integration_without_cct(file_io: io.BytesIO, file_name: str) -> dict:
    """Fonction de génération du fichier Excel de la liste des factures intégrées sans CCT"""
    titre_list = file_name.split("_")
    titre = " ".join(titre_list[:-3])
    list_excel = [file_io, [titre]]
    excel = GenericExcel(list_excel)
    get_clean_rows = get_rows()

    try:
        titre_page_writer(excel, 1, 0, 0, COLUMNS, titre)
        output_day_writer(excel, 1, 1, 0)
        columns_headers_writer(excel, 1, 3, 0, COLUMNS)
        f_lignes = [dict_row.get("f_ligne") for dict_row in COLUMNS]
        f_lignes_odd = [
            {**dict_row.get("f_ligne"), **{"bg_color": "#D9D9D9"}}
            for i, dict_row in enumerate(COLUMNS)
        ]
        rows_writer(excel, 1, 4, 0, get_clean_rows, f_lignes, f_lignes_odd)
        sheet_formatting(
            excel, 1, COLUMNS, {"sens": "landscape", "repeat_row": (0, 5), "fit_page": (1, 0)}
        )

    except:
        LOGGER_EXPORT_EXCEL.exception(f"{file_name!r}")
        return {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}

    finally:
        excel.excel_close()

    return {"OK": f"GENERATION DU FICHIER {file_name} TERMINEE AVEC SUCCES"}
