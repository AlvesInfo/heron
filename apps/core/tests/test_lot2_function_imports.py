# pylint: disable=E0401,W0621,W0212
"""
FR : Tests de l'itérateur de fichiers à insérer et de la validation par formulaire
     (apps/core/functions/function_imports.py)
EN : Tests for file iterator and model form insertion

created at: 2026-10-11
created by: Paulo ALVES
"""
import csv
import io
import uuid
from pathlib import Path

import pytest
import xlsxwriter
from django import forms

from apps.book.models import StatFamillyAxes
from apps.core.functions import function_imports
from apps.core.functions.function_imports import (
    CsvFileToStringIoError,
    ExcelToCsvError,
    ExcelToCsvFileError,
    GetAddDictError,
    IterFileToInsert,
    IterFileToInsertError,
    ModelFormInsertion,
    ValidationError,
    excel_file_to_csv_string_io,
    file_to_csv_string_io,
)
from conftest import patched_attrs

ROWS = [["code", "nom", "coefficient"], ["ACF", "Acuitis", "1.5"], ["GAF", "GrandAudition", "2"]]


def _csv(path, rows=ROWS, blank_line=False):
    with Path(path).open("w", encoding="utf8", newline="") as file:
        writer = csv.writer(file, delimiter=";", quotechar='"', lineterminator="\n")

        for index, row in enumerate(rows):
            writer.writerow(row)

            if blank_line and index == 1:
                file.write("\n")

    return Path(path)


def _xlsx(path, rows=ROWS):
    workbook = xlsxwriter.Workbook(str(path))
    worksheet = workbook.add_worksheet("Feuil1")

    for row_index, row in enumerate(rows):
        worksheet.write_row(row_index, 0, row)

    workbook.close()
    return Path(path)


# CONVERSIONS VERS StringIO ========================================================================


def test_excel_file_to_csv_string_io(tmp_path):
    """Classeur converti en csv quoté dans le StringIO, avec ou sans entête"""
    source = _xlsx(tmp_path / "classeur.xlsx")
    buffer = io.StringIO()

    assert excel_file_to_csv_string_io(source, buffer) is True
    assert buffer.read() == '"code";"nom";"coefficient"\n"ACF";"Acuitis";"1.5"\n"GAF";"GrandAudition";"2.0"\n'

    buffer = io.StringIO()
    excel_file_to_csv_string_io(source, buffer, header=False)
    assert buffer.read().startswith('"ACF";"Acuitis"')


def test_excel_file_to_csv_string_io_format_indetermine(tmp_path, monkeypatch):
    def _boom(*_args, **_kwargs):
        raise ValueError("format inconnu")

    buffer = io.StringIO()

    with patched_attrs(monkeypatch, function_imports.pd, read_excel=_boom), pytest.raises(ExcelToCsvFileError, match="'faux.xlsx'"):
        excel_file_to_csv_string_io(tmp_path / "faux.xlsx", buffer)


def test_file_to_csv_string_io(tmp_path):
    source = _csv(tmp_path / "fichier.csv")
    buffer = io.StringIO()

    file_to_csv_string_io(source, buffer)

    assert buffer.read() == "code;nom;coefficient\nACF;Acuitis;1.5\nGAF;GrandAudition;2\n"


def test_file_to_csv_string_io_fichier_absent(tmp_path):
    buffer = io.StringIO()

    with pytest.raises(CsvFileToStringIoError, match="'absent.csv'"):
        file_to_csv_string_io(tmp_path / "absent.csv", buffer)


# ITÉRATEUR DE FICHIER =============================================================================


def test_iter_colonnes_dans_l_ordre_du_fichier(tmp_path):
    """Colonnes à None : positions dans l'ordre, lignes rendues en dictionnaires"""
    source = _csv(tmp_path / "fichier.csv")

    with IterFileToInsert(source, {"code": None, "name": None, "coef": None}, first_line=2) as file_iter:
        assert file_iter.get_header() == [0, 1, 2]
        assert list(file_iter.chunk_dict()) == [
            {"code": "ACF", "name": "Acuitis", "coef": "1.5"},
            {"code": "GAF", "name": "GrandAudition", "coef": "2"},
        ]

    assert file_iter.csv_io.closed
    file_iter.close_buffer()


