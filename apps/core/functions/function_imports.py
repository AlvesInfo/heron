# pylint: disable=E0401
"""Module pour validation de fichiers à intégrer en base de donnée

Commentaire:

created at: 2021-10-30
created by: Paulo ALVES

modified at: 2021-10-30
modified by: Paulo ALVES
"""
import io
import logging
from pathlib import Path
from typing import Dict
import csv
from operator import itemgetter

from chardet.universaldetector import UniversalDetector
import pandas as pd

IMPORT_LOGGER = logging.getLogger("imports")


class ExcelToCsvError(Exception):
    """Exception niveau module"""


class EncodingError(Exception):
    """Exception sniff encodig"""


class ExcelToCsvFileError(Exception):
    """Exception transformation excel"""


class CsvFileToStringIoError(Exception):
    """Exception envoi du fichier dans un StringIO"""


class IterFileToInsertError(Exception):
    """Gestion d'erreur d'itération d'un fichier à insérer"""


class ValidationError(Exception):
    """Gestion d'erreur de forms_validation"""


def encoding_detect(path_file: Path):
    """Fonction qui renvoie"""
    try:
        detector = UniversalDetector()

        with open(path_file, "rb") as file:
            for line in file:
                detector.feed(line)

                if detector.done:
                    break

            detector.close()

    except Exception as error:
        raise EncodingError(f"encoding_detect : {path_file.name !r}") from error

    return detector.result["encoding"]


def excel_file_to_csv_string_io(excel_file: Path, string_io_file, header=True):
    """Fonction qui transforme un fichier excel en csv
    :param excel_file: string_io excel à passer en csv
    :param string_io_file: string_io en csv
    :param header: entête
    :return: fichier excel en csv
    """
    success = True

    try:
        data = pd.read_excel(excel_file.resolve(), engine="openpyxl")
        data.to_csv(
            string_io_file,
            sep=";",
            header=header,
            index=False,
            line_terminator="\n",
            quoting=csv.QUOTE_ALL,
            encoding="utf8",
        )
        string_io_file.seek(0)

    except ValueError as error:
        raise ExcelToCsvFileError(
            f"Impossible de déterminer si le fichier {excel_file.name!r}, est un fichier excel"
        ) from error

    return success


