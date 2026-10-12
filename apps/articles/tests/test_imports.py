# pylint: disable=E0401,W0621,R0913
"""FR : Tests des imports de comptes articles (imports/articles_without_account.py, articles_update_account.py)


EN : Tests for article accounts imports

created at: 2026-10-10
created by: Paulo ALVES
"""

import csv
from pathlib import Path

import openpyxl
import pytest
from xlrd.biffh import XLRDError

from apps.articles.forms.forms_djantic.forms_articles_account import ArticleAccountSageSchema
from apps.articles.imports import articles_without_account
from apps.articles.imports.articles_update_account import (
    update_articles_accounts,
    upsert_articles_accounts,
)
from apps.articles.imports.articles_without_account import (
    accounts_validation,
    delete_mac_files,
    file_for_insert_excel_to_csv,
    import_articles_without_account,
    insert_articles_without_account,
)
from apps.articles.models import ArticleAccount
from apps.data_flux.models import Trace
from conftest import patched_attrs

pytestmark = pytest.mark.django_db

ARTICLE_UUID = "6fa459ea-ee8a-3ca4-894e-db77e160355e"


def _line(article=ARTICLE_UUID, center="ACF", vat="001", purchase="607000", sale="707000"):
    """Ligne au format de l'écran articles sans comptes : 13 colonnes, comptes en 11 et 12"""
    return [
        article,
        center,
        "FOUR001",
        "Fournisseur",
        "ART-1",
        "Libellé",
        "OPT",
        "Marchandises",
        "",
        vat,
        "FRA",
        purchase,
        sale,
    ]


def _write_xlsx(path: Path, data_rows):
    """Classeur au format de l'export : 1 entête (consommée par pandas) + 3 lignes de titres

    (texte dans toutes les colonnes, sinon pandas convertit les comptes en float) + données
    """
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.append([f"col{i}" for i in range(13)])

    for _ in range(3):
        sheet.append(["titre"] * 13)

    for row in data_rows:
        sheet.append(list(row))

    workbook.save(path)
    return path


def _write_csv(path: Path, data_rows):
    with path.open("w", encoding="utf8", newline="") as file:
        writer = csv.writer(file, delimiter=";", quotechar='"', quoting=csv.QUOTE_ALL)

        for _ in range(3):
            writer.writerow(["ignorée"] + [""] * 12)

        writer.writerows(data_rows)

    return path


def _read_csv(path):
    with Path(path).open("r", encoding="utf8", newline="") as file:
        return list(csv.reader(file, delimiter=";", quotechar='"'))


@pytest.fixture
def comptes_sage(make_account):
    """Comptes du plan FRA utilisés dans les fichiers"""
    make_account("FRA", "607000")
    make_account("FRA", "707000")
    make_account("FRA", "601000")


# INSERT / UPSERT ==================================================================================


def test_insert_articles_without_account(fake_make_insert):
    """Trace nominative et make_insert en mode do_nothing (les comptes existants ne bougent pas)"""
    calls, _ = fake_make_insert

    trace, to_print = insert_articles_without_account(Path("/tmp/comptes.csv"))

    assert trace.trace_name == "Mise à jour Comptes manquant pour les articles"
    assert trace.application_name == "import_articles_without_account"
    assert trace.flow_name == "Articles_without_account"
    assert to_print == "Import : Articles_without_account"
    assert calls[0]["model"] is ArticleAccount
    assert calls[0]["validator"] is ArticleAccountSageSchema
    assert calls[0]["insert_mode"] == "do_nothing"
    assert set(calls[0]["params"]["add_fields_dict"]) == {"created_at", "modified_at"}


def test_upsert_articles_accounts(fake_make_insert):
    """Trace nominative et make_insert en mode upsert"""
    calls, _ = fake_make_insert

    trace, to_print = upsert_articles_accounts(Path("/tmp/comptes.csv"))

    assert trace.trace_name == "Mise à jour des Comptes des articles"
    assert trace.flow_name == "Update_articles_accounts"
    assert to_print == "Import : Update_articles_accounts"
    assert calls[0]["insert_mode"] == "upsert"


