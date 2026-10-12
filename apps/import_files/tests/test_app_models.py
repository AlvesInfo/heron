# pylint: disable=E0401,W0212
"""FR : Tests de la configuration et des modèles de l'app import_files (sha512 des fichiers importés)


EN : Tests for import_files app configuration and models

created at: 2026-10-11
created by: Paulo ALVES
"""

import importlib

import pytest
from django.apps import apps as django_apps
from django.contrib import admin
from django.db import IntegrityError, transaction

from apps.import_files import urls as import_files_urls
from apps.import_files.apps import ImportFilesConfig
from apps.import_files.models import HTML_COLORS, ErrorsShaImportFIles, ShaImportInvoicesFiles

pytestmark = pytest.mark.django_db


def test_app_config():
    """L'app est enregistrée et routée (URLconf vide), deux modèles, rien dans l'admin"""
    config = django_apps.get_app_config("import_files")

    assert isinstance(config, ImportFilesConfig)
    assert config.name == "apps.import_files"
    assert ImportFilesConfig.default_auto_field == "django.db.models.BigAutoField"
    assert {model.__name__ for model in config.get_models()} == {
        "ShaImportInvoicesFiles",
        "ErrorsShaImportFIles",
    }
    assert import_files_urls.urlpatterns == []
    assert not any(model._meta.app_label == "import_files" for model in admin.site._registry)


@pytest.mark.parametrize(
    "module_name",
    [
        "apps.import_files.views",
        "apps.import_files.bin",
        "apps.import_files.data_fixtures",
        "apps.import_files.essais",
        "apps.import_files.excel_outputs",
        "apps.import_files.exports",
        "apps.import_files.forms",
        "apps.import_files.forms.forms_django",
        "apps.import_files.forms.forms_djantic",
        "apps.import_files.forms.forms_pydantic",
        "apps.import_files.forms.forms_serializers",
        "apps.import_files.imports",
        "apps.import_files.loops",
        "apps.import_files.parameters",
        "apps.import_files.tasks",
        "apps.import_files.templates",
        "apps.import_files.templates.import_files",
        "apps.import_files.validations",
    ],
)
def test_packages_importables(module_name):
    assert importlib.import_module(module_name) is not None


def test_sha_des_fichiers_importes():
    """Un sha512 par fichier, tri par nom, affichage du nom (vide si absent)"""
    second = ShaImportInvoicesFiles.objects.create(
        id_sha512_file="b" * 128, file_name="facture_b.csv"
    )
    first = ShaImportInvoicesFiles.objects.create(
        id_sha512_file="a" * 128, file_name="facture_a.csv"
    )
    anonymous = ShaImportInvoicesFiles.objects.create(id_sha512_file="c" * 128)

    assert str(first) == "facture_a.csv"
    assert str(anonymous) == ""
    # tri par nom, les noms absents (NULL) en dernier sous PostgreSQL
    assert list(ShaImportInvoicesFiles.objects.all()) == [first, second, anonymous]
    assert first.uuid_identification != second.uuid_identification

    with pytest.raises(IntegrityError), transaction.atomic():
        ShaImportInvoicesFiles.objects.create(id_sha512_file="a" * 128, file_name="doublon.csv")


def test_erreurs_des_fichiers_importes():
    """Erreurs rattachées à un fichier, triées par ligne, supprimées avec lui ; couleurs html"""
    sha = ShaImportInvoicesFiles.objects.create(id_sha512_file="a" * 128, file_name="facture.csv")
    later = ErrorsShaImportFIles.objects.create(
        sha_file=sha,
        file_line=12,
        column="qty",
        value_on_error="x",
        error="entier attendu",
        html_color="#FF0000",
    )
    earlier = ErrorsShaImportFIles.objects.create(
        sha_file=sha, file_line=3, column="date", expected_format="jj/mm/aaaa", html_color="#00B050"
    )
    orphan = ErrorsShaImportFIles.objects.create(file_line=None)

    assert str(later) == "facture.csv - 12 - qty"
    assert str(orphan) == " -  - "
    assert list(sha.sha_file_sha.all()) == [earlier, later]
    assert later.get_html_color_display() == "red"
    assert HTML_COLORS == (("#FF0000", "red"), ("#00B050", "green"))

    sha.delete()

    assert set(ErrorsShaImportFIles.objects.values_list("pk", flat=True)) == {orphan.pk}
