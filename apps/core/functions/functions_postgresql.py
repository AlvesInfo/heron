"""
Module apportant des fonctionnalités pratiques à psycopg2 : exécution de requêtes
(connexion psycopg2 ou connexion Django) et lecture de requêtes depuis des fichiers sql
"""
import os
from typing import AnyStr, Dict
from pathlib import Path

import psycopg2
from django.conf import settings

from heron.loggers import LOGGER_DJANGO


def query_execute(cnx, sql_requete=None, params=None):
    """
    Fonction qui exécute une requête sql Postgresql.
        :param cnx: Connexion à la base postgresql psycopg2
        :param sql_requete: requête selection souhaitée
                                ex: "UPDATE table SET champ=1"
                                    "UPDATE table SET champ=1 WHERE x = 0"
                                    "DELETE FROM table"
        :param params: dictionnaire des paramètes à passer
        :return: nombre de lignes affectées, 0 sans requête ou si exception psycopg2
    """
    if sql_requete:
        try:
            with cnx.cursor() as cur:
                if params:
                    cur.execute(sql_requete, params)
                else:
                    cur.execute(sql_requete)

                rows = cur.rowcount

            return rows

        except psycopg2.Error as except_error:
            log_line = f"query_execute error: {except_error}\n"
            LOGGER_DJANGO.exception(log_line)

    return 0


def query_dict(cnx, sql_requete=None, params=None):
    """
    Fonction qui retourne le resultat d'une requête sql Postgresql, comme un dictionnaire
        :param cnx: connexion à la base postgresql psycopg2
        :param sql_requete: requête selection souhaitée
                                ex: "SELECT * FROM table"
        :param params: dictionnaire des paramètes à passer
        :return: La liste des dictionnaires de la requête, None sans requête ou si exception
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
            log_line = f"query_dict error: {except_error}\n"
            LOGGER_DJANGO.exception(log_line)

    return None


def _execute_query_file(cursor, query_str: str, file_path, base_dir, parmas_dict: Dict):
    """Exécute la requête passée en texte, ou lue dans le fichier sql
    :param cursor: curseur de la base postgresql
    :param query_str: requête en texte, prioritaire sur le fichier
    :param file_path: chemin du fichier sql, relatif à base_dir
    :param base_dir: répertoire de base du fichier
    :param parmas_dict: paramètres de la requête
    """
    if query_str:
        query = query_str

    else:
        file = Path(base_dir) / file_path

        if not file.is_file():
            raise Exception(f"Le fichier {file.name!r} n'existe pas")

        with file.open("r") as sql_file:
            query = sql_file.read()

    if parmas_dict:
        cursor.execute(query, parmas_dict)
    else:
        cursor.execute(query)


def query_file_dict_cursor(
    cursor,
    query_str: str = "",
    file_path: [AnyStr, Path] = None,
    base_dir: os.path = settings.BASE_DIR,
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
    _execute_query_file(cursor, query_str, file_path, base_dir, parmas_dict or {})
    columns = [col[0] for col in cursor.description]

    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def query_file_yield_dict_cursor(
    cursor,
    query_str: str = "",
    file_path: [AnyStr, Path] = None,
    base_dir: os.path = settings.BASE_DIR,
    parmas_dict: Dict = None,
):
    """Renvoie les résultats de la requête, dont le sql vient d'un fichier et renvoi le résultat de
    la requête sous la forme d'un générateur de dictionnaires
    :param cursor: connexion à la base postgresql psycopg2
    :param query_str: sql_context est utilisé si c'est une requête en str
    :param file_path: file pathlib.PATH
    :param base_dir: repertoire de base du fichier
    :param parmas_dict: paramètre de la requête
    :return: resultats de la requête sous forme d'un générateur de dictionnaires
    """
    yield from query_file_dict_cursor(cursor, query_str, file_path, base_dir, parmas_dict)


def query_file_cursor(
    cursor,
    query_str: str = "",
    file_path: [AnyStr, Path] = None,
    base_dir: os.path = settings.BASE_DIR,
    parmas_dict: Dict = None,
):
    """Renvoie les résultats de la requête, dont le sql vient d'un fichier et renvoi le résultat de
    la requête sous la forme de tuples
    :param cursor: connexion à la base postgresql psycopg2
    :param query_str: sql_context est utilisé si c'est une requête en str
    :param file_path: file pathlib.PATH
    :param base_dir: repertoire de base du fichier
    :param parmas_dict: paramètre de la requête
    :return: resultats de la requête sous forme de tuples
    """
    _execute_query_file(cursor, query_str, file_path, base_dir, parmas_dict or {})

    return cursor.fetchall()
