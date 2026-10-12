# pylint: disable=E0401,W0621
"""FR : Tests de la boucle d'import supervisor des tiers Sage (apps/book/loops/imports_loop.py)


EN : Tests for book supervisor import loop

created at: 2026-10-11
created by: Paulo ALVES
"""

import logging
import shutil

import pytest

from apps.book.imports import imports_sage
from apps.book.loops import imports_loop
from apps.book.models import (
    BookAdressesSage,
    BookBanksSage,
    BookContactsSage,
    BpcBookSage,
    BprBookSage,
    BpsBookSage,
    CodeContactsSage,
)
from apps.core.models.models_notifications import Notification
from apps.data_flux.models import Trace
from conftest import patched_attrs

pytestmark = pytest.mark.django_db


# CARTOGRAPHIE =====================================================================================


def test_processing_dict_couvre_les_fichiers_des_modeles():
    """Chaque fichier Sage attendu est routé vers sa fonction d'import, dans l'ordre des dépendances"""
    expected = {
        BprBookSage.file_import_sage(): imports_sage.bpr_sage,
        BpsBookSage.file_import_sage(): imports_sage.bps_sage,
        BpcBookSage.file_import_sage(): imports_sage.bpc_sage,
        BookAdressesSage.file_import_sage(): imports_sage.adress_sage,
        CodeContactsSage.file_import_sage(): imports_sage.code_contact_sage,
        BookContactsSage.file_import_sage(): imports_sage.contact_sage,
        BookBanksSage.file_import_sage(): imports_sage.bank_sage,
    }

    assert imports_loop.processing_dict == expected
    assert next(iter(imports_loop.processing_dict)) == "ZBIBPR_journalier.heron"


# GET PROCESSING FILES =============================================================================


def _drop_in_archive(sage_dirs, *names):
    for name in names:
        (sage_dirs.archive / name).write_text(f"contenu {name}", encoding="utf8")


def test_get_processing_files_deplace_les_fichiers_connus(sage_dirs):
    """Seuls les fichiers listés dans processing_dict sont déplacés de l'archive X3 vers processing"""
    _drop_in_archive(sage_dirs, "ZBIBANK_journalier.heron", "ZBIBPR_journalier.heron", "autre.txt")

    files = imports_loop.get_processing_files()

    assert [file.name for file in files] == ["ZBIBPR_journalier.heron", "ZBIBANK_journalier.heron"]
    assert all(file.parent == sage_dirs.processing and file.is_file() for file in files)
    assert [path.name for path in sage_dirs.archive.iterdir()] == ["autre.txt"]


@pytest.mark.usefixtures("sage_dirs")
def test_get_processing_files_archive_vide():
    assert imports_loop.get_processing_files() == []


# PROCESS ==========================================================================================


@pytest.fixture
def fake_processing(monkeypatch, make_trace):
    """Remplace processing_dict par des doublures (mêmes clés, même ordre) qui enregistrent

    l'ordre des appels, et neutralise les traitements finaux (emails, fichiers excel).
    """
    calls = {"files": [], "emails": 0, "excel": 0}

    def _make_fake(name):
        def _fake(file):
            calls["files"].append(file.name)
            return make_trace(file_name=file.name, flow_name=name), f"ok {name}"

        return _fake

    fake_dict = {name: _make_fake(name) for name in imports_loop.processing_dict}

    def _emails():
        calls["emails"] += 1

    def _excel():
        calls["excel"] += 1

    with patched_attrs(
        monkeypatch,
        imports_loop,
        processing_dict=fake_dict,
        check_emails_notifications=_emails,
        writre_book_files=_excel,
    ):
        yield calls, fake_dict


def test_process_traite_dans_l_ordre_et_sauvegarde(sage_dirs, fake_processing):
    """Les fichiers sont traités dans l'ordre de processing_dict puis déplacés en backup"""
    calls, _ = fake_processing
    _drop_in_archive(
        sage_dirs, "ZBIBANK_journalier.heron", "ZBIADDR_journalier.heron", "ZBIBPR_journalier.heron"
    )

    imports_loop.process()

    assert calls["files"] == [
        "ZBIBPR_journalier.heron",
        "ZBIADDR_journalier.heron",
        "ZBIBANK_journalier.heron",
    ]
    assert sorted(path.name for path in sage_dirs.backup.iterdir()) == sorted(calls["files"])
    assert list(sage_dirs.processing.iterdir()) == []
    assert Trace.objects.filter(errors=False).count() == 3
    assert (calls["emails"], calls["excel"]) == (1, 1)


