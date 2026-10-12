# pylint: disable=E0401,W0621
"""
FR : Tests de l'amorçage Django des scripts autonomes de centers_clients (BASE_DIR selon la machine)
EN : Tests for standalone scripts Django bootstrap

created at: 2026-10-10
created by: Paulo ALVES
"""
import importlib
import platform
import sys
import types

import pytest

from apps.centers_clients.data_fixtures import import_clients_from_bi_file
from apps.centers_clients.imports import import_maisons_bi
from conftest import patched_attrs


@pytest.mark.parametrize("module", [import_maisons_bi, import_clients_from_bi_file])
@pytest.mark.parametrize(("node", "expected"), [("MSI", r"C:\SitesWeb\heron"), ("serveur-prod", "/home/paulo/heron")])
def test_base_dir_selon_la_machine(monkeypatch, module, node, expected):
    """Poste Windows de dev ou serveur Linux : BASE_DIR différent, module rechargé"""
    monkeypatch.setattr(sys, "path", list(sys.path))

    try:
        with patched_attrs(monkeypatch, platform, uname=lambda: types.SimpleNamespace(node=node)):
            assert expected == importlib.reload(module).BASE_DIR
    finally:
        importlib.reload(module)
