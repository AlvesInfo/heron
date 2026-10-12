# pylint: disable=E0401,W0621
"""
FR : Tests des exports Excel de l'app articles
EN : Tests for articles Excel exports

created at: 2026-10-10
created by: Paulo ALVES
"""
import io
import logging

import pytest

from apps.articles.excel_outputs import (
    output_excel_articles_account_supplier_list,
    output_excel_articles_list,
    output_excel_articles_news_list,
    output_excel_articles_without_account_list,
)
from apps.articles.excel_outputs.output_excel_articles_columns import (
    columns_list_articles,
    columns_list_articles_news,
    columns_list_articles_without_account,
)
from apps.core.excel_outputs import generic_list_export
from conftest import patched_attrs

pytestmark = pytest.mark.django_db


@pytest.fixture
def catalogue(make_article, make_society, make_big_category, make_sub_category, make_section, make_article_account):
    """Un fournisseur avec deux articles, dont un avec comptes"""
    four = make_society("FOUR001", is_client=False, short_name="Fournisseur")
    marchandises = make_big_category("Marchandises")
    article = make_article(
        "MONT-1", society=four, big_category=marchandises, libelle="Monture", libelle_heron="Monture Héron",
        axe_pro=make_section("PRO", "OPT"), new_article=True, customs_code="9003",
        sub_category=make_sub_category("Montures", big_category=marchandises),
    )
    make_article("VERRE-1", society=four, big_category=marchandises, libelle="Verre", error_sub_category=True)
    make_article_account(article=article, child_center="ACF", vat="001")
    make_article_account(article=article, child_center="GAF", vat="001")
    return {"society": four, "category": marchandises, "article": article}


# LIGNES ===========================================================================================


def test_lignes_articles(catalogue):
    """Export des articles d'un fournisseur et d'une catégorie (SQL direct)"""
    rows = output_excel_articles_list.get_clean_rows("FOUR001", catalogue["category"].slug_name)

    assert len(rows) == 2
    assert len(rows[0]) == len(columns_list_articles)
    by_reference = {row[0]: row for row in rows}
    assert by_reference["MONT-1"][2] == "Monture Héron"
    assert by_reference["MONT-1"][11] == "OPT"
    assert by_reference["MONT-1"][16] == "X"
    assert by_reference["VERRE-1"][16] == ""
    assert output_excel_articles_list.get_clean_rows("FOUR001", "inconnue") == []


@pytest.mark.usefixtures('catalogue')
def test_lignes_nouveaux_articles():
    """Nouveaux articles et articles en erreur de rubrique, tiers libellé 'code - nom court'"""
    rows = output_excel_articles_news_list.get_clean_rows()

    assert len(rows) == 2
    assert len(rows[0]) == len(columns_list_articles_news)
    by_reference = {row[1]: row for row in rows}
    assert by_reference["MONT-1"][0] == "FOUR001 - Fournisseur"
    assert by_reference["MONT-1"][5] == "OPT"
    assert by_reference["MONT-1"][9] == "Montures"
    assert by_reference["MONT-1"][13] == ""
    assert by_reference["VERRE-1"][13] == "X"


@pytest.mark.usefixtures('catalogue')
def test_lignes_articles_avec_comptes_par_fournisseur():
    """Les comptes du fournisseur, hors centrale GAF"""
    rows = output_excel_articles_account_supplier_list.get_clean_rows("FOUR001")

    assert len(rows) == 1
    assert len(rows[0]) == len(columns_list_articles_without_account)
    assert rows[0][1] == "ACF"
    assert rows[0][4] == "MONT-1"
    assert rows[0][8] == "Montures"
    assert rows[0][11:] == ("607000", "707000")
    assert output_excel_articles_account_supplier_list.get_clean_rows("AUTRE") == []


