# pylint: disable=W0702,W1203,E1101
"""Module d'export du fichier excel pour les exclusion des rfa des enseignes

Commentaire:

created at: 2024-08-09
created by: Paulo ALVES

modified at: 2024-08-09
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
from apps.rfa.models import SignboardExclusion


columns_list = [
    {
        "entete": "Enseigne",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#DCE7F5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "center",
            },
        },
        "width": 11,
    },
    {
        "entete": "Intitulé",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#DCE7F5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "center",
            },
        },
        "width": 25,
    },
]


def get_row():
    """Class qui renvoie les bonnes colonnes pour le fichier Excel"""

    yield from [
        (
            row.get("signboard__code"),
            row.get("signboard__name"),
        )
        for row in SignboardExclusion.objects.all()
        .order_by("signboard__code")
        .values(
            "signboard__code",
            "signboard__name",
        )
        .order_by("signboard__code")
    ]


def excel_list_rfa_signboards_exclusion(file_io: io.BytesIO, file_name: str) -> dict:
    """Fonction de génération du fichier de liste des Enseignes à exclure des RFA"""
    titre_list = file_name.split("_")
    titre = " ".join(titre_list[:-4])
    list_excel = [file_io, [titre[:30]]]
    excel = GenericExcel(list_excel)
    columns = columns_list

    try:
        titre_page_writer(excel, 1, 0, 0, columns, titre)
        output_day_writer(excel, 1, 1, 0)
        columns_headers_writer(excel, 1, 4, 0, columns)
        f_lignes = [dict_row.get("f_ligne") for dict_row in columns]
        f_lignes_odd = [
            {**dict_row.get("f_ligne"), **{"bg_color": "#F2F2F2"}} for dict_row in columns
        ]
        rows_writer(excel, 1, 5, 0, get_row(), f_lignes_odd, f_lignes)
        sheet_formatting(
            excel, 1, columns, {"sens": "portrait", "repeat_row": (0, 5), "fit_page": (1, 0)}
        )

    except:
        LOGGER_EXPORT_EXCEL.exception(f"{file_name!r}")
        return {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}

    finally:
        excel.excel_close()

    return {"OK": f"GENERATION DU FICHIER {file_name} TERMINEE AVEC SUCCES"}
