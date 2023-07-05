"""
Module qui gère les fichiers Excel
"""
import re
import os
import sys
import glob
import codecs
import csv
from datetime import datetime
import shutil

from bs4 import BeautifulSoup
import xlsxwriter
import pandas as pd

from apps.core.functions.functions_dates import date_string_series, time_string_series
from apps.core.functions.functions_logs import LOG_FILE, write_log
from apps.core.functions.functions_utilitaires import N_DIC, delete_file, encoding_detect


XLSX_PAPER_SIZE = {
    "Printer default": (0, "Printer default"),
    "Letter": (1, "8 1/2 x 11 in"),
    "Letter Small": (2, "8 1/2 x 11 in"),
    "Tabloid": (3, "11 x 17 in"),
    "Ledger": (4, "17 x 11 in"),
    "Legal": (5, "8 1/2 x 14 in"),
    "Statement": (6, "5 1/2 x 8 1/2 in"),
    "Executive": (7, "7 1/4 x 10 1/2 in"),
    "A3": (8, "297 x 420 mm"),
    "A4": (9, "210 x 297 mm"),
    "A4 Small": (10, "210 x 297 mm"),
    "A5": (11, "148 x 210 mm"),
    "B4": (12, "250 x 354 mm"),
    "B5": (13, "182 x 257 mm"),
    "Folio": (14, "8 1/2 x 13 in"),
    "Quarto": (15, "215 x 275 mm"),
    "Note": (18, "8 1/2 x 11 in"),
    "Envelope 9": (19, "3 7/8 x 8 7/8"),
    "Envelope 10": (20, "4 1/8 x 9 1/2"),
    "Envelope 11": (21, "4 1/2 x 10 3/8"),
    "Envelope 12": (22, "4 3/4 x 11"),
    "Envelope 14": (23, "5 x 11 1/2"),
    "C size sheet": (24, "—"),
    "D size sheet": (25, "—"),
    "E size sheet": (26, "—"),
    "Envelope DL": (27, "110 x 220 mm"),
    "Envelope C3": (28, "324 x 458 mm"),
    "Envelope C4": (29, "229 x 324 mm"),
    "Envelope C5": (30, "162 x 229 mm"),
    "Envelope C6": (31, "114 x 162 mm"),
    "Envelope C65": (32, "114 x 229 mm"),
    "Envelope B4": (33, "250 x 353 mm"),
    "Envelope B5": (34, "176 x 250 mm"),
    "Envelope B6": (35, "176 x 125 mm"),
    "Envelope": (36, "110 x 230 mm"),
    "Monarch": (37, "3.875 x 7.5 in"),
    "Fanfold": (39, "14 7/8 x 11 in"),
    "German Std Fanfold": (40, "8 1/2 x 12 in"),
    "German Legal Fanfold": (41, "8 1/2 x 13 in"),
}


def get_paper_size(value: str):
    """retourne la valeur en int de la taille de la page demandée
        :param value: valeur demandée
        :return: int value
    """
    return XLSX_PAPER_SIZE.get(value, (0, "Printer default"))[0]


class ExcelToCsvError(Exception):
    """Exception niveau module"""


def excel_excel_to_csv(fichier_excel, fichier_csv, header=True, sheets=None):
    """
    Fonction qui transforme un fichier excel en csv
        :param fichier_excel: nom du fichier du excel
        :param fichier_csv: nom du fichier du csv
        :param header: entête
        :param sheets: feuilles
        :return: fichier excel en csv
    """
    success = []

    try:
        xls = pd.ExcelFile(fichier_excel)
        if sheets is None:
            data = pd.read_excel(xls)
            data.to_csv(
                fichier_csv,
                sep=";",
                header=header,
                index=False,
                lineterminator="\n",
                quoting=csv.QUOTE_ALL,
            )
            success = [fichier_csv]

        else:
            for sheet in sheets:
                pth = os.path.split(fichier_csv)[0]
                filename = str(sheet).replace(" ", "").upper() + ".csv"
                sheet_csv = os.path.join(pth, filename)
                success.append(sheet_csv)
                data = pd.read_excel(xls, sheet_name=sheet)
                data.to_csv(
                    sheet_csv,
                    sep=";",
                    header=header,
                    index=False,
                    lineterminator="\n",
                    quoting=csv.QUOTE_ALL,
                )

    except ExcelToCsvError:
        success = []
        ligne = f"{datetime.now().isoformat()} | Erreur excel_excel_to_csv : {sys.exc_info()[1]}\n"
        write_log(LOG_FILE, ligne)

    return success


