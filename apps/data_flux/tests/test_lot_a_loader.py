# pylint: disable=E0401,W0621
"""
FR : Tests du chargeur de fichiers (apps/data_flux/loader.py : TemplateDataLoader et FileLoader)
EN : Tests for the file loader

created at: 2026-10-11
created by: Paulo ALVES
"""
import csv
import io
import uuid

import pytest
from openpyxl import Workbook

from apps.data_flux import loader as loader_module
from apps.data_flux.exceptions import (
    ExcelToCsvError,
    ExcelToCsvFileError,
    FileToCsvError,
    GetAddDictError,
    IterFileToInsertError,
)
from apps.data_flux.loader import FileLoader, TemplateDataLoader
from apps.data_flux.models import Error, Line
from conftest import patched_attrs

pytestmark = pytest.mark.django_db

HEADER = ["Code", "Nom ", "Coef.\t", "N° Rang"]
ROWS = [["ACF", "Acuitis", "1.5", "1"], ["GAF", "GrandAudition", "2", "2"]]


def _csv(path, rows, **kwargs):
    with path.open("w", encoding="utf8", newline="") as file:
        csv.writer(file, delimiter=";", quotechar='"', lineterminator="\n", **kwargs).writerows(rows)

    return path


@pytest.fixture
def source(tmp_path):
    """Fichier csv (utf8) avec une ligne d'entête puis deux lignes de données"""
    return _csv(tmp_path / "centrales.csv", [HEADER, *ROWS])


UTF8 = {"encoding": "utf8"}


# TEMPLATE =========================================================================================


def test_template_methodes_a_implementer(make_trace):
    """Le template porte la trace et impose open / read / read_list / read_dict / close"""
    trace = make_trace()
    template = TemplateDataLoader("source", {"a": None}, params_dict={"trace": trace})

    assert template.trace is trace
    assert TemplateDataLoader("source", {"a": None}).trace is None

    for method, args in (("open", ()), ("read", ()), ("read_list", ()), ("read_dict", ()), ("close", ())):
        method_to_call = getattr(template, method)

        with pytest.raises(NotImplementedError):
            method_to_call(*args)


def test_template_trace_add_line_error(make_trace):
    """Une ligne de trace et son erreur sont créées, avec la désignation par défaut du type"""
    trace = make_trace()
    template = TemplateDataLoader("source", {"a": None}, params_dict={"trace": trace})

    template.trace_add_line_error("Errors", 3, error_dict={"attr_name": "code", "message": "mauvais"})
    template.trace_add_line_error(num_line=4, designation="ligne 4")
    template.trace_add_line_error("Create")

    lines = {line.num_line: line for line in Line.objects.filter(trace=trace)}
    assert lines[3].designation == "Cette ligne à généré une erreur"
    assert Error.objects.get(line=lines[3]).message == "mauvais"
    assert (lines[4].insertion_type, lines[4].designation) == ("Unknown", "ligne 4")
    assert lines[None].designation == "cette ligne à bien été créée"
    assert Error.objects.count() == 3


def test_template_context_manager_ferme(make_trace):
    """__exit__ appelle close : le template brut lève NotImplementedError"""
    with pytest.raises(NotImplementedError), TemplateDataLoader("source", {"a": None}, params_dict={}):
        pass


# OUVERTURE ========================================================================================


def test_fileloader_csv_positions_par_ordre(source):
    """Colonnes à None : prises dans l'ordre du fichier, entête sautée par first_line"""
    with FileLoader(source, {"code": None, "name": None}, first_line=2, params_dict=UTF8) as file_loader:
        file_loader.open()
        assert file_loader.get_header() == [0, 1]
        assert list(file_loader.read_dict()) == [{"code": "ACF", "name": "Acuitis"}, {"code": "GAF", "name": "GrandAudition"}]

    assert not hasattr(file_loader, "csv_io")


def test_fileloader_csv_positions_par_index(source):
    with FileLoader(source, {"coef": 2, "code": 0}, first_line=2, params_dict=UTF8) as file_loader:
        assert file_loader.get_header() == [2, 0]
        assert list(file_loader.read_list()) == [["1.5", "ACF"], ["2", "GAF"]]


def test_fileloader_csv_colonnes_nommees(source):
    """Entêtes nettoyées (minuscules, espaces, tabulations, degré) pour retrouver les colonnes"""
    with FileLoader(source, {"rang": "n_rang", "coef": "coef.", "name": "nom"}, first_line=1, params_dict=UTF8) as file_loader:
        assert file_loader.get_header() == [3, 2, 1]
        assert list(file_loader.read()) == ['"1";"1.5";"Acuitis"', '"2";"2";"GrandAudition"']


def test_fileloader_une_seule_colonne(source):
    """Une seule colonne demandée n'est pas découpée caractère par caractère"""
    with FileLoader(source, {"code": None}, first_line=2, params_dict=UTF8) as file_loader:
        assert list(file_loader.read_dict()) == [{"code": "ACF"}, {"code": "GAF"}]
        assert list(file_loader.read_list()) == [["ACF"], ["GAF"]]
        assert list(file_loader.read()) == ['"ACF"', '"GAF"']


