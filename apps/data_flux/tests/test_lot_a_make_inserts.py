# pylint: disable=E0401,W0621
"""FR : Tests de make_insert (apps/data_flux/make_inserts.py) : lecture, validation djantic et upsert


     réels sur le modèle d'essai EssaisZ
EN : Tests for make_insert

created at: 2026-10-11
created by: Paulo ALVES
"""

import csv
import logging
import uuid
from typing import ClassVar

import pytest
from djantic import ModelSchema

from apps.data_flux import make_inserts
from apps.data_flux.make_inserts import make_insert
from apps.data_flux.models import EssaisZ, Line
from apps.data_flux.postgres_save import PostgresKeyError, PostgresTypeError
from conftest import patched_attrs

pytestmark = pytest.mark.django_db


class EssaisZSchema(ModelSchema):
    """Validation des lignes du fichier d'essai"""

    class Config:
        """Config"""

        model = EssaisZ
        include: ClassVar[list[str]] = ["col_texte", "col_2", "col_3", "col_int"]


class EssaisZImport:
    """Métadonnées d'import du modèle d'essai (extend_model)"""

    @staticmethod
    def get_columns_import():
        return {"col_texte": 0, "col_2": 1, "col_3": 2, "col_int": 3}

    @staticmethod
    def get_uniques():
        return {"col_int"}


EssaisZ.get_columns_import = EssaisZImport.get_columns_import
EssaisZ.get_uniques = EssaisZImport.get_uniques


def _file(tmp_path, rows, name="essais.csv"):
    path = tmp_path / name

    with path.open("w", encoding="utf8", newline="") as file:
        csv.writer(file, delimiter=";", quotechar='"', lineterminator="\n").writerows(rows)

    return path


@pytest.fixture
def params(make_trace):
    return {"trace": make_trace(flow_name="essais"), "add_fields_dict": {}}


def test_make_insert_creation_puis_mise_a_jour(tmp_path, params):
    """Deux lignes créées, puis une mise à jour sur la clé col_int"""
    trace = params["trace"]

    to_print = make_insert(
        EssaisZ,
        "essais",
        _file(tmp_path, [["a", "x", "", "1"], ["b", "y", "z", "2"]]),
        trace,
        EssaisZSchema,
        params,
    )

    assert to_print == "Import : essais\n\nPas d'erreurs\n"
    assert dict(EssaisZ.objects.values_list("col_int", "col_texte")) == {1: "a", 2: "b"}
    trace.refresh_from_db()
    assert trace.errors is False
    assert trace.time_to_process is not None

    make_insert(
        EssaisZ,
        "essais",
        _file(tmp_path, [["a2", "x", "", "1"]]),
        trace,
        EssaisZSchema,
        params,
        extend_model=EssaisZImport,
    )

    assert dict(EssaisZ.objects.values_list("col_int", "col_texte")) == {1: "a2", 2: "b"}


def test_make_insert_lignes_en_erreur(tmp_path, params):
    """Une ligne invalide est tracée et comptée, les autres sont insérées"""
    trace = params["trace"]

    to_print = make_insert(
        EssaisZ,
        "essais",
        _file(tmp_path, [["a", "", "", "pas-un-entier"], ["b", "", "", "2"]]),
        trace,
        EssaisZSchema,
        params,
    )

    trace.refresh_from_db()
    assert "Lignes en erreur" in to_print
    assert trace.errors_numbers_records == 1
    assert list(EssaisZ.objects.values_list("col_int", flat=True)) == [2]
    assert Line.objects.filter(trace=trace, insertion_type="Errors").count() == 1


def test_make_insert_do_nothing_et_champs_ajoutes(tmp_path, params):
    """insert_mode do_nothing : la ligne existante n'est pas modifiée ; add_fields_dict absent toléré"""
    EssaisZ.objects.create(col_texte="deja", col_int=1)
    params["add_fields_dict"] = None

    make_insert(
        EssaisZ,
        "essais",
        _file(tmp_path, [["nouveau", "", "", "1"], ["b", "", "", "2"]]),
        params["trace"],
        EssaisZSchema,
        params,
        insert_mode="do_nothing",
    )

    assert dict(EssaisZ.objects.values_list("col_int", "col_texte")) == {1: "deja", 2: "b"}


@pytest.mark.parametrize(
    ("rows", "columns", "message"),
    [
        ([["a", "", "", "1"]], {"col_texte": "absente"}, "IterFileToInsertError"),
        ([["a", "", "", "1"]], {"col_texte": 0, "col_int": 3, "ident": None}, "GetAddDictError"),
    ],
)
def test_make_insert_erreurs_du_chargeur(tmp_path, params, caplog, rows, columns, message):
    """Colonne absente ou champ ajouté mal formé : journalisé, trace en erreur, pas d'insertion"""
    trace = params["trace"]
    trace.comment = None
    trace.save()

    if message == "GetAddDictError":
        params["add_fields_dict"] = {"ident": (uuid.uuid4,)}

    class _Import:
        @staticmethod
        def get_columns_import():
            return {key: value for key, value in columns.items() if key != "ident"}

        @staticmethod
        def get_uniques():
            return {"col_int"}

    with caplog.at_level(logging.ERROR, logger="imports"):
        to_print = make_insert(
            EssaisZ,
            "essais",
            _file(tmp_path, rows),
            trace,
            EssaisZSchema,
            params,
            extend_model=_Import,
        )

    trace.refresh_from_db()
    assert message in caplog.text
    assert to_print == "Import : essais\n"
    assert trace.errors is True
    assert trace.comment.endswith("\n. Une erreur c'est produite veuillez consulter les logs")
    assert EssaisZ.objects.count() == 0


def test_make_insert_fichier_absent_et_excel_invalide(tmp_path, params, caplog):
    with caplog.at_level(logging.ERROR, logger="imports"):
        make_insert(
            EssaisZ, "essais", tmp_path / "absent.csv", params["trace"], EssaisZSchema, params
        )
        make_insert(
            EssaisZ, "essais", tmp_path / "absent.xlsx", params["trace"], EssaisZSchema, params
        )

    assert "FileToCsvError" in caplog.text
    assert "ExcelToCsvError" in caplog.text


@pytest.mark.parametrize("exception", [PostgresKeyError, PostgresTypeError, RuntimeError])
def test_make_insert_erreurs_d_insertion(tmp_path, params, caplog, monkeypatch, exception):
    """Les erreurs de l'upsert postgres et les erreurs générales sont journalisées"""

    def _boom(self, **_kwargs):
        raise exception("insertion cassée")

    with (
        patched_attrs(monkeypatch, make_inserts.PostgresDjangoUpsert, insertion=_boom),
        caplog.at_level(logging.ERROR, logger="imports"),
    ):
        make_insert(
            EssaisZ,
            "essais",
            _file(tmp_path, [["a", "", "", "1"]]),
            params["trace"],
            EssaisZSchema,
            params,
        )

    assert exception.__name__ in caplog.text or "Exception Générale" in caplog.text
    assert params["trace"].errors is True
