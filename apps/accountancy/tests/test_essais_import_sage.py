# pylint: disable=E0401,W0621,R0903
"""FR : Tests du script d'essai d'import des devises (apps/accountancy/essais/essais_import_sage.py)


EN : Tests for currency import trial script

Commentaire:

Les classes ModelFormInsertion / IterFileToInsert (apps.core) sont remplacées par des doublures
context manager : on vérifie le câblage du script, pas la lecture de fichier.

created at: 2026-10-10
created by: Paulo ALVES
"""

import logging
from pathlib import Path
from typing import ClassVar

import pytest

from apps.accountancy.essais import essais_import_sage
from apps.accountancy.forms.forms_django.sage_forms import CurrencySageForm
from apps.accountancy.models import CurrencySage
from conftest import patched_attrs


class _FakeInsertion:
    """Doublure de ModelFormInsertion (context manager + validate + errors)"""

    created: ClassVar[list] = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.validated = False
        self.exited = False
        self.errors = ["erreur de test"]
        _FakeInsertion.created.append(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.exited = True
        return False

    def validate(self):
        self.validated = True


def _fake_iter_file(rows):
    class _FakeIterFile:
        """Doublure de IterFileToInsert"""

        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        @staticmethod
        def get_chunk_dict_rows():
            yield from rows

    return _FakeIterFile


@pytest.fixture(autouse=True)
def _reset_fakes():
    _FakeInsertion.created.clear()
    yield
    _FakeInsertion.created.clear()


def test_import_sage(monkeypatch):
    """import_sage construit l'insertion avec les colonnes du modèle et valide"""
    with patched_attrs(monkeypatch, essais_import_sage, ModelFormInsertion=_FakeInsertion):
        essais_import_sage.import_sage(Path("devises.heron"), CurrencySage, CurrencySageForm)

    fake = _FakeInsertion.created[0]
    assert fake.kwargs == {
        "file_to_iter": Path("devises.heron"),
        "columns_dict": CurrencySage.get_columns_import(),
        "validator": CurrencySageForm,
        "uniques": CurrencySage.get_uniques(),
    }
    assert fake.validated
    assert not fake.exited


def test_import_sage_z(monkeypatch, caplog):
    """import_sage_z utilise l'insertion en context manager et affiche les erreurs"""
    caplog.set_level(logging.INFO, logger="django")
    with patched_attrs(monkeypatch, essais_import_sage, ModelFormInsertion=_FakeInsertion):
        essais_import_sage.import_sage_z(Path("devises.heronz"), CurrencySageForm)

    fake = _FakeInsertion.created[0]
    assert fake.kwargs["columns_dict"] == {name: name for name in CurrencySage.get_columns_import()}
    assert fake.validated
    assert fake.exited
    assert "['erreur de test']" in caplog.text


def test_essai_iter_file_to_insert(monkeypatch, caplog):
    """Chaque ligne est validée par CurrencySageSchema : affichage du dict ou des erreurs"""
    caplog.set_level(logging.INFO, logger="django")
    valid_row: ClassVar = {
        "currency_current": "EUR",
        "currency_change": "USD",
        "exchange_date": "010124",
        "exchange_type": "1",
        "exchange_rate": "1.1",
        "exchange_inverse": "0.9",
        "divider": "1",
        "modification_date": "010124",
    }
    invalid_row: ClassVar = {**valid_row, "exchange_date": ""}

    with patched_attrs(
        monkeypatch, essais_import_sage, IterFileToInsert=_fake_iter_file([valid_row, invalid_row])
    ):
        essais_import_sage.essai_iter_file_to_insert(Path("devises.heronz"))

    out = caplog.text

    assert "'currency_current': 'EUR'" in out
    assert "datetime.date(2024, 1, 1)" in out
    assert "Input should be a valid date" in out


def test_constantes_du_script():
    """Les dictionnaires de colonnes sont (par virgule finale) des tuples d'un dict"""
    assert isinstance(essais_import_sage.columns_dict, tuple)
    assert list(essais_import_sage.columns_dict[0]) == list(CurrencySage.get_columns_import())
    assert set(essais_import_sage.columns_dict_z[0].values()) == {None}
