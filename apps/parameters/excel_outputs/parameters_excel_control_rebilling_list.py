""""Module d'export du fichier excel pour les Contrôles de Refacturation

Commentaire:

created at: 2026-02-16
created by: Paulo ALVES

modified at: 2026-02-16
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
from apps.parameters.models import ControlRebilling


columns_list_control_rebilling = [
    {
        "entete": "Contrôle",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#CCC0DA",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "left",
            },
        },
        "width": 20,
    },
    {
        "entete": "Commentaire",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#CCC0DA",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "left",
            },
        },
        "width": 80,
    },
]


def get_row():
    """Class qui renvoie les bonnes colonnes pour le fichier Excel"""

    yield from [
        (
            row.name,
            row.comment or "",
        )
        for row in ControlRebilling.objects.all()
    ]


def excel_liste_control_rebilling(file_io: io.BytesIO, file_name: str) -> dict:
    """Fonction de génération du fichier de liste des Controles de Refacturation"""
    titre_list = file_name.split("_")
    titre = " ".join(titre_list[:-4])
    list_excel = [file_io, [titre[:30]]]
    excel = GenericExcel(list_excel)
    columns = columns_list_control_rebilling

    try:
        titre_page_writer(excel, 1, 0, 0, columns, titre)
        output_day_writer(excel, 1, 1, 0)
        columns_headers_writer(excel, 1, 4, 0, columns)
        f_lignes = [dict_row.get("f_ligne") for dict_row in columns]
        f_lignes_odd = [
            {**dict_row.get("f_ligne"), **{"bg_color": "#D9D9D9"}} for dict_row in columns
        ]
        rows_writer(excel, 1, 5, 0, get_row(), f_lignes, f_lignes_odd)
        sheet_formatting(
            excel, 1, columns, {"sens": "portrait", "repeat_row": (0, 5), "fit_page": (1, 0)}
        )

    except Exception as error:
        LOGGER_EXPORT_EXCEL.exception(f"{file_name!r} : {error!r}")
        return {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}

    finally:
        excel.excel_close()

    return {"OK": f"GENERATION DU FICHIER {file_name} TERMINEE AVEC SUCCES"}
