# pylint: disable=E0401,W0621
"""
FR : Tests des boucles d'import supervisor (apps/accountancy/loops)
EN : Tests for supervisor import loops

created at: 2026-10-10
created by: Paulo ALVES
"""
import logging
import shutil
from pathlib import Path

import pytest

from apps.accountancy.imports import imports_sage
from apps.accountancy.loops import import_sage_data, imports_loop, manual_import
from apps.accountancy.models import (
    AccountSage,
    AxeSage,
    CategorySage,
    ModeReglement,
    PaymentCondition,
    SectionSage,
    TabDivSage,
    VatRatSage,
    VatRegimeSage,
    VatSage,
)
from apps.data_flux.models import Trace
from conftest import patched_attrs

pytestmark = pytest.mark.django_db


# CARTOGRAPHIE =====================================================================================


def test_processing_dict_couvre_les_fichiers_des_modeles():
    """Chaque fichier Sage attendu par un modèle est routé vers sa fonction d'import"""
    expected = {
        AccountSage.file_import_sage(): imports_sage.account_sage,
        AxeSage.file_import_sage(): imports_sage.axe_sage,
        SectionSage.file_import_sage(): imports_sage.section_sage,
        ModeReglement.file_import_sage(): imports_sage.mode_reglement,
        VatRegimeSage.file_import_sage(): imports_sage.vat_regime_sage,
        PaymentCondition.file_import_sage(): imports_sage.payement_condition,
        TabDivSage.file_import_sage(): imports_sage.tab_div_sage,
        CategorySage.file_import_sage()[0]: imports_sage.category_sage_client,
        CategorySage.file_import_sage()[1]: imports_sage.category_sage_supplier,
        VatSage.file_import_sage(): imports_sage.vat_sage,
        VatRatSage.file_import_sage(): imports_sage.vat_rat_sage,
    }

    assert imports_loop.processing_dict == expected
    # l'ordre du dict définit l'ordre d'intégration (dépendances : comptes, axes, sections, ...)
    assert list(imports_loop.processing_dict)[:3] == [
        "ZBIACCOUNT_journalier.heron",
        "ZBIAXES_journalier.heron",
        "ZBICCE_journalier.heron",
    ]


# GET PROCESSING FILES =============================================================================


def _drop_in_archive(sage_dirs, *names):
    paths = []

    for name in names:
        path = sage_dirs.archive / name
        path.write_text(f"contenu {name}", encoding="utf8")
        paths.append(path)

    return paths


def test_get_processing_files_deplace_les_fichiers_connus(sage_dirs):
    """Seuls les fichiers listés dans processing_dict sont déplacés de l'archive X3 vers processing"""
    _drop_in_archive(sage_dirs, "ZBIAXES_journalier.heron", "ZBIVAT_journalier.heron", "autre.txt")

    files = imports_loop.get_processing_files()

    assert sorted(file.name for file in files) == ["ZBIAXES_journalier.heron", "ZBIVAT_journalier.heron"]
    assert all(file.parent == sage_dirs.processing and file.is_file() for file in files)
    assert [path.name for path in sage_dirs.archive.iterdir()] == ["autre.txt"]


@pytest.mark.usefixtures('sage_dirs')
def test_get_processing_files_archive_vide():
    """Sans fichier dans l'archive : liste vide"""
    assert imports_loop.get_processing_files() == []


# PROCESS ==========================================================================================


@pytest.fixture
def fake_processing(monkeypatch, make_trace):
    """
    Remplace processing_dict par des doublures (mêmes clés, même ordre) qui enregistrent
    l'ordre des appels, et neutralise les extractions finales.
    """
    calls = {"files": [], "cct": 0, "plan": 0}

    def _make_fake(name):
        def _fake(file):
            calls["files"].append(file.name)
            return make_trace(file_name=file.name, flow_name=name), f"ok {name}"

        return _fake

    fake_dict = {name: _make_fake(name) for name in imports_loop.processing_dict}

    def _cct():
        calls["cct"] += 1

    def _plan():
        calls["plan"] += 1

    with patched_attrs(
        monkeypatch, imports_loop, processing_dict=fake_dict, update_cct_sage=_cct, update_code_plan=_plan
    ):
        yield calls, fake_dict


def test_process_traite_dans_l_ordre_et_sauvegarde(sage_dirs, fake_processing):
    """Les fichiers sont traités dans l'ordre de processing_dict puis déplacés en backup"""
    calls, _ = fake_processing
    _drop_in_archive(sage_dirs, "ZBIVAT_journalier.heron", "ZBICCE_journalier.heron", "ZBIACCOUNT_journalier.heron")

    imports_loop.process()

    assert calls["files"] == ["ZBIACCOUNT_journalier.heron", "ZBICCE_journalier.heron", "ZBIVAT_journalier.heron"]
    assert sorted(path.name for path in sage_dirs.backup.iterdir()) == sorted(calls["files"])
    assert list(sage_dirs.processing.iterdir()) == []
    assert Trace.objects.filter(errors=False).count() == 3
    assert (calls["cct"], calls["plan"]) == (1, 1)


