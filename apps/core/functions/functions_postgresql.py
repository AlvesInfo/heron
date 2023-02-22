# pylint: disable=E0401,R0913,W1514,W0702,R0914
"""
Module apportant des fonctionnalités pratique à psycopg2
"""
import sys
import os
import io
import random
import string
from typing import AnyStr, Dict
from pathlib import Path

import psycopg2
from psycopg2 import pool
from psycopg2.extensions import parse_dsn
from django.db import models, connection

from apps.core.functions.functions_sql import clean_sql_in
from apps.core.functions.loggers import POSTGRES_LOGGER
from heron.settings.base import BASE_DIR


class PostgresUpsertError(Exception):
    """Exceptions pour l'upsert dans une table postgresql"""


class PoolPostgresql:
    """
    Class de pool de connection à Postgresql, cela permet d'utiliser
    les fonctions qui demande une connection psycopg2
        :param string_of_connexion: string de connection à postgresql
        exemple d'utilisation :
            >>> from apps.core.functions.functions_postgresql import PoolPostgresql
            >>> cnx_string = (
                    f"dbname=dbname "
                    f"user=user "
                    f"password=password "
                    f"host=host "
                    f"port=port"
                )
            >>> with PoolPostgresql(cnx_string) as cnx:
            ...     with cnx.cursor() as cur:
            ...         cur.execute("SELECT * FROM articles_article limit 1")
            ...         print(cur.fetchall()[0][:3])
            (816134, datetime.datetime(2014, 8, 21), datetime.datetime(2019, 1, 29))
    """

    pool_instance = None
    cnx_string = None
    pool_cnx = None

    def __init__(self, string_of_connexion):
        self.key = id(self)

        if not PoolPostgresql.pool_instance:
            self.__class__.pool_instance = self
            self.__class__.cnx_string = string_of_connexion
            self.pool_connect()

        self.cnx = self.get_cnx()

    def pool_connect(self):
        """
        Fonction de génération du pool de connexion
        """
        if not self.__class__.pool_cnx:
            i = 0

            while i < 5:
                try:
                    self.__class__.pool_cnx = pool.SimpleConnectionPool(
                        1, 20, self.__class__.cnx_string
                    )
                    break

                except psycopg2.Error as except_error:
                    log_line = f"PoolPostgresql error: {except_error}\n"
                    print(log_line)

                i += 1

    def get_cnx(self):
        """
        Fonction de génération de demande de connexion au pool
        """
        cnx = None

        try:
            if not self.__class__.pool_cnx:
                self.pool_connect()
            cnx = self.__class__.pool_cnx.getconn(key=self.key)

        except psycopg2.pool.PoolError as except_error:
            if except_error == "cnx pool is closed":
                self.pool_connect()
                self.cnx = self.get_cnx()
            else:
                print(sys.exc_info()[1])

        return cnx

    def close_cnx(self):
        """
        Fonction de fermeture de la connexion au pool
        """
        if self.__class__.pool_cnx:
            self.__class__.pool_cnx.putconn(self.cnx, key=self.key, close=True)

    @classmethod
    def close_all(cls):
        """
        Fonction de fermeture de toutes les connexions
        """
        cls.pool_cnx.closeall()
        cls.pool_cnx = None

    def __enter__(self):
        """
        Fonction __enter__ pour la gestion du with
        """
        return self.get_cnx()

    def __exit__(self, *args, **kwargs):
        """
        Fonction __exit__ pour la gestion du with
        """
        self.close_cnx()


class WithCnxPostgresql:
    """
    Classe de connection à postgresql avec with
        conn = WithCnxPostgresql(dsn)
        # transaction 1
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql)
        # transaction 2
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql)
    """

    def __init__(self, string_of_connexion):
        self.connexion = None
        i = 0
        while i < 5:
            try:
                kwargs_cnx = parse_dsn(string_of_connexion)
                self.connexion = psycopg2.connect(**kwargs_cnx)
                break

            except psycopg2.Error as except_error:
                log_line = f"WithCnxPostgresql error: {except_error}\n"
                print(log_line)

            i += 1

    def __enter__(self):
        return self.connexion

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connexion is not None:
            self.connexion.close()


