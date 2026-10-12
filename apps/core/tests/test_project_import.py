"""Garde-fou de la directive D1 : le projet (settings, apps, URLconf) doit se charger sans base."""

import os
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[3]

IMPORT_SCRIPT = """
import django
django.setup()
import heron.urls
from django.db import connection
assert connection.connection is None, "une connexion a été ouverte à l'import"
print("patterns:", len(heron.urls.urlpatterns))
"""


def test_urlconf_imports_without_any_database():
    """L'URLconf s'importe alors que la base configurée n'existe pas : aucun module du projet ne

    doit interroger la base à l'import (anciennement les schémas djantic d'apps.edi).
    """
    env = {
        **os.environ,
        "DJANGO_SETTINGS_MODULE": "heron.settings.test",
        "TEST_NAME_DATABASE": "base_inexistante_pour_le_test_d_import",
        "PYTHONPATH": str(PROJECT_DIR),
    }

    result = subprocess.run(
        [sys.executable, "-c", IMPORT_SCRIPT],
        cwd=PROJECT_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )

    assert result.returncode == 0, result.stderr[-2000:]
    assert "patterns:" in result.stdout
