# pylint: disable=E0401,W0621,R0913,R0914
"""FR : Tests des vues de l'app parameters (CRUD, exports Excel, suppressions ajax, taux de change)


EN : Tests for parameters app views

created at: 2026-10-11
created by: Paulo ALVES
"""

import datetime
from decimal import Decimal

import pytest
from django.urls import reverse

from apps.core.functions.functions_http_response import CONTENT_TYPE_EXCEL
from apps.parameters.forms import DefaultAxeArticleForm
from apps.parameters.models import (
    Category,
    ControlRebilling,
    Counter,
    CounterNums,
    Email,
    ExchangeRate,
    InvoiceFunctions,
    Nature,
    SubCategory,
)
from apps.parameters.views import (
    categories_views,
    control_rebilling_views,
    exchange_rate_views,
    functions_views,
    nature_views,
    numberings_views,
)

pytestmark = pytest.mark.django_db

MONTH = "2026-01-01"


def _boom(*_args, **_kwargs):
    raise RuntimeError("export cassé")


# LISTES, CRÉATIONS, MODIFICATIONS =================================================================


@pytest.mark.parametrize(
    "route",
    [
        "categories_list",
        "category_create",
        "functions_list",
        "function_create",
        "numberings_list",
        "numbering_create",
        "natures_list",
        "nature_create",
        "emails_list",
        "email_create",
        "control_rebilling_list",
        "control_rebilling_create",
        "period_select_exchange",
    ],
)
def test_pages_sans_parametre(logged_client, route):
    response = logged_client.get(reverse(f"parameters:{route}"))

    assert response.status_code == 200


def test_categories_creation_et_modification(logged_client, make_big_category):
    created = logged_client.post(
        reverse("parameters:category_create"),
        {"ranking": 5, "code": "SERV", "name": "Services"},
        follow=True,
    )
    category = Category.objects.get(code="SERV")
    other = make_big_category("Marchandises")

    assert created.status_code == 200
    assert category.slug_name == "services"
    assert category.created_by == logged_client.user
    assert (
        logged_client.get(
            reverse("parameters:category_update", kwargs={"pk": other.pk})
        ).status_code
        == 200
    )

    updated = logged_client.post(
        reverse("parameters:category_update", kwargs={"pk": other.pk}),
        {"ranking": other.ranking, "code": other.code, "name": "Marchandises neuves"},
    )
    other.refresh_from_db()

    assert updated.status_code == 302
    assert other.name == "Marchandises neuves"
    assert other.modified_by == logged_client.user


def test_rubriques_creation_modification_et_404(
    logged_client, make_big_category, make_sub_category
):
    category = make_big_category("Marchandises")
    existing = make_sub_category("Montures", big_category=category)
    create_url = reverse("parameters:sub_category_create", kwargs={"category_pk": category.pk})

    page = logged_client.get(create_url)
    assert page.status_code == 200
    assert page.context["category_new"] == 2
    assert (
        logged_client.get(
            reverse("parameters:sub_category_create", kwargs={"category_pk": 99999})
        ).status_code
        == 404
    )
    assert (
        logged_client.post(
            reverse("parameters:sub_category_create", kwargs={"category_pk": 99999}), {}
        ).status_code
        == 404
    )

    created = logged_client.post(
        create_url,
        {
            "big_category": category.uuid_identification,
            "ranking": 2,
            "code": "VERRES",
            "name": "Verres",
        },
    )
    assert created.status_code == 302, created.context["form"].errors
    assert created.url == reverse("parameters:category_update", kwargs={"pk": category.pk})
    assert SubCategory.objects.get(code="VERRES").big_category == category

    update_url = reverse(
        "parameters:sub_category_update", kwargs={"category_pk": category.pk, "pk": existing.pk}
    )
    page = logged_client.get(update_url)
    assert page.status_code == 200
    assert page.context["category_new"] == existing.ranking

    updated = logged_client.post(
        update_url,
        {
            "big_category": category.uuid_identification,
            "ranking": existing.ranking,
            "code": existing.code,
            "name": "Montures solaires",
        },
    )
    existing.refresh_from_db()
    assert updated.status_code == 302
    assert existing.name == "Montures solaires"


