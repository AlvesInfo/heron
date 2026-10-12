# pylint: disable=E0401,W0621,R0913,R0914
"""
FR : Tests des vues de l'app rfa (CRUD du paramétrage, exports, suppressions ajax, génération)
EN : Tests for rfa app views

created at: 2026-10-12
created by: Paulo ALVES
"""
import pytest
from django.urls import reverse

from apps.core.functions.functions_http_response import CONTENT_TYPE_EXCEL
from apps.rfa.models import (
    ClientExclusion,
    ClientSupplierExclusion,
    SectionProExclusion,
    SectionRfa,
    SignboardExclusion,
    SupplierRate,
)
from apps.rfa.tests.conftest import RFA_PERIOD
from apps.rfa.views import (
    clients_suppliers_views,
    clients_views,
    rfa_views,
    sections_pro_views,
    sections_rfa_views,
    signboards_views,
    suppliers_rate_views,
)

pytestmark = pytest.mark.django_db

CASES = ["signboard", "client", "client_supplier", "rate", "section_rfa", "section_pro"]


def _boom(*_args, **_kwargs):
    raise RuntimeError("export cassé")


@pytest.fixture
def crud_cases(
    make_signboard, make_cct, make_maison, make_society, make_section, make_signboard_exclusion,
    make_client_exclusion, make_client_supplier_exclusion, make_supplier_rate, make_section_rfa,
    make_section_pro_exclusion,
):
    """Pour chaque paramétrage : routes, modèle, module de vue, instance existante et données postées"""
    make_signboard("DEM")
    make_signboard("GEM")
    # Seules les maisons de type vente (1, 2) dont le cct est actif sont exclues des RFA
    for cct in ("AF0001", "AF0002", "AF0003"):
        make_cct(cct, active=True)
    maison_1 = make_maison("AF0001", type_x3=1)
    maison_2 = make_maison("AF0002", type_x3=2)
    make_maison("AF0003", type_x3=1)
    make_society("FOUR002", is_client=False)
    rfa_2 = make_section("RFA", "2026RFA_02")
    rfa_3 = make_section("RFA", "2026RFA_03")
    pro_2 = make_section("PRO", "AUD")
    pro_3 = make_section("PRO", "VER")
    return {
        "signboard": {
            "routes": ("signboards_exclusion_list", "signboard_exclusion_create", "signboard_exclusion_update", "signboard_exclusion_delete", "signboard_exclusion_export_list"),
            "model": SignboardExclusion, "module": signboards_views, "instance": make_signboard_exclusion("ACF"),
            "create": {"signboard": "DEM"}, "update": {"signboard": "GEM"}, "invalid": {"signboard": "XXX"},
            "check": lambda obj: obj.signboard.code, "expected": ("DEM", "GEM"),
        },
        "client": {
            "routes": ("clients_exclusion_list", "client_exclusion_create", "client_exclusion_update", "client_exclusion_delete", "client_exclusion_export_list"),
            "model": ClientExclusion, "module": clients_views, "instance": make_client_exclusion(maison_1),
            "create": {"cct": "AF0002"}, "update": {"cct": "AF0003"}, "invalid": {"cct": "ZZ9999"},
            "check": lambda obj: obj.cct.cct.cct, "expected": ("AF0002", "AF0003"),
        },
        "client_supplier": {
            "routes": ("clients_suppliers_exclusion_list", "client_supplier_exclusion_create", "client_supplier_exclusion_update", "client_supplier_exclusion_delete", "client_supplier_exclusion_export_list"),
            "model": ClientSupplierExclusion, "module": clients_suppliers_views, "instance": make_client_supplier_exclusion(maison_1, "FOUR001"),
            "create": {"maison": maison_2.uuid_identification, "supplier": "FOUR001"},
            "update": {"maison": maison_1.uuid_identification, "supplier": "FOUR002"},
            "invalid": {"maison": "", "supplier": "FOUR001"},
            "check": lambda obj: f"{obj.maison.cct.cct}/{obj.supplier.third_party_num}", "expected": ("AF0002/FOUR001", "AF0001/FOUR002"),
        },
        "rate": {
            "routes": ("suppliers_rate_list", "supplier_rate_create", "supplier_rate_update", "supplier_rate_delete", "suppliers_rate_export_list"),
            "model": SupplierRate, "module": suppliers_rate_views, "instance": make_supplier_rate("FOUR001", "0.05"),
            "create": {"supplier": "FOUR002", "rfa_rate": "0.1"}, "update": {"supplier": "FOUR001", "rfa_rate": "0.2"},
            "invalid": {"supplier": "FOUR002", "rfa_rate": "abc"},
            "check": lambda obj: f"{obj.supplier.third_party_num}/{obj.rfa_rate}", "expected": ("FOUR002/0.10000", "FOUR001/0.20000"),
        },
        "section_rfa": {
            "routes": ("sections_rfa_list", "section_rfa_create", "section_rfa_update", "section_rfa_delete", "section_rfa_export_list"),
            "model": SectionRfa, "module": sections_rfa_views, "instance": make_section_rfa(RFA_PERIOD),
            "create": {"axe_rfa": rfa_2.uuid_identification}, "update": {"axe_rfa": rfa_3.uuid_identification},
            "invalid": {"axe_rfa": pro_2.uuid_identification},
            "check": lambda obj: obj.axe_rfa.section, "expected": ("2026RFA_02", "2026RFA_03"),
        },
        "section_pro": {
            "routes": ("sections_pro_exclusions_list", "section_pro_exclusion_create", "section_pro_exclusion_update", "section_pro_exlusion_delete", "section_pro_exclusions_export_list"),
            "model": SectionProExclusion, "module": sections_pro_views, "instance": make_section_pro_exclusion("OPT"),
            "create": {"axe_pro": pro_2.uuid_identification}, "update": {"axe_pro": pro_3.uuid_identification},
            "invalid": {"axe_pro": rfa_2.uuid_identification},
            "check": lambda obj: obj.axe_pro.section, "expected": ("AUD", "VER"),
        },
    }


