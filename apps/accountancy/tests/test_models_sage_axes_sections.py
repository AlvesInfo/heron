# pylint: disable=E0401,W0621
"""
FR : Tests des modèles AxeSage et SectionSage (apps/accountancy/models/sage_axes_sections.py)
EN : Tests for AxeSage and SectionSage models

created at: 2026-10-10
created by: Paulo ALVES
"""
import pytest
from django.db import IntegrityError, transaction
from django.db.models import Manager

from apps.accountancy.models import AxeSage, SectionSage
from apps.accountancy.models.sage_axes_sections import SectionSageQuerySet

pytestmark = pytest.mark.django_db

AXES_QUERYSETS = [
    ("BU", "bu_section", "axe_bu"),
    ("CCT", "cct_section", "axe_cct"),
    ("PRJ", "prj_section", "axe_prj"),
    ("PRO", "pro_section", "axe_pro"),
    ("PYS", "pys_section", "axe_pys"),
    ("RFA", "rfa_section", "axe_rfa"),
]


# AXE SAGE =========================================================================================


def test_axe_sage_metadonnees_import():
    """Les méthodes statiques décrivent le fichier Sage et ses colonnes"""
    assert AxeSage.file_import_sage() == "ZBIAXES_journalier.heron"
    assert AxeSage.get_columns_import() == {"axe": 0, "name": 1, "short_name": 2}
    assert AxeSage.get_uniques() == {"axe"}


def test_axe_sage_str_et_get_import(make_axe):
    """__str__ et la propriété get_import (placeholder) de l'axe"""
    axe = make_axe("BU", name="Business Unit")

    assert str(axe) == "BU - Business Unit"
    assert axe.get_import == "methode d'import à retourner"
    assert AxeSage._meta.ordering == ["axe"]  # pylint: disable=W0212


def test_axe_sage_ordonne_par_axe(make_axe):
    """L'ordering par défaut trie sur le code axe"""
    for code in ("PYS", "BU", "CCT"):
        make_axe(code)

    assert list(AxeSage.objects.values_list("axe", flat=True)) == ["BU", "CCT", "PYS"]


def test_axe_sage_unicite(make_axe):
    """Le code axe est unique en base"""
    make_axe("BU")

    with transaction.atomic(), pytest.raises(IntegrityError):
        AxeSage.objects.create(axe="BU")


# SECTION SAGE =====================================================================================


def test_section_sage_metadonnees_import():
    """Fichier, colonnes et clés d'unicité de la section"""
    assert SectionSage.file_import_sage() == "ZBICCE_journalier.heron"
    assert list(SectionSage.get_columns_import()) == [
        "axe",
        "section",
        "name",
        "short_name",
        "chargeable",
        "regroup_01",
        "regroup_02",
        "active",
        "cpy_fcy",
    ]
    assert list(SectionSage.get_columns_import().values()) == list(range(9))
    assert SectionSage.get_uniques() == {"axe", "section"}


def test_section_sage_str_get_import_et_meta(make_section):
    """__str__, get_import et options Meta de la section"""
    section = make_section("CCT", "AF0001", name="Acuitis Paris")
    meta = SectionSage._meta  # pylint: disable=W0212

    assert str(section) == "AF0001 - Acuitis Paris"
    assert section.get_import == "methode d'import à retourner"
    assert section.uuid_identification is not None
    assert section.chargeable is True
    assert section.active is True
    assert meta.ordering == ["section"]
    assert meta.unique_together == (("axe", "section"),)
    assert ["axe", "section"] in [list(fields) for fields in meta.index_together]


def test_section_sage_managers():
    """`axes` est un Manager standard, `objects` porte le QuerySet métier"""
    assert type(SectionSage.axes) is Manager  # pylint: disable=C0123
    assert isinstance(SectionSage.objects.all(), SectionSageQuerySet)
    assert not hasattr(SectionSage.axes, "bu_section")


@pytest.mark.parametrize(("axe", "queryset_method", "class_method"), AXES_QUERYSETS)
def test_section_sage_filtres_par_axe(make_section, axe, queryset_method, class_method):
    """Chaque filtre de QuerySet et chaque classmethod ne renvoie que les sections de son axe"""
    for code, _, _ in AXES_QUERYSETS:
        make_section(code, f"{code}-01")
        make_section(code, f"{code}-02")

    queryset = getattr(SectionSage.objects, queryset_method)()
    choices = getattr(SectionSage, class_method)()

    assert set(queryset.values_list("axe__axe", flat=True)) == {axe}
    assert queryset.count() == 2
    assert choices == [(f"{axe}-01", f"{axe}-01"), (f"{axe}-02", f"{axe}-02")]


def test_section_sage_filtres_chainables(make_section):
    """Les filtres du QuerySet restent chaînables avec l'ORM"""
    make_section("CCT", "AF0001", active=True)
    make_section("CCT", "AF0002", active=False)

    assert list(
        SectionSage.objects.cct_section().filter(active=True).values_list("section", flat=True)
    ) == ["AF0001"]


def test_section_sage_unicite_axe_section(make_section):
    """Le couple (axe, section) est unique, la même section peut exister sur deux axes"""
    make_section("CCT", "S1")
    make_section("BU", "S1")
    axe = AxeSage.objects.get(axe="CCT")

    with transaction.atomic(), pytest.raises(IntegrityError):
        SectionSage.objects.create(axe=axe, section="S1")


def test_section_sage_suppression_en_cascade(make_section):
    """La suppression d'un axe supprime ses sections (on_delete=CASCADE)"""
    section = make_section("PRJ", "P1")

    AxeSage.objects.filter(pk=section.axe.pk).delete()

    assert not SectionSage.objects.filter(pk=section.pk).exists()


def test_section_sage_related_name(make_section):
    """L'axe expose ses sections via related_name axe_axe"""
    section = make_section("PRO", "PR1")

    assert list(section.axe.axe_axe.all()) == [section]
