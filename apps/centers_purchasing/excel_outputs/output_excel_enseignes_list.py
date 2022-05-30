# pylint: disable=W0702,W1203,R0903,W1309
"""Module d'export du fichier excel pour les centrales Mères

Commentaire:

created at: 2022-05-12
created by: Paulo ALVES

modified at: 2022-05-12
modified by: Paulo ALVES
"""

import io

from heron.loggers import LOGGER_EXPORT_EXCEL
from apps.core.functions.functions_excel import GenericExcel
from apps.core.functions.functions_setups import CNX_STRING
from apps.core.functions.functions_postgresql import cnx_postgresql
from apps.core.excel_outputs.excel_writer import (
    titre_page_writer,
    output_day_writer,
    columns_headers_writer,
    sheet_formatting,
    rows_writer,
)
from apps.centers_purchasing.models import Signboard
from apps.centers_purchasing.excel_outputs.output_excel_enseignes_columns import (
    columns_list_enseignes,
)


class GetRows:
    """Class qui renvoie les bonnes colonnes pour le fichier Excel"""

    def __init__(self, meres: Signboard.objects):
        self.meres = meres

        self.query = f"""
        select
            "code", 
            "name", 
            "generic_coefficient", 
            "comment"
        from {self.meres._meta.db_table}
        """

    def get_clean_rows(self) -> iter:
        """Retourne les lignes à écrire"""
        with cnx_postgresql(CNX_STRING).cursor() as cursor:
            cursor.execute(self.query)
            return cursor.fetchall()


def excel_enseignes_list(file_io: io.BytesIO, file_name: str, meres: Signboard.objects) -> dict:
    """Fonction de génération du fichier de liste des Centrales Mère"""
    titre_list = file_name.split("_")
    titre = " ".join(titre_list[:-4])
    list_excel = [file_io, [titre[:30]]]
    excel = GenericExcel(list_excel)
    columns = columns_list_enseignes
    get_clean_rows = getattr(GetRows(meres), f"get_clean_rows")

    try:
        titre_page_writer(excel, 1, 0, 0, columns, titre)
        output_day_writer(excel, 1, 1, 0)
        columns_headers_writer(excel, 1, 3, 0, columns)
        f_lignes = [dict_row.get("f_ligne") for dict_row in columns]
        f_lignes_odd = [
            {**dict_row.get("f_ligne"), **{"bg_color": "#EBF1DE"}} for dict_row in columns
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
