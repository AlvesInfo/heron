# pylint: disable=E0401,W0621
"""FR : Tests des vues des familles statistiques / axes (apps/book/views/statistiques_edi_views.py)


EN : Tests for statistics families / axes views

created at: 2026-10-11
created by: Paulo ALVES
"""

import logging

import pytest
from django.contrib.messages import get_messages
from django.urls import reverse

from apps.book.models import StatFamillyAxes, SupplierFamilyAxes
from apps.book.views import statistiques_edi_views
from apps.core.models import ChangesTrace
from conftest import patched_attrs

pytestmark = pytest.mark.django_db


def _messages(response):
    return [message.message for message in get_messages(response.wsgi_request)]


@pytest.fixture
def definition(make_stat_familly, make_supplier_family_axes, make_unit):
    make_stat_familly("ACUITIS")
    return make_supplier_family_axes(
        "LUN", stat_name="ACUITIS", description="Lunettes", unit_weight=make_unit(1, "U")
    )


def _definition_data(stat, section, category, **overrides):
    data = {
        "stat_name": stat.name,
        "unit_weight": "1",
        "invoice_column": "famille",
        "regex_match": "VER",
        "expected_result": "VERRES",
        "axe_pro": str(section.uuid_identification),
        "big_category": str(category.uuid_identification),
        "description": "Verres",
        "item_weight": "0",
    }
    data.update(overrides)
    return data


# FAMILLES STATISTIQUES ============================================================================


def test_liste_des_statistiques(logged_client, make_stat_familly):
    make_stat_familly("BBGR")
    make_stat_familly("ACUITIS", regex_bool=True)

    response = logged_client.get(reverse("book:statistiques_list"))

    assert response.status_code == 200
    assert response.context["titre_table"] == "Familles Statistiques/Axes"
    assert [stat.name for stat in response.context["statistiques"]] == ["ACUITIS", "BBGR"]


def test_creation_statistique_get(logged_client):
    response = logged_client.get(reverse("book:statistique_create"))

    assert response.status_code == 200
    assert response.context["create"] is True
    assert response.context["chevron_retour"] == reverse("book:statistiques_list")
    assert response.context["titre_table"] == "Création d'une nouvelle Famille Statistiques/Axes"


def test_creation_statistique_post(logged_client):
    response = logged_client.post(
        reverse("book:statistique_create"),
        {"name": "ACUITIS", "description": "Acuitis", "regex_bool": "on"},
    )

    stat = StatFamillyAxes.objects.get(name="ACUITIS")
    assert response.status_code == 302
    assert response.url == reverse("book:statistique_update", args=["ACUITIS"])
    assert (stat.regex_bool, stat.created_by) == (True, logged_client.user)
    assert logged_client.session["level"] == 20
    assert ChangesTrace.objects.get().action_type == 1
    assert "a été créé avec success" in _messages(response)[0]


def test_creation_statistique_post_invalide(logged_client, make_stat_familly, caplog):
    """Nom manquant ou déjà pris : le formulaire est réaffiché"""
    make_stat_familly("ACUITIS")

    with caplog.at_level(logging.ERROR, logger="views"):
        response = logged_client.post(reverse("book:statistique_create"), {"name": "ACUITIS"})
        empty = logged_client.post(reverse("book:statistique_create"), {"name": ""})

    assert response.status_code == 200
    assert "name" in response.context["form"].errors
    assert empty.status_code == 200
    assert logged_client.session["level"] == 50
    assert StatFamillyAxes.objects.count() == 1
    assert "ChangeTraceMixin error" in caplog.text


def test_modification_statistique_get(logged_client, definition):
    response = logged_client.get(reverse("book:statistique_update", args=["ACUITIS"]))

    assert response.status_code == 200
    assert response.context["titre_table"] == "Mise à jour Famille Statistiques/Axes"
    assert response.context["chevron_retour"] == reverse("book:statistiques_list")
    assert "create" not in response.context
    assert "LUN" in response.content.decode()


def test_modification_statistique_post(logged_client, definition):
    stat = definition.stat_name

    response = logged_client.post(
        reverse("book:statistique_update", args=["ACUITIS"]),
        {"name": "ACUITIS", "description": "Nouvelle description"},
    )

    stat.refresh_from_db()
    assert response.status_code == 302
    assert response.url == reverse("book:statistique_update", args=["ACUITIS"])
    assert (stat.description, stat.modified_by) == ("Nouvelle description", logged_client.user)
    assert ChangesTrace.objects.get().difference["après"]["description"] == "Nouvelle description"


def test_modification_statistique_inconnue(logged_client):
    assert (
        logged_client.get(reverse("book:statistique_update", args=["ABSENTE"])).status_code == 404
    )


def test_export_des_statistiques(logged_client, definition):
    response = logged_client.get(reverse("book:statistiques_export_list"))

    assert response.status_code == 200
    assert response["Content-Disposition"].startswith(
        "attachment; filename=LISTING_DES_FAMILLES_STATISTIQUES_AXES_"
    )
    assert response.content[:2] == b"PK"


def test_export_des_statistiques_en_erreur(logged_client, monkeypatch, caplog):
    def _boom(*_args, **_kwargs):
        raise RuntimeError("excel cassé")

    with (
        patched_attrs(monkeypatch, statistiques_edi_views, excel_liste_statistiques=_boom),
        caplog.at_level(logging.ERROR, logger="views"),
    ):
        response = logged_client.get(reverse("book:statistiques_export_list"))

    assert response.status_code == 302
    assert response.url == reverse("book:statistiques_list")
    assert "statistiques_export_list" in caplog.text


