# pylint: disable=C0411, C0303, E1101, C0413, I1101, R1721
"""Module pour validation de fichiers à intégrer en base de donnée

Commentaire:

created at: 2021-10-30
created by: Paulo ALVES

modified at: 2021-10-30
modified by: Paulo ALVES
"""
import io
import csv
from operator import itemgetter


class IterFileToInsertError(Exception):
    """Gestion d'erreur de validations"""
    ...


class IterFileToInsert:
    """Iterateur de dictionnaire de données, ligne à ligne,
    d'un fichier ou d'un fichier bufferisé
    avec séparateur de type csv à insérer"""

    def __init__(self, file_to_iter, columns_dict, header_line=0, exclude_rows=()):
        """Instanciation des variables
            :param file_to_iter: fichier ou object io à insérer
            :param columns_dict: Plusieurs choix possibles :
                            - Dictionnaire: {
                                                "db_column_1" : None,
                                                "db_column_2" : None,
                                                ...,
                                            }
                                            pour récupérer le nombre de colonnes
                                            dans l'ordre du fichier
                            - Dictionnaire: {
                                                "db_column_1" : "file_column_x",
                                                "db_column_2" : "file_column_a",
                                                ...,
                                            }
                                            pour récupérer seulement
                                            les colonnes souhaitées par leur nom
                            - Dictionnaire: {
                                                "db_column_1" : 3,
                                                "db_column_2" : 0,
                                                ...,
                                            }
                                            pour récupérer seulement
                                            les colonnes souhaitées par leur index
                                            (index commence à 0)
            :param exclude_rows: lignes non souhaitées,
                                décision sur le n° de colonne
                                [
                                    (N°colonne, "texte à rechercher"),
                                    (N°colonne, "texte à rechercher"),
                                    (N°colonne, "texte à rechercher"),
                                ]
            :param header_line: line du header, ou None
        """
        self.file_to_iter = self.get_io(file_to_iter)
        self.file_to_iter.seek(0)
        self.columns_dict = columns_dict
        self.header_line = header_line
        self.first_line = 0 if header_line is None else header_line + 1
        self.exclude_row = exclude_rows
        self.delimiter = ";"
        self.quotechar = '"'

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

    @staticmethod
    def get_io(file_to_iter):
        """Fonction qui renvoie un io.StringIO, si le fichier envoyé n'est pas du bon type
            :param file_to_iter: Fichier reçu à l'instanciation
        """
        if not isinstance(file_to_iter, (io.StringIO,)):
            file_buffer = io.StringIO()

            with open(file_to_iter, "r", encoding="utf8") as file:
                file_buffer.write(file.read())

            return file_buffer

        return file_to_iter

    def close_buffer(self):
        """Fonction de fermeture du buffer"""
        if self.file_to_iter and self.file_to_iter is False:
            self.file_to_iter.close()

    def get_header(self):
        """Fonction qui récupère les colonnes d'entête du fichier
        Si self.columns_dict: {
                                "db_column_1" : None,
                                "db_column_2" : None,
                                ...,
                            }
                              pour récupérer le nombre de colonnes
                              dans l'ordre du fichier
        Si self.columns_dict: {
                                "db_column_1" : "file_column_x",
                                "db_column_2" : "file_column_a",
                                ...,
                            }
                              pour récupérer seulement
                              les colonnes souhaitées par leur nom
        Si self.columns_dict: {
                                "db_column_1" : 3,
                                "db_column_2" : 0,
                                ...,
                            }
                              pour récupérer seulement
                              les colonnes souhaitées par leur index
                              (index commence à 0)
        """

        columns_type = list(self.columns_dict.values())[0]
        rows = []
        columns = list(self.columns_dict.keys())

        # On va vérifer si on a au moins le nombre de colonnes demandées
        # dans le fichier sinon on raise une erreur
        csv_reader = csv.reader(
            self.file_to_iter.readlines(), delimiter=self.delimiter, quotechar=self.quotechar
        )
        self.seek_in_line_position(csv_reader, self.header_line)
        len_columns_file = len(next(csv_reader))
        len_columns_on_demand = len(self.columns_dict.keys())

        if len_columns_on_demand > len_columns_file:
            raise IterFileToInsertError(
                f"Les éléments n'ont pu être importés : "
                f"le fichier comporte {len_columns_file} "
                f"colonne{'s' if len_columns_file > 1 else ''}, "
                f"il est exigé au moins {len_columns_on_demand} "
                f"colonne{'s' if len_columns_on_demand > 1 else ''}"
            )

        self.file_to_iter.seek(0)

        # Si l'on n'a pas d'entêtes
        if columns_type is None:
            rows = [key for key, _ in enumerate(self.columns_dict.items())]

            # on revient à la première ligne du fichier à partir
            # de laquelle on veut démarrer la récupération des données
            self.seek_in_line_position(csv_reader, self.first_line)

        # Si l'on a du nom de colonnes à récupérer
        elif isinstance(columns_type, (str,)):
            # On vérifie si on a toutes les colonnes demandées dans le fichier
            csv_reader = csv.reader(
                self.file_to_iter.readlines(), delimiter=self.delimiter, quotechar=self.quotechar
            )
            self.seek_in_line_position(csv_reader, self.header_line)
            header_list_in_file = next(csv_reader)
            header_set_in_file = set(header_list_in_file)
            header_set_on_demand = set(self.columns_dict.values())

            # Si le fichier ne contient pas les colonnes demandées
            # on raise une ereur
            if not header_set_on_demand.issubset(header_set_in_file):
                differences = ", ".join(
                    f'"{value}"' for value in header_set_on_demand.difference(header_set_in_file)
                )
                raise IterFileToInsertError(
                    f"Les éléments n'ont pu être importés, "
                    f"le fichier ne contient pas les colonnes demandées : " + differences
                )

            # On va maintenant rechercher la position des colonnes du fichier,
            # pour chaque colonne en base de données
            columns = []

            for key, value in self.columns_dict.items():
                columns.append(key)
                rows.append(header_list_in_file.index(value))

        # Si l'on a des numéros de colonnes à récupérer
        elif isinstance(columns_type, (int,)):
            rows = list(self.columns_dict.values())

        return columns, rows

    def seek_in_line_position(self, csv_reader, row_index):
        self.file_to_iter.seek(0)
        for _ in range(row_index):
            next(csv_reader)

    def chunk_file(self, delimiter=";", quotechar='"'):
        """Itérateur des lignes du fichier retraitées
            :param delimiter: délimiteur des champs du fichier
            :param quotechar: caractère de quotation du fichier
            :return: itérateur des lignes
        """
        self.delimiter = delimiter
        self.quotechar = quotechar
        columns, rows = self.get_header()

        self.file_to_iter.seek(0)
        csv_reader = csv.reader(
            self.file_to_iter.readlines(), delimiter=delimiter, quotechar=quotechar
        )
        self.seek_in_line_position(csv_reader, self.first_line)

        # on renvoie pour chaque ligne du fichier le dictionnaire de données
        for line in csv_reader:
            yield dict(zip(columns, itemgetter(*rows)(line)))

    def __call__(self, delimiter=";", quotechar='"'):
        """Itérateur des lignes du fichier retraitées à l'appel de la classe
            :param delimiter: délimiteur des champs du fichier
            :param quotechar: caractère de quotation du fichier
            :return: itérateur des lignes
        """
        yield from self.chunk_file(delimiter=delimiter, quotechar=quotechar)
