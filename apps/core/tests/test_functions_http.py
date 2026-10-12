"""Tests des fonctions http : détection ajax (remplaçant de HttpRequest.is_ajax, supprimé dans
Django 4) et boutons de pagination"""
from pathlib import Path

import pytest
from django.template import Context, Template
from django.test import RequestFactory
from django.utils.safestring import SafeData

from apps.core.functions.functions_http import get_pagination_buttons, is_ajax
from apps.core.functions.functions_setups import settings


@pytest.mark.parametrize(
    ("headers", "expected"),
    [
        ({"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}, True),
        ({"HTTP_X_REQUESTED_WITH": "xmlhttprequest"}, True),
        ({"HTTP_X_REQUESTED_WITH": "fetch"}, False),
        ({}, False),
    ],
)
def test_is_ajax(headers, expected):
    request = RequestFactory().get("/", **headers)

    assert is_ajax(request) is expected


def test_is_ajax_post_sans_entete():
    assert is_ajax(RequestFactory().post("/", {"a": "1"})) is False


def test_aucun_appel_a_is_ajax_django_ne_subsiste():
    """La méthode HttpRequest.is_ajax() disparaît en Django 4 : plus aucun appel dans le code"""
    import subprocess  # pylint: disable=C0415

    result = subprocess.run(
        ["grep", "-rln", "--include=*.py", r"\.is_ajax()", "apps", "heron"],
        capture_output=True, text=True, check=False,
    )
    offenders = [line for line in result.stdout.split() if "/tests/" not in line]

    assert offenders == []


ACTIVE = '<div class="ui button pagination"  style="background-color: {color};">{label}</div>\n'
LINK = (
    '<div class="ui button pagination" onclick="paginateWithFilter({page})" '
    'style="background-color: {color};">{label}</div>\n'
)
LEFT = '<i class="angle double left icon"></i>'
RIGHT = '<i class="angle double right icon"></i>'


def render(pagination):
    """Rendu de la pagination dans un template, sans le filtre safe"""
    return Template("{{ pagination }}").render(Context({"pagination": pagination}))


def test_pagination_une_seule_page():
    assert get_pagination_buttons(1, 1) == ""


def test_pagination_toutes_les_pages_tiennent():
    pagination = get_pagination_buttons(2, 3, nbre_boutons=5, position_color="cadetblue")

    assert isinstance(pagination, SafeData)
    assert render(pagination) == (
        LINK.format(page=1, color="#FFFFFF", label=1)
        + ACTIVE.format(color="cadetblue", label=2)
        + LINK.format(page=3, color="#FFFFFF", label=3)
    )


def test_pagination_fenetre_au_milieu_avec_les_deux_fleches():
    pagination = get_pagination_buttons(10, 30, nbre_boutons=5, position_color="cadetblue")

    assert render(pagination) == (
        LINK.format(page=1, color="#FFFFFF", label=LEFT)
        + LINK.format(page=8, color="#FFFFFF", label=8)
        + LINK.format(page=9, color="#FFFFFF", label=9)
        + ACTIVE.format(color="cadetblue", label=10)
        + LINK.format(page=11, color="#FFFFFF", label=11)
        + LINK.format(page=12, color="#FFFFFF", label=12)
        + LINK.format(page=30, color="#FFFFFF", label=RIGHT)
    )


def test_pagination_premiere_page_sans_fleche_gauche():
    rendered = render(get_pagination_buttons(1, 30, nbre_boutons=5))

    assert LEFT not in rendered
    assert rendered.startswith(ACTIVE.format(color="blue", label=1))
    assert rendered.endswith(LINK.format(page=30, color="#FFFFFF", label=RIGHT))


def test_pagination_derniere_page_sans_fleche_droite():
    rendered = render(get_pagination_buttons(30, 30, nbre_boutons=5))

    assert RIGHT not in rendered
    assert rendered.startswith(LINK.format(page=1, color="#FFFFFF", label=LEFT))
    assert rendered.endswith(ACTIVE.format(color="blue", label=30))
    assert LINK.format(page=26, color="#FFFFFF", label=26) in rendered


def test_pagination_nombre_de_boutons_pair_arrondi_a_l_impair():
    rendered = render(get_pagination_buttons(10, 30, nbre_boutons=4))

    assert rendered.count("ui button pagination") == 7


def test_pagination_echappe_les_valeurs_non_sures():
    """Une valeur non construite par format_html ne peut pas injecter de balise"""
    rendered = render(
        get_pagination_buttons(
            10, 30, nbre_boutons=5, base_color='"><script>x</script>', icon_left="<b>g</b>"
        )
    )

    assert "<script>" not in rendered
    assert "<b>g</b>" not in rendered
    assert "&lt;b&gt;g&lt;/b&gt;" in rendered


def test_aucun_template_n_affiche_la_pagination_avec_le_filtre_safe():
    """La pagination est déjà un html sûr : le filtre safe masquerait un défaut d'échappement"""
    roots = (Path(settings.APPS_DIR), Path(settings.PROJECT_DIR))
    offenders = [
        str(template)
        for root in roots
        for template in root.rglob("*.html")
        if "pagination|safe" in template.read_text(encoding="utf8", errors="ignore").replace(" ", "")
    ]

    assert offenders == []