@pytest.mark.usefixtures('sage_dirs')
def test_process_sans_fichier(fake_processing):
    """Sans fichier, seules les extractions finales tournent"""
    calls, _ = fake_processing

    imports_loop.process()

    assert calls["files"] == []
    assert (calls["cct"], calls["plan"]) == (1, 1)


def test_process_type_error_sans_trace(sage_dirs, fake_processing, caplog):
    """Une fonction qui ne renvoie pas (trace, to_print) déclenche la branche TypeError"""
    calls, fake_dict = fake_processing
    fake_dict["ZBIAXES_journalier.heron"] = lambda file: None
    _drop_in_archive(sage_dirs, "ZBIAXES_journalier.heron", "ZBIVAT_journalier.heron")

    with caplog.at_level(logging.ERROR, logger="imports"):
        imports_loop.process()

    assert "TypeError" in caplog.text
    assert calls["files"] == ["ZBIVAT_journalier.heron"]
    assert (sage_dirs.processing / "ZBIAXES_journalier.heron").is_file()
    assert (sage_dirs.backup / "ZBIVAT_journalier.heron").is_file()
    assert Trace.objects.count() == 1


def test_process_exception_generale_sans_trace(sage_dirs, fake_processing, caplog):
    """Une exception levée avant la création de la trace est journalisée, la boucle continue"""
    calls, fake_dict = fake_processing

    def _boom(file):
        raise ValueError(f"fichier illisible {file.name}")

    fake_dict["ZBIACCOUNT_journalier.heron"] = _boom
    _drop_in_archive(sage_dirs, "ZBIACCOUNT_journalier.heron", "ZBIAXES_journalier.heron")

    with caplog.at_level(logging.ERROR, logger="imports"):
        imports_loop.process()

    assert "Exception Générale: ZBIACCOUNT_journalier.heron" in caplog.text
    assert "fichier illisible" in caplog.text
    assert calls["files"] == ["ZBIAXES_journalier.heron"]
    assert Trace.objects.count() == 1


@pytest.mark.usefixtures('fake_processing')
def test_process_exception_apres_trace_marque_la_trace_en_erreur(sage_dirs, caplog):
    """Si l'erreur survient après l'import (déplacement en backup impossible), la trace est marquée"""
    _drop_in_archive(sage_dirs, "ZBIAXES_journalier.heron")
    shutil.rmtree(sage_dirs.backup)

    with caplog.at_level(logging.ERROR, logger="imports"):
        imports_loop.process()

    trace = Trace.objects.get()
    assert trace.errors is True
    assert trace.comment.endswith("\n. Une erreur c'est produite veuillez consulter les logs")
    assert "Exception Générale: ZBIAXES_journalier.heron" in caplog.text
    assert (sage_dirs.processing / "ZBIAXES_journalier.heron").is_file()


@pytest.mark.usefixtures('sage_dirs', 'fake_processing')
def test_process_erreurs_des_extractions_finales(monkeypatch, caplog):
    """Les erreurs de update_cct_sage et update_code_plan sont journalisées sans interrompre"""

    def _cct_boom():
        raise RuntimeError("cct cassé")

    def _plan_boom():
        raise RuntimeError("plan cassé")

    with patched_attrs(monkeypatch, imports_loop, update_cct_sage=_cct_boom, update_code_plan=_plan_boom), caplog.at_level(
        logging.ERROR, logger="imports"
    ):
        imports_loop.process()

    assert "update_cct_sage()" in caplog.text
    assert "cct cassé" in caplog.text
    assert "update_code_plan()" in caplog.text
    assert "plan cassé" in caplog.text


@pytest.mark.usefixtures('sage_dirs')
def test_process_avec_les_vraies_extractions(make_section, make_account):
    """Sans fichier, process() exécute réellement update_cct_sage et update_code_plan"""
    make_section("CCT", "AF0001")
    make_account("FRA", "411000")

    imports_loop.process()

    from apps.accountancy.models import CctSage, CodePlanSage  # pylint: disable=C0415

    assert CctSage.objects.filter(cct="AF0001").exists()
    assert CodePlanSage.objects.filter(pk="FRA").exists()


# IMPORT SAGE DATA / MANUAL IMPORT =================================================================


def test_import_sage_data_main_enchaine_les_trois_imports(monkeypatch):
    """main() lance pays, comptabilité puis tiers, dans cet ordre"""
    order = []

    with patched_attrs(
        monkeypatch,
        import_sage_data,
        process_countries=lambda: order.append("countries"),
        process_accountancy=lambda: order.append("accountancy"),
        process_book=lambda: order.append("book"),
    ):
        import_sage_data.main()

    assert order == ["countries", "accountancy", "book"]


def test_import_sage_data_cible_les_vrais_process():
    """Sans doublure, main() pointe sur les process des apps countries, accountancy et book"""
    assert import_sage_data.process_accountancy is imports_loop.process
    assert import_sage_data.process_countries.__module__ == "apps.countries.loops.imports_loop"
    assert import_sage_data.process_book.__module__ == "apps.book.loops.imports_loop"


def test_manual_import_expose_main():
    """Le script d'import manuel réutilise main() de la boucle supervisor"""
    assert manual_import.main is import_sage_data.main
    assert Path(manual_import.BASE_DIR).is_absolute()
