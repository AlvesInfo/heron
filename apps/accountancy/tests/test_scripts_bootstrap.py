# pylint: disable=E0401,W0621
"""FR : Tests de l'amorçage Django des scripts autonomes (BASE_DIR selon la machine)


EN : Tests for standalone scripts Django bootstrap (BASE_DIR depending on the host)

Commentaire:

extraction_cct, import_sage_data et manual_import sont lancés hors Django (supervisor, cron) :
ils fixent BASE_DIR et appellent django.setup() à l'import. On recharge les modules avec un
nom de machine simulé pour couvrir les deux branches.

created at: 2026-10-10
created by: Paulo ALVES
"""

import importlib
import platform
import sys
import types

import pytest

from apps.accountancy.imports import extraction_cct
from apps.accountancy.loops import import_sage_data, manual_import
from conftest import patched_attrs


@pytest.mark.parametrize("module", [extraction_cct, import_sage_data, manual_import])
@pytest.mark.parametrize(
    ("node", "expected_base_dir"),
    [("MSI", "/"), ("PauloMSI", "/"), ("serveur-prod", "/home/paulo/heron")],
)
def test_base_dir_selon_la_machine(monkeypatch, module, node, expected_base_dir):
    """Sur les postes de dev Windows (PauloMSI, MSI) BASE_DIR reste "/", ailleurs /home/paulo/heron"""
    monkeypatch.setattr(sys, "path", list(sys.path))

    try:
        with patched_attrs(monkeypatch, platform, uname=lambda: types.SimpleNamespace(node=node)):
            reloaded = importlib.reload(module)

            assert expected_base_dir == reloaded.BASE_DIR
            assert expected_base_dir in sys.path
    finally:
        importlib.reload(module)

    assert hasattr(module, "main" if module is not extraction_cct else "update_cct_sage")