def test_axes_par_defaut(logged_client, make_default_axes, make_sub_category, make_big_category):
    axes = make_default_axes()
    inside = make_sub_category("Montures", big_category=axes.big_category)
    outside = make_sub_category("Hors catégorie", big_category=make_big_category("Services"))
    url = reverse("parameters:axes_articles_defaut", kwargs={"slug_name": "axes_articles"})
    data = {
        key: value
        for key, value in DefaultAxeArticleForm(instance=axes).initial.items()
        if value is not None
    }

    page = logged_client.get(url)
    assert page.status_code == 200
    assert list(page.context["big_sub_category"]) == [inside]

    response = logged_client.post(url, {**data, "sub_category": inside.uuid_identification})
    assert response.status_code == 302, response.context["form"].errors
    axes.refresh_from_db()
    assert axes.sub_category == inside

    assert (
        logged_client.post(url, {**data, "sub_category": outside.uuid_identification}).status_code
        == 302
    )
    axes.refresh_from_db()
    assert axes.sub_category is None

    assert logged_client.post(url, data).status_code == 302
    axes.refresh_from_db()
    assert axes.sub_category is None


def test_fonctions_creation_et_modification(logged_client, make_invoice_function):
    created = logged_client.post(
        reverse("parameters:function_create"),
        {
            "function_name": "ROYALTIES",
            "function": "apps.x.y",
            "absolute_path_windows": "",
            "absolute_path_linux": "",
            "description": "",
            "redirect": "",
        },
    )
    function = make_invoice_function("ABONNEMENT")
    update_url = reverse("parameters:function_update", kwargs={"pk": function.pk})

    assert created.status_code == 302
    assert InvoiceFunctions.objects.get(function_name="ROYALTIES").created_by == logged_client.user
    assert logged_client.get(update_url).status_code == 200

    updated = logged_client.post(
        update_url,
        {
            "function_name": "ABONNEMENT",
            "function": function.function,
            "absolute_path_windows": "",
            "absolute_path_linux": "",
            "description": "Mensuel",
            "redirect": "",
        },
    )
    function.refresh_from_db()
    assert updated.status_code == 302
    assert function.description == "Mensuel"


def test_numerotations_creation_et_modification(logged_client, make_counter):
    created = logged_client.post(
        reverse("parameters:numbering_create"),
        {
            "name": "factures",
            "prefix": "FAC",
            "suffix": "",
            "function": "",
            "lpad_num": 6,
            "description": "",
            "separateur": "-",
        },
    )
    counter = make_counter("avoirs")
    update_url = reverse("parameters:numbering_update", kwargs={"pk": counter.pk})

    assert created.status_code == 302, created.context["form"].errors

    assert Counter.objects.get(name="factures").lpad_num == 6
    assert logged_client.get(update_url).status_code == 200

    updated = logged_client.post(
        update_url,
        {
            "name": "avoirs",
            "prefix": "AV",
            "suffix": "",
            "function": "",
            "lpad_num": 5,
            "description": "",
            "separateur": "",
        },
    )
    counter.refresh_from_db()
    assert updated.status_code == 302
    assert counter.prefix == "AV"


def test_natures_creation_et_modification(logged_client, make_nature):
    created = logged_client.post(
        reverse("parameters:nature_create"),
        {"name": "Madame", "to_display": "Mme", "for_contact": "on"},
    )
    nature = make_nature("Monsieur")
    update_url = reverse("parameters:nature_update", kwargs={"pk": nature.pk})

    assert created.status_code == 302
    assert Nature.objects.get(name="Madame").for_contact is True
    assert logged_client.get(update_url).status_code == 200

    updated = logged_client.post(
        update_url, {"name": "Monsieur", "to_display": "M.", "for_personnel": "on"}
    )
    nature.refresh_from_db()
    assert updated.status_code == 302
    assert (nature.to_display, nature.for_personnel) == ("M.", True)


def test_emails_creation_et_modification(logged_client, make_email):
    created = logged_client.post(
        reverse("parameters:email_create"),
        {"description": "Factures", "subject": "Vos factures", "email_body": "<p>Bonjour</p>"},
    )
    email = Email.objects.get(description="Factures")
    other = make_email(1, description="Documents")
    update_url = reverse("parameters:email_update", kwargs={"pk": other.pk})

    assert created.status_code == 302
    assert email.name == 0
    assert logged_client.get(update_url).status_code == 200

    updated = logged_client.post(
        update_url,
        {"description": "Documents", "subject": "Nouveau sujet", "email_body": "<p>Hello</p>"},
    )
    other.refresh_from_db()
    assert updated.status_code == 302
    assert other.subject == "Nouveau sujet"


