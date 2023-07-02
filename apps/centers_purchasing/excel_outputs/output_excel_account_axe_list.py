# pylint: disable=W0702,W1203,E1101
"""Module d'export du fichier excel des Comptes par Centrale fille, Catégorie, Axe Pro, et TVA

Commentaire:

created at: 2023-01-21
created by: Paulo ALVES

modified at: 2023-01-21
modified by: Paulo ALVES
"""
import io
from typing import AnyStr, Dict

from heron.loggers import LOGGER_EXPORT_EXCEL
from apps.core.functions.functions_excel import GenericExcel
from apps.core.excel_outputs.excel_writer import (
    titre_page_writer,
    output_day_writer,
    columns_headers_writer,
    sheet_formatting,
    rows_writer,
    f_entetes,
    f_ligne,
)
from apps.centers_purchasing.models import AccountsAxeProCategory

columns = [
    {
        "entete": "Centrale\nFille",
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
        "entete": "Nom Centrale",
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
        "width": 20,
    },
    {
        "entete": "Rang\nCat.",
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
        "width": 6,
    },
    {
        "entete": "Catégorie",
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
        "width": 20,
    },
    {
        "entete": "Rang\nRub.",
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
        "width": 6,
    },
    {
        "entete": "Rubrique Presta",
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
        "width": 20,
    },
    {
        "entete": "Axe PRO",
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
        "entete": "Nom Axe PRO",
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
        "width": 20,
    },
    {
        "entete": "Plan\nTVA X3",
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
        "width": 7,
    },
    {
        "entete": "TVA X3",
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
        "width": 7,
    },
    {
        "entete": "Plan\nAchats",
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
        "width": 7,
    },
    {
        "entete": "Compte\nAchats",
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
        "entete": "Plan\nVentes",
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
        "width": 7,
    },
    {
        "entete": "Compte\nVentes",
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
]


def get_clean_rows(code_child_center):
    """
    Fonction qui renvoie les éléments pour le fichier Excel
    :param code_child_center: child_center manipulables par l'user
    :return:
    """

    queryset = AccountsAxeProCategory.objects.all()

    if code_child_center != "*":
        queryset = queryset.filter(child_center__in=code_child_center.split("|"))

    return [
        (
           dict_row.get("child_center__code", ""),
           dict_row.get("child_center__name", ""),
           str(dict_row.get("big_category__ranking", "")).zfill(2),
           dict_row.get("big_category__name", ""),
           str(dict_row.get("sub_category__ranking", "")).zfill(2).replace("None", ""),
           dict_row.get("sub_category__name", ""),
           dict_row.get("axe_pro__section", ""),
           dict_row.get("axe_pro__name", ""),
           dict_row.get("vat__vat_regime", ""),
           dict_row.get("vat__vat", ""),
           dict_row.get("purchase_account__code_plan_sage", ""),
           dict_row.get("purchase_account__account", ""),
           dict_row.get("sale_account__code_plan_sage", ""),
           dict_row.get("sale_account__account", ""),
        )
        for dict_row in queryset.values(
            "child_center__code",
            "child_center__name",
            "axe_pro__section",
            "axe_pro__name",
            "big_category__ranking",
            "big_category__name",
            "sub_category__ranking",
            "sub_category__name",
            "vat__vat",
            "vat__vat_regime",
            "purchase_account__code_plan_sage",
            "purchase_account__account",
            "sale_account__code_plan_sage",
            "sale_account__account",
        )
    ]


def excel_liste_account_axe(
    file_io: io.BytesIO, file_name: AnyStr, code_child_center: AnyStr
) -> Dict:
    """Fonction de génération du fichier
    des Comptes par Centrale fille, Catégorie, Axe Pro, et TVA
    """
    titre_list = file_name.split("_")
    titre = " ".join(titre_list[:-4])
    list_excel = [file_io, ["COMPTES CENTRALES"]]
    excel = GenericExcel(list_excel)

    try:
        titre_page_writer(excel, 1, 0, 0, columns, titre)
        output_day_writer(excel, 1, 1, 0)
        columns_headers_writer(excel, 1, 3, 0, columns)
        f_lignes = [dict_row.get("f_ligne") for dict_row in columns]
        f_lignes_odd = [
            {**dict_row.get("f_ligne"), **{"bg_color": "#D9D9D9"}} for dict_row in columns
        ]
        rows_writer(excel, 1, 4, 0, get_clean_rows(code_child_center), f_lignes, f_lignes_odd)
        sheet_formatting(
            excel, 1, columns, {"sens": "landscape", "repeat_row": (0, 5), "fit_page": (1, 0)}
        )

    except:
        LOGGER_EXPORT_EXCEL.exception(f"{file_name!r}")
        return {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}

    finally:
        excel.excel_close()

    return {"OK": f"GENERATION DU FICHIER {file_name} TERMINEE AVEC SUCCES"}
