import os
from pathlib import Path

from apps.core.functions.functions_setups import settings

path_dir = settings.APPS_DIR

apps = [
    # "accountancy",
    # "articles",
    # "book",
    "centers_clients",
    # "centers_purchasing",
    # "clients_invoices",
    # "clients_validations",
    # "core",
    # "countries",
    # "edi",
    # "groups",
    # "import_files",
    # "parameters",
    # "periods",
    # "permissions",
    # "suppliers_invoices",
    # "suppliers_validations",
    # "traces",
    # "users",
]

dirs = [
    "bin",
    "data_fixtures",
    "essais",
    "excel_outputs",
    "exports",
    "forms",
    "forms/forms_serializers",
    "forms/forms_django",
    "forms/forms_djantic",
    "forms/forms_pydantic",
    "imports",
    "loops",
    "migrations",
    "parameters",
    "tasks",
    "templates",
    "tests",
    "validations",
]

for app in apps:
    app_dir = path_dir / app
    Path.mkdir(app_dir, exist_ok=True)

    # os.system(f"django-admin startapp {app} {app_dir.resolve()}")
    for directory in dirs:
        Path.mkdir(app_dir / directory, exist_ok=True)
        if not Path(app_dir / directory / "__init__.py").exists():
            Path(app_dir / directory / "__init__.py").touch()

    # suppression des fichiers de tests remplacer par un package tests
    file = Path(app_dir) / "tests.py"
    if file.is_file():
        file.unlink()