def test_controles_creation_et_modification(logged_client, make_control):
    created = logged_client.post(
        reverse("parameters:control_rebilling_create"), {"name": "Essilor", "comment": ""}
    )
    control = make_control("Hoya")
    update_url = reverse("parameters:control_rebilling_update", kwargs={"pk": control.pk})

    assert created.status_code == 302
    assert ControlRebilling.objects.get(name="Essilor").created_by == logged_client.user
    assert logged_client.get(update_url).status_code == 200

    updated = logged_client.post(update_url, {"name": "Hoya", "comment": "à vérifier"})
    control.refresh_from_db()
    assert updated.status_code == 302
    assert control.comment == "à vérifier"


# EXPORTS EXCEL ====================================================================================


@pytest.mark.parametrize(
    ("route", "module", "fallback"),
    [
        ("categories_export_list", categories_views, "parameters:categories_list"),
        ("axe_articles_defaut_export_list", categories_views, None),
        ("functions_export_list", functions_views, "parameters:functions_list"),
        ("numberings_export_list", numberings_views, "parameters:numberings_list"),
        ("natures_export_list", nature_views, "parameters:natures_list"),
        (
            "control_rebilling_export_list",
            control_rebilling_views,
            "parameters:control_rebilling_list",
        ),
    ],
)
def test_exports_excel(logged_client, monkeypatch, make_default_axes, route, module, fallback):
    """L'export renvoie un fichier Excel ; en cas d'erreur il redirige vers la liste"""
    make_default_axes()
    url = reverse(f"parameters:{route}")

    response = logged_client.get(url)

    assert response.status_code == 200
    assert response["Content-Type"] == CONTENT_TYPE_EXCEL
    assert "attachment" in response["Content-Disposition"]

    monkeypatch.setattr(module, "response_file", _boom)
    failed = logged_client.get(url)

    assert failed.status_code == 302
    expected = (
        reverse(fallback)
        if fallback
        else reverse("parameters:axes_articles_defaut", kwargs={"slug_name": "axes_articles"})
    )
    assert failed.url == expected


# SUPPRESSIONS AJAX ================================================================================


@pytest.mark.parametrize(
    "route",
    [
        "delete_sub_category",
        "function_delete",
        "numbering_delete",
        "nature_delete",
        "delete_control_rebilling",
    ],
)
def test_suppressions_refusees_hors_ajax_ou_hors_post(logged_client, ajax_client, route):
    url = reverse(f"parameters:{route}")

    assert logged_client.post(url, {"pk": 1}).url == reverse("home")
    assert ajax_client.get(url).url == reverse("home")


def test_suppression_rubrique(ajax_client, make_sub_category):
    sub = make_sub_category("Montures")
    url = reverse("parameters:delete_sub_category")

    assert ajax_client.post(url, {"pk": sub.pk}).json() == {"success": "success"}
    assert SubCategory.objects.filter(pk=sub.pk).exists() is False
    assert ajax_client.post(url, {"pk": sub.pk}).json() == {"success": "ko"}


def test_suppression_controle(ajax_client, make_control):
    control = make_control()
    url = reverse("parameters:delete_control_rebilling")

    assert ajax_client.post(url, {"pk": control.pk}).json() == {"success": "success"}
    assert ControlRebilling.objects.filter(pk=control.pk).exists() is False
    assert ajax_client.post(url, {"pk": ""}).json() == {"success": "ko"}


def test_suppression_fonction(ajax_client, make_invoice_function):
    function = make_invoice_function("ROYALTIES")
    url = reverse("parameters:function_delete")

    assert ajax_client.post(url, {"pk": function.pk}).json() == {"success": "success"}
    assert InvoiceFunctions.objects.filter(pk=function.pk).exists() is False
    assert ajax_client.post(url, {"pk": function.pk}).json() == {"success": "ko"}


def test_suppression_nature(ajax_client, make_nature):
    nature = make_nature("Madame")
    url = reverse("parameters:nature_delete")

    assert ajax_client.post(url, {"pk": nature.pk}).json() == {"success": "success"}
    assert Nature.objects.filter(pk=nature.pk).exists() is False
    assert ajax_client.post(url, {"pk": 99999}).json() == {"success": "ko"}


