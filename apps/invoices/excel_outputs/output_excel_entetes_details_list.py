# pylint: disable=W0702,W1203,E1101
"""Module d'export du fichier excel Dictionnaire Axe Pro/Regroupement de facturation

Commentaire:

created at: 2023-01-21
created by: Paulo ALVES

modified at: 2023-01-21
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
from apps.invoices.models import EnteteDetails

columns = [
    {
        "entete": "Classement",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{"align": "center"},
        },
        "width": 15,
    },
    {
        "entete": "Entête Details",
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
        "width": 35,
    },
]


def get_clean_rows():
    """Fonction qui renvoie les éléments pour le fichier Excel"""

    return [
        (
            str(row.ranking),
            str(row.column_name),
        )
        for row in EnteteDetails.objects.all()
    ]


def excel_liste_entetes_details(file_io: io.BytesIO, file_name: str) -> dict:
    """Fonction de génération du fichier Dictionnaire Entêtes de détails de facturation"""
    titre_list = file_name.split("_")
    titre = " ".join(titre_list[:-4])
    list_excel = [file_io, ["ENTETES DETAILS FAC"]]
    excel = GenericExcel(list_excel)

    try:
        titre_page_writer(excel, 1, 0, 0, columns, titre)
        output_day_writer(excel, 1, 1, 0)
        columns_headers_writer(excel, 1, 3, 0, columns)
        f_lignes = [dict_row.get("f_ligne") for dict_row in columns]
        f_lignes_odd = [
            {**dict_row.get("f_ligne"), **{"bg_color": "#D9D9D9"}} for dict_row in columns
        ]
        rows_writer(excel, 1, 4, 0, get_clean_rows(), f_lignes, f_lignes_odd)
        sheet_formatting(
            excel, 1, columns, {"sens": "landscape", "repeat_row": (0, 5), "fit_page": (1, 0)}
        )

    except:
        LOGGER_EXPORT_EXCEL.exception(f"{file_name!r}")
        return {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}

    finally:
        excel.excel_close()

    return {"OK": f"GENERATION DU FICHIER {file_name} TERMINEE AVEC SUCCES"}
