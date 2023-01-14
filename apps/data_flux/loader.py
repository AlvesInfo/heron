# pylint: disable=E0401
"""
Module de loaders pour traitements des flux à intégrer en BDD, avec une pré-validation.
Ces flux renvoient des modes de consommation du flux, tels que :
    - read() : list des données
    - read_list() : dictionnaire de données
    - read_dict() : flux io.StringIO
    - load(data ou data_list ou data_dict) : yield l'un des flux ci-dessus.

Flux implémentés :
    FileLoader

Flux à Implémenter :
    ApiJsonLoader
    ApiXmlLoader

Pour l'implémentation FileLoader et dans le cas d'un fichier Excel comme source il sera transformé
en fichier csv, sinon le fichier source devra avoir une structure de csv.

Il faut utiliser le context manager afin de bien fermer les sources ou appeler la méthode close().

Commentaire:

created at: 2021-10-30
created by: Paulo ALVES

modified at: 2021-10-30
modified by: Paulo ALVES
"""
import io
import uuid
from typing import Dict, Any
import csv
from operator import itemgetter

from .utilities import excel_file_to_csv_string_io, file_to_csv_string_io
from .exceptions import (
    IterFileToInsertError,
    GetAddDictError,
    ExcelToCsvError,
    FileToCsvError,
    ExcelToCsvFileError,
    CsvFileToStringIoError,
)
from .models import Line, Error
from .opto_33_parser import EdiOpoto33Parser


class TemplateDataLoader:
    """Template Loader de data, après les avoir cleaner et modififiées à la vollée"""

    def __init__(
        self,
        source: Any,
        columns_dict: Dict,
        first_line: int = 1,
        params_dict: Dict = None,
    ):
        """Initialisation de la class"""
        self.source = source
        self.columns_dict = columns_dict
        self.first_line = first_line
        self.params_dict = params_dict or {}
        self.trace = params_dict.get("trace")

        # TODO : Implémenter une méthode pour les Traces du loader

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
        :param read_methode: Data pour un flux texte et data_dict pour un flux de dictionnaire
        :param all_lines:    Si dans le flux il y a des lignes vides :
                                all_lines = False -> shorcut l'itération des lignes vides
                                all_lines = True -> iterre même sur des lignes vides
        """
        self.open(self.params_dict)

        if read_methode == "data":
            yield from self.read(all_lines)
            return

        if read_methode == "data_list":
            yield from self.read(all_lines)
            return

        if read_methode == "data_dict":
            yield from self.read_dict(all_lines)
            return

        self.close()

    def trace_add_line_error(
        self, insertion_type: str = "Unknown", num_line: int = None, designation: str = None,
            error_dict=None
    ):
        """Ajoute d'une ligne sur la trace"""
        if error_dict is None:
            error_dict = {}

        insertion_dict = {
            "Create": "cette ligne à bien été créée",
            "Update": "cette ligne à bien été modifiée",
            "Errors": "Cette ligne à généré une erreur",
            "Passed": "Cette ligne n'a pas été traitée",
            "Unknown": "Cette ligne n'a pas été traitée",
        }
        uuid_line_identification = uuid.uuid4()
        line = Line.objects.create(
            **{
                "uuid_identification": uuid_line_identification,
                "trace": self.trace,
                "insertion_type": insertion_type,
                "num_line": num_line,
                "designation": designation or insertion_dict.get(insertion_type),
            }
        )
        line.save()

        error = Error.objects.create(**{**{"line": line}, **error_dict})
        error.save()

    def __exit__(self, tipe, value, traceback):
        """Post context manager, pour fermer la source de données
        :param tipe:      Valeur du type venant de la sortie de la classe
        :param value:     Valeur venant de la sortie de la classe
        :param traceback: Traceback sur une éventuele exception de la sortie de la classe
        """
        self.close()


