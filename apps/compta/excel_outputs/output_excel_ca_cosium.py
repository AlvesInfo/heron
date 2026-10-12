"""Module d'export du fichier excel du CA des Maisons par Familles.

Commentaire:

created at: 2023-03-07
created by: Paulo ALVES

modified at: 2023-03-07
modified by: Paulo ALVES
"""

import io

import pendulum
from xlsxwriter.utility import xl_rowcol_to_cell

from apps.compta.excel_outputs.columns_excel import columns_ca_cosium
from apps.compta.models import CaClients
from apps.core.excel_outputs.generic_list_export import excel_list_export


def get_clean_rows(date_debut: str, date_fin: str) -> list:
    """Retourne les lignes à écrire."""
    return [
        (
            sale_dict.get("date_ca", ""),
            sale_dict.get("cct_uuid_identification__pays") or "",
            sale_dict.get("code_cosium", ""),
            (
                (sale_dict.get("cct_uuid_identification__cct__cct") or "")
                + " - "
                + (sale_dict.get("cct_uuid_identification__intitule") or "")
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


def write_sum(excel, sheet, debut, row, titre):
    """Écrit une ligne de sous-total (par maison) ou de total (par pays) et renvoie la ligne suivante.

    :param excel: classeur
    :param sheet: N° de la feuille excel
    :param debut: première ligne de la somme
    :param row: ligne où écrire
    :param titre: titre du sous-total ou du total.
    """
    color_dict = {"bg_color": "#D8E4BC" if "SOUS" in titre else "#dce7f5", "bold": True}
    common_dict = {"font_size": 10, "font_name": "Calibri", "valign": "top", "bottom": 1, "top": 1}
    f_totaux = []

    for j, column in enumerate(columns_ca_cosium):
        if j < 6:
            left_right_dict: dict = {}
            if j == 0:
                left_right_dict = {"left": 1}
            elif j == 5:
                left_right_dict = {"right": 1, "align": "right"}

            f_totaux.append({**common_dict, **left_right_dict, **color_dict})
        else:
            f_totaux.append({**column["f_ligne"], **color_dict})

    divisor = "" if "SOUS" in titre else "/2"
    totaux = ["", "", "", "", "", titre] + [
        f"=SUM({xl_rowcol_to_cell(debut, i)}:{xl_rowcol_to_cell(row - 1, i)}){divisor}"
        for i in range(6, len(f_totaux))
    ]
    excel.write_rows(sheet, row, 0, totaux, f_totaux)

    return row + 1


def write_board(excel, sheet, _columns, clean_rows, f_lignes, f_lignes_odd):
    """Écrit les lignes avec un sous-total à chaque changement de maison et un total à chaque.

    changement de pays ; sans ligne, affiche que le CA n'a pas été généré.
    """
    row = 4
    col_pays, col_maison = 1, 3

    if not clean_rows:
        excel.write_row(
            sheet,
            row,
            0,
            "Le chiffre d'affaires par maisons/familles, n'a pas été généré",
            {"bold": True, "font_size": 14, "font_color": "red"},
        )
        return

    pays, maison = clean_rows[0][col_pays], clean_rows[0][col_maison]
    debut_pays = debut_maison = row

    for clean_row in clean_rows:
        if maison != clean_row[col_maison]:
            row = write_sum(excel, sheet, debut_maison, row, f"SOUS TOTAL {maison}")
            maison, debut_maison = clean_row[col_maison], row

        if pays != clean_row[col_pays]:
            row = write_sum(excel, sheet, debut_pays, row, f"TOTAL {pays}")
            pays, debut_pays = clean_row[col_pays], row
            debut_maison += 1

        excel.write_rows(sheet, row, 0, clean_row, f_lignes if row % 2 == 0 else f_lignes_odd)
        row += 1

    row = write_sum(excel, sheet, debut_maison, row, f"SOUS TOTAL {clean_rows[-1][col_maison]}")
    write_sum(excel, sheet, debut_pays, row, f"TOTAL {clean_rows[-1][col_pays]}")


def excel_ca_cosium(file_io: io.BytesIO, file_name: str, dte_d: str, dte_f: str) -> dict:
    """Fonction de génération du fichier de liste du chiffre d'affaires par maisons/familles."""
    date_debut = pendulum.parse(dte_d)
    date_fin = pendulum.parse(dte_f)
    titre = (
        f"CHIFFRE D'AFFAIRES COSIUM DU {date_debut.format('DD/MM/YYYY', locale='fr')} "
        f"AU {date_fin.format('DD/MM/YYYY', locale='fr')}"
    )

    return excel_list_export(
        file_io,
        file_name,
        sheet_name="CA COSIUM",
        title=titre,
        columns=columns_ca_cosium,
        rows=lambda: get_clean_rows(date_debut, date_fin),
        in_memory=True,
        writer=write_board,
    )
