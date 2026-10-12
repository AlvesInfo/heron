# pylint: disable=E0401,W0621,W0212
"""FR : Tests de l'insertion en base par psycopg2 (apps/data_flux/postgres_save.py) : découpage par


     pages, requêtes préparées, table temporaire, modes insert / do_nothing / upsert / prepared /
     pre_validation et exceptions Postgres*
EN : Tests for psycopg2 database insertion module

created at: 2026-10-11
created by: Paulo ALVES
"""

import contextlib
import io
import logging

import psycopg2
import pytest
from django.db import connection, transaction
from psycopg2 import sql

from apps.core.models.models_notifications import Notification
from apps.data_flux import postgres_save
from apps.data_flux.exceptions import (
    PostgresCardinalityViolationError,
    PostgresDjangoError,
    PostgresInsertMethodError,
    PostgresKeyError,
    PostgresPreparedError,
    PostgresTypeError,
    PostgresUniqueError,
)
from apps.data_flux.models import Essais, EssaisZ, Line
from apps.data_flux.postgres_save import (
    PostgresDjangoUpsert,
    execute_batch,
    execute_prepared_upsert,
    get_random_name,
    iter_slice,
)
from conftest import patched_attrs

pytestmark = pytest.mark.django_db

FIELDS = {"col_int": True, "col_texte": False, "col_2": False, "col_3": False}


def _file(*rows):
    """Fichier csv (séparateur ; et guillemets) des colonnes col_int, col_texte, col_2, col_3"""
    content = "\n".join(";".join(f'"{value}"' for value in row) for row in rows) + "\n"
    return io.StringIO(content)


def _rows():
    return {row.col_int: (row.col_texte, row.col_2, row.col_3) for row in EssaisZ.objects.all()}


@pytest.fixture
def upsert():
    return PostgresDjangoUpsert(EssaisZ, FIELDS, cnx=connection)


# DÉCOUPAGE ET REQUÊTES PRÉPARÉES ==================================================================


def test_iter_slice():
    assert list(iter_slice([1, 2, 3, 4, 5], 2)) == [(1, 2), (3, 4), (5,)]
    assert list(iter_slice("abc", 5, form=list)) == [["a", "b", "c"]]
    assert list(iter_slice([], 3)) == []


def test_get_random_name():
    name = get_random_name()

    assert len(name) == 10
    assert name.islower()
    assert len(get_random_name(3)) == 3
    assert get_random_name() != name


def test_execute_batch_insere_par_pages():
    """Les lignes sont envoyées par pages, les compteurs renvoient les lignes traitées"""
    with connection.cursor() as wrapper:
        error, counts = execute_batch(
            wrapper.cursor,
            'INSERT INTO "data_flux_essaisz" ("col_int", "col_texte") VALUES (%s, %s)',
            [(1, "un"), (2, "deux"), (3, "trois")],
            page_size=2,
        )

    assert (error, counts) == (False, (3, 3))
    assert set(EssaisZ.objects.values_list("col_int", flat=True)) == {1, 2, 3}


class _FailingCursor:
    """Curseur factice dont l'exécution lève l'erreur psycopg2 demandée"""

    def __init__(self, exception):
        self.exception = exception

    @staticmethod
    def mogrify(_sql, args):
        return repr(args).encode()

    def execute(self, _sql):
        raise self.exception("boum")


@pytest.mark.parametrize(
    ("exception", "message"),
    [
        (psycopg2.OperationalError, "Connexion à Postgres fermée"),
        (psycopg2.DataError, "Erreur sur les insertions execute_batch"),
    ],
)
def test_execute_batch_erreurs_journalisees(exception, message, caplog):
    """Une erreur psycopg2 sur une page est journalisée, le drapeau d'erreur est levé"""
    with caplog.at_level(logging.ERROR, logger="postgres_save"):
        error, counts = execute_batch(
            _FailingCursor(exception), "INSERT", [(1,), (2,), (3,)], page_size=2
        )

    assert error is True
    assert counts == (3, 0)
    assert message in caplog.text