def test_lignes_articles_sans_comptes(make_edi_import, make_article, make_society, make_section, make_big_category):
    """Lignes EDI dont l'article n'a pas de compte pour la centrale / tva"""
    four = make_society("FOUR001", is_client=False, short_name="Fournisseur")
    pro = make_section("PRO", "OPT")
    category = make_big_category("Marchandises")
    make_article("ART-1", society=four, libelle="Monture", axe_pro=pro, big_category=category)
    make_edi_import("FOUR001", "ART-1", axe_pro=pro, big_category=category, vat=make_section.__self__ if False else None)

    rows = output_excel_articles_without_account_list.get_clean_rows()

    assert len(rows) == 1
    assert rows[0][1:9] == ("ACF", "FOUR001", "Fournisseur", "ART-1", "Monture", "OPT", "Marchandises", "")
    assert rows[0][11:] == ("", "")


def test_lignes_articles_sans_comptes_vide():
    """Sans import EDI, aucune ligne"""
    assert output_excel_articles_without_account_list.get_clean_rows() == []


# FICHIERS =========================================================================================


def test_generation_excel_articles(catalogue):
    """Export des articles d'un fournisseur / catégorie : titre construit depuis le nom de fichier"""
    file_io = io.BytesIO()

    result = output_excel_articles_list.excel_liste_articles(
        file_io, "LISTING_DES_ARTICLES_2026_10_10_1.xlsx", "FOUR001", catalogue["category"].slug_name
    )

    assert result == {"OK": "GENERATION DU FICHIER LISTING_DES_ARTICLES_2026_10_10_1.xlsx TERMINEE AVEC SUCCES"}
    assert file_io.getvalue()[:2] == b"PK"


def test_generation_excel_articles_en_erreur(catalogue, monkeypatch, caplog):
    """Erreur d'écriture : KO journalisé"""

    def _boom(*_args, **_kwargs):
        raise RuntimeError("écriture")

    with patched_attrs(monkeypatch, generic_list_export, titre_page_writer=_boom), patched_attrs(monkeypatch, output_excel_articles_list, titre_page_writer=_boom), caplog.at_level(logging.ERROR, logger="export_excel"):
        result = output_excel_articles_list.excel_liste_articles(io.BytesIO(), "LISTING_DES_ARTICLES_2026_10_10_1.xlsx", "FOUR001", catalogue["category"].slug_name)

    assert result == {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}
    assert "LISTING_DES_ARTICLES" in caplog.text


@pytest.mark.parametrize(
    ("module", "function_name", "args"),
    [
        (output_excel_articles_news_list, "excel_liste_articles_news", ()),
        (output_excel_articles_without_account_list, "excel_liste_articles_without_account", ()),
        (output_excel_articles_account_supplier_list, "excel_liste_articles_account_supplier", ("FOUR001",)),
    ],
)
@pytest.mark.usefixtures('catalogue')
def test_generation_excel(module, function_name, args, monkeypatch, caplog):
    """Chaque export génère un xlsx et renvoie OK, puis KO en cas d'erreur d'écriture"""
    file_io = io.BytesIO()

    assert getattr(module, function_name)(file_io, "export.xlsx", *args) == {"OK": "GENERATION DU FICHIER export.xlsx TERMINEE AVEC SUCCES"}
    assert file_io.getvalue()[:2] == b"PK"

    def _boom(*_args, **_kwargs):
        raise RuntimeError("écriture")

    with patched_attrs(monkeypatch, generic_list_export, titre_page_writer=_boom), patched_attrs(monkeypatch, module, titre_page_writer=_boom), caplog.at_level(logging.ERROR, logger="export_excel"):
        assert getattr(module, function_name)(io.BytesIO(), "export.xlsx", *args) == {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}

    assert "export.xlsx" in caplog.text


def test_definition_des_colonnes():
    """Chaque colonne a un entête, des formats et une largeur"""
    for columns in (columns_list_articles, columns_list_articles_news, columns_list_articles_without_account):
        assert all({"entete", "f_entete", "f_ligne", "width"} <= set(column) for column in columns)
