# pylint: disable=E0401,R0913,W1203
"""Module d'insertion du flux de données validées

Commentaire:

created at: 2021-10-30
created by: Paulo ALVES

modified at: 2021-10-30
modified by: Paulo ALVES
"""
import io
import random
import string
from typing import AnyStr, Dict, Tuple

from psycopg2 import sql
import psycopg2
import django
from django.db import models, connection


class PostgresDjangoError(Exception):
    """Exceptions pour l'upsert dans une table postgresql"""


class PostgresInsertMethodError(PostgresDjangoError):
    """Exceptions pour l'upsert dans une table postgresql"""


class PostgresCardinalityViolationError(PostgresDjangoError):
    """Exceptions pour l'upsert dans une table postgresql"""


class PostgresUniqueError(PostgresDjangoError):
    """Exceptions pour l'upsert dans une table postgresql"""


class PostgresTypeError(PostgresDjangoError):
    """Exceptions pour un type en erreur dans une table postgresql"""


def get_random_name(size=10):
    """
    Retourne une suite de lettre alléatoire
    :param size: taille
    :return: suite de lettres en minuscule
    """
    ascii_choices = string.ascii_lowercase
    return "".join(random.SystemRandom().choice(ascii_choices) for _ in range(size)).lower()


class PostgresDjangoUpsert:
    """
    Class pour l'insertion en base de donnée de fichier de type csv
    (de préférence au format io.StringIO) par des méthodes de copy_from psycopg2.
    """

    # TODO : Implémentation de la validation des clés éxistantes à implémenter
    def __init__(
        self,
        model: models.Model,
        fields_dict: Dict,
        cnx: connection = connection,
        foreign_key: Tuple = None,
    ):
        """
        :param model:       Model Django
        :param fields_dict: Dictonnaire des champs à utiliser pour les insertions en base.
                            True pour les champs uniques et False pour les champs à update
                            ex : fields_dict = {"unique": True, "other": False, ...}
                            Attention! les champs devront être dans le même ordre
                            que les colonnes du fichier
        :param foreign_key: object connexion à Postgresql
        :param foreign_key: Tuple des clefs étrangères et tuples d'uniques_togheter pour
                            vérification quelles éxistent bien, avant insertion des données
                            ("trace", ("date", "mode"))
                            pour l'instant cette partie n'est pas implémentée
        """
        self.model = model
        self.fields_dict = fields_dict
        self.foreygn_key = foreign_key
        self.meta = self.model._meta
        self.table_name = self.meta.db_table
        self.cnx = cnx
        self.temp_table_name = self.get_temp_table_name()

    def table_is_exists(self, table_name):
        """
        Vérifie si le nom choisi pour la table temporaire existe en base
        :param table_name: nom de table à tester
        :return: bool
        """
        with self.cnx.cursor() as cursor:
            sql_exists = sql.SQL(
                'SELECT 1 FROM "information_schema"."tables" WHERE "table_name"=%(table)s'
            )
            cursor.execute(sql_exists, {"table": table_name})

            return bool(cursor.fetchone())

    def get_temp_table_name(self):
        """
        Retourne le nom de la table temporaire en s'assurant que le nom n'existe pas
        :return: Nom de la table temporaire
        """
        name = None

        while name is None:
            test_name = f"{get_random_name()}_{self.table_name}"

            if not self.table_is_exists(test_name):
                name = test_name

        return name

    def get_column_properties(self, field_key: AnyStr):
        """
        :param field_key: champ du model django à retouner
        :return: Le Sql des paramètres de création de la table temporaire
        """
        field_attr = self.meta.get_field(field_key)
        return f' "{field_attr.column}" {field_attr.db_type(self.cnx)}'

    def get_columns_upsert(self):
        """
        :return: Les clauses du SQL d'un upsert ON CONFICT ... UPDATE
        """
        fields_upsert_dict = {
            "conflict": [],
            "update": [],
        }

        for field_key, bool_value in self.fields_dict.items():
            if bool_value:
                fields_upsert_dict.get("conflict").append(field_key)
            else:
                fields_upsert_dict.get("update").append(field_key)

        return fields_upsert_dict

    @property
    def get_fields(self):
        """
        :return: les champs interprétés allant servir dans une requête
        """
        return sql.SQL(", ").join([sql.Identifier(field) for field in self.fields_dict.keys()])

    @property
    def get_base_insert(self):
        """
        :return: Le début du SQL de la requête d'insertion
        """
        insert_table = sql.Identifier(self.table_name)
        from_table = sql.Identifier(self.temp_table_name)

        return insert_table, from_table

    @property
    def get_ddl_temp_table(self):
        """
        :return: Le SQL du DDL de crétaion d'une table temporaire
        """
        create_table = sql.Identifier(self.temp_table_name)
        fields_list = [self.get_column_properties(field) for field in self.fields_dict]
        suffix_sql = f" ({', '.join(fields_list)})"
        sql_create = sql.SQL("CREATE TEMPORARY TABLE {create_table}" + suffix_sql).format(
            create_table=create_table
        )

        return sql_create

    @property
    def get_query_upsert(self):
        """
        :return: Le SQL de la clause ON CONFLICT ... DO UPDATE pour la requête upsert
        """
        fields_conflict = sql.SQL(", ").join(
            [sql.Identifier(field) for field in self.get_columns_upsert().get("conflict")]
        )
        update_columns = sql.SQL(", ").join(
            [
                sql.SQL("{field}=EXCLUDED.{field}").format(field=sql.Identifier(field))
                for field in self.get_columns_upsert().get("update")
            ]
        )
        insert_table, from_table = self.get_base_insert
        sql_upsert = sql.SQL(
            "INSERT INTO {insert_table} ({fields}) "
            "SELECT {fields} FROM {form_table} "
            "ON CONFLICT ({fields_conflict}) "
            "DO UPDATE SET {update_columns}"
        ).format(
            insert_table=insert_table,
            form_table=from_table,
            fields=self.get_fields,
            fields_conflict=fields_conflict,
            update_columns=update_columns,
        )

        return sql_upsert

    @property
    def get_query_do_nothing(self):
        """
        :return: Le SQL de la clause ON CONFLICT DO NOTHING pour la requête upsert
        """
        insert_table, from_table = self.get_base_insert
        sql_insert = sql.SQL(
            "INSERT INTO {insert_table} ({fields}) "
            "SELECT {fields} FROM {form_table} "
            "ON CONFLICT DO NOTHING"
        ).format(insert_table=insert_table, form_table=from_table, fields=self.get_fields)
        return sql_insert

    @property
    def get_drop_temp(self):
        """
        :return: Le SQL de suppression de la table provisoire
        """
        table_drop = sql.Identifier(self.temp_table_name)
        sql_drop = sql.SQL("DROP TABLE IF EXISTS {table_drop}").format(table_drop=table_drop)

        return sql_drop

    def insert(
        self,
        file: io.StringIO,
        insert_mode: AnyStr = "upsert",
        delimiter: AnyStr = ";",
        quote_character: AnyStr = '"',
    ):
        """
        Realise l'insertion choisie (upsert, do_nothing, insert)
        :param file: fichier au format io.StringIO
        :param insert_mode: mode d'insertion choisi
        :param delimiter: séparateur des lignes du fichier
        :param quote_character: quatation des champs
        """
        insert_mode_dict = {
            "insert": None,
            "do_nothing": self.get_query_do_nothing,
            "upsert": self.get_query_upsert,
        }

        if insert_mode not in insert_mode_dict:
            raise PostgresInsertMethodError(
                f"La methode {insert_mode!r} d'insertion choisie n'existe pas"
            )

        with self.cnx.cursor() as cursor:
            try:
                fields = self.get_fields
                delimiter = sql.SQL(delimiter)
                quote_character = sql.SQL(quote_character)
                sql_expert = (
                    "COPY {table} ({fields}) "
                    "FROM STDIN "
                    "WITH "
                    "DELIMITER AS '{delimiter}' "
                    "CSV "
                    "QUOTE AS '{quote_character}'"
                )

                if insert_mode == "insert":
                    # copy direct dans la table définitive
                    table = sql.Identifier(self.table_name)
                    sql_copy = sql.SQL(sql_expert).format(
                        table=table,
                        fields=fields,
                        delimiter=delimiter,
                        quote_character=quote_character,
                    )
                    cursor.copy_expert(sql=sql_copy, file=file)

                else:
                    # copy dans une table provisoire pour un do_nothing ou un upsert
                    table = sql.Identifier(self.temp_table_name)
                    cursor.execute(self.get_ddl_temp_table)
                    sql_copy = sql.SQL(sql_expert).format(
                        table=table,
                        fields=fields,
                        delimiter=delimiter,
                        quote_character=quote_character,
                    )
                    cursor.copy_expert(sql=sql_copy, file=file)

                    # do_nothing ou upsert
                    cursor.execute(insert_mode_dict.get(insert_mode))

                    # suppression de la table provisoire
                    cursor.execute(self.get_drop_temp)

            except (
                psycopg2.errors.CardinalityViolation,
                django.db.utils.ProgrammingError,
            ) as except_error:
                raise PostgresCardinalityViolationError("Conflit à l'insertion") from except_error

            except psycopg2.errors.InvalidTextRepresentation as except_error:
                raise PostgresTypeError("Erreur de type") from except_error

            except psycopg2.errors.UniqueViolation as except_error:
                raise PostgresUniqueError("Erreur sur clé dupliquée") from except_error

            except Exception as except_error:
                raise PostgresDjangoError("Erreur inconnue") from except_error
