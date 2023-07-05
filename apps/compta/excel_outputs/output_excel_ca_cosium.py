# pylint: disable=W0702,W1203,E0401,E1101,C0103,W0603
"""Module d'export du fichier excel du CA des Maisons par Familles

Commentaire:

created at: 2023-03-07
created by: Paulo ALVES

modified at: 2023-03-07
modified by: Paulo ALVES
"""
import io

import pendulum
from xlsxwriter.utility import xl_rowcol_to_cell

from heron.loggers import LOGGER_EXPORT_EXCEL
from apps.core.functions.functions_excel import GenericExcel
from apps.core.excel_outputs.excel_writer import (
    titre_page_writer,
    output_day_writer,
    columns_headers_writer,
    sheet_formatting,
)
from apps.compta.models import CaClients
from apps.compta.excel_outputs.columns_excel import columns_ca_cosium

num_ligne = 0


def get_clean_rows(date_debut: str, date_fin: str) -> iter:
    """Retourne les lignes à écrire"""

    clean_rows = [
        (
            sale_dict.get("date_ca", ""),
            sale_dict.get("cct_uuid_identification__pays", ""),
            sale_dict.get("code_cosium", ""),
            (
                sale_dict.get("cct_uuid_identification__cct__cct", "")
                + " - "
                + sale_dict.get("cct_uuid_identification__intitule", "")
            ),
            sale_dict.get("famille_cosium", ""),
            sale_dict.get("axe_pro__section", ""),
            sale_dict.get("ca_ht_eur", ""),
            sale_dict.get("ca_ht_devise", ""),
        )
        for sale_dict in CaClients.objects.filter(date_ca__range=(date_debut, date_fin))
        .values(
            "date_ca",
            "cct_uuid_identification__pays",
            "code_cosium",
            "cct_uuid_identification__cct__cct",
            "cct_uuid_identification__intitule",
            "famille_cosium",
            "axe_pro__section",
            "ca_ht_eur",
            "ca_ht_devise",
        )
        .order_by(
            "date_ca",
            "cct_uuid_identification__pays",
            "cct_uuid_identification__cct__cct",
            "axe_pro__section",
        )
    ]

    return clean_rows


def write_sum(excel, feuille, debut, titre):
    """Ecriture des Sous-Totaux
    :param excel: worksheet
    :param feuille: N° de la feuille excel
    :param debut: Ligne de début de la somme
    :param titre: Titre du sous total ou du total
    """
    global num_ligne
    col = 0
    f_totaux = []
    color_dict = {"bg_color": "#D8E4BC" if "SOUS" in titre else "#dce7f5", "bold": True}

    common_dict = {
        "font_size": 10,
        "font_name": "Calibri",
        "valign": "top",
        "bottom": 1,
        "top": 1,
    }

    for j, _ in enumerate(columns_ca_cosium):
        if j < 6:
            if j == 0:
                left_right_dict = {"left": 1}
            elif j == 5:
                left_right_dict = {"right": 1, "align": "right"}
            else:
                left_right_dict = {}

            f_totaux.append({**common_dict, **left_right_dict, **color_dict})

        else:
            f_totaux.append({**columns_ca_cosium[j].get("f_ligne").copy(), **color_dict})

    totaux = ["", "", "", "", "", titre]

    for i in range(6, len(f_totaux)):
        if "SOUS" in titre:
            totaux.append(
                f"=SUM({xl_rowcol_to_cell(debut, i)}:{xl_rowcol_to_cell(num_ligne - 1, i)})"
            )
        else:
            totaux.append(
                f"=SUM({xl_rowcol_to_cell(debut, i)}:{xl_rowcol_to_cell(num_ligne - 1, i)})/2"
            )

    excel.write_rows(feuille, num_ligne, col, totaux, f_totaux)
    num_ligne += 1


def write_board(excel, sheet, clean_rows, f_lignes, f_lignes_odd):
    """
    Ecriture sur la feuille excel des lignes
    :param excel: worksheet
    :param sheet: N° de la feuille excel
    :param clean_rows: lignes à écrire dans la feuille
    :param f_lignes: formatage des lignes paires
    :param f_lignes_odd: formatage des lignes impaires
    """
    global num_ligne
    col = 0
    col_pays = 1
    col_maison = 3

    pays = clean_rows[0][col_pays]
    debut_pays = num_ligne
    maison = clean_rows[0][col_maison]
    debut_maison = num_ligne

    for clean_row in clean_rows:

        if maison != clean_row[col_maison]:
            write_sum(excel, sheet, debut_maison, f"SOUS TOTAL {maison}")
            maison = clean_row[col_maison]
            debut_maison = num_ligne

        if pays != clean_row[col_pays]:
            write_sum(excel, sheet, debut_pays, f"TOTAL {pays}")
            pays = clean_row[col_pays]
            debut_pays = num_ligne
            debut_maison += 1

        excel.write_rows(
            sheet, num_ligne, col, clean_row, f_lignes if num_ligne % 2 == 0 else f_lignes_odd
        )
        num_ligne += 1

    # ON ECRIT LE DERNIER SOUS TOTAL ET LE DERNIER TOTAL
    write_sum(excel, sheet, debut_maison, f"SOUS TOTAL {clean_rows[-1][col_maison]}")
    write_sum(excel, sheet, debut_pays, f"TOTAL {clean_rows[-1][col_pays]}")


def excel_ca_cosium(file_io: io.BytesIO, file_name: str, dte_d: str, dte_f: str) -> dict:
    """Fonction de génération du fichier de liste du chiffre d'affaires par maisons/familles"""
    date_debut = pendulum.parse(dte_d)
    date_debut_texte = date_debut.format("DD/MM/YYYY", locale="fr")
    date_fin = pendulum.parse(dte_f)
    date_fin_texte = date_fin.format("DD/MM/YYYY", locale="fr")
    titre = f"CHIFFRE D'AFFAIRES COSIUM DU {date_debut_texte} AU {date_fin_texte}"
    list_excel = [file_io, ["VENTES COSIUM"]]
    excel = GenericExcel(list_excel, in_memory=True)
    columns = columns_ca_cosium
    global num_ligne

    try:
        titre_page_writer(excel, 1, 0, 0, columns, titre)
        output_day_writer(excel, 1, 1, 0)
        columns_headers_writer(excel, 1, 3, 0, columns)
        f_lignes = [dict_row.get("f_ligne") for dict_row in columns]
        f_lignes_odd = [
            {**dict_row.get("f_ligne"), **{"bg_color": "#D9D9D9"}} for dict_row in columns
        ]
        num_ligne = 4
        sheet = 1
        write_board(excel, sheet, get_clean_rows(date_debut, date_fin), f_lignes, f_lignes_odd)
        sheet_formatting(
            excel, 1, columns, {"sens": "portrait", "repeat_row": (0, 5), "fit_page": (1, 0)}
        )

    except:
        LOGGER_EXPORT_EXCEL.exception(f"{file_name!r}")
        return {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}

    finally:
        excel.excel_close()

    return {"OK": f"GENERATION DU FICHIER {file_name} TERMINEE AVEC SUCCES"}
