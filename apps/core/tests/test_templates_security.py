"""Tests de l'échappement dans les gabarits : plus de filtre safe sur des données, les filtres à


liste blanche n'acceptent que la mise en forme écrite par le code
"""

import json
import re
from pathlib import Path

import pytest
from django.template import Context, Template
from django.urls import reverse

from apps.core.functions.functions_setups import settings

pytestmark = pytest.mark.django_db

# Texte riche saisi par les administrateurs dans l'éditeur des centrales et des enseignes : le html
# est voulu, il est rendu dans les factures pdf
RICH_TEXT_TEMPLATES = {
    "apps/invoices/templates/invoices/pdf_generic_mentions_legales.html",
    "apps/invoices/templates/invoices/pdf_generic_footer_invoices.html",
    "apps/invoices/templates/invoices/pdf_summary.html",
}
HOSTILE = "</script><script>alert(1)</script>"


def render(source, **context):
    """Rendu d'un gabarit qui charge les filtres du projet"""
    return Template("{% load filters_tags %}" + source).render(Context(context))


def html_templates():
    """Tous les gabarits html du projet, en chemin relatif à la racine"""
    base_dir = Path(settings.BASE_DIR)

    for root in (Path(settings.APPS_DIR), Path(settings.PROJECT_DIR)):
        for template in root.rglob("*.html"):
            yield (
                str(template.relative_to(base_dir)),
                template.read_text(encoding="utf8", errors="ignore"),
            )


def test_seuls_les_textes_riches_des_pdf_utilisent_le_filtre_safe():
    offenders = {name for name, source in html_templates() if re.search(r"\|\s*safe\b", source)}

    assert offenders == RICH_TEXT_TEMPLATES


def test_aucun_gabarit_html_ne_desactive_l_echappement():
    """Les emails en texte brut portent l'extension .txt, les gabarits html échappent toujours"""
    offenders = [name for name, source in html_templates() if "autoescape off" in source]

    assert offenders == []


def test_keep_br_conserve_les_sauts_de_ligne_et_echappe_le_reste():
    assert render("{{ value|keep_br }}", value="Janvier<br>2026") == "Janvier<br>2026"
    assert render("{{ value|keep_br }}", value="A & B<br><b>x</b>") == (
        "A &amp; B<br>&lt;b&gt;x&lt;/b&gt;"
    )
    assert render("{{ value|keep_br }}", value=None) == ""


def test_trace_comment_conserve_la_mise_en_forme_des_imports():
    comment = (
        "Les ensembles (<div style='padding-left: 20px;'>F1 - 2026,<br>F2 - 2026"
        "</div>) ont dèjà été importés.<br>"
    )

    assert render("{{ value|trace_comment }}", value=comment) == (
        'Les ensembles (<div style="padding-left: 20px;">F1 - 2026,<br>F2 - 2026'
        "</div>) ont dèjà été importés.<br>"
    )


def test_trace_comment_echappe_les_donnees_des_fichiers():
    """Un numéro de facture hostile dans un fichier fournisseur n'est pas interprété"""
    rendered = render("{{ value|trace_comment }}", value=f"Facture {HOSTILE}<br>rejetée")

    assert "<script>" not in rendered
    assert rendered == ("Facture &lt;/script&gt;&lt;script&gt;alert(1)&lt;/script&gt;<br>rejetée")
    assert render("{{ value|trace_comment }}", value=None) == ""


def test_filtres_de_recherche_non_injectables_dans_le_script(logged_client):
    """Les paramètres de l'url sont transmis au script en json, jamais écrits bruts dans la page"""
    response = logged_client.get(
        reverse("articles:articles_search_list"), {"reference__icontains": HOSTILE}
    )
    content = response.content.decode()
    data = re.search(
        r'<script id="attrs_filter_data" type="application/json">(.*?)</script>', content
    )

    assert response.status_code == 200
    assert HOSTILE not in content
    assert json.loads(data.group(1)) == {"reference__icontains": HOSTILE}
    assert '11. Recherche Articles<span style="font-size: .8em;">' in content


def test_page_sans_filtre_sans_donnees_de_filtre(logged_client):
    content = logged_client.get(reverse("invoices:export_x3_files")).content.decode()

    assert 'id="attrs_filter_data"' not in content
    assert "let attrsFilter = (function (data) {" in content


def test_tri_du_tableau_ecrit_a_partir_de_donnees(logged_client):
    """Le tri de la liste des fichiers X3 est décrit par des données, le gabarit écrit le script"""
    content = logged_client.get(reverse("invoices:export_x3_files")).content.decode()

    assert "\"order\": [[ 1, 'desc' ],]," in content


def test_tableau_sans_tri_particulier():
    rendered = Template('{% include "heron/base_data_table.html" %}').render(Context({}))

    assert '"order"' not in rendered