# VALIDATION DES COMPTES ===========================================================================


@pytest.mark.usefixtures("comptes_sage")
def test_accounts_validation(make_account):
    """Vrai si tous les comptes existent dans le plan FRA, faux sinon"""
    make_account("BEL", "999999")

    assert accounts_validation({"607000", "707000"}) == (2,)
    assert accounts_validation({"607000", "999999"}) is None
    assert accounts_validation({"000000"}) is None


# EXCEL / CSV -> CSV D'IMPORT ======================================================================


@pytest.mark.usefixtures("comptes_sage")
def test_file_for_insert_excel_to_csv_xlsx(tmp_path):
    """Chaque ligne est doublée pour la centrale GAF, le csv intermédiaire supprimé"""
    excel = _write_xlsx(tmp_path / "comptes.xlsx", [_line()])

    error, result = file_for_insert_excel_to_csv(excel)

    assert error is False
    assert Path(result) == tmp_path / "new_comptes.csv"
    assert _read_csv(result) == [
        [ARTICLE_UUID, "ACF", "001", "607000", "707000"],
        [ARTICLE_UUID, "GAF", "001", "607000", "707000"],
    ]
    assert sorted(p.name for p in tmp_path.iterdir()) == ["comptes.xlsx", "new_comptes.csv"]


@pytest.mark.usefixtures("comptes_sage")
def test_file_for_insert_excel_to_csv_csv(tmp_path):
    """Un fichier csv est copié puis traité de la même façon"""
    source = _write_csv(tmp_path / "comptes.csv", [_line(), _line(vat="002", purchase="601000")])

    error, result = file_for_insert_excel_to_csv(source)

    assert error is False
    assert len(_read_csv(result)) == 4
    assert not (tmp_path / "copy_comptes.csv").exists()


@pytest.mark.usefixtures("comptes_sage")
def test_file_for_insert_excel_to_csv_update_mode(tmp_path):
    """En update : les lignes GAF du fichier sont ignorées et les clés dédoublonnées"""
    source = _write_csv(
        tmp_path / "comptes.csv",
        [
            _line(purchase="601000"),
            _line(center="GAF", purchase="999999"),
            _line(purchase="607000"),
        ],
    )

    error, result = file_for_insert_excel_to_csv(source, update_mode=True)

    assert error is False
    assert _read_csv(result) == [
        [ARTICLE_UUID, "ACF", "001", "607000", "707000"],
        [ARTICLE_UUID, "GAF", "001", "607000", "707000"],
    ]


@pytest.mark.usefixtures("comptes_sage")
def test_file_for_insert_excel_to_csv_informations_manquantes(tmp_path, caplog):
    """Une colonne obligatoire vide arrête la lecture : erreur explicite"""
    source = _write_csv(tmp_path / "comptes.csv", [_line(sale="")])

    error, message = file_for_insert_excel_to_csv(source)

    assert error is True
    assert message == "Il manque des informations obligatoires dans le fichier"
    assert "informations obligatoires" in caplog.text
    assert not (tmp_path / "new_comptes.csv").exists()


@pytest.mark.usefixtures("comptes_sage")
def test_file_for_insert_excel_to_csv_compte_inconnu(tmp_path):
    """Un compte absent du plan FRA est refusé"""
    source = _write_csv(tmp_path / "comptes.csv", [_line(purchase="000000")])

    error, message = file_for_insert_excel_to_csv(source)

    assert error is True
    assert "n'existent pas dans SAGE" in message


