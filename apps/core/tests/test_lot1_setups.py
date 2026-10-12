# pylint: disable=E0401,W0621
"""FR : Tests de l'amorçage Django des scripts (functions_setups.py) : BASE_DIR selon le système,


     tolérance au django.setup() déjà réalisé
EN : Tests for scripts Django bootstrap

created at: 2026-10-11
created by: Paulo ALVES
"""

import importlib
import platform
import sys

import django
import pytest

from apps.core.functions import functions_setups
from conftest import patched_attrs


@pytest.mark.parametrize(
    ("system", "expected"),
    [
        ("Darwin", "/Users/paulo/SitesWeb/heron"),
        ("Linux", "/home/paulo/heron"),
        ("Windows", r"C:\\SitesWeb\\heron"),
    ],
)
def test_base_dir_selon_le_systeme(monkeypatch, system, expected):
    """Le répertoire du projet est posé en tête de sys.path selon le système d'exploitation"""
    monkeypatch.setattr(sys, "path", list(sys.path))

    try:
        with patched_attrs(monkeypatch, platform, system=lambda: system):
            reloaded = importlib.reload(functions_setups)

        assert sys.path[0] == expected
        assert sys.path[-1] == expected
        assert reloaded is functions_setups
    finally:
        importlib.reload(functions_setups)

    assert functions_setups.CNX_STRING == functions_setups.settings.CNX_STRING
    assert functions_setups.User.__name__ == "User"


def test_django_deja_initialise_est_tolere(monkeypatch):
    """L'erreur « populate() isn't reentrant » d'un second django.setup() est ignorée"""
    monkeypatch.setattr(sys, "path", list(sys.path))

    def _already(*_args, **_kwargs):
        raise RuntimeError("populate() isn't reentrant")

    try:
        with patched_attrs(monkeypatch, django, setup=_already):
            reloaded = importlib.reload(functions_setups)

        assert reloaded.connection is functions_setups.connection
    finally:
        importlib.reload(functions_setups)


def test_autre_erreur_d_initialisation_remonte(monkeypatch):
    monkeypatch.setattr(sys, "path", list(sys.path))

    def _broken(*_args, **_kwargs):
        raise RuntimeError("réglages absents")

    try:
        with (
            patched_attrs(monkeypatch, django, setup=_broken),
            pytest.raises(RuntimeError, match="réglages absents"),
        ):
            importlib.reload(functions_setups)
    finally:
        importlib.reload(functions_setups)