def test_execute_prepared_upsert():
    """Requête préparée exécutée par pages puis libérée"""
    with connection.cursor() as wrapper:
        raw = wrapper.cursor
        error, counts = execute_prepared_upsert(
            raw,
            'PREPARE stmt_test (integer, character varying) AS INSERT INTO "data_flux_essaisz" ("col_int", "col_texte") VALUES ($1, $2)',
            "EXECUTE stmt_test (%s, %s)",
            "DEALLOCATE stmt_test",
            [(10, "dix"), (11, "onze")],
            page_size=1,
        )
        raw.execute("select count(*) from pg_prepared_statements where name = 'stmt_test'")
        remaining = raw.fetchone()[0]

    assert (error, counts) == (False, (2, 2))
    assert remaining == 0
    assert set(EssaisZ.objects.values_list("col_int", flat=True)) == {10, 11}


def test_execute_prepared_upsert_en_erreur(caplog):
    """Une requête préparée invalide lève PostgresPreparedError, le deallocate impossible est journalisé"""
    with (
        caplog.at_level(logging.ERROR, logger="postgres_save"),
        pytest.raises(PostgresPreparedError),
        transaction.atomic(),
        connection.cursor() as wrapper,
    ):
        execute_prepared_upsert(
            wrapper.cursor,
            "PREPARE stmt_ko AS SELECT * FROM table_inexistante",
            "EXECUTE stmt_ko",
            "DEALLOCATE stmt_ko",
            [()],
            10,
        )

    assert "deallocate impossible" in caplog.text


# PRÉPARATION DES REQUÊTES =========================================================================


def test_init_table_temporaire_et_champs(upsert, monkeypatch):
    assert upsert.table_name == "data_flux_essaisz"
    assert upsert.temp_table_name.endswith("_data_flux_essaisz")
    assert upsert.fields_list == ["col_int", "col_texte", "col_2", "col_3"]
    assert upsert.exclude_update_fields == set()
    assert upsert.table_is_exists("data_flux_essaisz") is True
    assert upsert.table_is_exists("table_inexistante") is False

    answers = iter([True, False])

    with patched_attrs(monkeypatch, upsert, table_is_exists=lambda _name: next(answers)):
        assert upsert.get_temp_table_name().endswith("_data_flux_essaisz")


def test_champ_inconnu():
    with pytest.raises(PostgresKeyError, match='la clé "absent"'):
        PostgresDjangoUpsert(EssaisZ, {"absent": True})


def test_proprietes_des_colonnes(upsert):
    """Type et nullité des colonnes, colonnes forcées à null, avec db_column (Line.trace)"""
    assert upsert.get_column_properties("col_int") == ' "col_int" integer NOT NULL'
    assert upsert.get_column_properties("col_2") == ' "col_2" varchar(10) NULL'
    assert upsert.get_null_fields() == 'FORCE_NULL ("col_2","col_3") '
    assert PostgresDjangoUpsert(EssaisZ, {"col_int": True}).get_null_fields() == ""

    lines = PostgresDjangoUpsert(Line, {"trace": True, "num_line": False, "insertion_type": False})
    assert lines.fields_list == ["trace", "num_line", "insertion_type"]
    assert lines.get_column_properties("trace") == ' "trace" uuid NOT NULL'
    assert lines.get_null_fields() == 'FORCE_NULL ("num_line","insertion_type") '
    assert lines.get_columns_upsert() == {
        "conflict": ["trace"],
        "update": ["num_line", "insertion_type"],
    }


