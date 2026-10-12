# pylint: disable=E0401,W0621,W0212
"""FR : Tests des modèles, de la trace, des exceptions, de la vue d'import et de la configuration


     de l'app data_flux
EN : Tests for data_flux models, trace, exceptions, import view and app configuration

created at: 2026-10-11
created by: Paulo ALVES
"""

import importlib
import uuid

import pytest
from django.apps import apps as django_apps
from django.contrib import admin
from django.contrib.messages import get_messages
from django.db import IntegrityError, transaction
from django.urls import reverse

from apps.data_flux import exceptions, urls as data_flux_urls
from apps.data_flux.apps import CoreConfig
from apps.data_flux.models import Error, Essais, EssaisZ, Line, Trace, UploadFiles
from apps.data_flux.trace import get_trace

pytestmark = pytest.mark.django_db


def test_app_config():
    config = django_apps.get_app_config("data_flux")

    assert isinstance(config, CoreConfig)
    assert config.name == "apps.data_flux"
    assert {model.__name__ for model in config.get_models()} == {
        "Trace",
        "Line",
        "Error",
        "UploadFiles",
        "Essais",
        "EssaisZ",
    }
    assert [pattern.name for pattern in data_flux_urls.urlpatterns] == ["processing_files"]
    assert data_flux_urls.app_name == "apps.data_flux"
    assert not any(model._meta.app_label == "data_flux" for model in admin.site._registry)


@pytest.mark.parametrize(
    "module_name",
    [
        "apps.data_flux.views",
        "apps.data_flux.templates",
        "apps.data_flux.templates.data_flux",
        "apps.data_flux.tests",
    ],
)
def test_packages_importables(module_name):
    assert importlib.import_module(module_name) is not None


def test_hierarchie_des_exceptions():
    """Les exceptions de validation et postgres héritent de leurs familles"""
    assert issubclass(exceptions.GetAddDictError, exceptions.IterFileToInsertError)
    assert issubclass(exceptions.IsValidError, exceptions.ValidationFormError)
    assert issubclass(exceptions.IsValidError, AssertionError)
    assert issubclass(exceptions.FluxtypeError, exceptions.ValidationFormError)
    assert all(
        issubclass(getattr(exceptions, name), exceptions.PostgresDjangoError)
        for name in (
            "PostgresInsertMethodError",
            "PostgresCardinalityViolationError",
            "PostgresUniqueError",
            "PostgresKeyError",
            "PostgresTypeError",
            "PostgresPreparedError",
        )
    )
    assert all(
        issubclass(getattr(exceptions, name), ValueError)
        for name in ("OptoDateError", "OptoLinesError", "OptoQualifierError")
    )


# MODÈLES ==========================================================================================


def test_get_trace_et_lignes(make_user):
    """get_trace crée la trace à zéro ; lignes et erreurs rattachées par uuid ; tri par date"""
    trace = get_trace("Import test", "fichier.heron", "tests", "flux", "commentaire")
    later = get_trace("Import suivant", "fichier2.heron", "tests", "flux", "")
    line = Line.objects.create(
        trace=trace, insertion_type=Line.Insertiontype.ER, num_line=2, designation="ligne 2"
    )
    error = Error.objects.create(
        line=line, attr_name="code", message="invalide", data_expected="int", data_received="x"
    )

    assert isinstance(trace.uuid_identification, uuid.UUID)
    assert (
        trace.created_numbers_records,
        trace.updated_numbers_records,
        trace.errors_numbers_records,
        trace.unknown_numbers_records,
    ) == (0, 0, 0, 0)
    assert (trace.errors, trace.invoices, trace.time_to_process) == (False, False, 0)
    assert list(Trace.objects.all()) == [later, trace]
    assert line.get_insertion_type_display() == "Errors"
    assert Line.Insertiontype.PA.label == "Passed"
    assert trace.line_trace.get() == line
    assert line.error_line.get() == error
    assert make_user is not None

    with pytest.raises(IntegrityError), transaction.atomic():
        Line.objects.create(trace=trace, uuid_identification=line.uuid_identification)


def test_upload_files_et_modeles_d_essai():
    """Fichiers téléversés triés par fichier ; modèles d'essai avec leurs contraintes"""
    second = UploadFiles.objects.create(
        base_name_file="b.csv",
        id_sha512_file="sha-b",
        file="processing/files/b.csv",
        action="ACCOUNTS",
    )
    first = UploadFiles.objects.create(
        base_name_file="a.csv",
        id_sha512_file="sha-a",
        file="processing/files/a.csv",
        action="ACCOUNTS",
    )
    essai = Essais.objects.create(col_texte="texte", col_int=1)
    essai_z = EssaisZ.objects.create(col_texte="texte", col_2="2", col_3="3", col_int=1)

    assert list(UploadFiles.objects.all()) == [first, second]
    assert first.stack_id is None
    assert essai.col_2 is None
    assert essai_z.trace is None

    with pytest.raises(IntegrityError), transaction.atomic():
        EssaisZ.objects.create(col_texte="autre", col_int=1)

    with pytest.raises(IntegrityError), transaction.atomic():
        EssaisZ.objects.create(col_texte="texte", col_2="2", col_3="3", col_int=2)


# VUE D'IMPORT =====================================================================================


def test_processing_files_fonction_inconnue(logged_client):
    """Fonction non paramétrée : message critique et retour à la liste des fonctions"""
    response = logged_client.get(reverse("data_flux:processing_files", args=["inconnue"]))

    assert response.status_code == 302
    assert response.url == reverse("parameters:functions_list")
    assert logged_client.session["level"] == 50
    assert "'inconnue'" in next(iter(get_messages(response.wsgi_request))).message


def test_processing_files_fonction_mal_pointee(logged_client, make_invoice_function):
    """Fonction paramétrée vers un objet inexistant : même traitement qu'une fonction inconnue"""
    make_invoice_function("CASSEE", function="apps.data_flux.trace.inexistante")

    response = logged_client.get(reverse("data_flux:processing_files", args=["CASSEE"]))

    assert response.status_code == 302
    assert response.url == reverse("parameters:functions_list")


def test_processing_files_fonction_connue(logged_client, make_invoice_function):
    """Fonction paramétrée : l'écran d'import s'affiche, en GET comme en POST"""
    make_invoice_function("IMPORT_TEST", function="apps.data_flux.trace.get_trace")
    url = reverse("data_flux:processing_files", args=["IMPORT_TEST"])

    response = logged_client.get(url)
    posted = logged_client.post(url, {})

    assert response.status_code == 200
    assert response.context["titre_table"] == "Import en masse de données - Fonction : IMPORT_TEST"
    assert posted.status_code == 200
