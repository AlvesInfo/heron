"""Module d'export de la liste des articles avec leurs comptes comptables, pour un fournisseur

Commentaire:
    Même format que l'export des articles sans comptes, limité aux articles du fournisseur
    ayant des comptes

created at: 2026-09-28
created by: Paulo ALVES

modified at: 2026-09-28
modified by: Paulo ALVES
"""
import io
from pathlib import Path

from django.db import connection

from django.conf import settings
from apps.book.models import Society
from apps.articles.excel_outputs.output_excel_articles_columns import (
    columns_list_articles_without_account,
)
from apps.core.excel_outputs.generic_list_export import excel_list_export


def get_clean_rows(third_party_num: str) -> iter:
    """Retourne les lignes à écrire"""
    file_path = Path(f"{settings.APPS_DIR!s}/articles/sql/articles_account_supplier_list.sql")

    with file_path.open("r") as sql_file, connection.cursor() as cursor:
        query = sql_file.read()
        # print(cursor.mogrify(query, {"third_party_num": third_party_num}).decode())
        cursor.execute(query, {"third_party_num": third_party_num})
        return cursor.fetchall()


def excel_liste_articles_account_supplier(
    file_io: io.BytesIO, file_name: str, third_party_num: str
) -> dict:
    """Fonction de génération du fichier excel des articles avec comptes d'un fournisseur"""
    titre = (
            "LISTE DES ARTICLES AVEC COMPTES DU FOURNISSEUR : "
            f"{Society.objects.get(third_party_num=third_party_num)!s}"
        )
    columns = columns_list_articles_without_account

    return excel_list_export(
        file_io,
        file_name,
        sheet_name='ARTICLES AVEC COMPTES',
        title=titre,
        columns=columns,
        rows=get_clean_rows(third_party_num),
        orientation="landscape",
    )