# DÉFINITIONS FAMILLES / AXES ======================================================================


def test_creation_definition_get(logged_client, make_stat_familly):
    stat = make_stat_familly("ACUITIS")

    response = logged_client.get(reverse("book:familly_axes_create", args=[stat.pk]))

    assert response.status_code == 200
    assert response.context["create"] is True
    assert response.context["statistique"] == stat
    assert response.context["titre_table"] == "Création Statistique Familles/Axes : ACUITIS"
    assert response.context["chevron_retour"] == reverse(
        "book:statistique_update", args=["ACUITIS"]
    )


def test_creation_definition_statistique_inconnue(logged_client):
    assert logged_client.get(reverse("book:familly_axes_create", args=[999999])).status_code == 404
    assert (
        logged_client.post(reverse("book:familly_axes_create", args=[999999]), {}).status_code
        == 404
    )


def test_creation_definition_post(
    logged_client, make_stat_familly, make_section, make_big_category, make_unit
):
    stat = make_stat_familly("ACUITIS")
    make_unit(1, "U")
    section = make_section("PRO", "OPT")
    category = make_big_category("Marchandises")

    response = logged_client.post(
        reverse("book:familly_axes_create", args=[stat.pk]),
        _definition_data(stat, section, category),
    )

    created = SupplierFamilyAxes.objects.get()
    assert response.status_code == 302
    assert response.url == reverse("book:statistique_update", args=["ACUITIS"])
    assert (created.stat_name, created.regex_match, created.axe_pro, created.created_by) == (
        stat,
        "VER",
        section,
        logged_client.user,
    )
    assert created.sub_category is None
    assert "ACUITIS a été créé avec success" in _messages(response)[0]
    assert ChangesTrace.objects.get().model_name == "supplierfamilyaxes"


def test_creation_definition_post_invalide(
    logged_client, make_stat_familly, make_section, make_big_category, make_unit, caplog
):
    stat = make_stat_familly("ACUITIS")
    make_unit(1, "U")

    with caplog.at_level(logging.ERROR, logger="views"):
        response = logged_client.post(
            reverse("book:familly_axes_create", args=[stat.pk]),
            _definition_data(
                stat, make_section("PRO", "OPT"), make_big_category("Marchandises"), regex_match=""
            ),
        )

    assert response.status_code == 200
    assert "regex_match" in response.context["form"].errors
    assert response.context["statistique"] == stat
    assert SupplierFamilyAxes.objects.count() == 0
    assert logged_client.session["level"] == 50


def test_modification_definition_get(logged_client, definition):
    response = logged_client.get(
        reverse("book:familly_axes_update", args=[definition.stat_name.pk, definition.pk])
    )

    assert response.status_code == 200
    assert response.context["create"] is True
    assert response.context["statistique"] == definition.stat_name
    assert response.context["titre_table"] == "Modification de la Statistique Familles/Axes"
    assert response.context["chevron_retour"] == reverse(
        "book:statistique_update", args=["ACUITIS"]
    )


def test_modification_definition_post(logged_client, definition):
    url = reverse("book:familly_axes_update", args=[definition.stat_name.pk, definition.pk])
    data = _definition_data(
        definition.stat_name,
        definition.axe_pro,
        definition.big_category,
        regex_match="LUN",
        expected_result="LUN",
        description="Lunettes solaires",
    )

    response = logged_client.post(url, data)

    definition.refresh_from_db()
    assert response.status_code == 302
    assert response.url == reverse("book:statistique_update", args=["ACUITIS"])
    assert (definition.description, definition.modified_by) == (
        "Lunettes solaires",
        logged_client.user,
    )
    assert "a été modifiée avec success" in _messages(response)[0]


def test_modification_definition_inconnue(logged_client, definition):
    assert (
        logged_client.get(
            reverse("book:familly_axes_update", args=[definition.stat_name.pk, 999999])
        ).status_code
        == 404
    )


# SUPPRESSION (AJAX) ===============================================================================


def test_suppression_definition(ajax_client, definition):
    response = ajax_client.post(reverse("book:delete_familly_axes"), {"pk": definition.pk})

    assert response.json() == {"success": "success"}
    assert SupplierFamilyAxes.objects.count() == 0
    assert ChangesTrace.objects.get().action_type == 0
    assert ajax_client.session["level"] == 20


def test_suppression_definition_inconnue(ajax_client, definition, caplog):
    with caplog.at_level(logging.ERROR, logger="views"):
        response = ajax_client.post(
            reverse("book:delete_familly_axes"), {"pk": definition.pk + 1000}
        )

    assert response.json() == {"success": "ko"}
    assert SupplierFamilyAxes.objects.count() == 1
    assert "delete_familly_axes, form invalid" in caplog.text


def test_suppression_definition_hors_ajax(logged_client, ajax_client, definition):
    assert logged_client.post(
        reverse("book:delete_familly_axes"), {"pk": definition.pk}
    ).url == reverse("home")
    assert ajax_client.get(reverse("book:delete_familly_axes")).url == reverse("home")
    assert SupplierFamilyAxes.objects.count() == 1
