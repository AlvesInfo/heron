# pylint: disable=E0401,W0621
"""FR : Tests des utilitaires postgresql de core (functions_postgresql.py) : exécution de requêtes


     sur une connexion Django ou psycopg2, lecture des requêtes depuis des fichiers sql
EN : Tests for core postgresql helpers

Commentaire:

Les connexions psycopg2 directes sont construites depuis les réglages de la base de test
courante (django.db.connection.settings_dict), jamais depuis CNX_STRING.

created at: 2026-10-11
created by: Paulo ALVES
"""

import logging
import types

import psycopg2
import pytest
from django.db import connection

from apps.core.functions import functions_postgresql
from apps.core.functions.functions_postgresql import (
    query_dict,
    query_execute,
    query_file_cursor,
    query_file_dict_cursor,
    query_file_yield_dict_cursor,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def pg_cnx():
    """Connexion psycopg2 directe à la base de test courante, annulée et fermée à la fin"""
    settings_dict = connection.settings_dict
    cnx = psycopg2.connect(
        dbname=settings_dict["NAME"],
        user=settings_dict["USER"],
        password=settings_dict["PASSWORD"],
        host=settings_dict["HOST"],
        port=settings_dict["PORT"],
    )

    try:
        yield cnx
    finally:
        cnx.rollback()
        cnx.close()


@pytest.fixture
def pays():
    """Table temporaire de pays dans la transaction de test, trois lignes"""
    with connection.cursor() as cursor:
        cursor.execute(
            "create temporary table tmp_pays (code varchar(2) primary key, nom varchar(30))"
        )
        cursor.execute(
            "insert into tmp_pays values ('FR', 'France'), ('BE', 'Belgique'), ('IT', 'Italie')"
        )


# QUERY EXECUTE / QUERY DICT =======================================================================


def test_query_execute_renvoie_le_nombre_de_lignes(pays):
    assert query_execute(connection, "update tmp_pays set nom = upper(nom)") == 3
    assert (
        query_execute(connection, "delete from tmp_pays where code = %(code)s", {"code": "IT"}) == 1
    )
    assert query_execute(connection, "delete from tmp_pays where code = 'ZZ'") == 0


def test_query_execute_sans_requete():
    assert query_execute(connection) == 0
    assert query_execute(connection, "") == 0


def test_query_execute_erreur_psycopg2_journalisee(pg_cnx, caplog):
    """Une requête invalide sur une connexion psycopg2 est journalisée et vaut 0"""
    with caplog.at_level(logging.ERROR, logger="django"):
        assert query_execute(pg_cnx, "update table_inexistante set x = 1") == 0

    assert "query_execute error" in caplog.text


def test_query_dict_renvoie_des_dictionnaires(pays):
    rows = query_dict(connection, "select code, nom from tmp_pays order by code")
    filtered = query_dict(
        connection, "select nom from tmp_pays where code = %(code)s", {"code": "FR"}
    )

    assert rows == [
        {"code": "BE", "nom": "Belgique"},
        {"code": "FR", "nom": "France"},
        {"code": "IT", "nom": "Italie"},
    ]
    assert filtered == [{"nom": "France"}]
    assert query_dict(connection, "select nom from tmp_pays where code = 'ZZ'") == []


def test_query_dict_sans_requete():
    assert query_dict(connection) is None
    assert query_dict(connection, "", {"a": 1}) is None


def test_query_dict_erreur_psycopg2_journalisee(pg_cnx, caplog):
    with caplog.at_level(logging.ERROR, logger="django"):
        assert query_dict(pg_cnx, "select * from table_inexistante") is None

    assert "query_dict error" in caplog.text


# REQUÊTES DEPUIS UN FICHIER SQL ===================================================================


@pytest.fixture
def sql_dir(tmp_path):
    """Répertoire de base avec deux fichiers sql (avec et sans paramètre)"""
    (tmp_path / "sql").mkdir()
    (tmp_path / "sql" / "pays.sql").write_text(
        "select code, nom from tmp_pays order by code", encoding="utf8"
    )
    (tmp_path / "sql" / "pays_code.sql").write_text(
        "select code, nom from tmp_pays where code = %(code)s", encoding="utf8"
    )
    return tmp_path


def test_query_file_dict_cursor_depuis_un_fichier(pays, sql_dir):
    with connection.cursor() as cursor:
        rows = query_file_dict_cursor(cursor, file_path="sql/pays.sql", base_dir=sql_dir)
        one = query_file_dict_cursor(
            cursor, file_path="sql/pays_code.sql", base_dir=sql_dir, parmas_dict={"code": "BE"}
        )

    assert [row["code"] for row in rows] == ["BE", "FR", "IT"]
    assert one == [{"code": "BE", "nom": "Belgique"}]


def test_query_file_dict_cursor_depuis_un_texte(pays):
    """La requête en texte est prioritaire sur le fichier"""
    with connection.cursor() as cursor:
        rows = query_file_dict_cursor(
            cursor, query_str="select count(*) as nb from tmp_pays", file_path="sql/absent.sql"
        )
        one = query_file_dict_cursor(
            cursor, "select nom from tmp_pays where code = %(code)s", parmas_dict={"code": "IT"}
        )

    assert rows == [{"nb": 3}]
    assert one == [{"nom": "Italie"}]


def test_query_file_dict_cursor_fichier_absent(pays, sql_dir):
    with (
        connection.cursor() as cursor,
        pytest.raises(Exception, match="Le fichier 'absent.sql' n'existe pas"),
    ):
        query_file_dict_cursor(cursor, file_path="sql/absent.sql", base_dir=sql_dir)


def test_query_file_yield_dict_cursor(pays, sql_dir):
    """Même résultat, sous forme de générateur"""
    with connection.cursor() as cursor:
        generator = query_file_yield_dict_cursor(
            cursor, file_path="sql/pays_code.sql", base_dir=sql_dir, parmas_dict={"code": "FR"}
        )

        assert isinstance(generator, types.GeneratorType)
        assert list(generator) == [{"code": "FR", "nom": "France"}]
        assert list(query_file_yield_dict_cursor(cursor, "select 1 as un")) == [{"un": 1}]


def test_query_file_cursor_renvoie_des_tuples(pays, sql_dir):
    with connection.cursor() as cursor:
        rows = query_file_cursor(cursor, file_path="sql/pays.sql", base_dir=sql_dir)
        one = query_file_cursor(
            cursor, "select nom from tmp_pays where code = %(code)s", parmas_dict={"code": "IT"}
        )

    assert rows == [("BE", "Belgique"), ("FR", "France"), ("IT", "Italie")]
    assert one == [("Italie",)]


def test_base_dir_par_defaut_est_la_racine_du_projet(pays):
    """Sans base_dir, le fichier est cherché depuis settings.BASE_DIR (répertoire du projet)"""
    with connection.cursor() as cursor, pytest.raises(Exception, match="n'existe pas"):
        query_file_cursor(cursor, file_path="apps/core/tests/absent.sql")

    assert (
        functions_postgresql.settings.BASE_DIR.exists()
        if hasattr(functions_postgresql.settings.BASE_DIR, "exists")
        else True
    )
