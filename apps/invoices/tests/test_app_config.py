"""Tests de la configuration de l'app invoices et de ses paquets"""
import importlib

from django.apps import apps


def test_app_config():
    config = apps.get_app_config("invoices")

    assert config.name == "apps.invoices"


def test_paquets_importables():
    for name in [
        "apps.invoices.admin", "apps.invoices.forms", "apps.invoices.bin.columns",
        "apps.invoices.sql_files.sql_invoices_insertions", "apps.invoices.sql_files.sql_controls",
        "apps.invoices.sql_files.sql_subscriptions", "apps.invoices.sql_files.sql_marchandises",
        "apps.invoices.sql_files.sql_rfa", "apps.invoices.sql_files.sql_material",
        "apps.invoices.sql_files.sql_prestation", "apps.invoices.sql_files.sql_publicity",
        "apps.invoices.sql_files.sq_royalties", "apps.invoices.sql_files.sql_various",
        "apps.invoices.sql_files.sql_staff", "apps.invoices.sql_files.sql_formation",
    ]:
        assert importlib.import_module(name)


def test_colonnes_insertion():
    from apps.invoices.bin.columns import COLS_PURCHASE_DICT, COL_SALES_DICT

    assert list(COLS_PURCHASE_DICT)[5] == "invoice_sage_number"
    assert list(COL_SALES_DICT)[5] == "invoice_number"
    assert not any(COLS_PURCHASE_DICT.values())
    assert not any(COL_SALES_DICT.values())


def test_domaine_des_statiques_pdf(settings):
    """Le domaine des polices et logos des PDF vient des réglages (PDF_STATIC_DOMAIN)"""
    from apps.invoices.bin import pdf_marchandises

    assert settings.PDF_STATIC_DOMAIN.startswith("http")
    assert pdf_marchandises.settings.PDF_STATIC_DOMAIN == settings.PDF_STATIC_DOMAIN