def test_suppression_numerotation(ajax_client, make_counter):
    """La numérotation générique ne peut pas être supprimée"""
    generic = make_counter("generic")
    other = make_counter("factures")
    url = reverse("parameters:numbering_delete")

    assert ajax_client.post(url, {"pk": generic.pk}).json() == {"success": "ko"}
    assert Counter.objects.filter(pk=generic.pk).exists()
    assert ajax_client.post(url, {"pk": other.pk}).json() == {"success": "success"}
    assert Counter.objects.filter(pk=other.pk).exists() is False
    assert CounterNums.objects.filter(counter__name="factures").exists() is False
    assert ajax_client.post(url, {"pk": other.pk}).json() == {"success": "ko"}


# TAUX DE CHANGE ===================================================================================


def test_selection_periode_taux(logged_client, monkeypatch, make_country_currency):
    """La sélection d'un mois crée les taux par défaut et redirige vers la liste du mois"""
    make_country_currency("EUR", "Euro")
    url = reverse("parameters:period_select_exchange")
    start = datetime.date.today().replace(day=1)
    end = (start + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1)
    periode = f"{start.isoformat()}_{end.isoformat()}"

    response = logged_client.post(url, {"periode": periode})
    assert response.status_code == 302
    assert response.url == reverse("parameters:exchanges_list", kwargs={"month": start.isoformat()})

    assert logged_client.post(url, {"periode": "n'importe quoi"}).status_code == 200

    monkeypatch.setattr(exchange_rate_views, "set_base_exchange_rate", _boom)
    assert logged_client.post(url, {"periode": periode}).status_code == 200


def test_liste_des_taux_du_mois(logged_client, make_country_currency, make_exchange_rate):
    """Le taux EUR/EUR du mois est créé à l'affichage, une seule fois"""
    make_country_currency("EUR", "Euro")
    make_exchange_rate("CHF", datetime.date(2026, 1, 1), "1.05")
    make_exchange_rate("GBP", datetime.date(2026, 2, 1), "0.85")
    url = reverse("parameters:exchanges_list", kwargs={"month": MONTH})

    response = logged_client.get(url)
    again = logged_client.get(url)

    assert response.status_code == 200
    assert again.status_code == 200
    assert "JANVIER 2026" in response.context["titre_table"]
    assert {rate.currency_change.code for rate in response.context["exchanges"]} == {"CHF", "EUR"}
    assert ExchangeRate.objects.filter(rate_month=MONTH, currency_change="EUR").count() == 1


def test_creation_taux(logged_client, make_country_currency, make_exchange_rate):
    """Création d'un taux, puis re-saisie de la même devise qui modifie le taux existant"""
    make_country_currency("CHF", "Franc suisse")
    url = reverse("parameters:exchange_create", kwargs={"month": MONTH})

    page = logged_client.get(url)
    assert page.status_code == 200
    assert "JANVIER 2026" in page.context["titre_table"]

    created = logged_client.post(url, {"currency_change": "CHF", "rate": "1.05"})
    rate = ExchangeRate.objects.get(currency_change="CHF", rate_month=MONTH)
    assert created.status_code == 302
    assert created.url == reverse("parameters:exchanges_list", kwargs={"month": MONTH})
    assert (rate.rate, rate.curency_base, rate.created_by) == (
        Decimal("1.05"),
        "EUR",
        logged_client.user,
    )

    again = logged_client.post(url, {"currency_change": "CHF", "rate": "0"})
    rate.refresh_from_db()
    assert again.status_code == 302
    assert ExchangeRate.objects.filter(currency_change="CHF").count() == 1
    assert rate.rate == Decimal(1)

    invalid = logged_client.post(url, {"currency_change": "XXX", "rate": "1"})
    assert invalid.status_code == 200
    assert invalid.context["form"].errors


def test_modification_taux(logged_client, make_exchange_rate):
    rate = make_exchange_rate("CHF", datetime.date(2026, 1, 1), "1.05")
    url = reverse("parameters:exchange_update", kwargs={"pk": rate.pk})

    page = logged_client.get(url)
    assert page.status_code == 200
    assert "JANVIER 2026" in page.context["titre_table"]

    updated = logged_client.post(url, {"currency_change": "CHF", "rate": "1.10"})
    rate.refresh_from_db()
    assert updated.status_code == 302
    assert updated.url == reverse("parameters:exchanges_list", kwargs={"month": rate.rate_month})
    assert (rate.rate, rate.rate_month, rate.modified_by) == (
        Decimal("1.10"),
        datetime.date(2026, 1, 1),
        logged_client.user,
    )
