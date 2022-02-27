import os
from pathlib import Path

path_dir = Path(r"C:\SitesWeb\heron\apps")

apps = [
    "articles",
    "bin",
    "business_centers",
    "centers_purchasing",
    "clients_invoices",
    "clients_book",
    "clients_validations",
    "core",
    "countries",
    "groups",
    "parameters",
    "permitions",
    "periods",
    "suppliers_invoices",
    "suppliers_book",
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

    os.system(f"django-admin startapp {app} {app_dir.resolve()}")