def test_fileloader_excel(tmp_path):
    """Un classeur xlsx est converti en csv avant lecture"""
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["code", "nom"])
    sheet.append(["ACF", "Acuitis"])
    sheet.append(["GAF", "GrandAudition"])
    path = tmp_path / "centrales.xlsx"
    workbook.save(path)

    with FileLoader(path, {"code": "code", "name": "nom"}) as file_loader:
        assert list(file_loader.read_dict()) == [{"code": "ACF", "name": "Acuitis"}, {"code": "GAF", "name": "GrandAudition"}]


def test_fileloader_parametres_csv_et_encodage(tmp_path):
    """Séparateur, quoting et encodage du fichier passés dans params_dict"""
    path = tmp_path / "latin.csv"
    path.write_bytes("code,nom\nACF,Aç\n".encode("latin-1"))

    with FileLoader(path, {"code": None, "name": None}, first_line=2, params_dict={"delimiter": ",", "encoding": "latin-1"}) as file_loader:
        assert list(file_loader.read_dict()) == [{"code": "ACF", "name": "Aç"}]


# LECTURES =========================================================================================


def test_fileloader_lignes_vides_et_exclusions(tmp_path):
    """Lignes vides sautées sauf all_lines ; exclusion sur le contenu d'une colonne (1 = première)"""
    path = _csv(tmp_path / "f.csv", [["ACF", "Acuitis"], ["", ""], ["GAF", "GrandAudition"], ["TOT", "Total général"]])
    params = {"exclude_rows_dict": {2: "total", 5: "absente"}}

    with FileLoader(path, {"code": None, "name": None}, params_dict=params) as file_loader:
        assert [row["code"] for row in file_loader.read_dict()] == ["ACF", "GAF"]
        assert [row[0] for row in file_loader.read_list(all_lines=True)] == ["ACF", "", "GAF"]
        assert list(file_loader.read()) == ['"ACF";"Acuitis"', '"GAF";"GrandAudition"']


def test_fileloader_champs_ajoutes(source):
    """add_fields_dict : valeurs fixes et fonctions (tuple fonction, arguments), dans les trois lectures"""
    params = {**UTF8, "add_fields_dict": {"origine": "import", "ident": (uuid.uuid5, {"namespace": uuid.NAMESPACE_DNS, "name": "heron"})}}
    expected_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, "heron")

    with FileLoader(source, {"code": None}, first_line=2, params_dict=params) as file_loader:
        assert file_loader.get_add_dict == {"origine": "import", "ident": expected_uuid}
        assert file_loader.get_add_values == ["import", expected_uuid]
        assert next(iter(file_loader.read_dict())) == {"code": "ACF", "origine": "import", "ident": expected_uuid}
        assert list(file_loader.read_list())[1] == ["GAF", "import", expected_uuid]
        assert next(iter(file_loader.read())) == f'"ACF";"import";"{expected_uuid}"'


def test_fileloader_make_io_et_load(source):
    """make_io écrit le csv nettoyé ; load distribue selon la méthode demandée"""
    buffer = io.StringIO()

    with FileLoader(source, {"code": None, "name": None}, first_line=2, params_dict=UTF8) as file_loader:
        file_loader.make_io(buffer)
        assert buffer.getvalue() == '"ACF";"Acuitis"\n"GAF";"GrandAudition"\n'
        assert buffer.tell() == 0
        assert list(file_loader.load("data")) == ['"ACF";"Acuitis"', '"GAF";"GrandAudition"']
        assert list(file_loader.load("data_list")) == [["ACF", "Acuitis"], ["GAF", "GrandAudition"]]
        rows = list(file_loader.load("data_dict"))
        assert rows[0] == {"code": "ACF", "name": "Acuitis"}
        assert list(file_loader.load("inconnue")) == []

    assert file_loader.close() is None


# ERREURS ==========================================================================================


def test_fileloader_colonnes_nommees_absentes(source, make_trace):
    """Colonne demandée absente : exception et trace commentée"""
    trace = make_trace()

    with FileLoader(source, {"code": "code", "ville": "ville"}, params_dict={"trace": trace, **UTF8}) as file_loader, pytest.raises(IterFileToInsertError, match='"ville"'):
        file_loader.get_header()

    trace.refresh_from_db()
    assert trace.errors is True
    assert "ne contient pas les colonnes demandées suivantes" in trace.comment

    with FileLoader(source, {"code": "code", "ville": "ville"}, params_dict=UTF8) as file_loader, pytest.raises(IterFileToInsertError):
        file_loader.get_header()


