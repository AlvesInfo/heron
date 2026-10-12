# pylint: disable=E0401,W0621
"""
FR : Tests du chargeur de fichiers EDI OPTO 33 (classe Opto33Loader de apps/data_flux/loader.py)
EN : Tests for the EDI OPTO 33 loader

created at: 2026-10-11
created by: Paulo ALVES
"""
import io
import uuid

import pytest

from apps.data_flux.exceptions import GetAddDictError, IterFileToInsertError
from apps.data_flux.loader import Opto33Loader
from apps.data_flux.models import Trace

pytestmark = pytest.mark.django_db

SEGMENTS = [
    "UNA:+.? ",
    "UNB+UNOC:3+FOUR001+ACUITIS+220420:1200+1863",
    "UNH+1+INVOIC:D:96B:UN:OPTO33",
    "BGM+380+FAC001+9",
    "DTM+3:20220420:102",
    "NAD+SU+12345+9+FOURNISSEUR+OPTIQUE SAS",
    "LIN+1++ART001:IN::21",
    "QTY+47:2",
    "PRI+AAA:90:CT:NTP",
    "LIN+2++ART002:IN::21",
    "QTY+47:1",
    "UNS+S",
    "MOA+125:1000",
    "UNT+12+1",
    "UNZ+1+1863",
]
COLUMNS = {"invoice_number": "invoice_number", "reference_article": "reference_article", "qty": "qty"}


@pytest.fixture
def edi_file(tmp_path):
    path = tmp_path / "FOUR001.edi"
    path.write_text("'\n".join(SEGMENTS) + "'", encoding="utf8")
    return path


def test_lecture_en_dictionnaires(edi_file):
    """Une ligne par article, colonnes demandées par leur nom dans le flux parsé"""
    with Opto33Loader(edi_file, COLUMNS, params_dict={}) as loader:
        loader.open()
        rows = list(loader.read_dict())

    assert loader.source_header == list(loader.opto_parse["get_columns"])
    assert loader.get_header() == ["invoice_number", "reference_article", "qty"]
    assert rows == [
        {"invoice_number": "FAC001", "reference_article": "ART001", "qty": "2"},
        {"invoice_number": "FAC001", "reference_article": "ART002", "qty": "1"},
    ]


def test_lecture_texte_et_listes(edi_file):
    """Le flux parsé est un générateur : une seule lecture par instance de chargeur"""
    with Opto33Loader(edi_file, COLUMNS, params_dict={"delimiter": "|"}) as loader:
        assert list(loader.read()) == ["FAC001|ART001|2", "FAC001|ART002|1"]
        assert list(loader.read()) == []

    with Opto33Loader(edi_file, COLUMNS, params_dict={}) as loader:
        assert list(loader.read_list()) == [["FAC001", "ART001", "2"], ["FAC001", "ART002", "1"]]

    with Opto33Loader(edi_file, COLUMNS, params_dict={}) as loader:
        csv_io = io.StringIO()
        loader.make_io(csv_io)

    assert csv_io.getvalue() == "FAC001;ART001;2\nFAC001;ART002;1\n"
    assert csv_io.tell() == 0


def test_champs_ajoutes_a_la_volee(edi_file):
    """Valeurs fixes ou calculées (tuple fonction, arguments) ajoutées à chaque ligne"""
    identifier = uuid.uuid4()
    params = {"add_fields_dict": {"uuid_identification": (lambda: identifier, {}), "flow": "Edi"}}

    with Opto33Loader(edi_file, COLUMNS, params_dict=params) as loader:
        assert loader.get_add_dict == {"uuid_identification": identifier, "flow": "Edi"}
        assert loader.get_add_values == [identifier, "Edi"]
        assert list(loader.read()) == [f"FAC001;ART001;2;{identifier};Edi", f"FAC001;ART002;1;{identifier};Edi"]

    with Opto33Loader(edi_file, COLUMNS, params_dict=params) as loader:
        assert list(loader.read_list())[1] == ["FAC001", "ART002", "1", str(identifier), "Edi"]

    with Opto33Loader(edi_file, COLUMNS, params_dict=params) as loader:
        assert next(iter(loader.read_dict())) == {
            "invoice_number": "FAC001", "reference_article": "ART001", "qty": "2", "uuid_identification": identifier, "flow": "Edi",
        }


def test_champ_ajoute_sans_arguments(edi_file, make_trace):
    """Un tuple sans dictionnaire d'arguments : GetAddDictError, tracée si une trace est fournie"""
    trace = make_trace()
    params = {"add_fields_dict": {"uuid_identification": (uuid.uuid4,)}, "trace": trace}

    with Opto33Loader(edi_file, COLUMNS, params_dict=params) as loader, pytest.raises(GetAddDictError, match="tuple de 2"):
        _ = loader.get_add_dict

    trace.refresh_from_db()
    assert trace.errors is True
    assert trace.comment == "La méthode get_add_dict a besoins d'un tuple de 2 élements"

    with Opto33Loader(edi_file, COLUMNS, params_dict={"add_fields_dict": {"x": (uuid.uuid4,)}}) as loader, pytest.raises(GetAddDictError):
        _ = loader.get_add_dict


def test_colonnes_absentes_du_flux(edi_file, make_trace):
    """Une colonne demandée inconnue du flux : IterFileToInsertError, tracée si une trace est fournie"""
    trace = make_trace()
    columns = {"invoice_number": "invoice_number", "inconnue": "colonne_inconnue"}

    with Opto33Loader(edi_file, columns, params_dict={"trace": trace}) as loader:
        rows = loader.read_dict()

        with pytest.raises(IterFileToInsertError, match='"colonne_inconnue"') as excinfo:
            list(rows)

    trace.refresh_from_db()
    assert trace.errors is True
    assert "FOUR001.edi" in trace.comment
    assert "le fichier contient les colonnes suivantes : supplier" in str(excinfo.value)
    assert Trace.objects.count() == 1

    with Opto33Loader(edi_file, columns, params_dict={}) as loader:
        rows = loader.read()

        with pytest.raises(IterFileToInsertError):
            list(rows)
