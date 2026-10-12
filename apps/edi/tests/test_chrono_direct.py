"""
Tests du script autonome chrono_direct (psycopg2 simulé)
"""
import csv
import logging
from decimal import Decimal
from pathlib import Path

import psycopg2
import pytest

from apps.edi.bin import chrono_direct
from conftest import patched_attrs


class FakeCursor:
    """Curseur psycopg2 simulé : enregistre les exécutions, renvoie des lignes fixes"""

    def __init__(self, rows=None, error=None):
        self.rows = rows or []
        self.error = error
        self.executed = []

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False

    def execute(self, sql_query, params=None):
        if self.error:
            raise self.error
        self.executed.append((sql_query, params))

    def fetchall(self):
        return self.rows


class FakeConnection:
    """Connexion psycopg2 simulée utilisable en context manager"""

    def __init__(self, cursor):
        self._cursor = cursor

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False

    def cursor(self):
        return self._cursor


def test_cnx_postgresql_ok(monkeypatch):
    seen = {}

    def _connect(**kwargs):
        seen.update(kwargs)
        return "connexion"

    with patched_attrs(monkeypatch, psycopg2, connect=_connect):
        assert chrono_direct.cnx_postgresql("dbname=heron user=paulo host=localhost") == "connexion"

    assert seen == {"dbname": "heron", "user": "paulo", "host": "localhost"}


def test_cnx_postgresql_error_logged(monkeypatch, caplog):
    def _connect(**_kwargs):
        raise psycopg2.OperationalError("refusé")

    with patched_attrs(monkeypatch, psycopg2, connect=_connect), caplog.at_level(
        logging.ERROR, logger="edi"
    ):
        assert chrono_direct.cnx_postgresql("dbname=heron") is None

    assert "cnx_postgresql error" in caplog.text


def test_query_select_without_query():
    assert chrono_direct.query_select(FakeConnection(FakeCursor())) is None


@pytest.mark.parametrize("params", [None, {"a": 1}])
def test_query_select_returns_rows(params):
    cursor = FakeCursor(rows=[("COS1", "AF0001")])

    rows = chrono_direct.query_select(FakeConnection(cursor), "select 1", params)

    assert rows == [("COS1", "AF0001")]
    assert cursor.executed == [("select 1", params)]


def test_query_select_error_logged(caplog):
    cursor = FakeCursor(error=psycopg2.OperationalError("boom"))

    with caplog.at_level(logging.ERROR, logger="edi"):
        assert chrono_direct.query_select(FakeConnection(cursor), "select 1") is None

    assert "query_select error" in caplog.text


@pytest.fixture
def chrono_file(tmp_path: Path):
    """Fichier Chronodirect cp1252 : libellé ; maison ; quantité ; achat ; cession"""

    def _write(rows):
        path = tmp_path / "chrono.csv"

        with path.open("w", encoding="cp1252", newline="") as file:
            csv.writer(file, delimiter=";", quotechar='"').writerows(rows)

        return path

    return _write


def test_set_generique_chrono_direct(monkeypatch, tmp_path, chrono_file, caplog):
    source = chrono_file(
        [
            ["Courrier audio été", "COS1", "4", "1,00", "10,00"],
            ["Courrier optique", "COS2", "2", "1,00", "5,50"],
        ]
    )
    target = tmp_path / "interne.csv"
    cursor = FakeCursor(rows=[("COS1", "AF0001"), ("COS2", "AF0002")])

    with patched_attrs(
        monkeypatch, chrono_direct, cnx_postgresql=lambda _dsn: FakeConnection(cursor)
    ), caplog.at_level(logging.INFO, logger="edi"):
        chrono_direct.set_generique_chrono_direct(
            "dbname=x", source, target, dte_fac="20250930"
        )

    with target.open(encoding="utf8", newline="") as file:
        lines = list(csv.DictReader(file, delimiter=";", quotechar='"'))

    assert "Le fichier à bien été créé" in caplog.text
    assert [line["reference_article"] for line in lines] == ["courrier audio", "courrier_optique"]
    assert lines[0]["code_maison"] == "AF0001"
    assert lines[0]["px_unitaire_net"] == "2.50"
    assert lines[0]["montant_ttc"] == "12.00"
    assert lines[1]["montant_tva"] == "1.10"
    assert lines[1]["num_facture"] == "GENERIQUE_INTERNAL_CHRONODIRECT_20250930"
    assert lines[1]["date_echeance"] == "20250930"
    assert Decimal(lines[1]["px_unitaire_brut"]) == Decimal("2.75")


def test_set_generique_chrono_direct_unknown_reference(monkeypatch, tmp_path, chrono_file):
    source = chrono_file([["Courrier", "INCONNUE", "1", "1", "2"]])
    cursor = FakeCursor(rows=[("COS1", "AF0001")])

    with patched_attrs(
        monkeypatch, chrono_direct, cnx_postgresql=lambda _dsn: FakeConnection(cursor)
    ), pytest.raises(ValueError, match="INCONNUE"):
        chrono_direct.set_generique_chrono_direct(
            "dbname=x", source, tmp_path / "interne.csv", dte_fac="20250930"
        )