def cnx_postgresql(string_of_connexion):
    """
    Fonction de connexion à Postgresql par psycopg2
        :param string_of_connexion: cnx_string = (
                                        f"dbname={NAME_DATABASE} "
                                        f"user={USER_DATABASE} "
                                        f"password={PASSWORD_DATABASE} "
                                        f"host={HOST_DATABASE} "
                                        f"port={PORT_DATABASE}"
                                    )
        :return: cnx
    """
    try:
        kwargs_cnx = parse_dsn(string_of_connexion)
        connexion = psycopg2.connect(**kwargs_cnx)

    except psycopg2.Error as except_error:
        log_line = f"cnx_postgresql error: {except_error}\n"
        print(log_line)
        connexion = None

    return connexion


def query_select(cnx, sql_requete=None):
    """
    Fonction qui retourne le resultat d'une requête sql Postgresql.
        :param cnx: Connexion à la base postgresql psycopg2
        :param sql_requete: requête selection souhaitée
                                ex: "SELECT * FROM table"
        :return: La liste des éléments de la requête
    """
    if sql_requete:
        try:
            with cnx.cursor() as cur:
                cur.execute(sql_requete)
                list_rows = cur.fetchall()
            return list_rows

        except psycopg2.Error as except_error:
            log_line = f"query_select error: {except_error}\n"
            print(log_line)
            # write_log(self.log_file, log_line)
            # envoi_mail_erreur(log_line)
    return None


def query_real_dict_cursor(cnx, sql_requete=None, params=None):
    """
    Fonction qui retourne le resultat d'une requête sql Postgresql, comme un dictionnaire
        :param cnx: connexion à la base postgresql psycopg2
        :param sql_requete: requête selection souhaitée
                                ex: "SELECT * FROM table"
        :param params: dictionnaire des paramètes à passer
        :return: La liste des dictionnaires de la requête
    """
    if params is None:
        params = dict()

    if sql_requete:
        try:
            with cnx.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                if params:
                    cur.execute(sql_requete, params)
                else:
                    cur.execute(sql_requete)
                list_rows = cur.fetchall()
            return list_rows

        except psycopg2.Error as except_error:
            log_line = f"query_real_dict_cursor error: {except_error}\n"
            print(log_line)
            # write_log(self.log_file, log_line)
            # envoi_mail_erreur(log_line)

    return None


def query_execute(cnx, sql_requete=None):
    """
    Fonction qui exécute une requête sql Postgresql.
        :param cnx: Connexion à la base postgresql psycopg2
        :param sql_requete: requête selection souhaitée
                                ex: "UPDATE table SET champ=1"
                                    "UPDATE table SET champ=1 WHERE x = 0"
                                    "DELETE FROM table"
        :return: True ou None si exception
    """
    if sql_requete:
        try:
            with cnx.cursor() as cur:
                cur.execute(sql_requete)
                cnx.commit()
            return True

        except psycopg2.Error as except_error:
            log_line = f"query_execute error: {except_error}\n"
            print(log_line)
            # write_log(self.log_file, log_line)
            # envoi_mail_erreur(log_line)

    return None


def query_dict(cnx, sql_requete=None, params=None):
    """
    Fonction qui retourne le resultat d'une requête sql Postgresql, comme un dictionnaire
        :param cnx: connexion à la base postgresql psycopg2
        :param sql_requete: requête selection souhaitée
                                ex: "SELECT * FROM table"
        :param params: dictionnaire des paramètes à passer
        :return: La liste des dictionnaires de la requête
    """
    if params is None:
        params = dict()

    if sql_requete:
        try:
            with cnx.cursor() as cur:
                if params:
                    cur.execute(sql_requete, params)
                else:
                    cur.execute(sql_requete)

                columns = [col[0] for col in cur.description]

                return [dict(zip(columns, row)) for row in cur.fetchall()]

        except psycopg2.Error as except_error:
            log_line = f"query_real_dict_cursor error: {except_error}\n"
            print(log_line)

    return None


