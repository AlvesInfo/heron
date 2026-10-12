"""
FR : Tests de la numérotation des compteurs : préfixes et suffixes (dates, tiers, cct)
EN : Counters prefix / suffix tests

created at: 2023-03-11, réécrit le 2026-10-11
created by: Paulo ALVES
"""
import pendulum
import pytest

from apps.parameters.bin.core import get_pre_suf

pytestmark = pytest.mark.django_db

NOW = pendulum.now()
DATE = pendulum.date(2023, 3, 23)


@pytest.mark.parametrize(
    ("name", "attr_instance", "expected"),
    [
        ("AAAAMM", None, NOW.format("YYYYMM", locale="fr")),
        ("AAAAMM", DATE, "202303"),
        ("AAAA-MM", None, NOW.format("YYYY-MM", locale="fr")),
        ("AAAA-MM", DATE, "2023-03"),
        ("AAAA_MM", DATE, "2023_03"),
        ("AAAAMMDD", DATE, "20230323"),
        ("AAAA-MM-DD", DATE, "2023-03-23"),
        ("AAAA_MM_DD", DATE, "2023_03_23"),
        ("LIBRE", None, "LIBRE"),
        ("", None, ""),
    ],
)
def test_get_pre_suf_dates_et_texte(name, attr_instance, expected):
    assert get_pre_suf(name=name, attr_instance=attr_instance) == expected


@pytest.mark.parametrize(
    ("name", "attr_instance", "expected"),
    [
        ("TIERS", None, ""),
        ("TIERS", "BBGR001", "BBGR001"),
        ("TIERS", "INCONNU", ""),
        ("TEST_TEST_TIERS", None, "TEST_TEST"),
        ("TEST_TEST_TIERS", "BBGR001", "TEST_TEST_BBGR001"),
        ("TIERS_TEST_TEST", None, "TEST_TEST"),
        ("TIERS_TEST_TEST", "BBGR001", "BBGR001_TEST_TEST"),
    ],
)
def test_get_pre_suf_tiers(make_society, name, attr_instance, expected):
    make_society("BBGR001")

    assert get_pre_suf(name=name, attr_instance=attr_instance) == expected


@pytest.mark.parametrize(
    ("name", "attr_instance", "expected"),
    [
        ("CCT", None, ""),
        ("CCT", "CLI001", "AF0014"),
        ("CCT_TEST_TEST", None, "TEST_TEST"),
        ("CCT_TEST_TEST", "CLI001", "AF0014_TEST_TEST"),
        ("TEST_TEST_CCT", None, "TEST_TEST"),
        ("TEST_TEST_CCT", "CLI001", "TEST_TEST_AF0014"),
        ("TEST_TEST_CCT", "INCONNU", "TEST"),
    ],
)
def test_get_pre_suf_cct(make_maison, name, attr_instance, expected):
    """Le cct est retrouvé à partir du tiers propriétaire de la maison"""
    make_maison("AF0014")

    assert get_pre_suf(name=name, attr_instance=attr_instance) == expected
