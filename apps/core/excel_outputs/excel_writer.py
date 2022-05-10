# pylint: disable=R0913
"""Module de simplification de l'écriture des titres de feuilles, date d'édition du fichier et
entêtes

créé le : 22/11/2020
par : Paulo ALVES

modifié le : 22/11/2020
par : Paulo ALVES
"""
from pathlib import Path

import pendulum

from apps.core.functions.functions_setups import settings
from apps.core.functions.functions_excel import get_paper_size

# ==========================================================================================
# FORMATAGES PAR DEFAUT
# ==========================================================================================
f_titre = {"font_size": 20, "bold": True, "bg_color": "#dce7f5"}

f_edit = {"font_size": 10, "font_name": "Calibri", "bold": True, "valign": "vcenter"}

f_entetes = {
    "font_name": "calibri",
    "bg_color": "#dce7f5",
    "top": 1,
    "bottom": 1,
    "left": 1,
    "right": 1,
    "bold": True,
    "text_wrap": True,
    "align": "center",
    "valign": "vcenter",
}

f_ligne = {
    "font_size": 10,
    "font_name": "Calibri",
    "valign": "top",
    "bottom": 1,
    "top": 1,
    "left": 1,
    "right": 1,
}


def logo_writer(excel, logo_path, sheet, row, col, dict_args=None):
    """Fonction d'écriture du logo
        :param excel: feuille excel ou écrire
        :param logo_path: path du logo
        :param sheet: N° de la feuille excel ou écrire
        :param row: ligne
        :param col: colonnes
        :param dict_args: dictionnaire des arguments supplémentaires
        :return: None
    """
    if logo_path.is_file():
        if dict_args:
            excel.excel_sheet(sheet).insert_image(row, col, logo_path, dict_args)
        else:
            excel.excel_sheet(sheet).insert_image(row, col, logo_path)


def titre_page_writer(excel, sheet, row, col, columns_list, titre, merge=False):
    """Ecriture sur la feuille excel, du titre de la feuille
        :param excel: feuille excel
        :param sheet: n° de feuille excel
        :param row: ligne
        :param col: colonne
        :param columns_list: liste des colonnes
        :param titre: titre à écrire
        :param merge: si le titre doit être mergé
        :return: None
    """
    nb_col = len(columns_list)

    if merge:
        f_titre["align"] = "center"
        excel.write_merge_h(sheet, row, col, nb_col, titre, f_titre)
    else:
        titres_list = [titre] + ["" for _ in range(nb_col - 1)]
        format_list = [f_titre for _ in range(nb_col)]
        excel.write_rows(sheet, row, col, titres_list, format_list)


def output_day_writer(excel, sheet, row, col, dict_format=None):
    """Mise en place de la date d'édition
        :param excel: feuille excel
        :param sheet: n° de feuille excel
        :param row: ligne
        :param col: colonne
        :param dict_format: dictionnaire des formats souhaités
        :return: None
    """
    formatage = dict_format or f_edit
    edite = f"Edité, le {pendulum.today().format('DD MMMM YYYY', locale='fr')}"
    excel.write_row(sheet, row, col, edite, formatage)


def columns_headers_writer(excel, sheet: int, num_row: int, num_col: int, columns_list):
    """Ecriture sur la feuille excel, du titre de la feuille
    """
    entetes_list = [dict_row.get("entete") for dict_row in columns_list]
    formats_list = [dict_row.get("f_entete") for dict_row in columns_list]
    excel.write_rows(sheet, num_row, num_col, entetes_list, formats_list)


def sheet_formatting(excel, sheet: int, columns_list, dict_args=None):
    """Formatage des largeurs de colonnes et du format à l'impression
        :param excel:
        :param sheet:
        :param columns_list:
        :param dict_args:
        :return:
    """
    if dict_args is None:
        dict_args = {}

    marge = dict_args.get("marge", 0.1)
    paper = get_paper_size(dict_args.get("paper", "A4"))
    sens = dict_args.get("sens", "portrait")
    center_horizontal = dict_args.get("centrer", True)
    repeat_row = dict_args.get("repeat_row")
    fit_page = dict_args.get("fit_page")

    # MISE EN PLACE DES LARGEUR DE COLONNES
    for i, dict_row in enumerate(columns_list):
        excel.excel_sheet(sheet).set_column(i, i, dict_row.get("width"))

    # MISE EN PLACE DU FORMATAGE A L'IMPRESSION
    excel.excel_sheet(sheet).set_paper(paper)
    excel.excel_sheet(sheet).set_margins(marge, marge, marge, marge)

    if sens == "portrait":
        excel.excel_sheet(sheet).set_portrait()
    else:
        excel.excel_sheet(sheet).set_landscape()

    if center_horizontal:
        excel.excel_sheet(sheet).center_horizontally()

    if repeat_row:
        excel.excel_sheet(sheet).repeat_rows(*repeat_row)

    if fit_page:
        excel.excel_sheet(sheet).fit_to_pages(*fit_page)


def rows_writer(excel, sheet, row, col, clean_rows, formatage, formatage_odd=None):
    """Ecriture sur la feuille des lignes de la feuille excel"""
    for clean_row in clean_rows:
        if formatage is None:
            excel.write_rows(sheet, row, col, clean_row, formatage)
        else:
            excel.write_rows(
                sheet, row, col, clean_row, formatage if row % 2 == 0 else formatage_odd
            )
        row += 1