def copy_from(cnx, file, table, sep=";", columns=None, size=8192, null=None, header=None):
    """
    Fonction qui integre un csv dans une table Postgresql.
        copy_from(file, table, sep='\t', null='\\N', columns=None)
        :param cnx: connexion à la base postgresql psycopg2
        :param file: fichier csv à intégrer
        :param table: table d'insertion
        :param sep: séparation des champs du fichier
        :param columns: colonnes
        :param size: taille du buffer
        :param null: valeur du null dans le fichier
        :param header: si il y a des entêtes dans le fichier
        :return: True ou None si exception
    """
    try:
        with cnx.cursor() as cur:
            with open(file, "r") as fichier:
                if header is not None:
                    next(fichier)

                if null is not None:
                    cur.copy_from(fichier, table, sep=sep, columns=columns, size=size, null=null)
                else:
                    cur.copy_from(fichier, table, sep=sep, columns=columns, size=size)

                return True, "succes"

    except psycopg2.Error as except_error:
        log_line = f"copy_from error: {except_error!r}\n"
        print(log_line)
        # write_log(self.log_file, log_line)
        # envoi_mail_erreur(log_line)
        return None, log_line


def get_types_champs(cnx, table, list_champs=None):
    """
    Fonction qui récupère les types de champs de la table et des champs demandés pour la requête
        :return: list des champs, (taille, type, list des champs)
    """
    columns = f"AND column_name {clean_sql_in(list_champs)}" if list_champs is not None else ""

    with cnx.cursor() as cursor:
        sql_champs = f"""
            SELECT column_name, data_type, character_maximum_length, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = '{table}' 
            {columns};
        """
        # print(sql_champs)
        cursor.execute(sql_champs)
        list_champs_taille_type = {r[0]: tuple(r[1:]) for r in cursor.fetchall()}

    return list_champs_taille_type, list_champs


def _paginate(seq, page_size):
    """
    Fonction prise à psycopg2.
    Slicing d'un itérable pour execute_batch
        :param seq: itérable
        :param page_size: taille en sortie
        :return: Slicing de l'itérateur par longeur de page_size
    """
    page = []
    ite = iter(seq)
    while 1:
        try:
            for _ in range(page_size):
                page.append(next(ite))
            yield page
            page = []
        except StopIteration:
            if page:
                yield page
            return


def executebatch(cur, sql, iterable, page_size=500):
    """
    Fonction prise à psycopg2.
    execute batch, qui renvoi le nombre d'éléments envoyés en insertion
        :param cur: cursor psycopg2
        :param sql: requete sql
        :param iterable: iterateur des données à insèrer en base
        :param page_size: taille du slicing des tranches
        :return: Slicing de l'itérateur par longeur de page_size
    """
    erreur = True
    count_initial = 0
    count_final = 0

    for page in _paginate(iterable, page_size=page_size):
        nbre = len(page)
        count_initial += nbre

        try:
            if erreur:
                sqls = [cur.mogrify(sql, args) for args in page]
                cur.execute(b";".join(sqls))
                count_final += nbre
                # print(count_final)
        except:
            # print("sys.exc_info() : ", sys.exc_info()[1])
            # print(sqls)
            POSTGRES_LOGGER.exception("execute_bash")
            erreur = None
            break

    return erreur, (count_initial, count_final)