def file_to_csv_string_io(file: Path, string_io_file: io.StringIO):
    """Fonction qui transforme un fichier en csv
    :param file: fichier csv, instance de Path (pathlib)
    :param string_io_file: fichier de type io.StringIO
    :return: string_io au format csv
    """
    try:
        encoding = encoding_detect(file)

        with file.open("r", encoding=encoding, errors="replace") as csv_file:
            string_io_file.write(csv_file.read())
            string_io_file.seek(0)

    except Exception as error:
        raise CsvFileToStringIoError(f"file_to_csv_string_io : {file.name!r}") from error


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
        """Instanciation de la classe
        :param file_to_iter: fichier de type Path à insérer
        :param columns_dict: Plusieurs choix possibles :
                        - pour récupérer le nombre de colonnes dans l'ordre du fichier
                            {"db_col_1" : None, "db_col_2" : None, ..., }

                        - pour récupérer seulement les colonnes souhaitées par leur nom
                            {"db_col_1" : "file_col_x", "db_col_2" : "file_col_a", ..., }

                        - pour récupérer seulement les colonnes souhaitées par leur index
                            (index commence à 0)
                            {"db_col_1" : 3, "db_col" : 0, ..., }

        :param header_line: line du header commence à 1
        :param mode_csv_dict: dictionnaire des caractéristiques du fichier
                {
                    "delimiter" : séparateur du fichier, par défaut ";"
                    "lineterminator": séparateur de lignes du fichier par défaut "\n"
                    "quoting": type de quoting par défaut csv.QUOTE_NONNUMERIC
                    "quotechar": le caractère de quoting par défaut '"'
                }
        """
        self.file_to_iter = file_to_iter
        self.csv_io = io.StringIO()
        self.columns_dict = columns_dict
        self.header_line = header_line if header_line is None else header_line - 1
        self.first_line = 0 if header_line is None else header_line
        self.mode_csv_dict = mode_csv_dict or {}
        self.csv_reader = csv.reader(
            self.csv_io.readlines(),
            delimiter=self.mode_csv_dict.get("delimiter", ";"),
            quotechar=self.mode_csv_dict.get("quotechar", '"'),
            lineterminator=self.mode_csv_dict.get("lineterminator", "\n"),
            quoting=self.mode_csv_dict.get("quoting", csv.QUOTE_ALL),
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
        envoyé est un fichier à plat ou un fichier Excel
        """
        try:
            if self.file_to_iter.suffix in {".xls", ".xlsx"}:
                excel_file_to_csv_string_io(self.file_to_iter, self.csv_io)
            else:
                file_to_csv_string_io(self.file_to_iter, self.csv_io)

        except Exception as error:
            raise ExcelToCsvError(
                "une erreur dans la transformation du fichier en csv StringIO"
            ) from error

    def close_buffer(self):
        """Fonction de fermeture du buffer io.StringIO"""
        if not self.csv_io.closed:
            self.csv_io.close()

    def seek_in_line_position(self, row_index):
        """Placement sur la première ligne demandée
        :param row_index: première ligne ou se placer
        """
        self.csv_io.seek(row_index or 0)
        self.csv_io.seek(row_index or 0)

    def get_csv_reader(self):
        """Instancie csv reader"""
        self.seek_in_line_position(self.header_line or 0)
        self.csv_reader = csv.reader(self.csv_io.readlines(), delimiter=";", quotechar='"')

    def check_nb_columns(self):
        """Fonction qui check si on a le nombre de colonnes suffisantes"""
        self.get_csv_reader()
        file_nb_cols = len(next(self.csv_reader))
        demand_nb_cols = len(self.columns_dict.keys())

        if demand_nb_cols > file_nb_cols:
            raise IterFileToInsertError(
                f"Les éléments n'ont pu être importés : le fichier comporte {file_nb_cols} "
                f"colonne{'s' if file_nb_cols > 1 else ''}, "
                f"il est exigé au moins {demand_nb_cols} "
                f"colonne{'s' if demand_nb_cols > 1 else ''}"
            )

    @staticmethod
    def get_check_columns(header_set_on_demand, header_set_in_file):
        """Check des colonnes, si invalid alors on raise une erreur
        :param header_set_on_demand: set des colonnes demandées
        :param header_set_in_file: set des colonnes de la bd
        """
        if not header_set_on_demand.issubset(header_set_in_file):
            values = ", ".join(
                f'"{value}"' for value in header_set_on_demand.difference(header_set_in_file)
            )
            raise IterFileToInsertError(
                "Les éléments n'ont pu être importés, "
                f"le fichier ne contient pas les colonnes demandées : {values}"
            )

    def get_columns_rows_if_columns_none(self):
        """Si l'on ne demande pas de colonnes"""
        rows = [key for key, _ in enumerate(self.columns_dict.items())]
        self.get_csv_reader()

        return rows

    def get_columns_rows_if_columns_name(self):
        """Si l'on a toutes les colonnes demandées dans le fichier"""
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

        # Si l'on a des noms de colonnes à récupérer
        if isinstance(columns_type, (str,)):
            return self.get_columns_rows_if_columns_name()

        columns = list(self.columns_dict.keys())

        # Si l'on n'a pas d'entêtes
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


class ModelFormInsertion(IterFileToInsert):
    """class pour la validation et l'insertion"""

    def __init__(self, validator, *args, map_line=None, uniques=(), **kwargs):
        """
        :param validator: Validateur pour le fichier, le validateur doit avoir les méthodes :
                            - is_valid() pour validation
                            - save() pour insertion en base
                            - une property errors qui renvoie les erreurs
                            si on a unique avec des noms de champs alors on va update ou create
        :param map_line: fonction de transformation des données avant validation,
        cela peut être un tuple ou une liste avec les numéros de colonnes
        ou un dictionnaire avec le nom des colonnes
        :param uniques: si l'on veut faire un update on envoie les champs uniques
        :param args: arguments de l'héritage
        :param kwargs: dict des arguments de l'héritage
        """
        super().__init__(*args, **kwargs)
        self.validator = validator
        self.map_line = map_line
        self.uniques = uniques
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
        sont bonnes ou ajoute les erreurs par lignes
        """
        for i, data_dict in enumerate(self.get_chunk_dict_rows(), 1):
            # Si on envoie les champs uniques alors on update
            if self.uniques:
                form = self.validator(data=data_dict)
                form.is_valid()
                attrs_instance = {
                    key: value
                    for key, value in {
                        key: value
                        for key, value in form.clean().items()
                        if key in self.uniques
                    }.items()
                }
                model = self.validator._meta.model
                try:
                    instance = model.objects.get(**attrs_instance)
                    validator = self.validator(data=data_dict, instance=instance)
                except model.DoesNotExist:
                    validator = self.validator(data=data_dict)
            else:
                validator = self.validator(data=data_dict)

            if validator.is_valid():
                validator.save()
            else:
                self.get_errors(i, validator.errors)

    def validate(self):
        """Validation des lignes du fichier, sauvegarde et renvoi des erreurs s'il y en a eu"""
        self.iter_validation()


def main():
    """Fonction main pour lancement dans __main__"""
    print(__name__)


if __name__ == "__main__":
    main()