class FileLoader(TemplateDataLoader):
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
                                    # model Django Trace pour fichiers trace
                                    "trace" : Trace

                                    # Encoding du fichier si on le connait
                                    "encoding": "ISO-8859-1"

                                    # attribus du paramétrage csv
                                    "delimiter" : séparateur du fichier, par défaut ";"
                                    "lineterminator": Passage à la ligne par défaut "\n"
                                    "quoting": type de quoting par défaut csv.QUOTE_MINIMAL
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
        """Surcharge de la méthode open, mais nous n'en avons pas besoins"""

    def _set_io(self):
        """
        Ecriture des données brutes dans le fichier self.csv_io de type io.StringIO de l'instance.
        Il y aura un prétraitement si le fichier envoyé est un fichier à plat ou un fichier Excel
        """
        try:
            if self.source.suffix in {".xls", ".xlsx", ".XLS", "XLSX"}:
                excel_file_to_csv_string_io(self.source, self.csv_io)
            else:
                file_to_csv_string_io(self.source, self.csv_io, self.params_dict.get("encoding"))

        except ExcelToCsvFileError as except_error:
            comment = (
                f"une erreur dans la transformation du fichier {self.source.name!r} "
                "excel en csv StringIO"
            )
            if self.trace:
                self.trace.errors = True
                self.trace.comment = comment
                self.trace.save()
            raise ExcelToCsvError(comment) from except_error

        except CsvFileToStringIoError as except_error:
            comment = (
                f"une erreur dans la transformation du fichier {self.source.name!r} "
                "en csv StringIO"
            )
            if self.trace:
                self.trace.errors = True
                self.trace.comment = comment
                self.trace.save()
            raise FileToCsvError(comment) from except_error

    def _get_csv_reader(self):
        """
        Le csv.reader étant un générateur, on initialise self.csv_reader à chaque fois,
        afin de pouvoir faire des opérations comme next() dessus.
        """
        self.csv_io.seek(self.first_line)
        self.csv_reader = csv.reader(
            self.csv_io,
            delimiter=self.params_dict.get("delimiter", ";"),
            quotechar=self.params_dict.get("quotechar", '"'),
            lineterminator=self.params_dict.get("lineterminator", "\n"),
            quoting=self.params_dict.get("quoting", csv.QUOTE_MINIMAL),
        )

    def _check_nb_columns(self):
        """Check si on a le nombre de colonnes suffisantes"""
        self._get_csv_reader()
        file_nb_cols = len(next(self.csv_reader))
        demand_nb_cols = len(self.columns_dict)

        if demand_nb_cols > file_nb_cols:
            comment = (
                f"Erreur sur les colonnes : le fichier {self.source.name} comporte {file_nb_cols} "
                f"colonne{'s' if file_nb_cols > 1 else ''}, "
                f"il est exigé au moins {demand_nb_cols} "
                f"colonne{'s' if demand_nb_cols > 1 else ''}"
            )
            if self.trace:
                self.trace.errors = True
                self.trace.comment = comment
                self.trace.save()
            raise IterFileToInsertError(comment)

    def _get_check_columns(self, header_on_demand, header_in_file):
        """
        Check des colonnes, si l'on a les mêmes dans le fichier et celles demandées.
        Si invalid alors on raise une erreur
        :param header_on_demand: set des colonnes demandées
        :param header_in_file: set des colonnes de la bdd
        """
        if not set(header_on_demand).issubset(set(header_in_file)):
            values = ", ".join(
                f'"{value}"' for value in set(header_on_demand).difference(set(header_in_file))
            )
            comment = (
                "Erreur sur les colonnes : "
                f"le fichier {self.source.name} ne contient pas "
                f"les colonnes demandées suivantes : {values}\n"
                f"le fichier contient les colonnes suivantes : {', '.join(header_in_file)}"
            )
            if self.trace:
                self.trace.errors = True
                self.trace.comment = comment
                self.trace.save()
            raise IterFileToInsertError(comment)

    def get_positons_for_none_columns(self):
        """
        Position des colonnes demandées dans l'attribut d'instance self.columns_dict,
        dans la même position que le fichier
        :return: Liste des positions des colonnes
        """
        postion_list = list(range(len(self.columns_dict)))

        return postion_list

    @staticmethod
    def _get_sanitaze(header_lit):
        """
        :param header_lit: List des entêtes du fichier
        :return: liste des entêtes du fichier cleannées
        """
        sanitaze = [
            str(value)
            .strip()
            .lower()
            .replace(" ", "_")
            .replace("\n", "")
            .replace("\r", "")
            .replace("\t", "")
            .replace("°", "")
            for value in header_lit
        ]
        return sanitaze

    def get_positions_if_columns_named(self):
        """
        Position des colonnes nommées dans l'attribut d'instance self.columns_dict
        :return: Liste des positions des colonnes
        """
        header_list_in_file = self._get_sanitaze(next(self.csv_reader))
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
        except IndexError as except_error:
            comment = "La méthode get_add_dict a besoins d'un tuple de 2 élements"
            if self.trace:
                self.trace.errors = True
                self.trace.comment = comment
                self.trace.save()
            raise GetAddDictError(comment) from except_error

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
        :param all_lines: Si dans le fichier il y a des lignes vides :
                            all_lines = False -> shorcut l'itération des lignes vides
                            all_lines = True -> iterre même sur des lignes vides
        """
        postion_list = self.get_header()

        # on renvoie pour chaque ligne du fichier les données au format csv
        for i, line in enumerate(self.csv_reader, 1):
            if (not any(line) and not all_lines) or any(
                str(value).strip().upper() in str(line[index - 1]).strip().upper()
                for index, value in self.params_dict.get("exclude_rows_dict", {}).items()
            ):
                continue

            try:
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

            except IndexError:
                if self.trace:
                    error_dict = {
                        "attr_name": "",
                        "message": (
                            "La ligne ne contient pas le même nombre de colonne que les autres"
                        ),
                        "data_expected": "",
                        "data_received": ";".join(line)
                    }
                    self.trace_add_line_error("Errors", i, error_dict=error_dict)

                raise IterFileToInsertError("Le fichier contient une ligne non comforme")

    def make_io(self, csv_io: io.StringIO, all_lines=False):
        """
        Ecrit le csv dans le fichier de type io.StringIO envoyé
        :param csv_io: Fichier de type io.StringIO
        :param all_lines: Si dans le fichier il y a des lignes vides :
                            all_lines = False -> shorcut l'itération des lignes vides
                            all_lines = True -> iterre même sur des lignes vides
        """
        for line in self.read(all_lines):
            csv_io.write(line + "\n")

        csv_io.seek(0)

    def read_list(self, all_lines: bool = False):
        """
        Méthode de lecture du flux de données, sous forme d'un tableau (list en python)
        :param all_lines: Si dans le fichier il y a des lignes vides :
                            all_lines = False -> shorcut l'itération des lignes vides
                            all_lines = True -> iterre même sur des lignes vides
        """
        postion_list = self.get_header()

        # on renvoie pour chaque ligne du fichier les données dans un tableau, une liste
        for i, line in enumerate(self.csv_reader, 1):
            if (not any(line) and not all_lines) or any(
                str(value).strip().upper() in str(line[index - 1]).strip().upper()
                for index, value in self.params_dict.get("exclude_rows_dict", {}).items()
            ):
                continue

            try:

                if self.params_dict.get("add_fields_dict", {}):
                    yield list(itemgetter(*postion_list)(line)) + self.get_add_values
                else:
                    yield list(itemgetter(*postion_list)(line))

            except IndexError:
                if self.trace:
                    error_dict = {
                        "attr_name": "",
                        "message": (
                            "La ligne ne contient pas le même nombre de colonne que les autres"
                        ),
                        "data_expected": "",
                        "data_received": ";".join(line)
                    }
                    self.trace_add_line_error("Errors", i, error_dict=error_dict)

                raise IterFileToInsertError("Le fichier contient une ligne non comforme")

    def read_dict(self, all_lines=False):
        """
        Générateurs du dictionaire des lignes de l'io.StringIO, avec le nom des colonnes à récupérer
        :param all_lines: Si dans le fichier il y a des lignes vides
                            all_lines=False, shorcut l'itération des lignes vides
                            all_lines=True, iterre même sur des lignes vides
        :return: Générateur des lignes du fichier retraitées sous forme de dictionnaire key: value
        """
        postion_list = self.get_header()

        # on renvoie pour chaque ligne du fichier le dictionnaire de données
        for i, line in enumerate(self.csv_reader, 1):
            if (not any(line) and not all_lines) or any(
                str(value).strip().upper() in str(line[index - 1]).strip().upper()
                for index, value in self.params_dict.get("exclude_rows_dict", {}).items()
            ):
                continue

            try:

                if self.params_dict.get("add_fields_dict", {}):
                    yield {
                        **dict(zip(list(self.columns_dict), itemgetter(*postion_list)(line))),
                        **self.get_add_dict,
                    }
                else:
                    yield dict(zip(list(self.columns_dict), itemgetter(*postion_list)(line)))

            except IndexError:
                if self.trace:
                    error_dict = {
                        "attr_name": "",
                        "message": (
                            "La ligne ne contient pas le même nombre de colonne que les autres"
                        ),
                        "data_expected": "",
                        "data_received": ";".join(line)
                    }
                    self.trace_add_line_error("Errors", i, error_dict=error_dict)

                raise IterFileToInsertError("Le fichier contient une ligne non comforme")

    def close(self):
        """Fermeture du buffer io.StringIO"""
        try:
            if not self.csv_io.closed:
                self.csv_io.close()
            del self.csv_io
        except (AttributeError, NameError):
            pass


class Opto33Loader(TemplateDataLoader):
    """
    Opto33Loader pour importer un fichier opto33 et le cleanner en vue d'une insertion en base
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
        """
        super().__init__(source, columns_dict, first_line, params_dict)
        self.opto_parse = EdiOpoto33Parser(source).parse()
        self.source_header = list(self.opto_parse.get("get_columns"))

    def open(self, flux_params_dict: Dict = None):
        """Surcharge de la méthode open, mais nous n'en avons pas besoins"""

    def _get_check_columns(self, header_on_demand, header_in_file):
        """
        Check des colonnes, si l'on a les mêmes dans le fichier et celles demandées.
        Si invalid alors on raise une erreur
        :param header_on_demand: set des colonnes demandées
        :param header_in_file: set des colonnes de la bdd
        """
        if not set(header_on_demand).issubset(set(header_in_file)):
            values = ", ".join(
                f'"{value}"' for value in set(header_on_demand).difference(set(header_in_file))
            )
            comment = (
                "Erreur sur les colonnes : "
                f"le fichier {self.source.name} ne contient pas "
                f"les colonnes demandées suivantes : {values}\n"
                f"le fichier contient les colonnes suivantes : {', '.join(header_in_file)}"
            )
            if self.trace:
                self.trace.errors = True
                self.trace.comment = comment
                self.trace.save()
            raise IterFileToInsertError(comment)

    def get_positions_if_columns_named(self):
        """
        Position des colonnes nommées dans l'attribut d'instance self.columns_dict
        :return: Liste des positions des colonnes
        """
        header_list_in_file = self.source_header
        header_on_demand = list(self.columns_dict.values())
        self._get_check_columns(header_on_demand, header_list_in_file)

        return header_on_demand

    def get_header(self):
        """
        :return: Liste des positions des colonnes
        """
        return self.get_positions_if_columns_named()

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
        except IndexError as except_error:
            comment = "La méthode get_add_dict a besoins d'un tuple de 2 élements"
            if self.trace:
                self.trace.errors = True
                self.trace.comment = comment
                self.trace.save()
            raise GetAddDictError(comment) from except_error

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

    def read(self, all_lines=None):
        """
        Méthode de lecture du flux de donées au format io.StringIO
        :param all_lines: Pas utilisé
        """
        postion_list = self.get_header()

        # on renvoie pour chaque ligne du fichier les données au format csv
        for line in self.opto_parse.get("invoices"):
            if self.params_dict.get("add_fields_dict", {}):
                yield f'{self.params_dict.get("delimiter", ";")}'.join(
                    [str(line.get(key)) for key in postion_list + self.get_add_values]
                )
            else:
                yield f'{self.params_dict.get("delimiter", ";")}'.join(
                    [str(line.get(key)) for key in postion_list]
                )

    def make_io(
        self,
        csv_io: io.StringIO,
    ):
        """
        Ecrit le csv dans le fichier de type io.StringIO envoyé
        :param csv_io: Fichier de type io.StringIO
        """
        for line in self.read():
            csv_io.write(line + "\n")

        csv_io.seek(0)

    def read_list(self, all_lines=None):
        """
        Méthode de lecture du flux de données, sous forme d'un tableau (list en python)
        :param all_lines: Pas utilisé
        """
        postion_list = self.get_header()

        # on renvoie pour chaque ligne du fichier les données dans un tableau, une liste
        for line in self.opto_parse.get("invoices"):
            if self.params_dict.get("add_fields_dict", {}):
                yield [str(line.get(key)) for key in postion_list + self.get_add_values]
            else:
                yield [str(line.get(key)) for key in postion_list]

    def read_dict(self, all_lines=None):
        """
        Générateurs du dictionaire des lignes de l'io.StringIO, avec le nom des colonnes à récupérer
        :param all_lines: Pas utilisé
        :return: Générateur des lignes du fichier retraitées sous forme de dictionnaire key: value
        """
        postion_list = self.get_header()

        # on renvoie pour chaque ligne du fichier le dictionnaire de données
        for line in self.opto_parse.get("invoices"):
            # print(line)
            if self.params_dict.get("add_fields_dict", {}):
                yield {
                    **{key: str(line.get(key)) for key in postion_list},
                    **self.get_add_dict,
                }
            else:
                yield {key: str(line.get(key)) for key in postion_list}

    def close(self):
        """Fermeture du buffer io.StringIO"""