def execute_prepared_upsert(kwargs_upsert):
    """Fonction qui exécute une requete préparée, INSERT ou UPSERT.
    Attention!!! Cette requête sera en autocommit.
    Exemple :
    cursor.execute("PREPARE stmt (int, text, bool)
    AS INSERT INTO foo VALUES ($1, $2, $3) ON CONFLICT DO NOTHING;")
    execute_batch(cursor, "EXECUTE stmt (%s, %s, %s)", list_values)
    cursor.execute("DEALLOCATE stmt")

        :param kwargs_upsert: {
                      cnx: connexion psycopg2
                    table: table concernée par la requête
                  columns: champs de la table, souhaités dans la requête
                     rows: Liste des valeurs à inserer dans la table
            champs_unique: liste des champs d'unicité dans la table,
                           si on veut un Upsert ON CONFLICT UPDATE
                   upsert: None explicit, si on ne souhaite pas d'upsert
                page_size: rien ou nbre par iteration
                }
        :return: True, (1000, 1000) en cas de succès
                 None, (elements_all, elements_ok) en cas d'erreur
    """
    dict_rows = get_types_champs(
        kwargs_upsert["cnx"], kwargs_upsert["table"], kwargs_upsert["columns"]
    )[0]
    prepare = "PREPARE stmt ("
    insert = "("
    colonnes = "("
    execute = "EXECUTE stmt ("

    for i, k in enumerate(kwargs_upsert["columns"]):
        champ, t_p = k, dict_rows[k][0]
        prepare += f"{t_p}, "
        insert += f"${str(i + 1)}, "
        colonnes += f'"{champ}", '
        execute += "%s, "
    colonnes = f"{colonnes[:-2]})"
    insert = f"{insert[:-2]})"
    prepare = f"""
    {prepare[:-2]}) AS INSERT INTO "{kwargs_upsert['table']}" {colonnes} VALUES {insert} 
    """
    execute = f"{execute[:-2]});"

    if kwargs_upsert["upsert"] is None:
        prepare += ";"

    else:
        if kwargs_upsert["champs_unique"] is None:
            prepare += "ON CONFLICT DO NOTHING;"

        else:
            chu = "("
            for k in kwargs_upsert["champs_unique"]:
                chu += f'"{k}", '
            chu = f"{chu[:-2]})"
            prepare += f" ON CONFLICT {chu} DO UPDATE SET "
            for champ in kwargs_upsert["columns"]:
                if champ not in kwargs_upsert["champs_unique"]:
                    prepare += f'"{str(champ)}" = excluded."{str(champ)}", '

            prepare = f"{prepare[:-2]};"

    page_size = kwargs_upsert.get("page_size", 500)
    print(prepare)
    print(insert)
    print(execute)
    try:
        # with kwargs_upsert["cnx"] as cnx:
        with kwargs_upsert["cnx"].cursor() as cursor:
            cursor.execute(prepare)
            error, tup_count = executebatch(
                cursor, execute, kwargs_upsert["rows"], page_size=page_size
            )
            cursor.execute("DEALLOCATE stmt")

    except psycopg2.Error as err:
        POSTGRES_LOGGER.exception("execute_prepared_upsert")
        tup_count = err
        error = None
        try:
            # with kwargs_upsert["cnx"] as cnx:
            with kwargs_upsert["cnx"].cursor() as cursor:
                cursor.execute("DEALLOCATE stmt")
        except:
            POSTGRES_LOGGER.exception("deallocate stmt")

    return error, tup_count


def get_random_name(size=10):
    """
    Retourne une suite de lettre alléatoire
    :param size: taille
    :return: texte
    """
    ascii_choices = string.ascii_lowercase
    return "".join(random.SystemRandom().choice(ascii_choices) for _ in range(size)).lower()


