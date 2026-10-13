# pylint: disable=E0401,W0621
"""FR : Tests de l'import Sage des pays (schéma djantic, fonction d'import, post-traitement, boucle)


     et des fixtures de pays
EN : Tests for countries Sage import and data fixtures

created at: 2026-10-11
created by: Paulo ALVES
"""

import csv
import datetime
import logging
import shutil
from pathlib import Path

import pytest

from apps.countries.bin.countries_post_processing import pays_post_insert
from apps.countries.data_fixtures.insert_fixtures import fixtures_pays, validate_boolean
from apps.countries.forms.forms_djantic.sage import CountrySageSchema
from apps.countries.imports import imports_sage
from apps.countries.imports.imports_sage import pays_sage
from apps.countries.loops import imports_loop
from apps.countries.models import Country
from apps.data_flux.models import Trace
from conftest import patched_attrs

pytestmark = pytest.mark.django_db

FILE_NAME = "ZBICRY_journalier.heron"


def _row(code, name, cee="1", cee_date="", cee_date_quit=""):
    """Ligne du fichier ZBICRY : 17 colonnes, booléens Sage 2 / 1, dates ddmmyy"""
    return [
        code,
        name,
        code,
        "99",
        code,
        f"{code}A",
        "250",
        "FRA",
        cee,
        cee_date,
        cee_date_quit,
        "",
        "EUR",
        "",
        "",
        "",
        "",
    ]


# SCHÉMA ===========================================================================================


def test_schema_config_et_nettoyage():
    """Colonnes du fichier, tildes et troncature, booléen Sage, dates ddmmyy ou 1900-01-01 par défaut"""
    validated = CountrySageSchema(
        country="FR",
        country_name="France~~France",
        country_iso_num="250",
        cee="2",
        cee_date="010195",
        cee_date_quit="",
    ).dict()

    assert CountrySageSchema.model_config["model"] is Country
    assert CountrySageSchema.model_config["include"] == list(Country.get_columns_import())
    assert validated["country_name"] == "France"
    assert validated["country_iso_num"] == 250
    assert validated["cee"] is True
    assert validated["cee_date"] == datetime.date(1995, 1, 1)
    assert validated["cee_date_quit"] == datetime.date(1900, 1, 1)
    assert validated["lang_iso"] is None


# IMPORT ===========================================================================================


@pytest.fixture
def sage_file(sage_dirs, make_csv, monkeypatch):
    """Fichier ZBICRY déposé dans le répertoire de processing (constante du module redirigée)"""
    monkeypatch.setattr(imports_sage, "proccessing_dir", sage_dirs.processing)

    def _factory(rows):
        written = make_csv(FILE_NAME, rows)
        destination = sage_dirs.processing / FILE_NAME
        written.replace(destination)
        return destination

    return _factory


def test_pays_sage_cree_la_trace_et_appelle_make_insert(sage_file, monkeypatch):
    calls = []

    def _recorder(model, flow_name, source, trace, validator, params_dict_loader, **kwargs):
        calls.append((model, flow_name, source, trace, validator, params_dict_loader, kwargs))
        return "Import : pays_sage\n\nPas d'erreurs\n"

    file = sage_file([_row("FR", "France")])

    with patched_attrs(monkeypatch, imports_sage, make_insert=_recorder):
        trace, to_print = pays_sage(file)

    model, flow_name, source, call_trace, validator, loader, kwargs = calls[0]
    assert isinstance(trace, Trace)
    assert (trace.trace_name, trace.flow_name, trace.application_name) == (
        "Mise à jour des Pays Sage",
        "pays_sage",
        "countries_imports_import_sage",
    )
    assert trace.comment == f"import journalier {FILE_NAME} des Pays Sage"
    assert "Pas d'erreurs" in to_print
    assert (model, flow_name, source, call_trace, validator) == (
        Country,
        "pays_sage",
        file,
        trace,
        CountrySageSchema,
    )
    assert loader == {"trace": trace, "add_fields_dict": {}}
    assert kwargs == {}