# CRUD DU PARAMÉTRAGE ==============================================================================


@pytest.mark.parametrize("name", CASES)
def test_listes(logged_client, crud_cases, name):
    case = crud_cases[name]

    response = logged_client.get(reverse(f"rfa:{case['routes'][0]}"))

    assert response.status_code == 200
    assert list(response.context["rfa_parameters"]) == [case["instance"]]


@pytest.mark.parametrize("name", CASES)
def test_creation(logged_client, crud_cases, name):
    case = crud_cases[name]
    url = reverse(f"rfa:{case['routes'][1]}")

    page = logged_client.get(url)
    created = logged_client.post(url, case["create"])
    invalid = logged_client.post(url, case["invalid"])
    duplicate = logged_client.post(url, case["create"])

    assert page.status_code == 200
    assert page.context["create"] is True
    assert created.status_code == 302, created.context["form"].errors
    assert created.url == reverse(f"rfa:{case['routes'][0]}")
    new = case["model"].objects.exclude(pk=case["instance"].pk).get()
    assert case["check"](new) == case["expected"][0]
    assert new.created_by == logged_client.user
    assert invalid.status_code == 200
    assert invalid.context["form"].errors
    assert duplicate.status_code == 200
    assert case["model"].objects.count() == 2


@pytest.mark.parametrize("name", CASES)
def test_modification(logged_client, crud_cases, name):
    case = crud_cases[name]
    instance = case["instance"]
    url = reverse(f"rfa:{case['routes'][2]}", kwargs={"pk": instance.pk})

    page = logged_client.get(url)
    updated = logged_client.post(url, case["update"])
    instance.refresh_from_db()

    assert page.status_code == 200
    assert page.context["chevron_retour"] == reverse(f"rfa:{case['routes'][0]}")
    assert updated.status_code == 302, updated.context["form"].errors
    assert case["check"](instance) == case["expected"][1]
    assert instance.modified_by == logged_client.user


@pytest.mark.parametrize("name", CASES)
def test_suppression(logged_client, ajax_client, crud_cases, name):
    """Suppression ajax : succès, puis identifiant inconnu ; refus hors ajax ou hors POST"""
    case = crud_cases[name]
    url = reverse(f"rfa:{case['routes'][3]}")
    pk = case["instance"].pk

    assert logged_client.post(url, {"pk": pk}).url == reverse("home")
    assert ajax_client.get(url).url == reverse("home")
    assert ajax_client.post(url, {"pk": pk}).json() == {"success": "success"}
    assert case["model"].objects.filter(pk=pk).exists() is False
    assert ajax_client.post(url, {"pk": pk}).json() == {"success": "ko"}


