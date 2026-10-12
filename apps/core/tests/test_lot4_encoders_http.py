# pylint: disable=E0401,W0621
"""
FR : Tests de l'encodeur JSON et des encodages base64 (apps/core/bin/encoders.py), des réponses
     fichiers (functions_http_response.py), de check_next_page (functions_http.py) et des
     régimes de tva (bin/get_sage_elements.py)
EN : Tests for JSON encoder, base64 helpers, file responses, next page check and vat regimes

created at: 2026-10-11
created by: Paulo ALVES
"""
import datetime
import decimal
import json
import types
import uuid
from pathlib import Path

import pytest
from django.core.files.storage import FileSystemStorage
from django.db.models.fields.files import ImageFieldFile
from django.utils.functional import lazy

from apps.core.bin import get_sage_elements
from apps.core.bin.encoders import PersonalizedDjangoJSONEncoder, get_base_64, set_base_64_list, set_base_64_str
from apps.core.functions import functions_http
from apps.core.functions.functions_http_response import CONTENT_TYPE_CSV, CONTENT_TYPE_EXCEL, response_file, x_accel_exists_file_response
from conftest import patched_attrs


def _encode(value):
    return json.loads(json.dumps({"v": value}, cls=PersonalizedDjangoJSONEncoder))["v"]


# ENCODEUR JSON ====================================================================================


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (datetime.datetime(2026, 1, 15, 10, 30, 45), "2026-01-15T10:30:45"),
        (datetime.datetime(2026, 1, 15, 10, 30, 45, 123456), "2026-01-15T10:30:45.123"),
        (datetime.datetime(2026, 1, 15, 10, 30, 45, tzinfo=datetime.UTC), "2026-01-15T10:30:45Z"),
        (datetime.datetime(2026, 1, 15, 10, 30, 45, 654321, tzinfo=datetime.UTC), "2026-01-15T10:30:45.654Z"),
        (datetime.date(2026, 1, 15), "2026-01-15"),
        (datetime.time(10, 30, 45), "10:30:45"),
        (datetime.time(10, 30, 45, 123456), "10:30:45.123"),
        (datetime.timedelta(days=1, hours=2), "P1DT02H00M00S"),
        (decimal.Decimal("12.50"), "12.50"),
        (uuid.UUID("12345678-1234-5678-1234-567812345678"), "12345678-1234-5678-1234-567812345678"),
    ],
)
def test_encodeur_json_types_geres(value, expected):
    assert _encode(value) == expected


def test_encodeur_json_promesse_et_fichier_image():
    assert _encode(lazy(lambda: "texte différé", str)()) == "texte différé"
    field = types.SimpleNamespace(storage=FileSystemStorage())
    assert _encode(ImageFieldFile(None, field, "logos/acuitis.png")) == "logos/acuitis.png"


def test_encodeur_json_heure_avec_fuseau_refusee():
    value = datetime.time(10, 0, tzinfo=datetime.UTC)

    with pytest.raises(ValueError, match="timezone-aware"):
        json.dumps(value, cls=PersonalizedDjangoJSONEncoder)


def test_encodeur_json_objet_inconnu():
    value = object()

    with pytest.raises(TypeError):
        json.dumps(value, cls=PersonalizedDjangoJSONEncoder)


# BASE 64 ==========================================================================================


def test_base_64_liste_et_chaine():
    encoded = set_base_64_list(["/book/", "AF0001"])

    assert get_base_64(encoded) == ["/book/", "AF0001"]
    assert get_base_64(set_base_64_str("seul")) == ["seul"]
    assert get_base_64(set_base_64_str(None)) == [""]
    assert get_base_64(None) == [""]
    # le remplissage "=" manquant est reconstitué
    assert get_base_64(encoded.rstrip("=")) == ["/book/", "AF0001"]


# RÉPONSES FICHIERS ================================================================================


def _writer(file_io, file_name, *args, **kwargs):
    file_io.write(f"{file_name}|{args}|{sorted(kwargs.items())}".encode())