def excel_excel_to_csv_string_io(excel_string_io, csv_string_io, header=True, sheets=None):
    """
    Fonction qui transforme un fichier excel en csv
        :param excel_string_io: string_io excel à passer en csv
        :param csv_string_io: string_io en csv
        :param header: entête
        :param sheets: feuilles
        :return: fichier excel en csv
    """
    success = True

    try:
        xls = pd.ExcelFile(excel_string_io)
        data = pd.read_excel(xls)
        data.to_csv(
            csv_string_io,
            sep=";",
            header=header,
            index=False,
            lineterminator="\n",
            quoting=csv.QUOTE_ALL,
        )
        csv_string_io.seek(0)
    except ExcelToCsvError:
        success = False
        ligne = f"{datetime.now().isoformat()} | Erreur excel_excel_to_csv : {sys.exc_info()[1]}\n"
        write_log(LOG_FILE, ligne)

    return success


def excel_xhtml_to_csv(fichier_excel, fichier_csv, header=True):
    """
    Fonction qui transforme un fichier Xhtml excel en csv
        :param fichier_excel: nom du fichier du Xhtml excel
        :param fichier_csv: nom du fichier du csv
        :param header: entête
        :return: fichier excel en csv
    """
    success = []

    try:
        encoding = encoding_detect(fichier_excel)

        with codecs.open(fichier_excel, "r", encoding=encoding, errors="replace") as file:

            with open(fichier_csv, "w", newline="", encoding="utf-8") as csvfile:
                csv_write = csv.writer(csvfile, delimiter=";", quoting=csv.QUOTE_ALL)
                soup = BeautifulSoup(file, "lxml-xml")
                for i, t_r in enumerate(soup.find_all("tr")):
                    ligne = ""

                    for t_d in t_r.find_all("td"):
                        lig = ""

                        for span in t_d.find_all("span"):
                            lig = (
                                span.string.replace("=", "")
                                .replace('"', "")
                                .replace(";", "")
                                .replace("\n", "")
                                .replace("\r", "")
                                + ";"
                            )

                        if not lig:
                            lig = ";"

                        ligne += lig

                    ligne = ligne[:-1]

                    if i == 0 and header is not None:
                        csv_write.writerow(ligne)

                    if i > 0:
                        csv_write.writerow(ligne)

        success.append(str(fichier_csv))

    except ExcelToCsvError:
        ligne = (
            f"{datetime.now().isoformat()} | Erreur excel_excel_to_csv : " f"{sys.exc_info()[1]}\n"
        )
        write_log(LOG_FILE, ligne)

    return success


def date_debut_nom_fichier():
    """
    Fonction qui renvoie la date du jour au format texte souligné
        :return: la date du jour au format texte souligné --> '2018_09_23'
    """
    return datetime.date(datetime.now()).isoformat().replace("-", "") + "_"


