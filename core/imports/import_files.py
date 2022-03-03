# pylint: disable=
# flake8: noqa: E501
"""Module pour validation de fichiers à intégrer en base de donnée

Commentaire:

created at: 2021-10-30
created by: Paulo ALVES

modified at: 2021-10-30
modified by: Paulo ALVES
"""
import io
from pathlib import Path
from typing import Dict
import csv
from operator import itemgetter

from chardet.universaldetector import UniversalDetector
import pandas as pd

from core.functions.loggers import IMPORT_LOGGER


class ExcelToCsvError(Exception):
    """Exception niveau module"""


class IterFileToInsertError(Exception):
    """Gestion d'erreur d'itération d'un fichier à insérer"""


class ValidationError(Exception):
    """Gestion d'erreur de validations"""


def encoding_detect(path_file):
    """Fonction qui renvoie """
    detector = UniversalDetector()
    with open(path_file, "rb") as file:
        for line in file:
            detector.feed(line)
            if detector.done:
                break
        detector.close()

    return detector.result["encoding"]


def excel_file_to_csv_string_io(excel_path, csv_string_io, header=True):
    """Fonction qui transforme un fichier excel en csv
    :param excel_path: string_io excel à passer en csv
    :param csv_string_io: string_io en csv
    :param header: entête
    :return: fichier excel en csv
    """
    success = True
    try:
        xls = pd.ExcelFile(excel_path)
        data = pd.read_excel(xls)
        data.to_csv(
            csv_string_io,
            sep=";",
            header=header,
            index=False,
            line_terminator="\n",
            quoting=csv.QUOTE_ALL,
            encoding="utf8",
        )
        csv_string_io.seek(0)

    except ExcelToCsvError:
        success = False
        IMPORT_LOGGER.exception("excel_excel_to_csv_string_io")

    return success


def file_to_csv_string_io(file: Path, csv_string_io: io.StringIO, mode_csv_dict: Dict = None):
    """Fonction qui transforme un fichier  en csv
    :param file: string_io excel à passer en csv
    :param csv_string_io: string_io en csv
    :param mode_csv_dict: dictionnaire des caractéristiques du fichier
                        "sep" : séparateur du fichier, par défaut ";"
                        "line_terminator": séparateur de lignes du fichier par défaut "\n"
                        "quoting": type de quoting par défaut csv.QUOTE_ALL
                        "quotechar": le caractère de quoting par défaut '"'
    :return: string_io au format csv
    """
    mode_csv_dict = mode_csv_dict or dict()
    csv_dict = {
        "delimiter": mode_csv_dict.get("delimiter", ";"),
        "lineterminator": mode_csv_dict.get("lineterminator", "\n"),
        "quoting": mode_csv_dict.get("quoting", csv.QUOTE_ALL),
        "quotechar": mode_csv_dict.get("quotechar", '"'),
    }
    encoding = encoding_detect(file)

    with file.open("r", encoding=encoding, errors="replace") as csv_file:
        csv_reader = csv.reader(csv_file, **csv_dict)

        for line in csv_reader:
            line_to_wrtie = ";".join(f'"{value}"' for value in line) + "\n"
            csv_string_io.write(line_to_wrtie)

        csv_string_io.seek(0)


