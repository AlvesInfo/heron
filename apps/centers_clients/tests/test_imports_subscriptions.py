# pylint: disable=E0401,W0621,R0913
"""
FR : Tests de l'import des abonnements par maison (imports/import_subcriptions.py)
EN : Tests for subscriptions import

created at: 2026-10-10
created by: Paulo ALVES
"""
import csv
from pathlib import Path

import openpyxl
import pytest
from xlrd.biffh import XLRDError

from apps.centers_clients.forms.forms_djantic.forms_maison_subscription import MaisonSubcriptionSchema
from apps.centers_clients.imports import import_subcriptions
from apps.centers_clients.imports.import_subcriptions import (
    file_for_insert_excel_to_csv,
    get_fields_values,
    import_abonnements_par_maisons,
    insert_maison_subscription,
)
from apps.centers_clients.models import MaisonSubcription
from apps.data_flux.models import Trace
from conftest import patched_attrs

pytestmark = pytest.mark.django_db


@pytest.fixture
def fake_make_insert(monkeypatch):
    """Doublure de data_flux.make_insert : enregistre les appels, peut marquer la trace en erreur"""
    calls = []
    state = {"errors": False}

    def _recorder(model, flow_name, source, trace, validator, params_dict_loader):
        calls.append({"model": model, "flow_name": flow_name, "source": source, "trace": trace, "validator": validator, "params": params_dict_loader})
        trace.errors = state["errors"]
        trace.save()
        return f"Import : {flow_name}"

    monkeypatch.setattr(import_subcriptions, "make_insert", _recorder)
    return calls, state


@pytest.fixture
def referentiel(make_maison, make_article, make_unit, make_invoice_function, make_signboard, make_subscription):
    """Maison AF0001, article ABO-1 déjà abonné, unité U, fonction ABONNEMENT, enseigne ACF"""
    maison = make_maison("AF0001")
    article = make_article("ABO-1")
    unit = make_unit(1, "U")
    function = make_invoice_function("ABONNEMENT")
    signboard = make_signboard("ACF")
    make_subscription(maison=maison, article=article, unit_weight=unit, function=function, for_signboard=signboard)
    return {"maison": maison, "article": article, "unit": unit, "function": function, "signboard": signboard}


def _write_xlsx(path: Path, data_rows):
    """Classeur au format de l'écran des abonnements : 1 entête pandas + 3 lignes ignorées + données"""
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.append(["CODE MAISON", "MAISON", "ARTICLE", "QTY", "UNITE", "PRIX NET", "FONCTION", "ENSEIGNE"])
    sheet.append(["ignorée 1"] + [""] * 7)
    sheet.append(["ignorée 2"] + [""] * 7)
    sheet.append(["ignorée 3"] + [""] * 7)

    for row in data_rows:
        sheet.append(list(row))

    workbook.save(path)
    return path


def _read_csv(path):
    with Path(path).open("r", encoding="utf-8", newline="") as file:
        return list(csv.reader(file, delimiter=";", quotechar='"'))


# INSERT ===========================================================================================


def test_insert_maison_subscription_cree_la_trace(fake_make_insert):
    """Sans trace fournie, une trace nominative est créée et make_insert appelé"""
    calls, _ = fake_make_insert

    trace, to_print = insert_maison_subscription(Path("/tmp/abonnements.csv"))

    assert isinstance(trace, Trace)
    assert trace.trace_name == "Mise à jour abonnements par maisons"
    assert trace.application_name == "import_abonnements_par_maisons"
    assert trace.flow_name == "Abonnements_par_maisons"
    assert trace.comment == "import abonnements.csv des abonnements par maisons"
    assert to_print == "Import : Abonnements_par_maisons"
    assert calls[0]["model"] is MaisonSubcription
    assert calls[0]["validator"] is MaisonSubcriptionSchema
    assert calls[0]["params"]["trace"] is trace
    assert set(calls[0]["params"]["add_fields_dict"]) == {"created_at", "modified_at"}


@pytest.mark.usefixtures('fake_make_insert')
def test_insert_maison_subscription_reutilise_la_trace(make_trace):
    """Une trace existante est réutilisée"""
    existing = make_trace()

    trace, _ = insert_maison_subscription(Path("/tmp/abonnements.csv"), existing)

    assert trace is existing
    assert Trace.objects.count() == 1


# RÉFÉRENTIEL ======================================================================================


def test_get_fields_values(referentiel):
    """Dictionnaires de correspondance libellé fichier -> identifiant base"""
    articles, maisons, signboards, functions, units = get_fields_values()

    assert articles == {"ABO-1": str(referentiel["article"].uuid_identification)}
    assert maisons == {"AF0001": "AF0001"}
    assert signboards == {"ACF": "ACF"}
    assert functions == {"ABONNEMENT": "ABONNEMENT"}
    assert units == {"U": str(referentiel["unit"].pk)}


@pytest.mark.usefixtures('referentiel')
def test_get_fields_values_article_sans_abonnement_ignore(make_article):
    """Seuls les articles déjà abonnés sont proposés"""
    make_article("AUTRE")

    assert "AUTRE" not in get_fields_values()[0]


# EXCEL -> CSV =====================================================================================


def test_file_for_insert_excel_to_csv_valide(referentiel, tmp_path):
    """Les libellés sont traduits en identifiants, le prix arrondi, le csv intermédiaire supprimé"""
    excel = _write_xlsx(tmp_path / "abonnements.xlsx", [("AF0001", "Maison", "ABO-1", 2, "U", 99.899, "ABONNEMENT", "ACF")])

    error, result = file_for_insert_excel_to_csv(excel)

    assert error is False
    assert Path(result) == tmp_path / "abonnements.csv"
    # pandas lit les colonnes numériques en float (lignes ignorées vides) : "2.0", prix arrondi à 2 décimales
    assert _read_csv(result) == [["AF0001", str(referentiel["article"].uuid_identification), "2.0", str(referentiel["unit"].pk), "99.90", "ABONNEMENT", "ACF"]]
    assert sorted(path.name for path in tmp_path.iterdir()) == ["abonnements.csv", "abonnements.xlsx"]


