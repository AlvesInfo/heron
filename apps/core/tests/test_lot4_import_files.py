# pylint: disable=E0401,W0621
"""FR : Tests du processus générique d'import de fichier (apps/core/bin/import_files.py)


EN : Tests for the generic file import process

created at: 2026-10-11
created by: Paulo ALVES
"""

import logging
from pathlib import Path

import pytest

from apps.core.bin import import_files
from apps.core.bin.import_files import import_file_process
from apps.data_flux.exceptions import DuplicatesError, ModelFieldError
from apps.data_flux.models import Trace
from conftest import patched_attrs

pytestmark = pytest.mark.django_db


@pytest.fixture
def source(tmp_path):
    file = tmp_path / "import.xlsx"
    file.write_bytes(b"classeur")
    return file


@pytest.fixture
def params():
    return {
        "model": object,
        "validator": object,
        "trace_name": "Import de test",
        "application_name": "tests",
        "flow_name": "flux_test",
        "comment": "import de test",
        "add_fields_dict": {"created_at": "now"},
        "translate_file": None,
        "pre_processing": None,
        "post_processing": None,
    }


@pytest.fixture
def fake_insert(monkeypatch):
    """Doublure de make_insert : enregistre les appels, lève l'exception demandée"""
    calls = {"inserts": [], "raise": None}

    def _insert(model, flow_name, source, trace, validator, params_dict_loader):
        calls["inserts"].append(
            {
                "model": model,
                "flow_name": flow_name,
                "source": source,
                "trace": trace,
                "loader": params_dict_loader,
            }
        )

        if calls["raise"]:
            raise calls["raise"]

        return "Import : flux_test\n\nPas d'erreurs\n"

    with patched_attrs(monkeypatch, import_files, make_insert=_insert):
        yield calls


def test_import_sans_traduction_efface_le_fichier(source, params, fake_insert):
    """Sans répertoire de sauvegarde, le fichier importé est supprimé ; la trace est finalisée"""
    error, to_print = import_file_process(source, params)

    trace = Trace.objects.get()
    call = fake_insert["inserts"][0]
    assert (error, to_print) == (False, "Import : flux_test\n\nPas d'erreurs\n")
    assert not source.exists()
    assert (trace.trace_name, trace.flow_name, trace.file_name, trace.errors) == (
        "Import de test",
        "flux_test",
        "import.xlsx",
        False,
    )
    assert trace.final_at is not None
    assert trace.time_to_process >= 0
    assert call["source"] == source
    assert call["loader"] == {"trace": trace, "add_fields_dict": {"created_at": "now"}}


def test_import_avec_traduction_pre_post_traitements_et_sauvegarde(
    source, params, fake_insert, tmp_path
):
    """Le fichier traduit est importé puis effacé, les traitements sont appelés, l'original sauvegardé"""
    steps = []
    translated = tmp_path / "import.csv"

    def _translate(file):
        translated.write_text("traduit", encoding="utf8")
        steps.append(("translate", file.name))
        return translated

    save_dir = tmp_path / "backup"
    save_dir.mkdir()
    params.update(
        {
            "translate_file": _translate,
            "pre_processing": lambda: steps.append("pre"),
            "post_processing": lambda: steps.append("post"),
        }
    )

    error, _ = import_file_process(source, params, save_dir=save_dir)

    assert error is False
    assert steps == [("translate", "import.xlsx"), "pre", "post"]
    assert fake_insert["inserts"][0]["source"] == translated
    assert not translated.exists()
    assert not source.exists()
    assert (save_dir / "import.xlsx").read_bytes() == b"classeur"


@pytest.mark.parametrize(
    ("exception", "expected_print", "log_text"),
    [
        (
            DuplicatesError("doublons"),
            "Vous avez des doublons dans le fichier",
            "TypeError",
        ),
        (
            ModelFieldError("champ"),
            "Vous avez des champs qui n'existent pas en base",
            "TypeError",
        ),
        (TypeError("type"), "", "TypeError"),
        (RuntimeError("cassé"), "", "Exception Générale: import.xlsx"),
    ],
)
def test_import_en_erreur_marque_la_trace_et_garde_le_fichier(
    source, params, fake_insert, caplog, exception, expected_print, log_text
):
    fake_insert["raise"] = exception

    with caplog.at_level(logging.ERROR, logger="imports"):
        error, to_print = import_file_process(source, params)

    trace = Trace.objects.get()
    assert (error, to_print) == (True, expected_print)
    assert trace.errors is True
    assert trace.comment.endswith("Une erreur c'est produite veuillez consulter les logs")
    assert source.exists()
    assert log_text in caplog.text


def test_import_en_erreur_apres_traduction_efface_le_fichier_traduit(
    source, params, fake_insert, tmp_path
):
    """Si l'insertion échoue, le fichier traduit encore présent est nettoyé dans le finally"""
    translated = tmp_path / "import.csv"
    translated.write_text("traduit", encoding="utf8")
    params["translate_file"] = lambda _file: translated
    fake_insert["raise"] = RuntimeError("cassé")

    error, _ = import_file_process(source, params)

    assert error is True
    assert not translated.exists()
    assert source.exists()


def test_import_erreur_avant_la_trace(source, params, monkeypatch, caplog):
    """Une erreur avant la création de la trace est journalisée sans trace à marquer"""

    def _boom(*_args):
        raise RuntimeError("trace cassée")

    with (
        patched_attrs(monkeypatch, import_files, get_trace=_boom),
        caplog.at_level(logging.ERROR, logger="imports"),
    ):
        error, to_print = import_file_process(source, params)

    assert (error, to_print) == (True, "")
    assert Trace.objects.count() == 0
    assert "trace cassée" in caplog.text
    assert isinstance(source, Path)