def test_requetes_sql(upsert):
    """DDL de la table temporaire, insertion, do nothing, upsert, suppression"""
    temp = upsert.temp_table_name
    with connection.cursor() as cursor:
        ddl = cursor.mogrify(upsert.get_ddl_temp_table()).decode()
        ddl_pk = cursor.mogrify(upsert.get_ddl_temp_table(bool_pk=True)).decode()
        insert = cursor.mogrify(upsert.get_query_insert).decode()
        nothing = cursor.mogrify(upsert.get_query_do_nothing).decode()
        full = cursor.mogrify(upsert.get_query_upsert).decode()
        drop = cursor.mogrify(upsert.get_drop_temp).decode()
        fields_pk = cursor.mogrify(upsert.get_fields(bool_pk=True)).decode()

    assert (
        ddl
        == f'CREATE TEMPORARY TABLE "{temp}" ( "col_int" integer NOT NULL,  "col_texte" varchar(12) NOT NULL,  "col_2" varchar(10) NULL,  "col_3" varchar(100) NULL)'
    )
    assert ddl_pk.startswith(f'CREATE TEMPORARY TABLE "{temp}" ("pk" bigint,  "col_int"')
    assert (
        insert
        == f'INSERT INTO "data_flux_essaisz" ("col_int", "col_texte", "col_2", "col_3")  SELECT "col_int", "col_texte", "col_2", "col_3" FROM "{temp}" '
    )
    assert nothing == insert + " ON CONFLICT DO NOTHING"
    assert (
        full
        == insert
        + ' ON CONFLICT ("col_int") DO UPDATE SET "col_texte"=EXCLUDED."col_texte", "col_2"=EXCLUDED."col_2", "col_3"=EXCLUDED."col_3"'
    )
    assert drop == f'DROP TABLE IF EXISTS "{temp}"'
    assert fields_pk == '"pk", "col_int", "col_texte", "col_2", "col_3"'


def test_upsert_sans_les_champs_exclus():
    """Les champs exclus de la mise à jour ne sont pas dans la clause DO UPDATE"""
    excluded = PostgresDjangoUpsert(EssaisZ, FIELDS, exclude_update_fields={"col_3"})

    assert (
        excluded.get_upsert_batch
        == 'ON CONFLICT ("col_int") DO UPDATE SET "col_texte"=EXCLUDED."col_texte", "col_2"=EXCLUDED."col_2"'
    )


def test_requetes_preparees(upsert):
    """PREPARE typé depuis information_schema, EXECUTE et DEALLOCATE, selon le mode"""
    with connection.cursor() as cursor:
        prepare, execute, deallocate = (
            cursor.mogrify(part).decode() for part in upsert.get_prepare_batch("stmt_a")
        )
        insert, _, _ = (
            cursor.mogrify(part).decode() for part in upsert.get_prepare_smt("insert", "stmt_b")
        )
        nothing, _, _ = (
            cursor.mogrify(part).decode() for part in upsert.get_prepare_smt("do_nothing", "stmt_c")
        )
        full, _, _ = (
            cursor.mogrify(part).decode() for part in upsert.get_prepare_smt("upsert", "stmt_d")
        )

    assert (
        prepare
        == 'PREPARE "stmt_a" (integer, character varying, character varying, character varying) AS INSERT INTO "data_flux_essaisz" ("col_int", "col_texte", "col_2", "col_3") VALUES ($1, $2, $3, $4) '
    )
    assert execute == 'EXECUTE "stmt_a" (%s, %s, %s, %s)'
    assert deallocate == 'DEALLOCATE "stmt_a"'
    assert insert.endswith("VALUES ($1, $2, $3, $4)  ")
    assert nothing.endswith("ON CONFLICT DO NOTHING")
    assert full.endswith(
        'ON CONFLICT ("col_int") DO UPDATE SET "col_texte"=EXCLUDED."col_texte", "col_2"=EXCLUDED."col_2", "col_3"=EXCLUDED."col_3"'
    )

    with pytest.raises(PostgresInsertMethodError, match="'inconnu'"):
        upsert.get_prepare_smt("inconnu", "stmt_e")


# INSERTIONS =======================================================================================


def test_insertion_directe(upsert):
    """Mode insert : copie directe dans la table, colonnes vides nullables mises à null"""
    assert (
        upsert.insertion(
            _file((1, "un", "a", "x"), (2, "deux", "", "")),
            insert_mode="insert",
            kwargs_prepared={},
        )
        is True
    )
    assert _rows() == {1: ("un", "a", "x"), 2: ("deux", None, None)}


def test_insertion_do_nothing():
    EssaisZ.objects.create(col_int=1, col_texte="existant")
    upsert = PostgresDjangoUpsert(EssaisZ, FIELDS)

    upsert.insertion(
        _file((1, "ecrase", "", ""), (2, "nouveau", "b", "")),
        insert_mode="do_nothing",
        kwargs_prepared=None,
    )

    assert _rows() == {1: ("existant", None, None), 2: ("nouveau", "b", None)}
    assert upsert.table_is_exists(upsert.temp_table_name) is False