class IterFileToInsert:
    """Iterateur de dictionnaire de données, ou ligne à ligne, d'un fichier ou d'un fichier
    bufferisé avec séparateur de type csv à insérer"""

    def __init__(
        self,
        file_to_iter: Path,
        columns_dict: Dict,
        header_line: int = None,
        mode_csv_dict: Dict = None,
    ):
        """Instanciation des variables
            :param file_to_iter: fichier dy type Path à insérer
            :param columns_dict: Plusieurs choix possible :
                            - pour récupérer le nombre de colonnes dans l'ordre du fichier
                                {"db_col_1" : None, "db_col_2" : None, ..., }

                            - pour récupérer seulement les colonnes souhaitées par leur nom
                                {"db_col_1" : "file_col_x", "db_col_2" : "file_col_a", ..., }

                            - pour récupérer seulement les colonnes souhaitées par leur index
                                (index commence à 0)
                                {"db_col_1" : 3, "db_col" : 0, ..., }

            :param header_line: line du header, ou None
            :param mode_csv_dict: dictionnaire des caractéristiques du fichier
                    {
                        "delimiter" : séparateur du fichier, par défaut ";"
                        "lineterminator": séparateur de lignes du fichier par défaut "\n"
                        "quoting": type de quoting par défaut csv.QUOTE_ALL
                        "quotechar": le caractère de quoting par défaut '"'
                    }
        """
        self.file_to_iter = file_to_iter
        self.csv_io = io.StringIO()
        self.columns_dict = columns_dict
        self.header_line = header_line
        self.first_line = 0 if header_line is None else header_line + 1
        self.mode_csv_dict = mode_csv_dict or dict()
        self.csv_reader = csv.reader(
            self.csv_io.readlines(),
            delimiter=self.mode_csv_dict.get("delimiter") or ";",
            quotechar=self.mode_csv_dict.get("quotechar") or '"',
            lineterminator=self.mode_csv_dict.get("lineterminator") or "\n",
            quoting=self.mode_csv_dict.get("quoting") or csv.QUOTE_ALL,
        )
        self.get_io()

    def __enter__(self):
        """Pré context manager"""
        return self

    def __exit__(self, tipe, value, traceback):
        """Post context manager, pour fermer
            :param tipe: valeur du type venant de la sortie de la classe
            :param value: valeur venant de la sortie de la classe
            :param traceback: traceback sur une éventuele exception de la sortie de la classe
        """
        self.close_buffer()

    def get_io(self):
        """Fonction qui renvoie un io.StringIO, Il y aura un prétraitement différent si le fichier
        envoyé est un fichier à plat, ou un fichier Excel
        """
        try:
            if self.file_to_iter.suffix in {".xls", ".xlsx"}:
                excel_file_to_csv_string_io(self.file_to_iter, self.csv_io)
            else:
                file_to_csv_string_io(self.file_to_iter, self.csv_io, self.mode_csv_dict)

        except ExcelToCsvError:
            IMPORT_LOGGER.exception("excel_excel_to_csv_string_io")

    def close_buffer(self):
        """Fonction de fermeture du buffer io.StringIO"""
        if not self.csv_io.closed:
            self.csv_io.close()

    def seek_in_line_position(self, csv_reader, row_index):
        """Placement sur la première ligne demandée
            :param csv_reader: instance de csv reader
            :param row_index: première ligne ou ce placer
        """
        self.csv_io.seek(0)
        for _ in range(row_index):
            next(csv_reader)

    def get_csv_reader(self):
        """Instancie csv reader"""
        self.seek_in_line_position(self.csv_io, self.header_line)
        self.csv_reader = csv.reader(self.csv_io.readlines(), delimiter=";", quotechar='"')

    def check_nb_columns(self):
        """Fonction qui check si on a le nombre de colonnes suffisantes"""
        self.get_csv_reader()
        file_nb_cols = len(next(self.csv_reader))
        demand_nb_cols = len(self.columns_dict.keys())

        if demand_nb_cols > file_nb_cols:
            raise IterFileToInsertError(
                "Les éléments n'ont pu être importés : le fichier comporte %s colonne%s, "
                "il est exigé au moins %s colonne%s"
                % (
                    file_nb_cols,
                    "s" if file_nb_cols > 1 else "",
                    demand_nb_cols,
                    "s" if demand_nb_cols > 1 else "",
                )
            )

    @staticmethod
    def get_check_columns(header_set_on_demand, header_set_in_file):
        """Check des colonnes, si invalid alors on raise une erreur
            :param header_set_on_demand: set des colonnes demandées
            :param header_set_in_file: set des colonnes de la bd
        """
        if not header_set_on_demand.issubset(header_set_in_file):
            raise IterFileToInsertError(
                "Les éléments n'ont pu être importés, "
                "le fichier ne contient pas les colonnes demandées : %s"
                % (
                    ", ".join(
                        f'"{value}"'
                        for value in header_set_on_demand.difference(header_set_in_file)
                    ),
                )
            )

    def get_columns_rows_if_columns_none(self):
        """Si l'on ne demande pas de colonnes"""
        rows = [key for key, _ in enumerate(self.columns_dict.items())]
        self.get_csv_reader()

        return rows

    def get_columns_rows_if_columns_name(self):
        """si l'on a toutes les colonnes demandées dans le fichier"""
        self.get_csv_reader()
        header_list_in_file = next(self.csv_reader)
        header_set_in_file = set(header_list_in_file)
        header_set_on_demand = set(self.columns_dict.values())
        self.get_check_columns(header_set_on_demand, header_set_in_file)
        # On va maintenant rechercher la position des colonnes du fichier
        columns, rows = [], []

        for key, value in self.columns_dict.items():
            columns.append(key)
            rows.append(header_list_in_file.index(value))

        return columns, rows

    def get_header(self):
        """Fonction qui récupère les index des colonnes du fichier à garder"""
        self.check_nb_columns()
        columns_type = list(self.columns_dict.values())[0]

        # Si l'on a des nom de colonnes à récupérer
        if isinstance(columns_type, (str,)):
            return self.get_columns_rows_if_columns_name()

        columns = list(self.columns_dict.keys())

        # Si l'on a pas d'entêtes
        if columns_type is None:
            return columns, self.get_columns_rows_if_columns_none()

        # Si l'on a des numéros de colonnes à récupérer
        self.get_csv_reader()
        return columns, list(self.columns_dict.values())

    def get_chunk_dict_rows(self):
        """Itérateur des lignes du fichier retraité
            :return: itérateur des lignes
        """
        columns, rows = self.get_header()

        # on renvoie pour chaque ligne du fichier le dictionnaire de données
        for line in self.csv_reader:
            yield dict(zip(columns, itemgetter(*rows)(line)))

    def get_chunk_io(self, chunk_io: io.StringIO):
        """Renvoie le fichier StringIO avec les bonnes colonnes"""
        _, rows = self.get_header()

        # on renvoie pour chaque ligne du fichier le dictionnaire de données
        for line in self.csv_reader:
            chunk_io.write(";".join(itemgetter(*rows)(line)) + "\n")

    def __call__(self):
        """Itérateur des lignes du fichier retraitées à l'appel de la classe, en dictionnaire
            :return: itérateur des lignes
        """
        yield from self.get_chunk_dict_rows()