@pytest.mark.integration
def test_integration_pays_sage_insertion_puis_upsert(sage_file):
    """Chaîne data_flux réelle : création, dates vides annulées par le post-traitement, puis mise à jour"""
    file = sage_file(
        [_row("FR", "France", cee="2", cee_date="010195"), _row("US", "Etats~~Unis", cee="1")]
    )

    trace, to_print = pays_sage(file)

    france = Country.objects.get(pk="FR")
    usa = Country.objects.get(pk="US")
    assert "Pas d'erreurs" in to_print
    assert trace.errors is False
    assert (france.country_name, france.cee, france.cee_date, france.cee_date_quit) == (
        "France",
        True,
        datetime.date(1995, 1, 1),
        None,
    )
    assert (usa.country_name, usa.cee, usa.cee_date, usa.country_iso_num) == (
        "Etats",
        False,
        None,
        250,
    )

    trace, _ = pays_sage(
        sage_file(
            [
                _row(
                    "FR",
                    "France métropolitaine",
                    cee="2",
                    cee_date="010195",
                    cee_date_quit="311220",
                )
            ]
        )
    )

    france.refresh_from_db()
    assert trace.errors is False
    assert Country.objects.count() == 2
    assert (france.country_name, france.cee_date_quit) == (
        "France métropolitaine",
        datetime.date(2020, 12, 31),
    )


def test_post_traitement_annule_les_dates_sentinelles(make_country):
    make_country("FR", cee_date=datetime.date(1900, 1, 1), cee_date_quit=datetime.date(1900, 1, 1))
    make_country("GB", cee_date=datetime.date(1973, 1, 1), cee_date_quit=datetime.date(2020, 1, 31))

    pays_post_insert()

    assert Country.objects.get(pk="FR").cee_date is None
    assert Country.objects.get(pk="FR").cee_date_quit is None
    assert Country.objects.get(pk="GB").cee_date_quit == datetime.date(2020, 1, 31)


def test_repertoire_de_processing_module():
    assert isinstance(imports_sage.proccessing_dir, Path)


# BOUCLE ===========================================================================================


def test_processing_dict_et_fichier_du_modele():
    assert imports_loop.processing_dict == {Country.file_import_sage(): imports_sage.pays_sage}


def test_get_processing_files_deplace_le_fichier_des_pays(sage_dirs):
    (sage_dirs.archive / FILE_NAME).write_text("contenu", encoding="utf8")
    (sage_dirs.archive / "autre.txt").write_text("contenu", encoding="utf8")

    files = imports_loop.get_processing_files()

    assert [file.name for file in files] == [FILE_NAME]
    assert files[0].parent == sage_dirs.processing
    assert [path.name for path in sage_dirs.archive.iterdir()] == ["autre.txt"]


@pytest.mark.usefixtures("sage_dirs")
def test_get_processing_files_archive_vide():
    assert imports_loop.get_processing_files() == []


@pytest.fixture
def fake_processing(monkeypatch, make_trace):
    """Doublure de l'import des pays enregistrant les appels"""
    calls = []

    def _fake(file):
        calls.append(file.name)
        return make_trace(file_name=file.name, flow_name="pays_sage"), "ok"

    with patched_attrs(monkeypatch, imports_loop, processing_dict={FILE_NAME: _fake}):
        yield calls


def test_process_traite_et_sauvegarde(sage_dirs, fake_processing):
    (sage_dirs.archive / FILE_NAME).write_text("contenu", encoding="utf8")

    imports_loop.process()

    assert fake_processing == [FILE_NAME]
    assert (sage_dirs.backup / FILE_NAME).is_file()
    assert list(sage_dirs.processing.iterdir()) == []
    assert Trace.objects.get().errors is False


@pytest.mark.usefixtures("sage_dirs", "fake_processing")
def test_process_sans_fichier():
    imports_loop.process()

    assert Trace.objects.count() == 0


