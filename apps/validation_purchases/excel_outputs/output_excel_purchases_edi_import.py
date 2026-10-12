"""Module d'export du fichier excel des achats Héron non finalisées

Commentaire:

created at: 2023-06-20
created by: Paulo ALVES

modified at: 2023-06-20
modified by: Paulo ALVES
"""
import io
from pathlib import Path

from psycopg2 import sql

from heron.loggers import LOGGER_EXPORT_EXCEL
from apps.core.functions.functions_setups import settings, connection
from apps.validation_purchases.excel_outputs.columns_excel import columns_purchases_edi
from apps.core.excel_outputs.generic_list_export import excel_list_export



def get_clean_rows():
    """Retourne les lignes à écrire"""

    sql_file = Path(settings.APPS_DIR) / "validation_purchases/sql_files/sql_current_purchases.sql"

    with connection.cursor() as cursor, sql_file.open("r") as sql_file:
        # print(cursor.mogrify(sql.SQL(sql_file.read())))
        cursor.execute(sql.SQL(sql_file.read()))

        return cursor.fetchall()


def excel_heron_purchases_edi_import(file_io: io.BytesIO, file_name: str) -> dict:
    """Fonction de génération du fichier de liste achats fournisseurs imports edi"""
    return excel_list_export(
        file_io,
        file_name,
        sheet_name="ACHATS FOURNISSEURS",
        title="ACHATS FOURNISSEUR IMPORT EDI",
        columns=columns_purchases_edi,
        rows=get_clean_rows,
        in_memory=True,
    )


def csv_heron_purchases_edi_import(emplacement: Path) -> dict:
    """Fonction de génération du fichier csv de liste achats fournisseurs imports edi"""

    try:

        sql_file = (
            Path(settings.APPS_DIR) / "validation_purchases/sql_files/sql_current_purchases_csv.sql"
        )
        with emplacement.open("w", encoding="utf8"):
            ...

        emplacement.chmod(0o777)

        with connection.cursor() as cursor, sql_file.open("r") as sql_file:
            # print(cursor.mogrify(sql_file.read(), {"to_csv": str(emplacement)}).decode("utf8"))
            cursor.execute(sql_file.read(), {"to_csv": str(emplacement)})

    except Exception:
        LOGGER_EXPORT_EXCEL.exception(f"{emplacement.name!r}")
        return {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}

    return {"OK": f"GENERATION DU FICHIER {emplacement.name} TERMINEE AVEC SUCCES"}
