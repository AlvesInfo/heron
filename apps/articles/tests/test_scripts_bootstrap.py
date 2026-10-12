# pylint: disable=E0401,W0621
"""FR : Tests de l'amorçage Django des scripts autonomes de l'app articles (BASE_DIR selon la machine)


EN : Tests for standalone scripts Django bootstrap

created at: 2026-10-10
created by: Paulo ALVES
"""

import importlib
import platform
import sys
import types

import pytest

from apps.articles.bin import (
    bbgr_002_articles,
    bbgr_003_articles,
    bbgr_004_articles,
    bbgr_006_articles,
)
from apps.articles.data_fixtures import articles_fixtures, familles_stat_fixtures
from apps.articles.loops import imports_articles
from conftest import patched_attrs

SLASH_MODULES = [
    bbgr_002_articles,
    bbgr_003_articles,
    bbgr_004_articles,
    bbgr_006_articles,
    imports_articles,
]
WINDOWS_MODULES = [articles_fixtures, familles_stat_fixtures]


@pytest.mark.parametrize(
    ("module", "dev_dir"),
    [(m, "/") for m in SLASH_MODULES] + [(m, r"C:\SitesWeb\heron") for m in WINDOWS_MODULES],
)
@pytest.mark.parametrize("node", ["MSI", "serveur-prod"])
def test_base_dir_selon_la_machine(monkeypatch, module, dev_dir, node):
    """Poste de dev ou serveur : BASE_DIR différent, module rechargé"""
    monkeypatch.setattr(sys, "path", list(sys.path))
    expected = dev_dir if node == "MSI" else "/home/paulo/heron"

    try:
        with patched_attrs(monkeypatch, platform, uname=lambda: types.SimpleNamespace(node=node)):
            assert expected == importlib.reload(module).BASE_DIR
    finally:
        importlib.reload(module)