@pytest.mark.usefixtures('referentiel')
def test_file_for_insert_excel_to_csv_doublon(tmp_path):
    """Deux lignes sur le même quadruplet : erreur de doublon et pas de csv produit"""
    row = ("AF0001", "Maison", "ABO-1", 1, "U", 10, "ABONNEMENT", "ACF")
    excel = _write_xlsx(tmp_path / "abonnements.xlsx", [row, row])

    error, message = file_for_insert_excel_to_csv(excel)

    assert error is True
    # numérotation sur le csv intermédiaire (entête consommée par pandas, 3 lignes ignorées) : 2e ligne de données = 6
    assert "la ligne 6, du fichier" in message
    assert "_abonnements.csv, est en doublon : AF0001 - ABO-1" in message
    assert not (tmp_path / "abonnements.csv").exists()


@pytest.mark.usefixtures('referentiel')
def test_file_for_insert_excel_to_csv_valeur_inconnue(tmp_path):
    """Un article inconnu donne None : erreur explicite avec les valeurs traduites"""
    excel = _write_xlsx(tmp_path / "abonnements.xlsx", [("AF0001", "Maison", "INCONNU", 1, "U", 10, "ABONNEMENT", "ACF")])

    error, message = file_for_insert_excel_to_csv(excel)

    assert error is True
    assert "contient des erreurs : AF0001 - None - 1" in message


@pytest.mark.usefixtures('referentiel')
def test_file_for_insert_excel_to_csv_format_non_supporte(tmp_path, monkeypatch, caplog):
    """Un classeur non lisible (XLRDError) est signalé"""

    class _Broken:
        def __init__(self, **_kwargs): ...

        @staticmethod
        def make_csv():
            raise XLRDError("format inconnu")

    with patched_attrs(monkeypatch, import_subcriptions, ExcelToCsv=_Broken):
        error, message = file_for_insert_excel_to_csv(tmp_path / "abonnements.xlsx")

    assert error is True
    assert message == "Erreur de conversion en csv, la version du fichier excel n'est pas supportée"
    assert "Erreur de conversion" in caplog.text


# IMPORT COMPLET ===================================================================================


@pytest.mark.usefixtures('subscription_dirs', 'fake_make_insert')
def test_import_sans_fichier():
    """Répertoire vide : aucun message"""
    assert import_abonnements_par_maisons() == ("", "")


@pytest.mark.usefixtures('referentiel')
def test_import_fichier_valide(subscription_dirs, fake_make_insert):
    """Fichier intégré : message ok, csv supprimé, excel déplacé en backup"""
    calls, _ = fake_make_insert
    _write_xlsx(subscription_dirs.processing / "abos.xlsx", [("AF0001", "M", "ABO-1", 1, "U", 10, "ABONNEMENT", "ACF")])

    errors, oks = import_abonnements_par_maisons()

    assert errors == ""
    assert oks == "\nLe fichier abos.xlsx a bien été intégré "
    assert calls[0]["source"] == subscription_dirs.processing / "abos.csv"
    assert list(subscription_dirs.processing.iterdir()) == []
    assert (subscription_dirs.backup / "abos.xlsx").is_file()
    assert Trace.objects.get().errors is False


@pytest.mark.usefixtures('referentiel')
def test_import_fichier_en_erreur_de_conversion(subscription_dirs, fake_make_insert):
    """Fichier invalide : trace en erreur avec le détail, message d'erreur, excel sauvegardé"""
    calls, _ = fake_make_insert
    _write_xlsx(subscription_dirs.processing / "abos.xlsx", [("AF0001", "M", "INCONNU", 1, "U", 10, "ABONNEMENT", "ACF")])

    errors, oks = import_abonnements_par_maisons()

    trace = Trace.objects.get()
    assert oks == ""
    assert errors.startswith("\nIl y a eu une erreur d'import pour le fichier abos.xlsx: ")
    assert trace.errors is True
    assert "contient des erreurs" in trace.comment
    assert trace.final_at is not None
    assert calls == []
    assert (subscription_dirs.backup / "abos.xlsx").is_file()


@pytest.mark.usefixtures('referentiel')
def test_import_trace_en_erreur_apres_insertion(subscription_dirs, fake_make_insert):
    """Si l'insertion marque la trace en erreur, le message renvoie vers la trace"""
    _, state = fake_make_insert
    state["errors"] = True
    _write_xlsx(subscription_dirs.processing / "abos.xlsx", [("AF0001", "M", "ABO-1", 1, "U", 10, "ABONNEMENT", "ACF")])

    errors, oks = import_abonnements_par_maisons()

    assert oks == ""
    assert f"Consulté la Trace N° {Trace.objects.get().uuid_identification}" in errors


@pytest.mark.usefixtures('referentiel', 'fake_make_insert')
def test_import_backup_deja_present(subscription_dirs):
    """Si le backup existe déjà, l'excel est simplement supprimé"""
    (subscription_dirs.backup / "abos.xlsx").write_bytes(b"ancien")
    _write_xlsx(subscription_dirs.processing / "abos.xlsx", [("AF0001", "M", "ABO-1", 1, "U", 10, "ABONNEMENT", "ACF")])

    import_abonnements_par_maisons()

    assert (subscription_dirs.backup / "abos.xlsx").read_bytes() == b"ancien"
    assert not (subscription_dirs.processing / "abos.xlsx").exists()
