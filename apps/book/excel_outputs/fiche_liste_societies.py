import io

from apps.core.functions.functions_excel import GenericExcel
from apps.book.loggers import EXPORT_EXCEL_LOGGER

from apps.core.excel_outputs.excel_writer import (
    f_entetes,
    f_ligne,
    titre_page_writer,
    output_day_writer,
    columns_headers_writer,
    sheet_formatting,
    rows_writer,
)
from apps.book.models import Society

columns_list = [
    {
        "entete": "N° Tiers",
        "f_entete": f_entetes,
        "f_ligne": {
            **f_ligne,
            **{
                "align": "center",
            },
        },
        "width": 14,
    },
    {
        "entete": "Nature",
        "f_entete": f_entetes,
        "f_ligne": {**f_ligne, **{"align": "center", "num_format": "dd/mm/yy"}},
        "width": 10,
    },
    {
        "entete": "Tiers",
        "f_entete": f_entetes,
        "f_ligne": {**f_ligne, **{"text_wrap": True}},
        "width": 35,
    },
]


def get_clean_rows(societies: Society.objects) -> iter:
    """Renvoie les lignes du query_set avec les colonnes souhaitées et cleannées"""
    return (
        (
            society.third_party_num,
            society.nature,
            society.name,
        )
        for society in societies
    )


def excel_liste_societies(file_io: io.BytesIO, file_name: str, societies: Society.objects) -> dict:
    """Fonction de génération du fichier de liste des Banques"""
    list_excel = [file_io, ["LISTE DES FOURNISSEURS"]]
    excel = GenericExcel(list_excel)
    try:
        titre_list = file_name.split("_")
        titre_page_writer(excel, 1, 0, 0, columns_list, " ".join(titre_list[:3]))
        output_day_writer(excel, 1, 1, 0)
        columns_headers_writer(excel, 1, 3, 0, columns_list)
        f_lignes = [dict_row.get("f_ligne") for dict_row in columns_list]
        f_lignes_odd = [
            {**dict_row.get("f_ligne"), **{"bg_color": "#EBF1DE"}} for dict_row in columns_list
        ]
        rows_writer(excel, 1, 4, 0, get_clean_rows(societies), f_lignes, f_lignes_odd)
        sheet_formatting(
            excel, 1, columns_list, {"sens": "landscape", "repeat_row": (0, 5), "fit_page": (1, 0)}
        )

    except:
        EXPORT_EXCEL_LOGGER.exception(f"{file_name!r}")
        return {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}

    finally:
        excel.excel_close()

    return {"OK": f"GENERATION DU FICHIER {file_name} TERMINEE AVEC SUCCES"}