def test_fileloader_pas_assez_de_colonnes(tmp_path, make_trace):
    trace = make_trace()
    path = _csv(tmp_path / "f.csv", [["ACF"]])

    with FileLoader(path, {"code": None, "name": None}, params_dict={"trace": trace}) as file_loader, pytest.raises(IterFileToInsertError, match="comporte 1 colonne, il est exigé au moins 2 colonnes"):
        file_loader.get_header()

    trace.refresh_from_db()
    assert trace.errors is True

    with FileLoader(path, {"code": None, "name": None}) as file_loader, pytest.raises(IterFileToInsertError):
        file_loader.get_header()


def test_fileloader_fichier_vide(tmp_path, make_trace):
    """Fichier vide : exception, trace commentée si suivie"""
    trace = make_trace()
    path = _csv(tmp_path / "vide.csv", [])

    with FileLoader(path, {"code": None}, params_dict={"trace": trace}) as file_loader, pytest.raises(IterFileToInsertError, match="est vide"):
        file_loader.get_header()

    trace.refresh_from_db()
    assert trace.comment == "Erreur sur les colonnes : le fichier vide.csv est vide"

    with FileLoader(path, {"code": None}) as file_loader, pytest.raises(IterFileToInsertError):
        file_loader.get_header()


@pytest.mark.parametrize("method", ["read", "read_list", "read_dict"])
def test_fileloader_ligne_non_conforme(tmp_path, make_trace, method):
    """Une ligne plus courte que les colonnes demandées est tracée puis l'import s'arrête"""
    trace = make_trace()
    path = _csv(tmp_path / "f.csv", [["ACF", "Acuitis", "1"], ["GAF"]])

    with FileLoader(path, {"code": 0, "coef": 2}, params_dict={"trace": trace}) as file_loader:
        rows = getattr(file_loader, method)()

        with pytest.raises(IterFileToInsertError, match="ligne non conforme"):
            list(rows)

    line = Line.objects.get(trace=trace)
    assert (line.insertion_type, line.num_line) == ("Errors", 2)
    assert Error.objects.get(line=line).data_received == "GAF"


@pytest.mark.parametrize("method", ["read", "read_list", "read_dict"])
def test_fileloader_ligne_non_conforme_sans_trace(tmp_path, method):
    path = _csv(tmp_path / "f.csv", [["ACF", "Acuitis", "1"], ["GAF"]])

    with FileLoader(path, {"code": 0, "coef": 2}) as file_loader:
        rows = getattr(file_loader, method)()

        with pytest.raises(IterFileToInsertError):
            list(rows)

    assert Line.objects.count() == 0


def test_fileloader_champ_ajoute_mal_forme(source, make_trace):
    """Un tuple d'un seul élément dans add_fields_dict : GetAddDictError et trace commentée"""
    trace = make_trace()
    params = {"trace": trace, **UTF8, "add_fields_dict": {"ident": (uuid.uuid4,)}}

    with FileLoader(source, {"code": None}, first_line=2, params_dict=params) as file_loader:
        rows = file_loader.read_dict()

        with pytest.raises(GetAddDictError):
            list(rows)

    trace.refresh_from_db()
    assert trace.comment == "La méthode get_add_dict a besoins d'un tuple de 2 élements"

    with FileLoader(source, {"code": None}, first_line=2, params_dict={**UTF8, "add_fields_dict": {"ident": (uuid.uuid4,)}}) as file_loader, pytest.raises(GetAddDictError):
        _ = file_loader.get_add_dict


def test_fileloader_fichier_texte_introuvable(tmp_path, make_trace):
    """Fichier absent : FileToCsvError, trace commentée"""
    trace = make_trace()

    with pytest.raises(FileToCsvError, match="en csv StringIO"):
        FileLoader(tmp_path / "absent.csv", {"code": None}, params_dict={"trace": trace})

    trace.refresh_from_db()
    assert trace.errors is True

    with pytest.raises(FileToCsvError):
        FileLoader(tmp_path / "absent.csv", {"code": None})


def test_fileloader_excel_introuvable_ou_invalide(tmp_path, make_trace, monkeypatch):
    """Classeur absent (OSError) ou non reconnu (ExcelToCsvFileError) : ExcelToCsvError"""
    trace = make_trace()

    with pytest.raises(ExcelToCsvError, match="excel en csv StringIO"):
        FileLoader(tmp_path / "absent.xlsx", {"code": None}, params_dict={"trace": trace})

    trace.refresh_from_db()
    assert trace.errors is True

    def _boom(*_args, **_kwargs):
        raise ExcelToCsvFileError("pas un classeur")

    (tmp_path / "faux.xls").write_bytes(b"x")

    with patched_attrs(monkeypatch, loader_module, excel_file_to_csv_string_io=_boom), pytest.raises(ExcelToCsvError):
        FileLoader(tmp_path / "faux.xls", {"code": None})


def test_fileloader_close_tolere_les_appels_repetes(source):
    file_loader = FileLoader(source, {"code": None})
    file_loader.csv_io.close()

    file_loader.close()
    file_loader.close()

    assert not hasattr(file_loader, "csv_io")