def test_iter_colonnes_nommees_et_par_index(tmp_path):
    """Colonnes par nom de l'entête (ligne 1 lue comme entête) ou par index"""
    source = _csv(tmp_path / "fichier.csv")

    with IterFileToInsert(source, {"name": "nom", "code": "code"}, first_line=1) as file_iter:
        assert file_iter.get_header() == [1, 0]
        assert list(file_iter.chunk_dict()) == [{"name": "Acuitis", "code": "ACF"}, {"name": "GrandAudition", "code": "GAF"}]

    with IterFileToInsert(source, {"coef": 2, "code": 0}, first_line=2) as file_iter:
        assert file_iter.get_header() == [2, 0]
        assert next(file_iter.chunk_dict()) == {"coef": "1.5", "code": "ACF"}


def test_iter_premiere_ligne_au_dela_du_fichier(tmp_path):
    """Une première ligne plus loin que la fin du fichier ne renvoie aucune ligne"""
    source = _csv(tmp_path / "fichier.csv")

    with IterFileToInsert(source, {"code": 0}, first_line=10) as file_iter:
        assert file_iter.first_line == len(source.read_text(encoding="utf8"))
        assert file_iter.csv_io.read() == ""


def test_iter_depuis_un_classeur(tmp_path):
    source = _xlsx(tmp_path / "classeur.xlsx")

    with IterFileToInsert(source, {"code": None, "name": None}, first_line=2) as file_iter:
        assert next(file_iter.chunk_dict()) == {"code": "ACF", "name": "Acuitis"}


def test_iter_classeur_illisible(tmp_path):
    (tmp_path / "faux.xlsx").write_text("pas un classeur", encoding="utf8")

    with pytest.raises(ExcelToCsvError, match="'faux.xlsx'"):
        IterFileToInsert(tmp_path / "faux.xlsx", {"code": None})


def test_iter_pas_assez_de_colonnes(tmp_path):
    source = _csv(tmp_path / "fichier.csv", [["a"], ["1"]])

    with IterFileToInsert(source, {"x": None, "y": None}, first_line=2) as file_iter, pytest.raises(
        IterFileToInsertError, match="le fichier comporte 1 colonne, il est exigé au moins 2 colonnes"
    ):
        file_iter.get_header()


def test_iter_colonnes_nommees_absentes(tmp_path):
    source = _csv(tmp_path / "fichier.csv")

    with IterFileToInsert(source, {"code": "code", "x": "absente"}, first_line=1) as file_iter, pytest.raises(
        IterFileToInsertError, match='ne contient pas les colonnes demandées suivantes : "absente"'
    ):
        file_iter.get_header()


def test_iter_champs_ajoutes(tmp_path):
    """Champs ajoutés à la volée : valeur fixe ou fonction appelée pour chaque ligne"""
    source = _csv(tmp_path / "fichier.csv")
    params = {"add_fields_dict": {"uuid_identification": (uuid.uuid4, {}), "origine": "import"}}

    with IterFileToInsert(source, {"code": None}, first_line=2, params_dict=params) as file_iter:
        rows = list(file_iter.chunk_dict())
        values = file_iter.get_add_values

    assert [row["code"] for row in rows] == ["ACF", "GAF"]
    assert all(row["origine"] == "import" for row in rows)
    assert isinstance(rows[0]["uuid_identification"], uuid.UUID)
    assert rows[0]["uuid_identification"] != rows[1]["uuid_identification"]
    assert isinstance(values[0], uuid.UUID)
    assert values[1] == "import"


def test_iter_champ_ajoute_mal_declare(tmp_path):
    """Un tuple sans dictionnaire d'arguments est refusé"""
    source = _csv(tmp_path / "fichier.csv")

    with IterFileToInsert(source, {"code": None}, first_line=2, params_dict={"add_fields_dict": {"x": (uuid.uuid4,)}}) as file_iter, pytest.raises(
        GetAddDictError
    ):
        _ = file_iter.get_add_dict


def test_iter_lignes_exclues_et_vides(tmp_path):
    """Lignes vides sautées par défaut, lignes exclues sur le contenu d'une colonne"""
    source = _csv(tmp_path / "fichier.csv", blank_line=True)
    params = {"exclude_rows_dict": {1: "gaf"}}

    with IterFileToInsert(source, {"code": None, "name": None}, first_line=2, params_dict=params) as file_iter:
        assert list(file_iter.chunk_dict()) == [{"code": "ACF", "name": "Acuitis"}]

    with IterFileToInsert(_csv(tmp_path / "plein.csv"), {"code": None}, first_line=2) as file_iter:
        assert [row["code"] for row in file_iter.chunk_dict(all_lines=True)] == ["ACF", "GAF"]