class ExcelToCsv:
    """
    Class pour tansformation des fichiers Excel
    """

    def __init__(
        self,
        rep=None,
        rep_sauv=None,
        header=True,
        first_date=True,
        deletion=None,
        log=None,
        sheets=None,
        file_name=None,
    ):
        self.rep = rep
        self.rep_sauv = rep_sauv
        self.log_file = log if log is not None else LOG_FILE
        self.header = header
        self.first_date = first_date
        self.deletion = deletion
        self.sheets = sheets
        self.file_name = file_name

    @staticmethod
    def excel_is_xhtml(fichier):
        """
        Fonction qui vérifie si le fichier est un fichier Xhtml excel
            :param fichier: fichier
            :return: True ou False
        """
        with open(fichier, "r", encoding="utf-8", errors="replace") as file:
            test_xhtml = file.readline()[0:5]

        return test_xhtml == "<html"

    def make_csv(self):
        """
        Fonction qui transforme un fichier excel en csv
            :return: la liste des fichiers traités
        """
        treated_files = []

        if self.rep:
            # imports pdb;pdb.set_trace()
            try:
                if self.file_name is None:
                    rep = self.rep + "/*.*"
                else:
                    rep = self.rep + f"/{self.file_name}"

                files = [fichier for fichier in glob.glob(rep)]

                for file in files:
                    filename, ext = os.path.splitext(os.path.basename(file))

                    if ext in {".xls", ".xlsb", ".xlsm", ".xlsx"}:
                        pth, fichier = os.path.split(file)
                        f_name = filename + ".csv"

                        if self.first_date is not None:
                            f_name = date_debut_nom_fichier() + f_name

                        csv_file = os.path.join(pth, f_name)
                        delete_file(csv_file)

                        if self.excel_is_xhtml(file):
                            success = excel_xhtml_to_csv(file, csv_file, self.header)

                        else:
                            success = excel_excel_to_csv(file, csv_file, self.header, self.sheets)

                        if success:
                            treated_files.extend(success)

                        else:
                            ligne = (
                                f"{datetime.now().isoformat()} | Erreur de Conversion .xls "
                                f"en .csv : {fichier}\n"
                                f"\t\t\t{sys.exc_info()[1]}\n"
                            )

                            write_log(self.log_file, ligne)

                        if self.deletion:
                            os.remove(file)

                        if self.rep_sauv is not None and self.deletion is None:
                            excel_sauv = os.path.join(self.rep_sauv, fichier)
                            shutil.move(file, excel_sauv)

            except ExcelToCsvError:
                ligne = (
                    f"{datetime.now().isoformat()} | Erreur de conversion fichiers .xls en .csv : "
                    f"{sys.exc_info()[1]}\n"
                )
                write_log(self.log_file, ligne)

        return treated_files