class PostresDjangoUpsert:
    """
    Class pour l'insertion en base de donnée de fichier de type csv
    (de préférence au format io.StringIO) par des méthodes de copy_from psycopg2.
    Ces méthodes d'insertion sont plus rapides, mais elle empêche d'avoir les erreurs par lignes
    """

    def __init__(
        self, model: models.Model, fields_dict: AnyStr, cnx: connection, exclude_fields_set=None
    ):
        """
        :param model:               Model Django
        :param fields_dict:         Dictonnaire des champs à utiliser pour les insertions en base.
                                    True pour les champs uniques et False pour les champs à update
                                    ex : fields_dict = {"unique": True, "other": False, ...}
                                    Attention! les champs devront être dans le même ordre
                                    que les colonnes du fichier
        :param cnx:                 Connexion à Postgresql
        :param exclude_fields_set:  Set de champ à exclure en cas de conflit à l'insertion
                                    et à ne pas mettre à jour,
                                    par exemple comme le champ created_at, qui devrait être
                                    créé la première fois et ne pas être mis à jour
        """
        self.model = model
        self.fields_dict = fields_dict
        self.cnx = cnx
        self.exclude_fields_set = set() if exclude_fields_set is None else exclude_fields_set
        self.meta = self.model._meta
        self.table_name = self.meta.db_table
        self.temp_table_name = self.get_temp_table_name()

    def table_is_exists(self, name):
        """
        Vérifie si le nom choisi pour la table temporaire existe en base
        :param name: nom de table à tester
        :return: bool
        """
        with self.cnx.cursor() as cursor:
            sql = f"""SELECT 1 FROM information_schema."tables" WHERE table_name='{name}'"""
            cursor.execute(sql)
            test_exists = cursor.fetchone() is not None

        return test_exists

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
        :param field_key: Champ du model django à retouner
        :return: Le Sql des paramètres de création de la table temporaire
        """
        field_attr = self.meta.get_field(field_key)
        return f' "{field_attr.column}" {field_attr.db_type(connection)}'

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
                if field_key not in self.exclude_fields_set:
                    fields_upsert_dict.get("update").append(field_key)

        return fields_upsert_dict

    @property
    def get_colmuns_table(self):
        """
        :return: Le SQL des champs de la table pour l'insert
        """
        return ", ".join(f'"{column}"' for column in self.fields_dict)

    @property
    def get_insert_values(self):
        """
        :return: Le SQL des interpolations des champs à inserrer
        """
        return ", ".join(f"%({column})s" for column in self.fields_dict)

    @property
    def get_insert(self):
        """
        :return: Le début du SQL de la requête d'insertion
        """
        return (
            f'INSERT INTO "{self.table_name}" ({self.get_colmuns_table}) '
            f"SELECT {self.get_colmuns_table} FROM {self.temp_table_name}"
        )

    @property
    def get_ddl_temp_table(self):
        """
        :return: Le SQL du DDL de crétaion d'une table temporaire
        """
        columns_list = [self.get_column_properties(field) for field in self.fields_dict]
        return f'CREATE TEMPORARY TABLE "{self.temp_table_name}" ({",".join(columns_list)[1:]})'

    @property
    def get_query_upsert(self):
        """
        :return: Le SQL la clause ON CONFLICT ... DO UPDATE pour la requête upsert
        """
        conflict_columns = ", ".join(
            f'"{column}"' for column in self.get_columns_upsert().get("conflict")
        )
        update_columns = ", ".join(
            f'"{column}"=EXCLUDED."{column}"' for column in self.get_columns_upsert().get("update")
        )
        return f"{self.get_insert} ON CONFLICT ({conflict_columns}) DO UPDATE SET {update_columns}"

    @property
    def get_query_do_nothing(self):
        """
        :return: La clause ON CONFLICT DO NOTHING pour la requête upsert
        """
        return f"{self.get_insert} ON CONFLICT DO NOTHING"

    @property
    def get_query_insert(self):
        """
        :return: Le SQL d'insertion en mode upsert
        """
        return self.get_insert

    @property
    def get_drop_temp(self):
        """
        :return: Le SQL de suppression de la table provisoire
        """
        return f'DROP TABLE IF EXISTS "{self.temp_table_name}"'

    def set_insertion(
        self,
        file: io.StringIO,
        sep: AnyStr = ";",
        size: int = 1024,
        insert_mode: AnyStr = "upsert",
    ):
        """
        Realise l'insertion choisie (upsert, do_nothing, insert)
        """
        insert_mode_dict = {
            "upsert": self.get_query_upsert,
            "do_nothing": self.get_query_do_nothing,
            "insert": self.get_query_insert,
        }

        if insert_mode not in insert_mode_dict:
            raise PostgresUpsertError("La methode d'insertion choisie n'existe pas")

        with self.cnx.cursor() as cursor:
            if insert_mode == "insert":
                cursor.copy_from(
                    file, self.table_name, sep=sep, size=size, columns=list(self.fields_dict)
                )
            else:
                cursor.execute(self.get_ddl_temp_table)
                cursor.copy_from(file, self.temp_table_name, sep=sep, size=size)
                cursor.execute(insert_mode_dict.get(insert_mode))
                cursor.execute(self.get_drop_temp)

    def set_insertion_copy_expert(self):
        """Fais l'insertion en base par copy_expert psycopg2"""
        with self.cnx.cursor() as cursor:
            cursor.copy_expert()


