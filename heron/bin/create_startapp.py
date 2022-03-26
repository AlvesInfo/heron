import os
from pathlib import Path

from apps.core.functions.functions_setups import settings

path_dir = settings.APPS_DIR

apps = [
    "accountancy",
    "articles",
    "book",
    "centers_purchasing",
    "clients_invoices",
    "clients_validations",
    "core",
    "countries",
    "edi",
    "groups",
    "import_files",
    "parameters",
    "periods",
    "permissions",
    "suppliers_invoices",
    "suppliers_validations",
    "users",
]

for app in apps:
    app_dir = path_dir / app
    Path.mkdir(app_dir, exist_ok=True)
    # Répertoires des migrations
    Path.mkdir(app_dir / "migrations", exist_ok=True)
    Path(app_dir / "migrations" / "__init__.py").touch()
    # Répertoires de templates
    Path.mkdir(app_dir / "templates", exist_ok=True)
    Path(app_dir / "templates" / "__init__.py").touch()
    Path.mkdir(app_dir / "templates" / app, exist_ok=True)
    Path(app_dir / "templates" / app / "__init__.py").touch()
    # Répertoire bin
    Path.mkdir(app_dir / "bin", exist_ok=True)
    Path(app_dir / "bin" / "__init__.py").touch()
    # Répertoire excel_outputs
    Path.mkdir(app_dir / "excel_outputs", exist_ok=True)
    Path(app_dir / "excel_outputs" / "__init__.py").touch()
    # Répertoire serializers
    Path.mkdir(app_dir / "serializers", exist_ok=True)
    Path(app_dir / "serializers" / "__init__.py").touch()
    # Répertoire data_fixtures
    Path.mkdir(app_dir / "data_fixtures", exist_ok=True)
    Path(app_dir / "data_fixtures" / "__init__.py").touch()
    # Répertoire tests
    Path.mkdir(app_dir / "tests", exist_ok=True)
    Path(app_dir / "tests" / "__init__.py").touch()
    # Répertoire tests essais
    Path.mkdir(app_dir / "tests/essais", exist_ok=True)
    Path(app_dir / "tests/essais" / "__init__.py").touch()
    # Répertoire tests test_fixtures
    Path.mkdir(app_dir / "tests/test_fixtures", exist_ok=True)
    Path(app_dir / "tests/test_fixtures" / "__init__.py").touch()

    os.system(f"django-admin startapp {app} {app_dir.resolve()}")

    # suppression des fichiers de tests remplacer par un package tests
    file = Path(app_dir) / "tests.py"
    if file.is_file():
        file.unlink()