@pytest.mark.usefixtures("sage_dirs")
def test_process_sans_fichier(fake_processing):
    calls, _ = fake_processing

    imports_loop.process()

    assert calls["files"] == []
    assert (calls["emails"], calls["excel"]) == (1, 1)


def test_process_type_error_sans_trace(sage_dirs, fake_processing, caplog):
    """Une fonction qui ne renvoie pas (trace, to_print) déclenche la branche TypeError"""
    calls, fake_dict = fake_processing
    fake_dict["ZBIBPS_journalier.heron"] = lambda file: None
    _drop_in_archive(sage_dirs, "ZBIBPS_journalier.heron", "ZBIBANK_journalier.heron")

    with caplog.at_level(logging.ERROR, logger="imports"):
        imports_loop.process()

    assert "TypeError" in caplog.text
    assert calls["files"] == ["ZBIBANK_journalier.heron"]
    assert (sage_dirs.processing / "ZBIBPS_journalier.heron").is_file()
    assert (sage_dirs.backup / "ZBIBANK_journalier.heron").is_file()
    assert Trace.objects.count() == 1


def test_process_exception_generale_sans_trace(sage_dirs, fake_processing, caplog):
    """Une exception levée avant la création de la trace est journalisée, la boucle continue"""
    calls, fake_dict = fake_processing

    def _boom(file):
        raise ValueError(f"fichier illisible {file.name}")

    fake_dict["ZBIBPR_journalier.heron"] = _boom
    _drop_in_archive(sage_dirs, "ZBIBPR_journalier.heron", "ZBIBPC_journalier.heron")

    with caplog.at_level(logging.ERROR, logger="imports"):
        imports_loop.process()

    assert "Exception Générale: ZBIBPR_journalier.heron" in caplog.text
    assert "fichier illisible" in caplog.text
    assert calls["files"] == ["ZBIBPC_journalier.heron"]
    assert Trace.objects.count() == 1


@pytest.mark.usefixtures("fake_processing")
def test_process_exception_apres_trace_marque_la_trace_en_erreur(sage_dirs, caplog):
    """Si l'erreur survient après l'import (déplacement en backup impossible), la trace est marquée"""
    _drop_in_archive(sage_dirs, "ZBIBPC_journalier.heron")
    shutil.rmtree(sage_dirs.backup)

    with caplog.at_level(logging.ERROR, logger="imports"):
        imports_loop.process()

    trace = Trace.objects.get()
    assert trace.errors is True
    assert "Une erreur c'est produite veuillez consulter les logs" in trace.comment
    assert "Exception Générale: ZBIBPC_journalier.heron" in trace.comment
    assert (sage_dirs.processing / "ZBIBPC_journalier.heron").is_file()


@pytest.mark.usefixtures("sage_dirs", "fake_processing")
def test_process_erreur_des_fichiers_excel(monkeypatch, caplog):
    """L'erreur de génération des fichiers excel est journalisée sans interrompre"""

    def _boom():
        raise RuntimeError("excel cassé")

    with (
        patched_attrs(monkeypatch, imports_loop, writre_book_files=_boom),
        caplog.at_level(logging.ERROR, logger="imports"),
    ):
        imports_loop.process()

    assert "writre_book_files()" in caplog.text
    assert "excel cassé" in caplog.text


@pytest.mark.usefixtures("sage_dirs")
def test_process_avec_les_vrais_traitements_finaux(settings, tmp_path, make_society, make_user):
    """Sans fichier, process() vérifie réellement les emails et écrit les trois fichiers excel"""
    settings.MEDIA_EXCEL_FILES_DIR = tmp_path / "excel"
    (tmp_path / "excel").mkdir()
    make_user()
    make_society("TIERS01", email_01="faux")

    imports_loop.process()

    assert Notification.objects.filter(title="Erreurs Emails").count() == 1
    assert sorted(path.name for path in (tmp_path / "excel").iterdir()) == [
        "LISTING_DES_CLIENTS.xlsx",
        "LISTING_DES_FOURNISSEURS.xlsx",
        "LISTING_DES_TIERS.xlsx",
    ]
