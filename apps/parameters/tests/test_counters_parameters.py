# pylint: disable=E0401
"""
FR : Module de tests
EN : tests Module

Commentaire:

created at: 2023-03-11
created by: Paulo ALVES

modified at: 2023-03-11
modified by: Paulo ALVES
"""
import os
import platform
import sys
import django

BASE_DIR = r"/"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")
django.setup()

import pytest
import pendulum

from apps.parameters.bin.core import get_pre_suf


def test_get_pre_suf():
    date_now = pendulum.now()

    test_list = [
        ("AAAAMM", None, f"{date_now.format('YYYYMM', locale='fr')}"),
        ("AAAAMM", pendulum.date(2023, 3, 23), "202303"),
        ("AAAA-MM", None, f"{date_now.format('YYYY-MM', locale='fr')}"),
        ("AAAA-MM", pendulum.date(2023, 3, 23), "2023-03"),
        ("AAAA_MM", None, f"{date_now.format('YYYY_MM', locale='fr')}"),
        ("AAAA_MM", pendulum.date(2023, 3, 23), "2023_03"),
        ("AAAAMMDD", None, f"{date_now.format('YYYYMMDD', locale='fr')}"),
        ("AAAAMMDD", pendulum.date(2023, 3, 23), "20230323"),
        ("AAAA-MM-DD", None, f"{date_now.format('YYYY-MM-DD', locale='fr')}"),
        ("AAAA-MM-DD", pendulum.date(2023, 3, 23), "2023-03-23"),
        ("AAAA_MM_DD", None, f"{date_now.format('YYYY_MM_DD', locale='fr')}"),
        ("AAAA_MM_DD", pendulum.date(2023, 3, 23), "2023_03_23"),
        ("TIERS", None, ""),
        ("TIERS", "BBGR001", "BBGR001"),
        ("TEST_TEST_TIERS", None, "TEST_TEST"),
        ("TEST_TEST_TIERS", "BBGR001", "TEST_TEST_BBGR001"),
        ("TIERS_TEST_TEST", None, "TEST_TEST"),
        ("TIERS_TEST_TEST", "BBGR001", "BBGR001_TEST_TEST"),
        ("CCT", None, ""),
        ("CCT", "AF0014", "AF0014"),
        ("CCT_TEST_TEST", None, "TEST_TEST"),
        ("CCT_TEST_TEST", "AF0014", "AF0014_TEST_TEST"),
        ("TEST_TEST_CCT", None, "TEST_TEST"),
        ("TEST_TEST_CCT", "AF0014", "TEST_TEST_AF0014"),
    ]

    for row in test_list:
        name, attr_instance, expected_result = row
        print(
            name,
            attr_instance,
            expected_result,
            get_pre_suf(name=name, attr_instance=attr_instance),
            sep=" | "
        )
        assert get_pre_suf(name=name, attr_instance=attr_instance) == expected_result
