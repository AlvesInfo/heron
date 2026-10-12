"""Module d'export du fichier excel des ventes Héron non finalisées (version optimisée).

Commentaire:

created at: 2023-06-20
created by: Paulo ALVES

modified at: 2025-01-14
modified by: Optimized version
"""

import io
from pathlib import Path

from psycopg2 import sql

from apps.core.excel_outputs.generic_list_export import excel_list_export
from apps.core.functions.functions_setups import connection, settings
from apps.validation_sales.excel_outputs.columns_excel import columns_sales_heron


def fetch_rows():
    """Lignes à écrire, lues par lots de 1000 (générateur, optimisé mémoire)."""
    sql_file_path = Path(settings.APPS_DIR) / "validation_sales/sql_files/sales_not_final.sql"

    with connection.cursor() as cursor, sql_file_path.open("r", encoding="utf-8") as sql_file:
        cursor.execute(sql.SQL(sql_file.read()))

        while True:
            rows = cursor.fetchmany(1000)

            if not rows:
                break

            yield from rows


def excel_heron_sales_not_final(file_io: io.BytesIO, file_name: str) -> dict:
    """Fonction de génération du fichier des ventes Héron non finalisés."""
    return excel_list_export(
        file_io,
        file_name,
        sheet_name="VENTES HERON",
        title="VENTES HERON A FINALISER",
        columns=columns_sales_heron,
        rows=fetch_rows,
        in_memory=True,
    )
