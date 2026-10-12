# pylint: disable=E0401,W0621
"""FR : Tests des extractions post-import (imports/extraction_cct.py, imports/extraction_code_plan.py)


EN : Tests for post-import extractions

created at: 2026-10-10
created by: Paulo ALVES
"""

import pytest

from apps.accountancy.imports.extraction_cct import update_cct_sage
from apps.accountancy.imports.extraction_code_plan import update_code_plan
from apps.accountancy.models import CctSage, CodePlanSage
from conftest import captured_queries

pytestmark = pytest.mark.django_db


# CODE PLAN ========================================================================================


def test_update_code_plan_cree_les_plans_distincts(make_account):
    """Un CodePlanSage par plan distinct présent dans les comptes"""
    make_account("FRA", "411000")
    make_account("FRA", "401000")
    make_account("BEL", "411000")

    update_code_plan()

    assert list(CodePlanSage.objects.values_list("code_plan_sage", flat=True).order_by("pk")) == [
        "BEL",
        "FRA",
    ]


def test_update_code_plan_idempotent(make_account, make_code_plan):
    """Les plans existants sont conservés, pas de doublon au second passage"""
    make_code_plan("FRA")
    make_account("FRA", "411000")

    update_code_plan()
    update_code_plan()

    assert CodePlanSage.objects.count() == 1


def test_update_code_plan_sans_compte():
    """Sans compte, aucune requête d'écriture"""
    with captured_queries() as queries:
        update_code_plan()

    assert CodePlanSage.objects.count() == 0
    assert all("INSERT" not in query["sql"] for query in queries.captured_queries)


# CCT ==============================================================================================


def test_update_cct_sage_cree_depuis_les_sections_cct(make_section):
    """Seules les sections de l'axe CCT alimentent CctSage, avec l'uuid de la section"""
    paris = make_section(
        "CCT",
        "AF0001",
        name="Paris",
        short_name="PAR",
        chargeable=True,
        regroup_01="R1",
        regroup_02="R2",
        active=True,
    )
    make_section("BU", "AF0001", name="Pas un cct")

    update_cct_sage()

    cct = CctSage.objects.get()
    assert cct.cct == "AF0001"
    assert cct.name == "Paris"
    assert cct.short_name == "PAR"
    assert cct.chargeable is True
    assert cct.active is True
    assert (cct.regroup_01, cct.regroup_02) == ("R1", "R2")
    assert cct.uuid_identification == paris.uuid_identification


def test_update_cct_sage_met_a_jour_les_existants(make_section, make_cct):
    """Un cct existant est mis à jour et garde son propre uuid"""
    existing = make_cct("AF0001", name="Ancien nom", chargeable=True)
    make_section(
        "CCT",
        "AF0001",
        name="Nouveau nom",
        short_name="NN",
        chargeable=False,
        active=False,
        regroup_01="X",
    )

    update_cct_sage()

    existing.refresh_from_db()
    assert CctSage.objects.count() == 1
    assert existing.name == "Nouveau nom"
    assert existing.short_name == "NN"
    assert existing.chargeable is False
    assert existing.active is False
    assert existing.regroup_01 == "X"


def test_update_cct_sage_idempotent(make_section):
    """Deux passages successifs ne créent pas de doublon"""
    make_section("CCT", "AF0001")
    make_section("CCT", "AF0002")

    update_cct_sage()
    update_cct_sage()

    assert CctSage.objects.count() == 2