def test_process_type_error_sans_trace(sage_dirs, monkeypatch, caplog):
    (sage_dirs.archive / FILE_NAME).write_text("contenu", encoding="utf8")

    with (
        patched_attrs(monkeypatch, imports_loop, processing_dict={FILE_NAME: lambda file: None}),
        caplog.at_level(logging.ERROR, logger="imports"),
    ):
        imports_loop.process()

    assert "TypeError" in caplog.text
    assert (sage_dirs.processing / FILE_NAME).is_file()


def test_process_exception_generale_sans_trace(sage_dirs, monkeypatch, caplog):
    def _boom(file):
        raise ValueError(f"illisible {file.name}")

    (sage_dirs.archive / FILE_NAME).write_text("contenu", encoding="utf8")

    with (
        patched_attrs(monkeypatch, imports_loop, processing_dict={FILE_NAME: _boom}),
        caplog.at_level(logging.ERROR, logger="imports"),
    ):
        imports_loop.process()

    assert f"Exception Générale: {FILE_NAME}" in caplog.text
    assert Trace.objects.count() == 0


@pytest.mark.usefixtures("fake_processing")
def test_process_exception_apres_trace_marque_la_trace(sage_dirs, caplog):
    """Déplacement en backup impossible : la trace est marquée en erreur"""
    (sage_dirs.archive / FILE_NAME).write_text("contenu", encoding="utf8")
    shutil.rmtree(sage_dirs.backup)

    with caplog.at_level(logging.ERROR, logger="imports"):
        imports_loop.process()

    trace = Trace.objects.get()
    assert trace.errors is True
    assert trace.comment.endswith("\n. Une erreur c'est produite veuillez consulter les logs")


# FIXTURES DE DONNÉES ==============================================================================


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("true", True),
        ("OUI", True),
        ("1", True),
        ("false", False),
        ("non", False),
        ("0", False),
        ("peut-être", "peut-être"),
        (3, True),
        (0, False),
        (None, None),
    ],
)
def test_validate_boolean(value, expected):
    assert validate_boolean(value) == expected


def _csv_rows():
    path = Path(__file__).resolve().parents[1] / "data_fixtures" / "pays_fixtures.csv"

    with path.open(encoding="utf8") as file:
        return [row for row in csv.reader(file, delimiter=";", quotechar='"') if row]


def test_fixtures_pays_charge_le_fichier(make_country):
    """Un pays par code (première ligne conservée), les pays déjà présents ne sont pas modifiés"""
    make_country("IT", "Italie déjà là")
    rows = _csv_rows()

    fixtures_pays()

    france = Country.objects.get(pk="FR")
    usa = Country.objects.get(pk="US")
    assert Country.objects.count() == len({row[1] for row in rows})
    assert (
        france.country_name,
        france.currency_sigle,
        france.currency_name,
        france.currency_iso,
        france.cee,
    ) == ("FRANCE", "€", "Euro", "EUR", True)
    assert france.phone_indicatif is None
    assert (usa.country_name, usa.phone_indicatif, usa.cee) == ("ETATS UNIS", "1", False)
    assert Country.objects.get(pk="GB").country_name == "ANGLETERRE"
    assert Country.objects.get(pk="IT").country_name == "Italie déjà là"
    assert Country.objects.get(pk="AF").currency_sigle is None

    fixtures_pays()

    assert Country.objects.count() == len({row[1] for row in rows})


def test_fixtures_pays_ignore_les_lignes_vides(settings, tmp_path):
    """Les lignes vides du fichier sont ignorées (répertoire des apps redirigé vers tmp_path)"""
    file = tmp_path / "countries" / "data_fixtures" / "pays_fixtures.csv"
    file.parent.mkdir(parents=True)
    file.write_text('"BELGIQUE";"BE";"€";"Euro";"EUR";"";"true";"999"\n\n', encoding="utf8")
    settings.APPS_DIR = tmp_path

    fixtures_pays()

    assert list(Country.objects.values_list("country", "cee")) == [("BE", True)]
