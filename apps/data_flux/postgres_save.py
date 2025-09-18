# pylint: disable=C0303,E0401,R0913,R0914
"""
Module d'insertion en base de donnée Postgresql,
Par des méthode rapides de psycopg2

Commentaire:

created at: 2021-10-30
created by: Paulo ALVES

modified at: 2021-10-30
modified by: Paulo ALVES
"""
import io
import random
import string
import csv
from itertools import chain, islice
from typing import AnyStr, Dict

from psycopg2 import sql
import psycopg2
import django
from django.db import models, connection

from heron.loggers import LOGGER_POSTGRES_SAVE
from .models import Trace, Line
from .exceptions import (
    PostgresDjangoError,
    PostgresInsertMethodError,
    PostgresCardinalityViolationError,
    PostgresUniqueError,
    PostgresKeyError,
    PostgresTypeError,
    PostgresPreparedError,
)


def iter_slice(iterable, taille, form=tuple):
    """
    Parcourir n'importe quel itérable, par tailles
        exemple :
            l = [1, 2, 3, 4, 5, 6, 7, 8, 9]
            rows = iter_slice(l, 4)
            for r in rows:
                print(r)
            ... (1, 2, 3, 4)
            ... (5, 6, 7, 8)
            ... (9, )
        :param iterable: List, tuple, set, str etc...
        :param taille: Nombre
        :param form: Format de sortie, par default tuple, mais on peut choisir, list, set ...
        :return: Générateur par tranches
    """
    try:
        i_t = iter(iterable)
        while True:
            yield form(chain((next(i_t),), islice(i_t, taille - 1)))
    except StopIteration:
        return


def execute_batch(cur, sql_execute, iterable, page_size=500):
    """
    Fonction prise à psycopg2.
    execute batch, avec ajout de renvoi du nombre d'éléments envoyés en insertion
        :param cur:         Cursor psycopg2
        :param sql_execute: Requete sql
        :param iterable:    Iterateur des données à insèrer en base
        :param page_size:   Taille du slicing des tranches
        :return: Slicing de l'itérateur par longeur de page_size
    """
    erreur = False
    count_initial = 0
    count_final = 0

    for page in iter_slice(iterable, taille=page_size):
        nbre = len(page)
        count_initial += nbre

        try:
            sqls = [cur.mogrify(sql_execute, args) for args in page]
            cur.execute(b";".join(sqls))
            count_final += nbre

        except psycopg2.OperationalError:
            LOGGER_POSTGRES_SAVE.exception("Cconnexion à Postgres fermée de manière inattendue")

        except psycopg2.Error:
            LOGGER_POSTGRES_SAVE.exception("Erreur sur les insertions execute_bach")

    return erreur, (count_initial, count_final)


def execute_prepared_upsert(cursor, sql_prepare, sql_execute, sql_deallocate, rows, page_size):
    """
    Fonction qui exécute une requete préparée, INSERT ou UPSERT.
        Attention!!! Cette requête sera en autocommit.
    Exemple :
        cursor.execute("PREPARE stmt (int) AS INSERT INTO foo VALUES ($1) ON CONFLICT DO NOTHING;")
        execute_batch(cursor, "EXECUTE stmt (%s, %s, %s)", list_values)
        cursor.execute("DEALLOCATE stmt")
    :param cursor:          Cusor au sens psycopg2
    :param sql_prepare:     Requête préparée
    :param sql_execute:     Requête de l'exécution propement dite
    :param sql_deallocate:  Sql pour le deallocate
    :param rows:            Flux iterateur
    :param page_size:       Taille des passes
    """
    try:
        cursor.execute(sql_prepare)
        error, tup_count = execute_batch(cursor, sql_execute, rows, page_size=page_size)
        cursor.execute(sql_deallocate)

    except psycopg2.Error as except_error:
        cursor.execute(sql_deallocate)
        raise PostgresPreparedError("Erreur sur execute_prepared_upsert") from except_error

    return error, tup_count


def get_random_name(size=10):
    """
    Génère une suite de lettre alléatoire en minuscule
    :param size: taille
    :return: suite de lettres en minuscule
    """
    ascii_choices = string.ascii_lowercase
    return "".join(random.SystemRandom().choice(ascii_choices) for _ in range(size)).lower()


