# pylint: disable=W0702,W1203,E0401,E1101
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

from heron.settings.base import APPS_DIR
from heron.loggers import LOGGER_EXPORT_EXCEL
from apps.core.functions.functions_excel import GenericExcel
from apps.core.excel_outputs.excel_writer import (
    titre_page_writer,
    output_day_writer,
    columns_headers_writer,
    sheet_formatting,
    rows_writer,
)
from apps.book.models import Society
from apps.articles.excel_outputs.output_excel_articles_columns import (
    columns_list_articles_without_account,
)


def get_clean_rows(third_party_num: str) -> iter:
    """Retourne les lignes à écrire"""
    file_path = Path(f"{str(APPS_DIR)}/articles/sql/articles_account_supplier_list.sql")

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
        f"{str(Society.objects.get(third_party_num=third_party_num))}"
    )
    list_excel = [file_io, ["ARTICLES AVEC COMPTES"]]
    excel = GenericExcel(list_excel)
    columns = columns_list_articles_without_account

    try:
        titre_page_writer(excel, 1, 0, 0, columns, titre)
        output_day_writer(excel, 1, 1, 0)
        columns_headers_writer(excel, 1, 3, 0, columns)
        f_lignes = [dict_row.get("f_ligne") for dict_row in columns]
        f_lignes_odd = [
            {**dict_row.get("f_ligne"), **{"bg_color": "#D9D9D9"}} for dict_row in columns
        ]
        rows_writer(
            excel, 1, 4, 0, get_clean_rows(third_party_num), f_lignes, f_lignes_odd
        )
        sheet_formatting(
            excel, 1, columns, {"sens": "landscape", "repeat_row": (0, 5), "fit_page": (1, 0)}
        )

    except:
        LOGGER_EXPORT_EXCEL.exception(f"{file_name!r}")
        return {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}

    finally:
        excel.excel_close()

    return {"OK": f"GENERATION DU FICHIER {file_name} TERMINEE AVEC SUCCES"}