@pytest.mark.parametrize(
    ("args", "kwargs", "expected"),
    [
        ((), {}, "f.csv|()|[]"),
        (("a",), {}, "f.csv|('a',)|[]"),
        ((), {"k": 1}, "f.csv|()|[('k', 1)]"),
        (("a",), {"k": 1}, "f.csv|('a',)|[('k', 1)]"),
    ],
)
def test_response_file_transmet_les_arguments(args, kwargs, expected):
    response = response_file(_writer, "f.csv", CONTENT_TYPE_CSV, *args, **kwargs)

    assert response.content.decode() == expected
    assert response["Content-Type"] == CONTENT_TYPE_CSV
    assert response["Content-Disposition"] == "attachment; filename=f.csv"
    assert "download_complete_" not in response.cookies


def test_response_file_jeton_de_telechargement():
    response = response_file(_writer, "f.xlsx", CONTENT_TYPE_EXCEL, download_token="abc")

    cookie = response.cookies["download_complete_abc"]
    assert cookie.value == "true"
    assert cookie["max-age"] == 60
    assert cookie["samesite"] == "Lax"


def test_x_accel_en_debug_lit_le_fichier(settings, tmp_path):
    settings.DEBUG = True
    file = tmp_path / "LISTING.xlsx"
    file.write_bytes(b"PK contenu")

    response = x_accel_exists_file_response(file)

    assert response.content == b"PK contenu"
    assert response["Content-Type"] == CONTENT_TYPE_EXCEL
    assert response["Content-Disposition"] == 'attachment; filename="LISTING.xlsx"'
    assert "X-Accel-Redirect" not in response


def test_x_accel_hors_debug_delegue_a_nginx(settings):
    settings.DEBUG = False

    response = x_accel_exists_file_response(Path("/nulle/part/LISTING.csv"), CONTENT_TYPE_CSV)

    assert response["X-Accel-Redirect"] == "/excel_media/LISTING.csv"
    assert response["content-type"] == ""
    assert response.content == b""


# PAGE SUIVANTE ====================================================================================


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (None, "/"),
        ("", "/"),
        ("http://pirate.example/vol", "/"),
        ("http://heron.local/book/societies_list/", "http://heron.local/book/societies_list/"),
        ("/book/societies_list/", "/book/societies_list/"),
        ("/book/societies_list/?page=2", "/book/societies_list/?page=2"),
        ("//pirate.example/vol", "/"),
        ("javascript:alert(1)", "/"),
        ("http://heron.local.pirate.example/", "/"),
    ],
)
def test_check_next_page(monkeypatch, url, expected):
    """Urls relatives internes et urls absolues d'un domaine de la liste blanche conservées,
    domaine étranger, //hôte, schéma javascript renvoyés vers la racine"""
    with patched_attrs(monkeypatch, functions_http, DOMAINS_WHITELIST=["heron.local"]):
        assert functions_http.check_next_page(url) == expected


# RÉGIME DE TVA ====================================================================================


@pytest.mark.django_db
def test_get_uuid_des_axes(make_section):
    """Chaque axe est résolu par sa section ; l'axe RFA inconnu retombe sur NAF"""
    sections = {axe: make_section(axe, f"S{axe}") for axe in ("PYS", "PRO", "PRJ", "BU", "RFA")}
    naf = make_section("RFA", "NAF")

    for function in (get_sage_elements.get_uuid_pys, get_sage_elements.get_uuid_pro, get_sage_elements.get_uuid_prj, get_sage_elements.get_uuid_bu, get_sage_elements.get_uuid_rfa):
        function.cache_clear()

    assert get_sage_elements.get_uuid_pys("SPYS") == sections["PYS"].uuid_identification
    assert get_sage_elements.get_uuid_pro("SPRO") == sections["PRO"].uuid_identification
    assert get_sage_elements.get_uuid_prj("SPRJ") == sections["PRJ"].uuid_identification
    assert get_sage_elements.get_uuid_bu("SBU") == sections["BU"].uuid_identification
    assert get_sage_elements.get_uuid_rfa("SRFA") == sections["RFA"].uuid_identification
    assert get_sage_elements.get_uuid_rfa("INCONNU") == naf.uuid_identification
    assert get_sage_elements.get_uuid_pro("INCONNU") is None


@pytest.mark.django_db
def test_get_vat_regime(make_vat):
    make_vat("002", vat_regime="BEL")
    get_sage_elements.get_vat_regime.cache_clear()

    assert get_sage_elements.get_vat_regime("002") == "BEL"
    assert get_sage_elements.get_vat_regime("999") == "FRA"
