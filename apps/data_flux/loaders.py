# pylint: disable=E0401
"""Module de loaders pour traitements des flux à intégrer en BDD
Flux implémentés :
    File loader
    API loader

Commentaire:

created at: 2021-10-30
created by: Paulo ALVES

modified at: 2021-10-30
modified by: Paulo ALVES
"""
import io
import logging
from pathlib import Path
from typing import Dict, Any
import csv
from operator import itemgetter

from chardet.universaldetector import UniversalDetector
import pandas as pd

IMPORT_LOGGER = logging.getLogger("imports")


class EncodingError(Exception):
    """Exception sniff encodig"""


class ExcelToCsvError(Exception):
    """Exception transformation excel"""


class ExcelToCsvFileError(Exception):
    """Exception transformation excel"""


class CsvFileToStringIoError(Exception):
    """Exception envoi du fichier dans un StringIO"""


class IterFileToInsertError(Exception):
    """Gestion d'erreur d'itération d'un fichier à insérer"""


class GetAddDictError(IterFileToInsertError):
    """Gestion d'erreur d'itération d'un fichier à insérer"""


class ValidationError(Exception):
    """Gestion d'erreur de validation"""


def encoding_detect(path_file):
    """Fonction qui renvoi l'encoding le plus probable du fichier passé en paramètre"""
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
        # noinspection PyArgumentList
        data = pd.read_excel(excel_file.resolve(), engine="openpyxl")
        data.to_csv(
            string_io_file,
            sep=";",
            header=header,
            index=False,
            line_terminator="\n",
            quoting=csv.QUOTE_NONNUMERIC,
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


class CleanDataLoader:
    """Template Laader de data, après les avoir cleaner et modififiées à la vollée"""

    def __init__(
        self,
        source: Any,
        columns_dict: Dict,
        first_line: int = 1,
        params_dict: Dict = None,
    ):
        """Initialisation de la class"""
        self.source = source
        self.source = source
        self.columns_dict = columns_dict
        self.first_line = first_line
        self.params_dict = params_dict or {}

    def __enter__(self):
        """Pré context manager"""
        return self

    def open(self, flux_params_dict: Dict = None):
        """Méthode d'ouverture du flux de données"""
        raise NotImplementedError

    def read(self, all_lines: bool = False):
        """Méthode de lecture du flux de données au format io.StringIO"""
        raise NotImplementedError

    def read_list(self, all_lines: bool = False):
        """Méthode de lecture du flux de données, sous forme d'un tableau (list en python)"""
        raise NotImplementedError

    def read_dict(self, all_lines: bool = False):
        """Méthode de lecture du flux de données sous forme d'un dictionnaire"""
        raise NotImplementedError

    def close(self):
        """Méthode de fermeture du flux de données"""
        raise NotImplementedError

    def load(self, read_methode: str = "data", all_lines: bool = False):
        """
        Générateur du flux de données
        :param read_methode: data pour un flux texte et data_dict pour un flux de dictionnaire
        :param all_lines:    Si dans le flux il y a des lignes vides :
                                all_lines = False -> shorcut l'itération des lignes vides
                                all_lines = True -> iterre même sur des lignes des lignes vides
        :return:
        """
        self.open(self.params_dict)

        if read_methode == "data":
            yield from self.read(all_lines)

        if read_methode == "data_dict":
            yield from self.read_dict(all_lines)

        self.close()

    def __exit__(self, tipe, value, traceback):
        """Post context manager, pour fermer la source de données
        :param tipe: valeur du type venant de la sortie de la classe
        :param value: valeur venant de la sortie de la classe
        :param traceback: traceback sur une éventuele exception de la sortie de la classe
        """
        self.close()


class FileLoader(CleanDataLoader):
    """
    Fileloader pour importer un fichier de type Path et le cleanner en vue d'une insertion en base
    """

    def __init__(
        self,
        source: Any,
        columns_dict: Dict,
        first_line: int = 1,
        params_dict: Dict = None,
    ):
        """
        :param source:          Fichier source à transfomer
        :param columns_dict:    Plusieurs choix possibles pour :
                                - Récupérer le nombre de colonnes dans l'ordre du fichier
                                    {"db_col_1" : None, "db_col_2" : None, ..., }

                                - Récupérer seulement les colonnes souhaitées par leur nom
                                    {"db_col_1" : "file_col_x", "db_col_2" : "file_col_a", ...}

                                - Récupérer seulement les colonnes souhaitées par leur index
                                    (index commence à 0)
                                    {"db_col_1" : 3, "db_col" : 0, ..., }

        :param first_line:      Première ligne du flux de données commence à 1 par defaut

        :param params_dict:     Dictionnaire des paramètres à appliquer au flux de donneés
                                params_dict = {

                                    # attribus du paramétrage csv
                                    "delimiter" : séparateur du fichier, par défaut ";"
                                    "lineterminator": Passage à la ligne par défaut "\n"
                                    "quoting": type de quoting par défaut csv.QUOTE_NONNUMERIC
                                    "quotechar": le caractère de quoting par défaut '"'
                                    "escapechar": le caractère de quoting par défaut '"'

                                    # Lignes non souhaitées par n° Colonne (index commence à 1)
                                    "exclude_rows_dict": {
                                        "N°colonne": "texte à rechercher",
                                        "N°colonne": "texte à rechercher",
                                        "N°colonne": "texte à rechercher",
                                    },

                                    # Ajout de colonnes à la vollée, pour
                                    # par exemple rajouter un uuid, created_date, ...
                                    # Si l'on veut appliquer une fonction à chaque ligne,
                                    # alors on passe un tuple :
                                    # (référence à la fonction à appliquer, dict des attributs)
                                    "add_fields_dict": {
                                        "uuid_identification": (uuid.uuid4, {}),
                                        "created_date": datetime.isoformat,
                                        "modified_date": datetime.isoformat,
                                }
        """
        super().__init__(source, columns_dict, first_line, params_dict)

        self.csv_io = io.StringIO()
        self._set_io()
        self.csv_io.seek(0)
        self.first_line = 0

        # Pour connaître la position (seek) à partir de laquelle récupérer les lignes du fichier
        for i, line in enumerate(self.csv_io):
            if i == (first_line - 1):
                break
            self.first_line += len(line)

        self._get_csv_reader()

    def open(self, flux_params_dict: Dict = None):
        """
        Surcharge de la méthode open, mais nous n'en avons pas besoins
        """

    def _set_io(self):
        """
        Ecriture des données brutes dans le fichier self.csv_io de type io.StringIO de l'instance.
        Il y aura un prétraitement si le fichier envoyé est un fichier à plat ou un fichier Excel
        """
        try:

            if self.source.suffix in {".xls", ".xlsx"}:
                excel_file_to_csv_string_io(self.source, self.csv_io)
            else:
                file_to_csv_string_io(self.source, self.csv_io)

        except Exception as error:
            raise ExcelToCsvError(
                f"une erreur dans la transformation du fichier {self.source.name!r} "
                "en csv StringIO"
            ) from error

    def _get_csv_reader(self):
        """Le csv.reader étant un générateur on initialise self.csv_reader à chaque fois"""
        self.csv_io.seek(self.first_line)
        self.csv_reader = csv.reader(
            self.csv_io,
            delimiter=self.params_dict.get("delimiter", ";"),
            quotechar=self.params_dict.get("quotechar", '"'),
            lineterminator=self.params_dict.get("lineterminator", "\n"),
            quoting=self.params_dict.get("quoting", csv.QUOTE_ALL),
        )

    def _check_nb_columns(self):
        """Check si on a le nombre de colonnes suffisantes"""
        self._get_csv_reader()
        file_nb_cols = len(next(self.csv_reader))
        demand_nb_cols = len(self.columns_dict)

        if demand_nb_cols > file_nb_cols:
            raise IterFileToInsertError(
                f"Erreur sur les colonnes : le fichier comporte {file_nb_cols} "
                f"colonne{'s' if file_nb_cols > 1 else ''}, "
                f"il est exigé au moins {demand_nb_cols} "
                f"colonne{'s' if demand_nb_cols > 1 else ''}"
            )

    @staticmethod
    def _get_check_columns(header_on_demand, header_in_file):
        """Check des colonnes, si invalid alors on raise une erreur
        :param header_on_demand: set des colonnes demandées
        :param header_in_file: set des colonnes de la bd
        """
        if not set(header_on_demand).issubset(set(header_in_file)):
            values = ", ".join(
                f'"{value}"' for value in set(header_on_demand).difference(set(header_in_file))
            )
            raise IterFileToInsertError(
                "Erreur sur les colonnes : "
                f"le fichier ne contient pas les colonnes demandées suivantes : {values}\n"
                f"le fichier contient les colonnes suivantes : {', '.join(header_in_file)}"
            )

    def get_positons_for_none_columns(self):
        """
        Position des colonnes demandées dans l'attribut d'instance self.columns_dict,
        dans la même position que le fichier
        :return: Liste des positions des colonnes
        """
        postion_list = list(range(len(self.columns_dict)))

        return postion_list

    def get_positions_if_columns_named(self):
        """
        Position des colonnes nommées dans l'attribut d'instance self.columns_dict
        :return: Liste des positions des colonnes
        """
        header_list_in_file = next(self.csv_reader)
        header_on_demand = list(self.columns_dict.values())
        self._get_check_columns(header_on_demand, header_list_in_file)
        postion_list = [header_list_in_file.index(value) for value in self.columns_dict.values()]

        return postion_list

    def get_header(self):
        """
        :return: Liste des positions des colonnes
        """
        self._check_nb_columns()
        self._get_csv_reader()
        columns_type = list(self.columns_dict.values())[0]

        # Si l'on a des noms de colonnes du fichier à récupérer
        if isinstance(columns_type, (str,)):
            return self.get_positions_if_columns_named()

        # Dans la position des colonnes du fichier
        if columns_type is None:
            return self.get_positons_for_none_columns()

        # Si l'on a des numéros de colonnes à récupérer
        return list(self.columns_dict.values())

    @property
    def get_add_dict(self):
        """
        :return: Dictionnaire des noms d'attributs et valeurs à ajouter à la vollée dans le fichier
        """
        try:
            add_dict = {
                key: value[0](**value[1]) if isinstance(value, (tuple,)) else value
                for key, value in self.params_dict.get("add_fields_dict", {}).items()
            }
        except IndexError as error:
            raise GetAddDictError(
                "La méthode get_add_dict a besoins d'un tuple de 2 élements"
            ) from error

        return add_dict

    @property
    def get_add_values(self):
        """
        :return: Liste des valeurs à ajouter à la vollée dans le fichier
        """
        add_list = [
            value[0](**value[1]) if isinstance(value, (tuple,)) else value
            for value in self.params_dict.get("add_fields_dict", {}).values()
        ]
        return add_list

    def read(self, all_lines=False):
        """
        Méthode de lecture du flux de donées au format io.StringIO
        :param all_lines:   Si dans le fichier il y a des lignes vides :
                                all_lines = False -> shorcut l'itération des lignes vides
                                all_lines = True -> iterre même sur des lignes des lignes vides
        """
        postion_list = self.get_header()

        # on renvoie pour chaque ligne du fichier les données au format csv
        for line in self.csv_reader:
            if (not line and not all_lines) or any(
                str(value).strip().upper() in str(line[index - 1]).strip().upper()
                for index, value in self.params_dict.get("exclude_rows_dict", {}).items()
            ):
                continue

            if self.params_dict.get("add_fields_dict", {}):
                yield f'{self.params_dict.get("delimiter", ";")}'.join(
                    [
                        f'"{str(value)}"'
                        for value in list(itemgetter(*postion_list)(line)) + self.get_add_values
                    ]
                )
            else:
                yield f'{self.params_dict.get("delimiter", ";")}'.join(
                    [f'"{str(value)}"' for value in itemgetter(*postion_list)(line)]
                )

    def read_list(self, all_lines: bool = False):
        """
        Méthode de lecture du flux de données, sous forme d'un tableau (list en python)
        :param all_lines:       Si dans le fichier il y a des lignes vides :
                                    all_lines = False -> shorcut l'itération des lignes vides
                                    all_lines = True -> iterre même sur des lignes des lignes vides
        """
        postion_list = self.get_header()

        # on renvoie pour chaque ligne du fichier les données dans un tableau, une liste
        for line in self.csv_reader:
            if (not line and not all_lines) or any(
                str(value).strip().upper() in str(line[index - 1]).strip().upper()
                for index, value in self.params_dict.get("exclude_rows_dict", {}).items()
            ):
                continue

            if self.params_dict.get("add_fields_dict", {}):
                yield list(itemgetter(*postion_list)(line)) + self.get_add_values
            else:
                yield list(itemgetter(*postion_list)(line))

    def read_dict(self, all_lines=False):
        """
        Générateurs du dictionaire des lignes de l'io.StringIO, avec le nom des colonnes à récupérer
        :param all_lines: si dans le fichier il y a des lignes vides
                            all_lines=False, shorcut l'itération des lignes vides
                            all_lines=True, iterre même sur des lignes des lignes vides
        :return: Générateur des lignes du fichier retraitées sous forme de dictionnaire key: value
        """
        postion_list = self.get_header()

        # on renvoie pour chaque ligne du fichier le dictionnaire de données
        for line in self.csv_reader:
            if (not line and not all_lines) or any(
                str(value).strip().upper() in str(line[index - 1]).strip().upper()
                for index, value in self.params_dict.get("exclude_rows_dict", {}).items()
            ):
                continue

            if self.params_dict.get("add_fields_dict", {}):
                yield {
                    **dict(zip(list(self.columns_dict), itemgetter(*postion_list)(line))),
                    **self.get_add_dict,
                }
            else:
                yield dict(zip(list(self.columns_dict), itemgetter(*postion_list)(line)))

    def close(self):
        """Fermeture du buffer io.StringIO"""
        if not self.csv_io.closed:
            self.csv_io.close()


class ApiJsonLoader(CleanDataLoader):
    """
    ApiLoader pour importer un flux de données par API au format json
    et le cleanner en vue d'une insertion en base
    """

    # TODO : Finaliser ApiJsonLoader
    def __init__(
        self,
        source: Any,
        columns_dict: Dict,
        first_line: int = 1,
        params_dict: Dict = None,
    ):
        """
        :param source:          Fichier source à transfomer
        :param columns_dict:    Plusieurs choix possibles pour :
                                - Récupérer le nombre de colonnes dans l'ordre du fichier
                                    {"db_col_1" : None, "db_col_2" : None, ..., }

                                - Récupérer seulement les colonnes souhaitées par leur nom
                                    {"db_col_1" : "file_col_x", "db_col_2" : "file_col_a", ...}

                                - Récupérer seulement les colonnes souhaitées par leur index
                                    (index commence à 0)
                                    {"db_col_1" : 3, "db_col" : 0, ..., }

        :param first_line:      Première ligne du flux de données commence à 1 par defaut

        :param params_dict:     Dictionnaire des paramètres à appliquer au flux de donneés
                                params_dict = {

                                    # attribus du paramétrage csv
                                    "delimiter" : séparateur du fichier, par défaut ";"
                                    "lineterminator": Passage à la ligne par défaut "\n"
                                    "quoting": type de quoting par défaut csv.QUOTE_NONNUMERIC
                                    "quotechar": le caractère de quoting par défaut '"'
                                    "escapechar": le caractère de quoting par défaut '"'

                                    # Lignes non souhaitées par n° Colonne (index commence à 1)
                                    "exclude_rows_dict": {
                                        "N°colonne": "texte à rechercher",
                                        "N°colonne": "texte à rechercher",
                                        "N°colonne": "texte à rechercher",
                                    },

                                    # Ajout de colonnes à la vollée, pour
                                    # par exemple rajouter un uuid, created_date, ...
                                    # Si l'on veut appliquer une fonction à chaque ligne,
                                    # alors on passe un tuple :
                                    # (référence à la fonction à appliquer, dict des attributs)
                                    "add_fields_dict": {
                                        "uuid_identification": (uuid.uuid4, {}),
                                        "created_date": datetime.isoformat,
                                        "modified_date": datetime.isoformat,
                                }
        """
        super().__init__(source, columns_dict, first_line, params_dict)
        self.csv_io = io.StringIO()
        self._set_io()
        self.csv_io.seek(0)

    def open(self, flux_params_dict: Dict = None):
        """
        Surcharge de la méthode open, mais nous n'en avons pas besoins
        """

    def _set_io(self):
        """
        Ecriture des données brutes dans le fichier self.csv_io de type io.StringIO de l'instance.
        """

    def _get_csv_reader(self):
        """Instanciation l'attribut d'instance self.csv_reader"""

    def read(self, all_lines=False):
        """
        Méthode de lecture du flux de donées au format io.StringIO
        :param all_lines:       Si dans le fichier il y a des lignes vides :
                                    all_lines = False -> shorcut l'itération des lignes vides
                                    all_lines = True -> iterre même sur des lignes des lignes vides
        """
        yield "ApiLodaer non finalisée"

    def read_list(self, all_lines: bool = False):
        """
        Méthode de lecture du flux de données, sous forme d'un tableau (list en python)
        :param all_lines:       Si dans le fichier il y a des lignes vides :
                                    all_lines = False -> shorcut l'itération des lignes vides
                                    all_lines = True -> iterre même sur des lignes des lignes vides
        """
        yield "ApiLodaer non finalisée"

    def read_dict(self, all_lines=False):
        """
        Générateurs du dictionaire des lignes de l'io.StringIO, avec le nom des colonnes à récupérer
        :param all_lines: si dans le fichier il y a des lignes vides
                            all_lines=False, shorcut l'itération des lignes vides
                            all_lines=True, iterre même sur des lignes des lignes vides
        :return: Générateur des lignes du fichier retraitées sous forme de dictionnaire key: value
        """
        yield {"message": "ApiLodaer non finalisée"}

    def close(self):
        """Fermeture du buffer io.StringIO"""
        if not self.csv_io.closed:
            self.csv_io.close()


class ApiXmlLoader(CleanDataLoader):
    """
    ApiXmlLoader pour importer un flux de données par API au format xml
    et le cleanner en vue d'une insertion en base
    """

    # TODO : Finaliser ApiXmlLoader
    def __init__(
        self,
        source: Any,
        columns_dict: Dict,
        first_line: int = 1,
        params_dict: Dict = None,
    ):
        """
        :param source:          Fichier source à transfomer
        :param columns_dict:    Plusieurs choix possibles pour :
                                - Récupérer le nombre de colonnes dans l'ordre du fichier
                                    {"db_col_1" : None, "db_col_2" : None, ..., }

                                - Récupérer seulement les colonnes souhaitées par leur nom
                                    {"db_col_1" : "file_col_x", "db_col_2" : "file_col_a", ...}

                                - Récupérer seulement les colonnes souhaitées par leur index
                                    (index commence à 0)
                                    {"db_col_1" : 3, "db_col" : 0, ..., }

        :param first_line:      Première ligne du flux de données commence à 1 par defaut

        :param params_dict:     Dictionnaire des paramètres à appliquer au flux de donneés
                                params_dict = {

                                    # attribus du paramétrage csv
                                    "delimiter" : séparateur du fichier, par défaut ";"
                                    "lineterminator": Passage à la ligne par défaut "\n"
                                    "quoting": type de quoting par défaut csv.QUOTE_NONNUMERIC
                                    "quotechar": le caractère de quoting par défaut '"'
                                    "escapechar": le caractère de quoting par défaut '"'

                                    # Lignes non souhaitées par n° Colonne (index commence à 1)
                                    "exclude_rows_dict": {
                                        "N°colonne": "texte à rechercher",
                                        "N°colonne": "texte à rechercher",
                                        "N°colonne": "texte à rechercher",
                                    },

                                    # Ajout de colonnes à la vollée, pour
                                    # par exemple rajouter un uuid, created_date, ...
                                    # Si l'on veut appliquer une fonction à chaque ligne,
                                    # alors on passe un tuple :
                                    # (référence à la fonction à appliquer, dict des attributs)
                                    "add_fields_dict": {
                                        "uuid_identification": (uuid.uuid4, {}),
                                        "created_date": datetime.isoformat,
                                        "modified_date": datetime.isoformat,
                                }
        """
        super().__init__(source, columns_dict, first_line, params_dict)
        self.csv_io = io.StringIO()
        self._set_io()
        self.csv_io.seek(0)

    def open(self, flux_params_dict: Dict = None):
        """
        Surcharge de la méthode open, mais nous n'en avons pas besoins
        """

    def _set_io(self):
        """
        Ecriture des données brutes dans le fichier self.csv_io de type io.StringIO de l'instance.
        """

    def _get_csv_reader(self):
        """Instanciation l'attribut d'instance self.csv_reader"""

    def read(self, all_lines=False):
        """
        Méthode de lecture du flux de donées au format io.StringIO
        :param all_lines:       Si dans le fichier il y a des lignes vides :
                                    all_lines = False -> shorcut l'itération des lignes vides
                                    all_lines = True -> iterre même sur des lignes des lignes vides
        """
        yield "ApiLodaer non finalisée"

    def read_list(self, all_lines: bool = False):
        """
        Méthode de lecture du flux de données, sous forme d'un tableau (list en python)
        :param all_lines:       Si dans le fichier il y a des lignes vides :
                                    all_lines = False -> shorcut l'itération des lignes vides
                                    all_lines = True -> iterre même sur des lignes des lignes vides
        """
        yield "ApiLodaer non finalisée"

    def read_dict(self, all_lines=False):
        """
        Générateurs du dictionaire des lignes de l'io.StringIO, avec le nom des colonnes à récupérer
        :param all_lines: si dans le fichier il y a des lignes vides
                            all_lines=False, shorcut l'itération des lignes vides
                            all_lines=True, iterre même sur des lignes des lignes vides
        :return: Générateur des lignes du fichier retraitées sous forme de dictionnaire key: value
        """
        yield {"message": "ApiLodaer non finalisée"}

    def close(self):
        """Fermeture du buffer io.StringIO"""
        if not self.csv_io.closed:
            self.csv_io.close()