def test_insertion_upsert_avec_champs_exclus():
    EssaisZ.objects.create(col_int=1, col_texte="existant", col_3="garde")
    upsert = PostgresDjangoUpsert(EssaisZ, FIELDS, exclude_update_fields={"col_3"})

    upsert.insertion(
        _file((1, "modifie", "a", "ecrase"), (2, "nouveau", "", "")),
        insert_mode="upsert",
        kwargs_prepared={"trace": "T1"},
    )

    assert _rows() == {1: ("modifie", "a", "garde"), 2: ("nouveau", None, None)}


def test_mode_d_insertion_inconnu(upsert):
    fichier = _file()

    with pytest.raises(PostgresInsertMethodError, match="'copier'"):
        upsert.insertion(fichier, insert_mode="copier")


def test_cle_dupliquee(upsert):
    EssaisZ.objects.create(col_int=1, col_texte="existant")
    fichier = _file((1, "doublon", "", ""))

    with pytest.raises(PostgresUniqueError, match="trace N° : 'T2'"), transaction.atomic():
        upsert.insertion(fichier, insert_mode="insert", kwargs_prepared={"trace": "T2"})


def test_erreur_de_type(upsert, caplog):
    fichier = _file(("pas un entier", "texte", "", ""))

    with (
        caplog.at_level(logging.ERROR, logger="postgres_save"),
        pytest.raises(PostgresTypeError, match="Erreur de type"),
        transaction.atomic(),
    ):
        upsert.insertion(fichier, insert_mode="insert", kwargs_prepared={})

    assert "pas un entier" in caplog.text


def test_conflit_de_cardinalite(upsert):
    """Deux lignes du fichier sur la même clé : l'upsert ne peut pas affecter une ligne deux fois"""
    fichier = _file((1, "a", "", ""), (1, "b", "", ""))

    with pytest.raises(PostgresCardinalityViolationError), transaction.atomic():
        upsert.insertion(fichier, insert_mode="upsert", kwargs_prepared={})


class _BrokenConnection:
    """Connexion factice dont le curseur échoue à la copie"""

    class _Cursor:
        @staticmethod
        def copy_expert(**_kwargs):
            raise RuntimeError("copie impossible")

    @contextlib.contextmanager
    def cursor(self):
        yield self._Cursor()


def test_erreur_inconnue(upsert, caplog):
    upsert.cnx = _BrokenConnection()
    fichier = _file((1, "a", "", ""))

    with (
        caplog.at_level(logging.ERROR, logger="postgres_save"),
        pytest.raises(PostgresDjangoError, match="Erreur inconnue"),
    ):
        upsert.insertion(fichier, insert_mode="insert", kwargs_prepared={"trace": "T3"})

    assert "copie impossible" in caplog.text


@pytest.mark.parametrize("mode", ["insert", "do_nothing", "upsert"])
def test_insertion_preparee(mode):
    """Mode prepared : requête préparée et exécutée par pages, compteurs renvoyés"""
    EssaisZ.objects.create(col_int=1, col_texte="existant", col_3="garde")
    upsert = PostgresDjangoUpsert(EssaisZ, FIELDS)
    rows = (
        [(2, "deux", "b", "y"), (3, "trois", "c", "z")]
        if mode == "insert"
        else [(1, "modifie", "a", "x"), (2, "deux", "b", "y")]
    )

    result = upsert.insertion(
        _file(*rows), insert_mode="prepared", kwargs_prepared={"mode": mode, "page_size": 1}
    )

    expected = {
        "insert": ("existant", None, "garde"),
        "do_nothing": ("existant", None, "garde"),
        "upsert": ("modifie", "a", "x"),
    }
    assert result == (False, (2, 2))
    assert _rows()[1] == expected[mode]
    assert _rows()[2] == ("deux", "b", "y")


