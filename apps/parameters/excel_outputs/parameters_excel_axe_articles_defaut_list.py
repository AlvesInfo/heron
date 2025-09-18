# pylint: disable=W0702,W1203,E1101
"""Module d'export du fichier excel pour sortie la liste des axes et catégories par défaut

Commentaire:

created at: 2023-01-19
created by: Paulo ALVES

modified at: 2023-01-19
modified by: Paulo ALVES
"""

import io

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
from apps.parameters.models import DefaultAxeArticle

columns_list = [
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
        "width": 30,
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
        "width": 15,
    },
    {
        "entete": "Axe BU",
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
        "entete": "Axe PRJ",
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
        "entete": "Axe PYS",
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
        "entete": "Axe RFA",
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
]


def get_row():
    """Fonction qui renvoie les bonnes colonnes pour le fichier Excel"""

    yield from [
        (
            row.big_category.__str__().replace("None", ""),
            row.sub_category.__str__().replace("None", ""),
            row.axe_bu.__str__().replace("None", ""),
            row.axe_prj.__str__().replace("None", ""),
            row.axe_pys.__str__().replace("None", ""),
            row.axe_rfa.__str__().replace("None", ""),
        )
        for row in DefaultAxeArticle.objects.filter(slug_name="axes_articles").order_by("id")
    ]


def excel_list_axe_article_defaut(file_io: io.BytesIO, file_name: str) -> dict:
    """Fonction de génération du fichier de liste des axes et catégories par défaut"""
    titre_list = file_name.split("_")
    titre = " ".join(titre_list[:-4])
    list_excel = [file_io, [titre[:30]]]
    excel = GenericExcel(list_excel)

    try:
        titre_page_writer(excel, 1, 0, 0, columns_list, titre)
        output_day_writer(excel, 1, 1, 0)
        columns_headers_writer(excel, 1, 3, 0, columns_list)
        f_lignes = [dict_row.get("f_ligne") for dict_row in columns_list]
        f_lignes_odd = [
            {**dict_row.get("f_ligne"), **{"bg_color": "#D9D9D9"}} for dict_row in columns_list
        ]
        rows_writer(excel, 1, 4, 0, get_row(), f_lignes, f_lignes_odd)
        sheet_formatting(
            excel, 1, columns_list, {"sens": "landscapa", "repeat_row": (0, 5), "fit_page": (1, 0)}
        )

    except:
        LOGGER_EXPORT_EXCEL.exception(f"{file_name!r}")
        return {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}

    finally:
        excel.excel_close()
    print("fin excel")
    return {"OK": f"GENERATION DU FICHIER {file_name} TERMINEE AVEC SUCCES"}