class ApiJsonLoader(TemplateDataLoader):
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
                                    # model Django Trace pour fichiers trace
                                    "trace" : Trace
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
                                    all_lines = True -> iterre même sur des lignes vides
        """
        yield "ApiLodaer non finalisée"

    def read_list(self, all_lines: bool = False):
        """
        Méthode de lecture du flux de données, sous forme d'un tableau (list en python)
        :param all_lines:       Si dans le fichier il y a des lignes vides :
                                    all_lines = False -> shorcut l'itération des lignes vides
                                    all_lines = True -> iterre même sur des lignes vides
        """
        yield "ApiLodaer non finalisée"

    def read_dict(self, all_lines=False):
        """
        Générateurs du dictionaire des lignes de l'io.StringIO, avec le nom des colonnes à récupérer
        :param all_lines: si dans le fichier il y a des lignes vides
                            all_lines=False, shorcut l'itération des lignes vides
                            all_lines=True, iterre même sur des lignes vides
        :return: Générateur des lignes du fichier retraitées sous forme de dictionnaire key: value
        """
        yield {"message": "ApiLodaer non finalisée"}

    def close(self):
        """Fermeture du buffer io.StringIO"""
        if not self.csv_io.closed:
            self.csv_io.close()


class ApiXmlLoader(TemplateDataLoader):
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
                                    # model Django Trace pour fichiers trace
                                    "trace" : Trace
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
                                    all_lines = True -> iterre même sur des lignes vides
        """
        yield "ApiLodaer non finalisée"

    def read_list(self, all_lines: bool = False):
        """
        Méthode de lecture du flux de données, sous forme d'un tableau (list en python)
        :param all_lines:       Si dans le fichier il y a des lignes vides :
                                    all_lines = False -> shorcut l'itération des lignes vides
                                    all_lines = True -> iterre même sur des lignes vides
        """
        yield "ApiLodaer non finalisée"

    def read_dict(self, all_lines=False):
        """
        Générateurs du dictionaire des lignes de l'io.StringIO, avec le nom des colonnes à récupérer
        :param all_lines: si dans le fichier il y a des lignes vides
                            all_lines=False, shorcut l'itération des lignes vides
                            all_lines=True, iterre même sur des lignes vides
        :return: Générateur des lignes du fichier retraitées sous forme de dictionnaire key: value
        """
        yield {"message": "ApiLodaer non finalisée"}

    def close(self):
        """Fermeture du buffer io.StringIO"""
        if not self.csv_io.closed:
            self.csv_io.close()