def test_insertion_preparee_sans_parametres(upsert):
    """Sans dictionnaire des attributs, l'erreur PostgresPreparedError est remontée en erreur inconnue"""
    fichier = _file((1, "a", "", ""))

    with pytest.raises(PostgresDjangoError) as excinfo:
        upsert.insertion(fichier, insert_mode="prepared", kwargs_prepared=None)

    assert isinstance(excinfo.value.__cause__, PostgresPreparedError)


# PRÉ-VALIDATION ===================================================================================


def test_contraintes_de_la_table(upsert):
    """Unicités (simple et groupée) restreintes aux colonnes du fichier, clés étrangères par table"""
    with connection.cursor() as cursor:
        cursor.execute(upsert.get_ddl_temp_table(bool_pk=True))
        uniques, foreign_keys = upsert.get_columns_constraints(cursor)
        cursor.execute(upsert.get_drop_temp)

    assert sorted(sorted(group) for group in uniques) == [
        ["col_2", "col_3", "col_texte"],
        ["col_int"],
    ]
    assert foreign_keys == {"data_flux_trace": [("trace_id", "uuid_identification", False)]}


def test_contraintes_plusieurs_cles_vers_la_meme_table():
    """Deux clés étrangères vers la même table (Notification.user et created_by)"""
    notifications = PostgresDjangoUpsert(Notification, {"title": False})

    with connection.cursor() as cursor:
        uniques, foreign_keys = notifications.get_columns_constraints(cursor)

    assert uniques == []
    assert {column for column, _, _ in foreign_keys["auth_user"]} == {"user_id", "created_by_id"}


def test_check_unique_key(upsert):
    """Doublons sur une clé simple et sur une clé groupée, dans la table temporaire"""
    with connection.cursor() as cursor:
        cursor.execute(upsert.get_ddl_temp_table())
        cursor.execute(
            sql.SQL(
                "INSERT INTO {} (\"col_int\", \"col_texte\", \"col_2\", \"col_3\") VALUES (1, 'a', 'b', 'c'), (1, 'a', 'b', 'c'), (2, 'z', NULL, NULL)"
            ).format(sql.Identifier(upsert.temp_table_name))
        )
        duplicates = upsert.check_unique_key(
            cursor, upsert.temp_table_name, [["col_int"], ["col_texte", "col_2", "col_3"]]
        )
        cursor.execute(upsert.get_drop_temp)

    assert sorted(duplicates) == [("col_int", "1", 2), ("col_texte__col_2__col_3", "a | b | c", 2)]
    assert upsert.check_foreign_key(None) is None


def test_insertion_avec_pre_validation(upsert, make_trace, caplog):
    """Les doublons de clés du fichier sont journalisés, la table temporaire est supprimée"""
    with caplog.at_level(logging.INFO, logger="postgres_save"):
        result = upsert.insertion(
            _file((1, "a", "b", "c"), (1, "a", "b", "c")),
            insert_mode="pre_validation",
            kwargs_prepared={"trace": make_trace()},
        )

    assert result is True
    assert "values :  col_int 1 2" in caplog.text
    assert "col_2--col_3--col_texte b | c | a 2" in caplog.text
    assert upsert.table_is_exists(upsert.temp_table_name) is False
    assert EssaisZ.objects.count() == 0


def test_pre_validation_sans_contrainte_d_unicite(caplog):
    """Sur une table sans contrainte (Essais), aucune vérification de doublons"""
    essais = PostgresDjangoUpsert(Essais, {"col_texte": False, "col_int": False})

    with caplog.at_level(logging.INFO, logger="postgres_save"):
        essais.insert_with_pre_validation(io.StringIO('"a";"1"\n"a";"1"\n'))

    assert "[] {}" in caplog.text
    assert "values" not in caplog.text


def test_nettoyage_des_objets_postgres_save():
    """Les exceptions du module sont toutes des PostgresDjangoError"""
    for exception in (
        PostgresInsertMethodError,
        PostgresCardinalityViolationError,
        PostgresUniqueError,
        PostgresKeyError,
        PostgresTypeError,
        PostgresPreparedError,
    ):
        assert issubclass(exception, PostgresDjangoError)

    assert postgres_save.LOGGER_POSTGRES_SAVE.name == "postgres_save"