class PostgresDjangoUpsert:
    """
    Class pour l'insertion en base de donnée de fichier de type csv
    (de préférence au format io.StringIO) par des méthodes de copy_expert, copy_from
    et execute_batch psycopg2.
    """

    def __init__(
        self,
        model: models.Model,
        fields_dict: Dict,
        cnx: connection = connection,
        exclude_update_fields: set = None,
    ):
        """
        :param model:       Model Django
        :param fields_dict: Dictonnaire des champs à utiliser pour les insertions en base.
                            True pour les champs uniques et False pour les champs à update
                            ex : fields_dict = {"unique": True, "other": False, ...}
                            Attention! les champs devront être dans le même ordre
                            que les colonnes du fichier
        :param cnx:         Object connexion à Postgresql
        """
        self.model = model
        self.fields_dict = fields_dict
        self.meta = self.model._meta
        self.table_name = self.meta.db_table
        self.cnx = cnx
        if exclude_update_fields is None:
            exclude_update_fields = set()
        self.exclude_update_fields = exclude_update_fields
        self.temp_table_name = self.get_temp_table_name()
        self.fields_list = self.get_fields_list()

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

    def get_column_field(self, field_key: AnyStr):
        """
        :param field_key: Champ du model django à retouner
        :return: Le Sql des paramètres de création de la table temporaire
        """

        try:
            field_attr = self.meta.get_field(field_key)

        except django.core.exceptions.FieldDoesNotExist as except_error:
            raise PostgresKeyError(
                f"""la clé "{field_key}" n'éxiste pas dans la table"""
            ) from except_error

        return field_attr

    def get_column_properties(self, field_key: AnyStr):
        """
        :param field_key: Champ du model django à retouner
        :return: Le Sql des paramètres de création de la table temporaire
        """
        field_attr = self.get_column_field(field_key)
        return (
            f' "{field_attr.column if field_attr.db_column is None else field_attr.db_column}" '
            f"{field_attr.db_type(self.cnx)} "
            f'{"NOT NULL" if not self.meta.get_field(field_key).null else "NULL"}'
        )

    def get_null_fields(self):
        """Retourne la liste des champs qui peuvent être null"""
        null_fields_list = []

        for field_key in self.fields_dict.keys():
            field = self.meta.get_field(field_key)
            if field.null:
                null_fields_list.append(
                    f'"{field.column}"' if field.db_column is None else f'"{field.db_column}"'
                )

        if null_fields_list:
            return f"FORCE_NULL ({','.join(null_fields_list)}) "

        return ""

    def get_fields_list(self):
        """
        Retourne la liste des champs db_column
        :return:
        """
        fields_list = []

        for field_key in self.fields_dict.keys():
            field_attr = self.get_column_field(field_key)
            fields_list.append(
                field_attr.column if field_attr.db_column is None else field_attr.db_column
            )

        return fields_list

    def get_prepare_batch(self, stmt_name: AnyStr):
        """
        :param stmt_name: Nom du prepare stmt
        :return: Les bases de la requête préparée
        """
        with self.cnx.cursor() as cursor:
            sql_champs = sql.SQL(
                "SELECT column_name, data_type, character_maximum_length, is_nullable "
                "FROM information_schema.columns "
                "WHERE table_name = '{table}'"
            ).format(table=sql.SQL(self.table_name))
            cursor.execute(sql_champs)
            dict_fields = {row[0]: row[1] for row in cursor.fetchall()}
            tipes = [sql.SQL(dict_fields.get(key)) for key in self.fields_list]
            stmt_ident = sql.Identifier(stmt_name)
            params = ", ".join([f"${i}" for i, _ in enumerate(tipes, 1)])
            exe_val = ", ".join(["%s" for _ in tipes])
            prepare = sql.SQL(
                "PREPARE {stmt_name} ({tipes}) AS INSERT INTO {table} ({fields}) "
                "VALUES ({params}) "
            ).format(
                stmt_name=stmt_ident,
                tipes=sql.SQL(", ").join(tipes),
                table=sql.Identifier(self.table_name),
                fields=self.get_fields(),
                params=sql.SQL(params),
            )
            sql_execute = sql.SQL("EXECUTE {stmt_name} ({exe_val})").format(
                stmt_name=stmt_ident,
                exe_val=sql.SQL(exe_val),
            )
            sql_deallocate = sql.SQL("DEALLOCATE {stmt_name}").format(stmt_name=stmt_ident)

            return prepare, sql_execute, sql_deallocate

    def get_columns_upsert(self):
        """
        :return: Les clauses du SQL d'un upsert ON CONFICT ... UPDATE
        """
        fields_upsert_dict = {
            "conflict": [],
            "update": [],
        }

        for field_key, bool_value in self.fields_dict.items():
            field_attr = self.get_column_field(field_key)
            field = field_attr.column if field_attr.db_column is None else field_attr.db_column
            if bool_value:
                fields_upsert_dict.get("conflict").append(field)
            else:
                fields_upsert_dict.get("update").append(field)

        return fields_upsert_dict

    def get_fields(self, bool_pk=False):
        """
        :param bool_pk: Si on a besoins d'un champ pk, pour un ordre idention aux insertions
        :return: les champs interprétés allant servir dans une requête
        """

        return sql.SQL(", ").join(
            [sql.Identifier(field) for field in self.fields_list]
            if not bool_pk
            else [sql.Identifier("pk")] + [sql.Identifier(field) for field in self.fields_list]
        )

    @property
    def get_base_insert(self):
        """
        :return: Le début du SQL de la requête d'insertion
        """
        insert_table = sql.Identifier(self.table_name)
        from_table = sql.Identifier(self.temp_table_name)

        return insert_table, from_table

    def get_ddl_temp_table(self, bool_pk=False):
        """
        :param bool_pk: Si on a besoins d'un champ pk, pour un ordre idention aux insertions
        :return: Le SQL du DDL de création d'une table temporaire
        """
        create_table = sql.Identifier(self.temp_table_name)
        fields_list = (
            [self.get_column_properties(field) for field in self.fields_dict]
            if not bool_pk
            else ['"pk" bigint'] + [self.get_column_properties(field) for field in self.fields_dict]
        )
        suffix_sql = f" ({', '.join(fields_list)})"
        sql_create = sql.SQL("CREATE TEMPORARY TABLE {create_table}" + suffix_sql).format(
            create_table=create_table
        )

        return sql_create

    @property
    def get_query_insert(self):
        """
        :return: Le SQL de la clause ON CONFLICT DO NOTHING pour la requête upsert
        """
        insert_table, from_table = self.get_base_insert
        sql_insert = sql.SQL(
            "INSERT INTO {insert_table} ({fields})  SELECT {fields} FROM {form_table} "
        ).format(insert_table=insert_table, form_table=from_table, fields=self.get_fields())
        return sql_insert

    @property
    def get_query_do_nothing(self):
        """
        :return: Le SQL de la clause ON CONFLICT DO NOTHING pour la requête upsert
        """
        sql_insert = sql.SQL("{base} ON CONFLICT DO NOTHING").format(base=self.get_query_insert)
        return sql_insert

    @property
    def get_conflict_upsert_fields(self):
        """
        :return: Le SQL de la clause ON CONFLICT ... DO UPDATE pour la requête paramétrée
        """

        fields_conflict = sql.SQL(", ").join(
            [sql.Identifier(field) for field in self.get_columns_upsert().get("conflict")]
        )
        update_columns = sql.SQL(", ").join(
            [
                sql.SQL("{field}=EXCLUDED.{field}").format(field=sql.Identifier(field))
                for field in self.get_columns_upsert().get("update")
                if field not in self.exclude_update_fields
            ]
        )
        return fields_conflict, update_columns

    @property
    def get_query_upsert(self):
        """
        :return: Le SQL de la clause ON CONFLICT ... DO UPDATE pour la requête upsert
        """
        fields_conflict, update_columns = self.get_conflict_upsert_fields
        sql_upsert = sql.SQL(
            "{base} ON CONFLICT ({fields_conflict}) DO UPDATE SET {update_columns}"
        ).format(
            base=self.get_query_insert,
            fields_conflict=fields_conflict,
            update_columns=update_columns,
        )

        return sql_upsert

    @property
    def get_upsert_batch(self):
        """
        :return: Le SQL de la clause ON CONFLICT ... DO UPDATE pour la requête paramétrée
        """
        with self.cnx.cursor() as cursor:
            fields_conflict, update_columns = self.get_conflict_upsert_fields
            sql_upsert = sql.SQL(
                "ON CONFLICT ({fields_conflict}) DO UPDATE SET {update_columns}"
            ).format(fields_conflict=fields_conflict, update_columns=update_columns)

            return cursor.mogrify(sql_upsert).decode()

    def get_prepare_smt(self, mode: AnyStr, stmt_name: AnyStr):
        """
        :param mode:      Mode d'insertion d'une requête préparée
        :param stmt_name: Nom du prepare stmt
        :return: Le SQL de la clause ON CONFLICT ... DO UPDATE pour la requête upsert
        """
        dict_mode = {
            "insert": "",
            "do_nothing": "ON CONFLICT DO NOTHING",
            "upsert": self.get_upsert_batch,
        }
        prepare, sql_execute, sql_deallocate = self.get_prepare_batch(stmt_name)

        sql_prepare = sql.SQL("{prepare} {mode_insert}").format(
            prepare=prepare, mode_insert=sql.SQL(dict_mode.get(mode))
        )

        return sql_prepare, sql_execute, sql_deallocate

    @property
    def get_drop_temp(self):
        """
        :return: Le SQL de suppression de la table provisoire
        """
        table_drop = sql.Identifier(self.temp_table_name)
        sql_drop = sql.SQL("DROP TABLE IF EXISTS {table_drop}").format(table_drop=table_drop)

        return sql_drop

    def insertion(
        self,
        file: io.StringIO,
        insert_mode: AnyStr = "upsert",
        delimiter: AnyStr = ";",
        quote_character: AnyStr = '"',
        kwargs_prepared: Dict = None,
    ):
        """
        Realise l'insertion choisie (upsert, do_nothing, insert)
        :param file:            Fichier au format io.StringIO
        :param insert_mode:     Mode d'insertion choisi
        :param delimiter:       Séparateur des lignes du fichier
        :param quote_character: Quotation des champs
        :param kwargs_prepared: Dictionnaire des attributs nécessaires à la requête préparée
                                kwargs_prepared = {
                                    "mode": "insert" ou "do_nothing" ou "upsert",
                                    "page_size": None ou nbre par iteration par défault 500,

                                }
        """

        insert_mode_dict = {
            "insert": None,
            "do_nothing": self.get_query_do_nothing,
            "upsert": self.get_query_upsert,
            "prepared": "",
            "pre_validation": "",
        }
        trace_prepared = kwargs_prepared.get("trace", {})

        if insert_mode not in insert_mode_dict:
            raise PostgresInsertMethodError(
                f"La methode {insert_mode!r} d'insertion choisie n'existe pas"
            )

        with self.cnx.cursor() as cursor:
            try:
                fields = self.get_fields()
                delimiter = sql.SQL(delimiter)
                quote_character = sql.SQL(quote_character)
                get_null_field = (
                    f"{self.get_null_fields()}{', ' if self.get_null_fields() else ''} "
                )
                sql_expert = (
                    "COPY {table} ({fields}) "
                    "FROM STDIN "
                    "WITH ("
                    "DELIMITER '{delimiter}', "
                    f"{get_null_field}"
                    "QUOTE '{quote_character}', "
                    "FORMAT CSV )"
                )
                # print("sql_expert :", sql_expert)
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

                elif insert_mode == "prepared":
                    # Insertion en base avec une requête préparée.
                    if kwargs_prepared is None:
                        raise PostgresPreparedError(
                            "Vous devez donner le dictionnaire des attributs pour execute_bach, "
                            "pour le mode d'insertion prepared"
                        )
                    stmt_name = get_random_name()

                    # if kwargs_prepared.get("mode") not in {"insert", "do_nothing", "upsert"}:
                    #     raise PostgresInsertMethodError(
                    #         f"La methode {kwargs_prepared.get('mode')!r} "
                    #         "d'insertion choisie n'existe pas"
                    #     )
                    sql_prepare, sql_execute, sql_deallocate = self.get_prepare_smt(
                        kwargs_prepared.get("mode"), stmt_name
                    )
                    csv_rows = csv.reader(
                        file,
                        delimiter=";",
                        quotechar='"',
                        lineterminator="\n",
                        quoting=csv.QUOTE_MINIMAL,
                    )
                    error, tup_count = execute_prepared_upsert(
                        cursor,
                        sql_prepare,
                        sql_execute,
                        sql_deallocate,
                        csv_rows,
                        kwargs_prepared.get("page_size", 500),
                    )

                    return error, tup_count

                elif insert_mode == "pre_validation":
                    self.insert_with_pre_validation(
                        file,
                        delimiter=delimiter,
                        quote_character=quote_character,
                        trace=trace_prepared,
                    )

                else:
                    # copy dans une table provisoire pour un do_nothing ou un upsert
                    table = sql.Identifier(self.temp_table_name)
                    # print(cursor.mogrify(self.get_ddl_temp_table()).decode())
                    cursor.execute(self.get_ddl_temp_table())
                    sql_copy = sql.SQL(sql_expert).format(
                        table=table,
                        fields=fields,
                        delimiter=delimiter,
                        quote_character=quote_character,
                    )
                    # print(cursor.mogrify(sql_copy).decode())
                    # print(*file)
                    # file.seek(0)
                    # for line in file:
                    #     print(line)

                    file.seek(0)
                    cursor.copy_expert(sql=sql_copy, file=file)

                    # do_nothing ou upsert
                    # print(
                    #     "insert_mode_dict.get(insert_mode) : ",
                    #     insert_mode_dict.get(insert_mode)
                    # )
                    cursor.execute(insert_mode_dict.get(insert_mode))

                    # suppression de la table provisoire
                    cursor.execute(self.get_drop_temp)

            except (
                psycopg2.errors.CardinalityViolation,
                django.db.utils.ProgrammingError,
            ) as except_error:
                raise PostgresCardinalityViolationError(
                    f"Conflit à l'insertion, trace N° : {trace_prepared!r}"
                ) from except_error

            except psycopg2.errors.InvalidTextRepresentation as except_error:
                file.seek(0)
                LOGGER_POSTGRES_SAVE.exception(
                    f"{except_error}\ntable : {table}\nfields : {fields}\n{file.read()!r}"
                )
                raise PostgresTypeError(
                    f"Erreur de type, trace N° : {trace_prepared!r}"
                ) from except_error

            except psycopg2.errors.UniqueViolation as except_error:
                raise PostgresUniqueError(
                    f"Erreur sur clé dupliquée, trace N° : {trace_prepared!r}"
                ) from except_error

            except Exception as except_error:
                file.seek(0)
                LOGGER_POSTGRES_SAVE.exception(
                    f"{except_error}\ntable : {table}\nfields : {fields}\n{file.read()!r}"
                )
                raise PostgresDjangoError(
                    f"Erreur inconnue, trace N° : {trace_prepared!r}"
                ) from except_error

        return True

    def get_columns_constraints(self, cursor):
        """
        :param cursor: Cursor de connexion psycopg2 à Postgresql
        :return: Retourne les contraintes d'unicité et les foreign key obligatoire
        """
        uniques_list = []
        foreign_keys_dict = {}

        cursor.execute(
            sql.SQL(
                """
        select column_name
        from information_schema.columns 
        where table_name = '{table_name}'
        """
            ).format(table_name=sql.SQL(self.temp_table_name))
        )
        columns_temps_table = {columns[0] for columns in cursor.fetchall()}

        cursor.execute(
            sql.SQL(
                """
        select
            pgc.contype, 
            ccu.table_name,
            case when pgc.contype = 'u' then '' else pga.attname end as column,
            string_agg(distinct ccu.column_name, ';') as constraint_columns,
            case 
                when pgc.contype = 'u' then false
                when is_nullable='YES' then false 
                else true 
            end as mandatory
        from pg_constraint pgc
            join pg_namespace nsp on nsp.oid = pgc.connamespace
            join pg_class  cls on pgc.conrelid = cls.oid
            left join information_schema.constraint_column_usage ccu
                   on pgc.conname = ccu.constraint_name
                  and nsp.nspname = ccu.constraint_schema
            left join pg_attribute pga
                   on pga.attrelid = pgc.conrelid
                  and pga.attnum   = ANY(pgc.conkey) 
            left join information_schema.columns ccc
                on nsp.nspname = ccc.table_schema 
                and pga.attname = ccc.column_name
        where cls.relname = '{table_name}'
        and contype  in ('f', 'u')
        group by case when pgc.contype = 'u' then '' else pga.attname end,
                 cls.relname, 
                 ccu.table_name, 
                 pgc.contype, 
                 pgc.conkey,
                 case 
                    when pgc.contype = 'u' then false
                    when is_nullable='YES' then false 
                    else true 
                 end
        """
            ).format(table_name=sql.SQL(self.table_name))
        )

        for constraints in cursor.fetchall():
            test_constraints = constraints[0]
            constraint_columns = constraints[3]

            if test_constraints == "u":
                uniques_list.append(
                    [
                        column
                        for column in constraints[3].split(";")
                        if column in columns_temps_table
                    ]
                )

            if test_constraints == "f":
                table = constraints[1]
                column = constraints[2]
                mandatory = constraints[4]
                # if column in columns_temps_table:
                if foreign_keys_dict.get(table):
                    foreign_keys_dict[table].append((column, constraint_columns, mandatory))
                else:
                    foreign_keys_dict[table] = [(column, constraint_columns, mandatory)]

        return uniques_list, foreign_keys_dict

    @staticmethod
    def check_unique_key(cursor, table, uniques_list):
        """
        :param cursor:       Cursor de connexion psycopg2 à Postgresql
        :param table:        Table en BDD à tester
        :param uniques_list: Liste des champs uniques dans la table y compris groupe d'unicité
        :return: Check des combinaisons  clefs uniques dans la table
        """
        base_sql = """
        select '{columns}' as col, {separate_columns}::TEXT as val, count({concat_columns}) as nb
        from {table}
        group by {separate_columns}::TEXT
        having count({concat_columns}) > 1
        """

        sql_uniques = "union all".join(
            [
                base_sql.format(
                    columns="__".join(cols),
                    separate_columns=(
                        f"""concat({", ' | ', ".join([f'"{col}"' for col in cols])})"""
                        if len(cols) > 1
                        else f'"{cols[0]}"'
                    ),
                    concat_columns=(
                        f"""concat({" , ".join([f'"{col}"' for col in cols])})"""
                        if len(cols) > 1
                        else f'"{cols[0]}"'
                    ),
                    table=table,
                )
                for cols in uniques_list
            ]
        )
        cursor.execute(sql.SQL(sql_uniques))

        return cursor.fetchall()

    def check_foreign_key(self, cursor):
        """
        :param cursor: Cursor de connexion psycopg2 à Postgresql
        :return: Check que les clefs étrangères existent dans la table liée
        """

    def insert_with_pre_validation(
        self,
        file: io.StringIO,
        delimiter: AnyStr = ";",
        quote_character: AnyStr = '"',
        trace: Trace = None,
    ):
        """
        Méthode pour insertion avec auparavant, une pré-validation, des clés primaires
        ou des clés groupées. Une Trace sera mise en place dans le cadre d'import de fichier suivi.
        :param file:            Fichier au format io.StringIO
        :param delimiter:       Séparateur des lignes du fichier
        :param quote_character: Quatation des champs
        :param trace:           models Django Trace, pour tracer un import
        :return:
        """
        # TODO : Implémentation de la validation des clés éxistantes à finir d'implémenter
        numbered_io_file = io.StringIO()

        if trace:
            error_line = Line
            print(error_line)

        for i, line in enumerate(file):
            numbered_io_file.write(f"{quote_character}{str(i)}{quote_character}{delimiter}" + line)

        numbered_io_file.seek(0)

        with self.cnx.cursor() as cursor:
            # copy dans une table provisoire pour un do_nothing ou un upsert
            fields = self.get_fields(bool_pk=True)
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
            table = sql.Identifier(self.temp_table_name)
            cursor.execute(self.get_ddl_temp_table(bool_pk=True))
            sql_copy = sql.SQL(sql_expert).format(
                table=table,
                fields=fields,
                delimiter=delimiter,
                quote_character=quote_character,
            )
            cursor.copy_expert(sql=sql_copy, file=numbered_io_file)

            uniques_list, foreign_keys_dict = self.get_columns_constraints(cursor)

            print(uniques_list, foreign_keys_dict)
            if any(uniques_list):
                uniques = self.check_unique_key(cursor, self.temp_table_name, uniques_list)

                for columns, values, number in uniques:
                    print("values : ", "--".join(columns.split("__")), values, number)

            # # do_nothing ou upsert
            # cursor.execute(insert_mode_dict.get(insert_mode))

            # suppression de la table provisoire
            cursor.execute(self.get_drop_temp)