class GenericExcel:
    """
    Class pour manager plus simplement les fichiers excel XlsxWriter
    """

    def __init__(self, excel_workbooks, in_memory=None):
        if in_memory is not None:
            self.workbook = xlsxwriter.Workbook(excel_workbooks[0], {"constant_memory": True})
        else:
            self.workbook = xlsxwriter.Workbook(excel_workbooks[0])
        self.worksheets = []
        for sheet in excel_workbooks[1]:
            self.worksheets.append(self.workbook.add_worksheet(sheet))

    def write_headers_h(self, num_sheet, row, col, valeurs, styles=None):
        """
            Ecriture des entêtes à deux étages, en horizontal
            exemple :   |     ENTETE PRINCIPAL      |
                        | t 01 | t 02 | t 03 | t 04 |
        :param num_sheet: Numéro de la feuille, dans laquelle il faut écrire
        :param row: Numéro de la ligne de l'entête principal, débute à 0
        :param col: Numéro de la colonne de l'entête principal, débute à 0
        :param valeurs: Liste des valeurs à inserer dans les cellules
        :param styles: Liste des sytles à appliquer aux cellules, par défaut pas de styles
        :return: Ne retourne rien
        """
        feuille = num_sheet - 1
        wsexcel = self.worksheets[feuille]
        nb_col = len(valeurs)
        col_01 = col
        col_02 = col + nb_col - 2

        for num in range(nb_col):
            val = valeurs[num]
            if num == 0:
                if styles:
                    f_m = self.workbook.add_format(styles[num])
                    wsexcel.merge_range(row, col_01, row, col_02, val, f_m)
                else:
                    wsexcel.merge_range(row, col_01, row, col_02, val)
            else:
                if styles:
                    f_m = self.workbook.add_format(styles[num])
                    wsexcel.write(row + 1, col_01, val, f_m)
                else:
                    wsexcel.write(row + 1, col_01, val)
                col_01 += 1

    def write_headers_v(self, num_sheet, row, col, valeurs, styles=None):
        """
            Ecriture des entêtes à deux étages, en vertical
            exemple :   | E | t 01 |
                        | N | t 02 |
                        | T | t 03 |
                        | E | t 04 |
                        | T | t 05 |
                        | E | t 06 |
        :param num_sheet: Numéro de la feuille, dans laquelle il faut écrire
        :param row: Numéro de la ligne de l'entête principal, débute à 0
        :param col: Numéro de la colonne de l'entête principal, débute à 0
        :param valeurs: Liste des valeurs à inserer dans les cellules
        :param styles: Liste des sytles à appliquer aux cellules, par défaut pas de styles
        :return: Ne retourne rien
        """
        feuille = num_sheet - 1
        wsexcel = self.worksheets[feuille]
        nb_col = len(valeurs)
        r_02 = row + nb_col - 2
        col_02 = col + 1

        for num in range(nb_col):
            val = valeurs[num]
            if num == 0:
                if styles:
                    f_m = self.workbook.add_format(styles[num])
                    wsexcel.merge_range(row, col, r_02, col, val, f_m)
                else:
                    wsexcel.merge_range(row, col, r_02, col, val)
            else:
                if styles:
                    f_m = self.workbook.add_format(styles[num])
                    wsexcel.write(row, col_02, val, f_m)
                else:
                    wsexcel.write(row, col_02, val)
                row += 1

    def write_merge_h(self, num_sheet, row, col_01, col_02, valeur, style=None):
        """
            Ecriture d'une valeur merge, en horizontal
            exemple :   |   cellule     |
                        |   |   |   |   |
        :param num_sheet: Numéro de la feuille, dans laquelle il faut écrire
        :param row: Numéro de la ligne, débute à 0
        :param col_01: Première colonne du merge, débute à 0
        :param col_02: Dernière colonne du merge, débute à 0
        :param valeur: Valeur à inserer dans la cellule
        :param style: Sytle à appliquer à la cellules, par défaut pas de styles
        :return: Ne retourne rien
        """
        feuille = num_sheet - 1
        wsexcel = self.worksheets[feuille]
        if style:
            f_m = self.workbook.add_format(style)
            wsexcel.merge_range(row, col_01, row, col_02, valeur, f_m)
        else:
            wsexcel.merge_range(row, col_01, row, col_02, valeur)

    def write_merge_v(self, num_sheet, row_01, row_02, col, valeur, style=None):
        """
            Ecriture d'une valeur merge, en Vertical
            exemple :   | E |   |
                        | N |   |
                        | T |   |
                        | E |   |
                        | T |   |
                        | E |   |
        :param num_sheet: Numéro de la feuille, dans laquelle il faut écrire
        :param row_01: Première ligne du merge, débute à 0
        :param row_02: Dernière ligne du merge, débute à 0
        :param col: Colonne, débute à 0
        :param valeur: Valeur à inserer dans la cellule
        :param style: Sytle à appliquer à la cellules, par défaut pas de styles
        :return: Ne retourne rien
        """
        feuille = num_sheet - 1
        wsexcel = self.worksheets[feuille]
        if row_01 == row_02:
            if style:
                f_m = self.workbook.add_format(style)
                wsexcel.write(row_01, col, valeur, f_m)
            else:
                wsexcel.write(row_01, col, valeur)
        else:
            if style:
                f_m = self.workbook.add_format(style)
                wsexcel.merge_range(row_01, col, row_02, col, valeur, f_m)
            else:
                wsexcel.merge_range(row_01, col, row_02, col, valeur)

    def write_merge(self, num_sheet, cells, valeur, style=None):
        """
            Ecriture d'une valeur, dans des cellules mergées
        :param num_sheet: Numéro de la feuille, dans laquelle il faut écrire
        :param cells: cellules en notation 'A1:B5'
        :param valeur: Valeur à inserer dans la cellule
        :param style: Sytle à appliquer à la cellules, par défaut pas de styles
        :return: Ne retourne rien
        """
        feuille = num_sheet - 1
        wsexcel = self.worksheets[feuille]
        if style:
            f_m = self.workbook.add_format(style)
            wsexcel.merge_range(cells, valeur, f_m)
        else:
            wsexcel.merge_range(cells, valeur)

    def write_row(self, num_sheet, row, col, valeur, style=None):
        """
            Ecriture d'une seule cellule
        :param num_sheet: Numéro de la feuille, dans laquelle il faut écrire
        :param row: Numéro de la ligne de l'entête principal, débute à 0
        :param col: Numéro de la colonne de l'entête principal, débute à 0
        :param valeur: valeur à inserer dans la cellules
        :param style: sytle à appliquer à la cellule, par défaut pas de style
        :return: Ne retourne rien
        """
        feuille = num_sheet - 1
        wsexcel = self.worksheets[feuille]

        if style:
            f_m = self.workbook.add_format(style)
            wsexcel.write(row, col, valeur, f_m)
        else:
            wsexcel.write(row, col, valeur)

    def write_rows(self, num_sheet, row, col, valeurs, styles=None):
        """
        Ecriture de plusieurs cellules adjacentes
            :param num_sheet: Numéro de la feuille, dans laquelle il faut écrire
            :param row: Numéro de la ligne de l'entête principal, débute à 0
            :param col: Numéro de la colonne de l'entête principal, débute à 0
            :param valeurs: Liste des valeurs à inserer dans les cellules
            :param styles:  Liste des styles à appliquer aux cellules, par défaut pas de styles.
                            Si toutes les valeurs ont le même style à appliquer, alors on peut
                            n'envoyer qu'un seul
            :return: Ne retourne rien
        """
        f_o = styles
        nb_col = len(valeurs)

        if isinstance(styles, (dict,)) or nb_col != len(styles):
            f_o = []
            f_o.extend([styles] * nb_col)

        feuille = num_sheet - 1
        wsexcel = self.worksheets[feuille]
        # print(len(valeurs), len(styles))
        # print(valeurs)
        for num in range(nb_col):
            val = valeurs[num]
            if styles:
                f_m = self.workbook.add_format(f_o[num])
                wsexcel.write(row, col, val, f_m)
            else:
                wsexcel.write(row, col, val)
            col += 1

    def write_image(self, num_sheet, row, col, image, options=None):
        """
        Fonction qui écrit une image dans le fichier excel
            :param num_sheet: Numéro de la feuille, dans laquelle il faut écrire
            :param row: Numéro de la ligne de l'entête principal, débute à 0
            :param col: Numéro de la colonne de l'entête principal, débute à 0
            :param image: Image
            :param options: Options
            :return: None
        """
        feuille = num_sheet - 1
        wsexcel = self.worksheets[feuille]
        if options:
            wsexcel.insert_image(row, col, image, options)
        else:
            wsexcel.insert_image(row, col, image)

    def excel_sheet(self, num_sheet):
        """
        Fonction qui gère les feuiles du fichier à générer
            :param num_sheet: Numéro de la feuille débute à 1
            :return: la feuille à manipuler
        """
        feuille = num_sheet - 1
        return self.worksheets[feuille]

    def sheet_zoom(self, num_sheet, zoom_value):
        """
        Fonction qui place un zoom sur la feuille
            :param num_sheet: Numéro de la feuille débute à 1
            :param zoom_value: Valeur du zoom en int
            :return: None
        """
        feuille = num_sheet - 1
        wsexcel = self.worksheets[feuille]
        wsexcel.set_zoom(zoom_value)

    def sheet_hide_zero(self, num_sheet):
        """
        Fonction qui masque les valeur 0 dans la feuille
            :param num_sheet: Numéro de la feuille débute à 1
            :return: None
        """
        feuille = num_sheet - 1
        wsexcel = self.worksheets[feuille]
        wsexcel.hide_zero()

    def sheet_tab_color(self, num_sheet, color):
        """
        Fonction qui colore l'onglet de la feuille dans le classeur
            :param num_sheet: Numéro de la feuille débute à 1
            :param color: Couleur de l'onglet
            :return: None
        """
        feuille = num_sheet - 1
        wsexcel = self.worksheets[feuille]
        wsexcel.set_tab_color(color)

    def conditional_value(self, num_sheet, str_plage, valeur, type_format="cell", criteria="<", style=None):
        """
        Fonction qui pose des conditions
            :param num_sheet: Numéro de la feuille débute à 1
            :param str_plage: Plage de la feuille conditionnelle
            :param valeur: valeur conditionnelle
            :param type_format: type de formatage cell, formula, ....
            :param criteria: Critère
            :param style: Style
            :return: None
        """
        feuille = num_sheet - 1
        cellule = str_plage
        if style:
            f_m = self.workbook.add_format(style)
            self.worksheets[feuille].conditional_format(
                cellule, {"type": type_format, "criteria": criteria, "value": valeur, "format": f_m}
            )
        else:
            self.worksheets[feuille].conditional_format(
                cellule, {"type": type_format, "criteria": criteria, "value": valeur}
            )

    def excel_close(self):
        """
        Fonction qui ferme le fichier excel
            :return: None
        """
        self.workbook.close()