class Validation(IterFileToInsert):
    """class pour la validation et l'insertion"""

    def __init__(self, validator, map_line=None, insertion="insert_or_none", *args, **kwargs):
        """
            :param validator: Validateur pour le fichier, le validateur doit avoir les méthodes :
                                - is_valid() pour insertion en base
                                - save() pour insertion en base
                                - une property errors qui renvoie les erreurs
            :param map_line: fonction de transformation des données avant validation,
            cela peut être un tuple ou une liste avec les numéros de colonnes
            ou un dictionnaire avec le nom des colonnes
            :param insertion: "insert": insertion hors erreurs
                              "insert_or_none": insertion si pas d'erreurs
                              "upsert": upsert
                              "upsert_or_none": upsert si pas d'erreur
            :param args: arguments de l'héritage
            :param kwargs: dict des arguments de l'héritage
        """
        super().__init__(*args, **kwargs)
        self.validator = validator
        self.map_line = map_line
        self.map_line_dict = isinstance(self.map_line, (dict,))
        self.errors = []

    def get_errors(self, num_ligne, errors):
        """Rempli la list error de l'instance"""
        error_dict = {f"ligne n°{num_ligne:>6} : ": []}

        for champ, details in errors.items():
            error, *_ = details
            error_dict[f"ligne n°{num_ligne:>6} : "].append({champ: str(error)})

        self.errors.append(error_dict)

    def get_transform_list_line(self, line):
        """Fonction qui va gérer les remplacements à faire à partir d'une liste"""
        for index, func in enumerate(self.map_line):
            line[index] = func(line[index])

    def get_transform_dict_line(self, line):
        """Fonction qui va gérer les remplacements à faire à partir d'un dictionnaire"""
        for key, func in self.map_line.items():
            line[key] = func(line.get(key))

    def set_transform_line(self, line):
        """Fonction qui applique la transformation en place de la ligne à tranformer"""
        if self.map_line_dict:
            self.get_transform_dict_line(line)
        else:
            self.get_transform_list_line(line)

    def iter_validation(self):
        """Parcours les éléments du fichier à valider, puis insère en base si les données
        sont bonnes, ou ajoute les erreurs par lignes
        """
        for i, data_dict in enumerate(self.get_chunk_dict_rows(), 1):
            validator = self.validator(data=data_dict)

            if validator.is_valid():
                validator.save()
            else:
                self.get_errors(i, validator.errors)

    def validate(self):
        """Validation des lignes du fichier, sauvegarde et renvoi des erreurs si il y en a eu"""
        self.iter_validation()


