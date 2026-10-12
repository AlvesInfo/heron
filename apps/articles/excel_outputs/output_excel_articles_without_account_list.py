"""Module d'export de la liste des articles sans comptes comptablesexcel

Commentaire:

created at: 2022-05-29
created by: Paulo ALVES

modified at: 2022-05-29
modified by: Paulo ALVES
"""
import io
from pathlib import Path

from django.db import connection

from django.conf import settings
from apps.articles.excel_outputs.output_excel_articles_columns import (
    columns_list_articles_without_account,
)
from apps.core.excel_outputs.generic_list_export import excel_list_export


def get_clean_rows() -> iter:
    """Retourne les lignes à écrire"""
    file_path = Path(
        f"{settings.APPS_DIR!s}/articles/sql/articles_wihout_account_list.sql"
    )

    with file_path.open("r") as sql_file, connection.cursor() as cursor:
        query = sql_file.read()
        # print(cursor.mogrify(query).decode())
        cursor.execute(query)
        return cursor.fetchall()


def excel_liste_articles_without_account(file_io: io.BytesIO, file_name: str) -> dict:
    """Fonction de génération du fichier de la liste des articles sans copte comptable excel"""
    titre = "LISTE DE ARTICLES SANS COMPTES"
    columns = columns_list_articles_without_account

    return excel_list_export(
        file_io,
        file_name,
        sheet_name=titre[:30],
        title=titre,
        columns=columns,
        rows=get_clean_rows(),
        orientation="landscape",
    )