def nom_feuilles_excel(nom, majuscule=True):
    """
    Fonction qui renvoie le nom des feuilles ecel cleaner
        :param nom: nom initial
        :param majuscule: Si l'on souhaite mettre le nom en majuscule
        :return: nom de la feuille cleaner
    """
    new_name = nom

    # compilation regex
    re_alpha = re.compile(r"[0-9a-zA-Z\- ]")

    # Remplacement des caractères accentués contenus dans n_dic
    for key, val in N_DIC.items():
        for s_lettre in new_name:
            if s_lettre in val:
                new_name = new_name.replace(s_lettre, key)

    # Mise en majuscule si demandé
    new_name = new_name.upper() if majuscule else new_name.lower()
    # Remplacement des caractères spéciaux
    new_name = "".join(re.findall(re_alpha, new_name))[:31]

    return new_name


if __name__ == "__main__":
    EXCEL_DIR = "D://SitesWeb//sav//files"
    EXCEL_FILE = (
        f"{EXCEL_DIR}//{'Test_Class_excel'}_{date_string_series()}" f"_{time_string_series()}.xlsx"
    )
    EXCEL_SHEETS = ["f_01", "f_02", "f_03", "f_04"]
    E_X = [EXCEL_FILE, EXCEL_SHEETS]

    EXCEL = GenericExcel(E_X)
    EXCEL.write_row(1, 0, 0, "f_01", None)
    EXCEL.write_rows(1, 8, 0, [1, 2, 3])
    EXCEL.write_row(2, 0, 0, "f_02", None)
    EXCEL.write_row(3, 0, 0, "f_03", None)
    EXCEL.write_row(4, 0, 0, "f_04", None)
    EXCEL.write_headers_h(1, 2, 0, ["e1", "e01", "e02", "e03"])
    EXCEL.write_headers_v(1, 4, 0, ["e1", "e01", "e02", "e03"])
    EXCEL.excel_close()
