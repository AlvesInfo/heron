"""Tests d'accessibilité des gabarits : une action au clic est portée par un élément natif"""

import re
from pathlib import Path

from apps.core.functions.functions_setups import settings

TAG = re.compile(
    r"<([a-zA-Z][a-zA-Z0-9]*)\b((?:[^<>\"'`]|\"[^\"]*\"|'[^']*'|`[^`]*`)*)>", re.DOTALL
)
NATIVE = {"button", "input", "select", "textarea", "option", "summary", "body", "form"}


def html_tags():
    """Toutes les balises ouvrantes des gabarits html du projet : (gabarit, balise, attributs)"""
    base_dir = Path(settings.BASE_DIR)

    for root in (Path(settings.APPS_DIR), Path(settings.PROJECT_DIR)):
        for template in root.rglob("*.html"):
            source = template.read_text(encoding="utf8", errors="ignore")

            for match in TAG.finditer(source):
                yield str(template.relative_to(base_dir)), match.group(1).lower(), match.group(2)


def test_aucun_element_non_interactif_ne_porte_de_clic():
    """Une icône ou un bloc cliquable est inaccessible au clavier : on utilise un bouton natif"""
    offenders = sorted(
        {
            template
            for template, tag, attrs in html_tags()
            if re.search(r"\bonclick\s*=", attrs)
            and tag not in NATIVE
            and not (tag == "a" and re.search(r"\bhref\s*=", attrs))
        }
    )

    assert offenders == []


def test_aucun_role_bouton_a_la_place_d_un_bouton_natif():
    offenders = sorted(
        {template for template, _, attrs in html_tags() if re.search(r"\brole=.button", attrs)}
    )

    assert offenders == []


def test_les_boutons_de_suppression_gardent_l_icone_corbeille():
    """Le bouton natif est transparent et sans bordure : seule l'icône corbeille rouge s'affiche"""
    button = re.compile(
        r'<button type="button" style="background: none; border: 0; padding: 0; margin: 0; '
        r'cursor: pointer; color: inherit; font: inherit;" aria-label="Supprimer"\s+'
        r'onclick="[^"]*"><i class="red trash icon" aria-hidden="true"></i></button>'
    )
    count = 0

    for root in (Path(settings.APPS_DIR), Path(settings.PROJECT_DIR)):
        for template in root.rglob("*.html"):
            source = template.read_text(encoding="utf8", errors="ignore")
            assert len(button.findall(source)) == source.count("red trash icon"), template.name
            count += source.count("red trash icon")

    assert count > 0