def main():
    """TESTS"""
    csv_dict = {
        "delimiter": ";",
        "lineterminator": "\n",
        "quoting": csv.QUOTE_ALL,
        "quotechar": '"',
    }

    csv_file = Path(r"E:\SENSEE\test_colonnes_fichier.csv")
    excel_file = Path(r"E:\SENSEE\test_colonnes_fichier.xlsx")

    # dict_01 = {"col1": "col1", "col2": "col2", "col4": "col4"}
    # # =============================================================
    # print("\ndict_01 - csv =====================================================================")
    # ite = IterFileToInsert(csv_file, dict_01, header_line=0)
    # for i, line in enumerate(ite.get_chunk_dict_rows(), 1):
    #     print("Ligne N°", i, " : ", line)
    # # =============================================================
    # print("\ndict_01 - excel ===================================================================")
    # ite = IterFileToInsert(excel_file, dict_01, header_line=0)
    # for i, line in enumerate(ite.get_chunk_dict_rows(), 1):
    #     print("Ligne N°", i, " : ", line)
    #
    # dict_02 = {"col1": None, "col2": None, "col3": None, "col4": None}
    # # =============================================================
    # print("\ndict_02 - csv =====================================================================")
    # ite = IterFileToInsert(csv_file, dict_02, header_line=0)
    # for i, line in enumerate(ite.get_chunk_dict_rows(), 1):
    #     print("Ligne N°", i, " : ", line)
    # # =============================================================
    # print("\ndict_02 - excel ===================================================================")
    # ite = IterFileToInsert(excel_file, dict_02, header_line=0)
    # for i, line in enumerate(ite.get_chunk_dict_rows(), 1):
    #     print("Ligne N°", i, " : ", line)

    dict_03 = {"col3": 2, "col1": 0, "col2": 1, "col4": 3}
    # # =============================================================
    # print("\ndict_03 - csv =====================================================================")
    # ite = IterFileToInsert(csv_file, dict_03, header_line=3)
    # for i, line in enumerate(ite.get_chunk_dict_rows(), 1):
    #     print("Ligne N°", i, " : ", line)
    # # =============================================================
    # print("\ndict_03 - excel ===================================================================")
    # ite = IterFileToInsert(excel_file, dict_03, header_line=3, mode_csv_dict=csv_dict)
    # for i, line in enumerate(ite.get_chunk_dict_rows(), 1):
    #     print("Ligne N°", i, " : ", line)
    # =============================================================
    print("\ndict_03 - stringIO ==================================================================")
    ite = Validation(
        file_to_iter=excel_file,
        columns_dict=dict_03,
        header_line=3,
        mode_csv_dict=csv_dict,
        map_line=((0, int),),
    )
    file_io = io.StringIO()
    ite.get_chunk_io(file_io)
    file_io.seek(0)
    print(file_io.read())
    file_io.close()


if __name__ == "__main__":
    main()