@pytest.mark.parametrize("name", CASES)
def test_exports(logged_client, monkeypatch, crud_cases, name):
    """L'export renvoie un fichier Excel ; en cas d'erreur il redirige vers la liste"""
    case = crud_cases[name]
    url = reverse(f"rfa:{case['routes'][4]}")

    response = logged_client.get(url)

    assert response.status_code == 200
    assert response["Content-Type"] == CONTENT_TYPE_EXCEL
    assert "LISTING_DES_" in response["Content-Disposition"]

    monkeypatch.setattr(case["module"], "response_file", _boom)
    failed = logged_client.get(url)

    assert failed.status_code == 302
    assert failed.url == reverse(f"rfa:{case['routes'][0]}")


# GÉNÉRATION DES RFA ===============================================================================


def test_generation_integration_en_cours(logged_client, monkeypatch):
    monkeypatch.setattr(rfa_views, "get_actions_in_progress", lambda: True)

    response = logged_client.get(reverse("rfa:rfa_generation"))

    assert response.status_code == 200
    assert response.context["en_cours"] is True
    assert response.context["titre_table"] == "DES INTEGRATIONS SONT EN COURS, PATIENTEZ..."


def test_generation_sans_rfa(logged_client):
    response = logged_client.get(reverse("rfa:rfa_generation"))

    assert response.status_code == 200
    assert response.context["have_rfa"] == []
    assert response.context["titre_table"] == "GENERATION DES RFA"


def test_generation_bloquee_par_nouveaux_articles(logged_client, monkeypatch, make_article):
    make_article()
    monkeypatch.setattr(rfa_views, "have_rfa_to_be_invoiced", lambda: ["FOUR001"])

    response = logged_client.get(reverse("rfa:rfa_generation"))

    assert response.status_code == 302
    assert response.url == reverse("articles:new_articles_list")
    assert logged_client.session["level"] == 50


@pytest.mark.parametrize("control", ["supplier_control_validation", "supplier_control_cct"])
def test_generation_bloquee_par_les_controles(logged_client, monkeypatch, control):
    """Factures non validées ou sans CCT : redirection vers l'écran de validation, en GET et en POST"""
    monkeypatch.setattr(rfa_views, "have_rfa_to_be_invoiced", lambda: ["FOUR001"])
    monkeypatch.setattr(rfa_views, control, lambda: "Contrôle en échec")
    url = reverse("rfa:rfa_generation")

    for response in (logged_client.get(url), logged_client.post(url, {"section": RFA_PERIOD})):
        assert response.status_code == 302
        assert response.url == reverse("validation_purchases:integration_purchases")
        assert logged_client.session["level"] == 50


def test_generation_lancement(logged_client, monkeypatch, rfa_data):
    """GET affiche les fournisseurs à traiter, POST lance la génération et redirige"""
    launches = []

    def _fake_launch(user_pk, suppliers, period):
        launches.append((user_pk, suppliers, period))
        return False, "RFA intégrées"

    monkeypatch.setattr(rfa_views, "rfa_generation_launch", _fake_launch)
    url = reverse("rfa:rfa_generation")

    page = logged_client.get(url)
    assert page.status_code == 200
    assert page.context["have_rfa"] == ["FOUR001"]
    assert page.context["form"].fields["section"].initial == RFA_PERIOD

    launched = logged_client.post(url, {"section": RFA_PERIOD})
    assert launched.status_code == 302
    assert launched.url == url
    assert launches == [(logged_client.user.pk, ["FOUR001"], RFA_PERIOD)]
    assert logged_client.session["level"] == 20

    invalid = logged_client.post(url, {"section": "INCONNUE"})
    assert invalid.status_code == 200
    assert invalid.context["form"].errors


def test_generation_refusee_sans_periode_ouverte(logged_client, monkeypatch, rfa_data):
    """Sans période de facturation ouverte, rien n'est lancé et l'utilisateur est prévenu"""
    monkeypatch.setattr(rfa_views, "rfa_generation_launch", lambda *_args: pytest.fail("ne doit pas être lancé"))
    rfa_data["validation"].final = True
    rfa_data["validation"].save()
    url = reverse("rfa:rfa_generation")

    response = logged_client.post(url, {"section": RFA_PERIOD})

    assert response.status_code == 302
    assert response.url == url
    assert logged_client.session["level"] == 50

    monkeypatch.setattr(rfa_views, "rfa_generation_launch", lambda *_: (True, "Erreur - broker"))
    failed = logged_client.post(url, {"section": RFA_PERIOD})
    assert failed.status_code == 302
    assert logged_client.session["level"] == 50
