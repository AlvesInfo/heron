# pylint: disable=W0621,E0401,R0913,C0415
"""FR : conftest de l'app articles - fabriques des articles, comptes, imports EDI et table B.I


EN : articles app conftest - factories for articles, accounts, EDI imports and B.I table

Commentaire:

Les référentiels partagés (make_article, make_society, make_big_category, make_section, make_vat,
make_account, make_child_center, make_maison, ...) viennent du conftest racine.

created at: 2026-10-10
created by: Paulo ALVES
"""

import types
from collections.abc import Callable
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from django.db import connection

from conftest import next_code

BI_ARTICLES_COLUMNS = {
    "code_ean": "text",
    "designation": "text",
    "marque": "text",
    "poids": "numeric",
    "fabricant": "text",
    "code_douanier": "text",
    "px_revient_aval": "numeric",
    "px_cession_ht_eur": "numeric",
    "famille": "text",
    "made_in": "text",
    "code_rayon": "text",
}


@pytest.fixture
def default_sections(make_section) -> dict[str, Any]:
    """Sections par défaut posées par Article.save() : BU/CAHA, PRJ/NAF, PYS/FR, RFA/NAF, et PRO/DIV"""
    return {
        "BU": make_section("BU", "CAHA"),
        "PRJ": make_section("PRJ", "NAF"),
        "PYS": make_section("PYS", "FR"),
        "RFA": make_section("RFA", "NAF"),
        "PRO": make_section("PRO", "DIV"),
    }


@pytest.fixture
def bi_articles_table(make_society, make_country) -> Callable[..., None]:
    """Crée la table B.I heron_bi_articles (FDW en production) dans la transaction de test,

    les tiers BBGR002/003/004/006, les pays FR et CN, et retourne une fonction d'insertion
    """
    for code in ("BBGR002", "BBGR003", "BBGR004", "BBGR006"):
        make_society(code, is_client=False)

    make_country("FR", "France")
    make_country("CN", "Chine")

    ddl = ", ".join(f"{name} {kind}" for name, kind in BI_ARTICLES_COLUMNS.items())

    with connection.cursor() as cursor:
        cursor.execute(f"create table heron_bi_articles ({ddl})")

    def _insert(**values: Any) -> None:
        row = {
            "code_ean": next_code("EAN"),
            "designation": "Monture",
            "marque": "Marque",
            "poids": Decimal("0.5"),
            "fabricant": "Fabricant",
            "code_douanier": "9003",
            "px_revient_aval": Decimal(10),
            "px_cession_ht_eur": Decimal(20),
            "famille": "LUNETTES",
            "made_in": "France",
            "code_rayon": "OPT",
        }
        row.update(values)
        placeholders = ", ".join(f"%({name})s" for name in row)

        with connection.cursor() as cursor:
            cursor.execute(
                f"insert into heron_bi_articles ({', '.join(row)}) values ({placeholders})", row
            )

    return _insert


@pytest.fixture
def articles_dirs(tmp_path: Path, settings) -> types.SimpleNamespace:
    """Redirige les répertoires d'import/backup des comptes articles vers tmp_path"""
    dirs = types.SimpleNamespace(
        without_account=tmp_path / "sans_comptes",
        without_account_backup=tmp_path / "backup_sans_comptes",
        update_accounts=tmp_path / "update_comptes",
        update_accounts_backup=tmp_path / "backup_update_comptes",
    )

    for directory in vars(dirs).values():
        directory.mkdir(parents=True, exist_ok=True)

    settings.PROCESSING_WITHOUT_ACCOUNT_DIR = dirs.without_account
    settings.BACKUP_WITHOUT_ACCOUNT_DIR = dirs.without_account_backup
    settings.PROCESSING_UPDATE_ARTICLES_ACCOUNTS_DIR = dirs.update_accounts
    settings.BACKUP_UPDATE_ARTICLES_ACCOUNTS_DIR = dirs.update_accounts_backup
    return dirs


@pytest.fixture
def fake_make_insert(monkeypatch) -> tuple[list[dict[str, Any]], dict[str, bool]]:
    """Doublure de data_flux.make_insert pour les deux modules d'import des comptes articles"""
    from apps.articles.imports import articles_update_account, articles_without_account

    calls: list[dict[str, Any]] = []
    state = {"errors": False}

    def _recorder(model, flow_name, source, trace, validator, params_dict_loader, **kwargs):
        calls.append(
            {
                "model": model,
                "flow_name": flow_name,
                "source": source,
                "trace": trace,
                "validator": validator,
                "params": params_dict_loader,
                **kwargs,
            }
        )
        trace.errors = state["errors"]
        trace.save()
        return f"Import : {flow_name}"

    monkeypatch.setattr(articles_without_account, "make_insert", _recorder)
    monkeypatch.setattr(articles_update_account, "make_insert", _recorder)
    return calls, state


@pytest.fixture
def article_post_data(
    make_society, make_big_category, make_unit, make_country, default_sections
) -> dict[str, str]:
    """Données POST valides pour ArticleForm"""
    make_society("FOUR001", is_client=False)
    category = make_big_category("Marchandises")
    make_unit(1, "U")
    make_country("FR")
    return {
        "third_party_num": "FOUR001",
        "big_category": str(category.uuid_identification),
        "reference": "REF-001",
        "libelle": "Monture test",
        "libelle_heron": "Monture Héron",
        "item_weight": "0.5",
        "unit_weight": "1",
        "packaging_qty": "1",
        "catalog_price": "100",
        "customs_item_weight": "0",
        "customs_unit_weight": "1",
        "axe_pro": str(default_sections["PRO"].uuid_identification),
        "made_in": "FR",
    }