def test_iter_write_io(tmp_path):
    """Écriture des colonnes retenues dans un StringIO, avec ou sans champs ajoutés"""
    source = _csv(tmp_path / "fichier.csv", blank_line=True)
    buffer = io.StringIO()

    with IterFileToInsert(source, {"name": "nom", "code": "code"}, first_line=1) as file_iter:
        file_iter.write_io(buffer)

    assert buffer.getvalue() == '"Acuitis";"ACF"\r\n"GrandAudition";"GAF"\r\n'

    buffer = io.StringIO()
    params = {"add_fields_dict": {"origine": "import"}, "exclude_rows_dict": {1: "ACF"}}

    with IterFileToInsert(_csv(tmp_path / "plein.csv"), {"code": None}, first_line=2, params_dict=params) as file_iter:
        file_iter.write_io(buffer, all_lines=True)

    assert buffer.getvalue() == '"GAF";"import"\r\n'


# VALIDATION PAR FORMULAIRE ========================================================================


class StatForm(forms.ModelForm):
    """Formulaire de validation des familles statistiques"""

    class Meta:
        model = StatFamillyAxes
        fields = ("name", "description", "regex_bool")


STAT_ROWS = [["name", "description", "regex_bool"], ["ACUITIS", "Acuitis", "True"], ["BBGR", "Bbgr", "False"]]
COLUMNS = {"name": None, "description": None, "regex_bool": None}


@pytest.mark.django_db
def test_model_form_insertion_cree_puis_met_a_jour(tmp_path):
    """Avec les champs uniques, une famille existante est mise à jour, les autres créées"""
    existing = StatFamillyAxes.objects.create(name="ACUITIS", description="Ancienne", regex_bool=False)
    source = _csv(tmp_path / "stats.csv", STAT_ROWS)

    with ModelFormInsertion(StatForm, source, COLUMNS, first_line=2, uniques=("name",)) as insertion:
        insertion.validate()

    existing.refresh_from_db()
    assert insertion.errors == []
    assert (existing.description, existing.regex_bool) == ("Acuitis", True)
    assert StatFamillyAxes.objects.get(name="BBGR").description == "Bbgr"
    assert StatFamillyAxes.objects.count() == 2


@pytest.mark.django_db
def test_model_form_insertion_sans_unique_ni_champ_unique_present(tmp_path):
    """Sans champ unique, ou si un champ unique manque dans le fichier, chaque ligne est créée"""
    _csv(tmp_path / "stats.csv", STAT_ROWS)

    ModelFormInsertion(StatForm, tmp_path / "stats.csv", COLUMNS, first_line=2).validate()
    assert StatFamillyAxes.objects.count() == 2

    with ModelFormInsertion(StatForm, tmp_path / "stats.csv", COLUMNS, first_line=2, uniques=("name", "absent")) as insertion:
        insertion.validate()

    assert len(insertion.errors) == 2
    assert "name" in str(insertion.errors[0])


@pytest.mark.django_db
def test_model_form_insertion_erreurs_de_validation(tmp_path):
    """Une ligne invalide est consignée avec son numéro et son champ en erreur"""
    source = _csv(tmp_path / "stats.csv", [["name"], [""], ["BBGR"]])

    with ModelFormInsertion(StatForm, source, {"name": None}, first_line=2) as insertion:
        insertion.validate()

    assert insertion.errors == [{"ligne n°     1 : ": [{"name": "Ce champ est obligatoire."}]}]
    assert StatFamillyAxes.objects.filter(name="BBGR").exists()


@pytest.mark.django_db
def test_model_form_insertion_erreur_inattendue(tmp_path, monkeypatch):
    source = _csv(tmp_path / "stats.csv", STAT_ROWS)

    def _boom():
        raise RuntimeError("fichier corrompu")

    with ModelFormInsertion(StatForm, source, COLUMNS, first_line=2) as insertion, patched_attrs(
        monkeypatch, insertion, chunk_dict=_boom
    ), pytest.raises(ValidationError, match="une erreur c'est produite pendant la validation"):
        insertion.validate()


def test_model_form_insertion_transformations_de_ligne(tmp_path):
    """Transformation en place par liste de fonctions (positions) ou dictionnaire (clés)"""
    source = _csv(tmp_path / "stats.csv", STAT_ROWS)

    with ModelFormInsertion(StatForm, source, COLUMNS, first_line=2, map_line=[str.lower, str.upper]) as insertion:
        line = ["ACF", "acuitis", "x"]
        insertion.set_transform_line(line)

    assert insertion.map_line_dict is False
    assert line == ["acf", "ACUITIS", "x"]

    with ModelFormInsertion(StatForm, source, COLUMNS, first_line=2, map_line={"name": str.strip}) as insertion:
        line = {"name": " ACF "}
        insertion.set_transform_line(line)

    assert insertion.map_line_dict is True
    assert line == {"name": "ACF"}