def query_file_dict_cursor(
    cursor,
    query_str: str = "",
    file_path: [AnyStr, Path] = None,
    base_dir: os.path = BASE_DIR,
    parmas_dict: Dict = None,
):
    """Renvoie les résultats de la requête, dont le sql vient d'un fichier et renvoi le résultat de
    la requête sous la forme d'un dictionnaire
    :param cursor: connexion à la base postgresql psycopg2
    :param query_str: sql_context est utilisé si c'est une requête en str
    :param file_path: file pathlib.PATH
    :param base_dir: repertoire de base du fichier
    :param parmas_dict: paramètre de la requête
    :return: resultats de la requête sous forme d'un dictionnaire
    """

    parmas_dict = parmas_dict or {}

    if query_str:
        query = query_str

    else:
        file = Path(base_dir) / file_path

        if file.is_file():
            with file.open("r") as sql_file:
                query = sql_file.read()

        else:
            raise Exception(f"Le fichier {file.name!r} n'existe pas")

    # print(cursor.mogrify(query, parmas.decode())
    if parmas_dict:
        cursor.execute(query, parmas_dict)
    else:
        cursor.execute(query)

    columns = [col[0] for col in cursor.description]

    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def query_file_yield_dict_cursor(
    cursor,
    query_str: str = "",
    file_path: [AnyStr, Path] = None,
    base_dir: os.path = BASE_DIR,
    parmas_dict: Dict = None,
):
    """Renvoie les résultats de la requête, dont le sql vient d'un fichier et renvoi le résultat de
    la requête sous la forme d'un dictionnaire
    :param cursor: connexion à la base postgresql psycopg2
    :param query_str: sql_context est utilisé si c'est une requête en str
    :param file_path: file pathlib.PATH
    :param base_dir: repertoire de base du fichier
    :param parmas_dict: paramètre de la requête
    :return: resultats de la requête sous forme d'un dictionnaire
    """

    parmas_dict = parmas_dict or {}

    if query_str:
        query = query_str

    else:
        file = Path(base_dir) / file_path

        if file.is_file():
            with file.open("r") as sql_file:
                query = sql_file.read()

        else:
            raise Exception(f"Le fichier {file.name!r} n'existe pas")

    # print(cursor.mogrify(query, parmas.decode())
    if parmas_dict:
        cursor.execute(query, parmas_dict)
    else:
        cursor.execute(query)

    columns = [col[0] for col in cursor.description]

    yield from [dict(zip(columns, row)) for row in cursor.fetchall()]


def query_file_cursor(
    cursor,
    query_str: str = "",
    file_path: [AnyStr, Path] = None,
    base_dir: os.path = BASE_DIR,
    parmas_dict: Dict = None,
):
    """Renvoie les résultats de la requête, dont le sql vient d'un fichier et renvoi le résultat de
    la requête sous la forme d'un dictionnaire
    :param cursor: connexion à la base postgresql psycopg2
    :param query_str: sql_context est utilisé si c'est une requête en str
    :param file_path: file pathlib.PATH
    :param base_dir: repertoire de base du fichier
    :param parmas_dict: paramètre de la requête
    :return: resultats de la requête sous forme d'un dictionnaire
    """

    parmas_dict = parmas_dict or {}

    if query_str:
        query = query_str

    else:
        file = Path(base_dir) / file_path

        if file.is_file():
            with file.open("r") as sql_file:
                query = sql_file.read()

        else:
            raise Exception(f"Le fichier {file.name!r} n'existe pas")

    # print(cursor.mogrify(query, parmas.decode())
    if parmas_dict:
        cursor.execute(query, parmas_dict)
    else:
        cursor.execute(query)

    return cursor.fetchall()


if __name__ == "__main__":
    pass
