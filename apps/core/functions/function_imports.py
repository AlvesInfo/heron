# pylint: disable=E0401
"""Module pour validation et import en base de donnée, de fichiers à intégrer

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

import pandas as pd

from apps.core.functions.functions_utilitaires import encoding_detect


LOGGER_IMPORT = logging.getLogger("imports")


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
            quoting=csv.QUOTE_ALL,
            encoding="utf8",
        )
        string_io_file.seek(0)

    except ValueError as except_error:
        raise ExcelToCsvFileError(
            f"Impossible de déterminer si le fichier {excel_file.name!r}, est un fichier excel"
        ) from except_error

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

    except Exception as except_error:
        raise CsvFileToStringIoError(f"file_to_csv_string_io : {file.name!r}") from except_error


class IterFileToInsert:
    """
    Iterateur de dictionnaire de données ou ligne à ligne
    Attention! Si cette classe n'est pas appelée par le context manager il faudra penser à fermer le
    fichier de type io.StringIO : self.csv_io, par la méthode d'instance self.close_buffer
    """

    def __init__(
        self,
        file_to_iter: Path,
        columns_dict: Dict,
        first_line: int = 1,
        params_dict: Dict = None,
    ):
        """
        :param file_to_iter:        Fichier de type Path à insérer
        :param columns_dict:        Plusieurs choix possibles pour :
                                    - Récupérer le nombre de colonnes dans l'ordre du fichier
                                        {"db_col_1" : None, "db_col_2" : None, ..., }

                                    - Récupérer seulement les colonnes souhaitées par leur nom
                                        {"db_col_1" : "file_col_x", "db_col_2" : "file_col_a", ...}

                                    - Récupérer seulement les colonnes souhaitées par leur index
                                        (index commence à 0)
                                        {"db_col_1" : 3, "db_col" : 0, ..., }

        :param first_line:          Première ligne du fichier commence à 1 par defaut

        :param params_dict:         Dictionnaire des paramètres à appliquer
                                    params_dict = {

                                        # attribus du paramétrage csv
                                        "delimiter" : séparateur du fichier, par défaut ";"
                                        "lineterminator": Passage à la ligne par défaut "\n"
                                        "quoting": type de quoting par défaut csv.QUOTE_ALL
                                        "quotechar": le caractère de quoting par défaut '"'

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
        self.file_to_iter = file_to_iter
        self.csv_io = io.StringIO()
        self.columns_dict = columns_dict
        self.first_line = 0
        self.params_dict = params_dict or {}
        self._get_io()
        self.csv_io.seek(0)

        # Pour connaître la position (seek) à partir de laquelle récupérer les lignes du fichier
        for i, line in enumerate(self.csv_io):
            if i == (first_line - 1):
                break
            self.first_line += len(line)

        self.csv_io.seek(self.first_line)
        self.csv_reader = csv.reader(
            self.csv_io,
            delimiter=self.params_dict.get("delimiter", ";"),
            quotechar=self.params_dict.get("quotechar", '"'),
            lineterminator=self.params_dict.get("lineterminator", "\n"),
            quoting=self.params_dict.get("quoting", csv.QUOTE_MINIMAL),
        )

    def __enter__(self):
        """Pré context manager"""
        return self

    def __exit__(self, tipe, value, traceback):
        """Post context manager, pour fermer le fichier de type io.StringIO
        :param tipe: valeur du type venant de la sortie de la classe
        :param value: valeur venant de la sortie de la classe
        :param traceback: traceback sur une éventuele exception de la sortie de la classe
        """
        self.close_buffer()

    def _get_io(self):
        """Ecriture des données dans le fichier self.csv_io de type io.StringIO de l'instance.
        Il y aura un prétraitement si le fichier envoyé est un fichier à plat ou un fichier Excel
        """
        try:
            if self.file_to_iter.suffix in {".xls", ".xlsx"}:
                excel_file_to_csv_string_io(self.file_to_iter, self.csv_io)
            else:
                file_to_csv_string_io(self.file_to_iter, self.csv_io)
        except Exception as except_error:
            raise ExcelToCsvError(
                f"une erreur dans la transformation du fichier {self.file_to_iter.name!r} "
                "en csv StringIO"
            ) from except_error

    def close_buffer(self):
        """Fermeture du buffer io.StringIO"""
        if not self.csv_io.closed:
            self.csv_io.close()

    def _get_csv_reader(self):
        """Instanciation l'attribut d'instance self.csv_reader"""
        self.csv_io.seek(self.first_line)
        self.csv_reader = csv.reader(
            self.csv_io.readlines(),
            delimiter=self.params_dict.get("delimiter", ";"),
            quotechar=self.params_dict.get("quotechar", '"'),
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
        header_in_file = header_list_in_file
        header_on_demand = list(self.columns_dict.values())
        self._get_check_columns(header_on_demand, header_in_file)

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
            raise GetAddDictError(
                "La méthode get_add_dict a besoins d'un tuple de 2 élements"
            ) from except_error

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

    def chunk_dict(self, all_lines=False):
        """
        Générateurs du dictionaire des lignes du fichier, avec le nom des colonnes à récupérer
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

    def write_io(self, chunk_file_io: io.StringIO, all_lines=False):
        """
        Rempli le fichier io.StringIO reçu avec lignes du fichier avec les colonnes à récupérer
        :param chunk_file_io:   Fichier de type io.StringIO à remplir
        :param all_lines:       Si dans le fichier il y a des lignes vides :
                                    all_lines = False -> shorcut l'itération des lignes vides
                                    all_lines = True -> iterre même sur des lignes des lignes vides
        """
        postion_list = self.get_header()
        csv_writer = csv.writer(
            chunk_file_io,
            delimiter=self.params_dict.get("delimiter", ";"),
            quotechar=self.params_dict.get("quotechar", '"'),
            quoting=csv.QUOTE_ALL,
        )

        # on écrit dans le fichier io.StringIO reçu les lignes du fichier à récupérer
        for line in self.csv_reader:
            if (not line and not all_lines) or any(
                str(value).strip().upper() in str(line[index - 1]).strip().upper()
                for index, value in self.params_dict.get("exclude_rows_dict", {}).items()
            ):
                continue

            if self.params_dict.get("add_fields_dict", {}):
                csv_writer.writerow(list(itemgetter(*postion_list)(line)) + self.get_add_values)
            else:
                csv_writer.writerow(itemgetter(*postion_list)(line))


class ModelFormInsertion(IterFileToInsert):
    """class pour la validation et l'insertion"""

    def __init__(self, validator, *args, map_line=None, uniques=(), **kwargs):
        """
        :param validator:   Validateur pour le fichier, le validateur doit avoir les méthodes :
                                - is_valid() pour validation
                                - save() pour insertion en base
                                - une property errors qui renvoie les erreurs
                            Si on a unique avec des noms de champs alors on va update ou create
        :param map_line:    Fonction de transformation des données avant validation,
                            cela peut être un tuple ou une liste avec les numéros de colonnes
                            ou un dictionnaire avec le nom des colonnes
        :param uniques:     Si l'on veut faire un update on envoie les champs uniques
        :param args:        Arguments de l'héritage
        :param kwargs:      Dictionnaire des arguments de l'héritage
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
        """Méthode qui va gérer les remplacements à faire à partir d'une liste"""
        for index, func in enumerate(self.map_line):
            line[index] = func(line[index])

    def get_transform_dict_line(self, line):
        """Méthode qui va gérer les remplacements à faire à partir d'un dictionnaire"""
        for key, func in self.map_line.items():
            line[key] = func(line.get(key))

    def set_transform_line(self, line):
        """Méthode qui applique la transformation en place de la ligne à tranformer"""
        if self.map_line_dict:
            self.get_transform_dict_line(line)
        else:
            self.get_transform_list_line(line)

    def iter_validation(self):
        """Parcours les éléments du fichier à valider, puis insère en base si les données
        sont bonnes ou ajoute les erreurs par lignes
        """
        for i, data_dict in enumerate(self.chunk_dict(), 1):
            # Si on envoie les champs uniques alors on update
            if self.uniques:
                validator = self.validator(data=data_dict)
                validator.is_valid()

                # On va tester que l'on a tous les champs uniques
                uniques_list = {key for key in validator.clean() if key in self.uniques}

                if uniques_list == set(self.uniques):
                    attrs_instance = {
                        key: value
                        for key, value in validator.clean().items()
                        if key in self.uniques
                    }
                    model = self.validator._meta.model

                    try:
                        instance = model.objects.get(**attrs_instance)
                        validator = self.validator(data=data_dict, instance=instance)

                    except model.DoesNotExist:
                        validator = self.validator(data=data_dict)
                else:
                    validator = self.validator(data=data_dict)
            else:
                validator = self.validator(data=data_dict)

            if validator.is_valid():
                validator.save()
            else:
                self.get_errors(i, validator.errors)

    def validate(self):
        """Validation des lignes du fichier, sauvegarde et renvoi des erreurs s'il y en a eu"""
        try:
            self.iter_validation()
        except Exception as except_error:
            raise ValidationError(
                "une erreur c'est produite pendant la validation"
            ) from except_error


# class ImportModelFileFactory(IterFileToInsert):
#     """class Import Model File Factory"""
#
#     def __init__(self, model, validator, *args, **kwargs):
#         """
#         :param validator: validateur des champs du fichier, peut être du type serializer DRF,
#                           mais doit avoir une method is_valid et une méthode save
#         """
#         super().__init__(*args, **kwargs)
#         self.model = model
#         self.validator = validator
#         self.errors = []
#         self.iter_valide_data_file = io.StringIO()
#
#     def __enter__(self):
#         """Pré context manager"""
#         return self
#
#     def __exit__(self, tipe, value, traceback):
#         """Post context manager, pour fermer
#         :param tipe: valeur du type venant de la sortie de la classe
#         :param value: valeur venant de la sortie de la classe
#         :param traceback: traceback sur une éventuele exception de la sortie de la classe
#         """
#         self.close_buffer()
#
#     def close_buffer(self):
#         """Méthode de fermeture du buffer"""
#         if isinstance(self.iter_valide_data_file, (io.StringIO,)):
#             self.iter_valide_data_file.close()
#
#     def _set_errors(self, ligne, errors, errors_limits):
#         """Remplie la list error de l'instance"""
#
#         if not len(self.errors) >= errors_limits:
#             list_or_dict = "dict"
#
#             try:
#                 dict(errors)
#             except ValueError:
#                 list_or_dict = "list"
#
#             if list_or_dict == "dict":
#                 error_dict = {f"Ligne n°{ligne:>5} : ": []}
#
#                 for champ, details in errors.items():
#                     error, *_ = details
#                     error_dict[f"Ligne n°{ligne:>5} : "].append({champ: str(error)})
#
#                 self.errors.append(error_dict)
#
#             else:
#                 for i, dict_row in enumerate(errors, ligne):
#                     if len(self.errors) >= errors_limits:
#                         break
#
#                     if dict_row:
#                         error_dict = {f"Ligne n°{i:>5} : ": []}
#
#                         for champ, details in dict_row.items():
#                             error, *_ = details
#                             error_dict[f"Ligne n°{i:>5} : "].append({champ: str(error)})
#
#                         self.errors.append(error_dict)
#
#     def get_validate_file(self, strict=False):
#         """
#         :param strict: True ou False
#         :return: Retourne un fichier de type IO.StringIO, avec seulement les lignes valides
#         """
#         self.validate(strict)
#         self.iter_valide_data_file.seek(0)
#         return self.iter_valide_data_file
#
#     def get_errors(self):
#         """
#         :return: Retourne les erreurs de validation
#         """
#         return self.errors
#
#     def validate(self, strict=False, errors_limits=100, save=False):
#         """
#         Parcours ligne par ligne du fichier pour validation, puis ajoute la ligne dans fichier
#         io.StringIO les data validées ou on ajoute les erreurs dans une liste.
#         Si aucunes de lignes du fichier ne doit être fausse alors on valide l'ensemble
#         :param strict: True ou False
#         :param errors_limits: nbre d'erreurs maxi à remonter
#         :param save: si l'on veut que le serializer sauvegarde les données in time validation,
#                     cette méthode est beaucoup moins efficace que les autres methodes implémentées
#         """
#         test_errors = False
#
#         if strict:
#             serializer = self.validator(data=list(self.chunk_dict()), many=True)
#
#             if serializer.is_valid():
#                 self.iter_valide_data_file.writelines(
#                     f"{self.delimiter}".join(str(value) for value in row.values()) + "\n"
#                     for row in serializer.data
#                 )
#                 if save:
#                     serializer.save()
#             else:
#                 test_errors = True
#                 self._set_errors(self.first_line + 1, serializer.errors, errors_limits)
#         else:
#             for i, data_dict in enumerate(self.chunk_dict(), self.first_line + 1):
#                 serializer = self.validator(data=data_dict)
#
#                 if serializer.is_valid():
#                     self.iter_valide_data_file.write(
#                         f"{self.delimiter}".join(str(value) for value in serializer.data.values())
#                         + "\n"
#                     )
#                     if save:
#                         serializer.save()
#                 else:
#                     test_errors = True
#                     self._set_errors(i, serializer.errors, errors_limits)
#
#         return test_errors
#
#     def csv_reader_insertion(self):
#         """
#         :return: Retourne une instance de csv.reader du fichier à intégrer
#         """
#         self.iter_valide_data_file.seek(0)
#
#         for row in csv.reader(
#             self.iter_valide_data_file, delimiter=self.delimiter, quotechar=self.quotechar
#         ):
#             yield dict(zip(self.columns, row))
#
#     def django_method_save(self):
#         """
#         Insertion par le modèle django et bulk_create
#         """
#         self.iter_valide_data_file.seek(0)
#         self.model.objects.bulk_create(
#             [self.model(**row_dict) for row_dict in self.csv_reader_insertion()]
#         )
#
#     def bulk_insert(self, cnx):
#         """
#         Insertion directe en BDD par copy_from psycopg2. La méthode est très efficiente,
#         mais ne permet pas de gérer les conflits
#         :param cnx: connection postgresql
#         """
#         self.iter_valide_data_file.seek(0)
#         with cnx.cursor() as cursor:
#             cursor.copy_from(
#                 self.iter_valide_data_file,
#                 self.model.objects.model._meta.db_table,
#                 columns=self.columns_dict,
#                 sep=self.delimiter,
#                 size=1024,
#             )
#             cnx.commit()


'''
def postgres_upsert(self, cnx, insert_mode="upsert", fields_dict=None, fields_set=None):
    """
    Insertion en BDD par postgres_upsert et io.StringIO
    :param cnx: connection postgresql
    :param insert_mode: mode d'insertion souhaité choix possibles:
                        - insert : Insertion normale, génère une erreur en cas de conflit.
                                   Il vaut prévilégier la méthode bulk_insert, ci-dessus.
                        - upsert : Insertion en create ou update
                        - do_nothing : insertion si conflit ne fait rien, ne génère pas d'erreur

    :param fields_dict: Dictonnaire des champs à utiliser pour les insertions en base.
                            True pour les champs uniques et False pour les champs à update
                            ex : fields_dict = {"unique": True, "other": False, ...}
                            Attention! les champs devront être dans le même ordre
                            que les colonnes du fichier
    :param cnx: connexion à Postgresql
    :param fields_set: set de champ à exclure en cas de conflit à l'insertion et à ne pas
                       mettre à jour, comme par exmple le champ created_at, qui devrait être
                       créé la première fois et ne pas être mis à jour
    """
    if fields_dict is None and insert_mode in {"upsert", "do_nothing"}:
        raise IterFileToInsertError(
            "Pour un upsert ou un do_nothing il faut les colonnes unique constraint !"
        )

    self.iter_valide_data_file.seek(0)
    post_upsert = PostresDjangoUpsert(self.model, fields_dict, cnx, fields_set)
    post_upsert.set_insertion(file=self.iter_valide_data_file, insert_mode=insert_mode)
'''