def test_file_for_insert_excel_to_csv_format_non_supporte(tmp_path, monkeypatch, caplog):
    """XLRDError : message de conversion"""

    class _Broken:
        def __init__(self, **_kwargs): ...

        @staticmethod
        def make_csv():
            raise XLRDError("format")

    with patched_attrs(monkeypatch, articles_without_account, ExcelToCsv=_Broken):
        error, message = file_for_insert_excel_to_csv(tmp_path / "comptes.xlsx")

    assert error is True
    assert message == "Erreur de conversion en csv, la version du fichier excel n'est pas supportée"
    assert "Erreur de conversion" in caplog.text


def test_delete_mac_files(tmp_path):
    """Les fichiers ._* de macOS sont supprimés, les autres conservés"""
    (tmp_path / "._comptes.xlsx").write_bytes(b"mac")
    (tmp_path / "comptes.xlsx").write_bytes(b"ok")
    (tmp_path / "._dossier").mkdir()

    delete_mac_files(tmp_path)

    assert sorted(p.name for p in tmp_path.iterdir()) == ["._dossier", "comptes.xlsx"]


# IMPORTS COMPLETS =================================================================================


@pytest.mark.parametrize(
    ("function", "directory", "backup", "error_label", "flow"),
    [
        (
            import_articles_without_account,
            "without_account",
            "without_account_backup",
            "import",
            "Articles_without_account",
        ),
        (
            update_articles_accounts,
            "update_accounts",
            "update_accounts_backup",
            "update",
            "Update_articles_accounts",
        ),
    ],
)
@pytest.mark.usefixtures("comptes_sage")
def test_import_complet(
    articles_dirs, fake_make_insert, function, directory, backup, error_label, flow
):
    """Fichier valide intégré, fichier en erreur signalé, fichiers parasites supprimés, backup"""
    calls, _ = fake_make_insert
    processing = getattr(articles_dirs, directory)
    _write_xlsx(processing / "bon.xlsx", [_line()])
    _write_csv(processing / "mauvais.csv", [_line(purchase="000000")])
    (processing / "._bon.xlsx").write_bytes(b"mac")
    (processing / "notes.txt").write_text("à ignorer", encoding="utf8")
    (processing / "sous.dossier").mkdir()

    errors, oks = function()

    assert oks == "\nLe fichier bon.xlsx a bien été intégré "
    assert errors.startswith(
        f"\nIl y a eu une erreur d'{error_label} pour le fichier mauvais.csv: "
    )
    assert calls[0]["flow_name"] == flow
    assert calls[0]["source"] == processing / "new_bon.csv"
    assert sorted(p.name for p in processing.iterdir()) == ["sous.dossier"]
    assert sorted(p.name for p in getattr(articles_dirs, backup).iterdir()) == [
        "bon.xlsx",
        "mauvais.csv",
    ]


@pytest.mark.parametrize(
    ("function", "directory", "error_label"),
    [
        (import_articles_without_account, "without_account", "import"),
        (update_articles_accounts, "update_accounts", "update"),
    ],
)
@pytest.mark.usefixtures("comptes_sage")
def test_import_trace_en_erreur_et_backup_existant(
    articles_dirs, fake_make_insert, function, directory, error_label
):
    """Trace en erreur après insertion : message vers la trace ; backup déjà présent : fichier supprimé"""
    _, state = fake_make_insert
    state["errors"] = True
    processing = getattr(articles_dirs, directory)
    backup_dir = getattr(articles_dirs, f"{directory}_backup")
    _write_xlsx(processing / "bon.xlsx", [_line()])
    (backup_dir / "bon.xlsx").write_bytes(b"ancien")

    errors, oks = function()

    assert oks == ""
    assert (
        f"Il y a eu une erreur d'{error_label} pour le fichier bon.xlsx: Consulté la Trace N° {Trace.objects.get().uuid_identification}"
        in errors
    )
    assert (backup_dir / "bon.xlsx").read_bytes() == b"ancien"
    assert not (processing / "bon.xlsx").exists()


@pytest.mark.usefixtures("articles_dirs", "fake_make_insert")
def test_imports_sans_fichier():
    """Répertoires vides"""
    assert import_articles_without_account() == ("", "")
    assert update_articles_accounts() == ("", "")
