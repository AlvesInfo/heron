# pylint: disable=E0401,W0621,W0611
"""Tests de l'export csv des achats (COPY PostgreSQL)"""
import io
import logging

import pendulum
import pytest

from apps.invoices.bin import export_csv_achats
from apps.invoices.tests.helpers_external import reload_with_node

pytestmark = pytest.mark.django_db
PERIOD = (pendulum.parse("2026-01-01"), pendulum.parse("2026-01-31"))


def test_get_achats(make_invoice, make_purchase_detail, make_cct, make_article, make_society):
    invoice = make_invoice()
    make_purchase_detail(invoice, make_cct("AF0001"))
    make_article(reference="ART-1", society=make_society("FOUR001", is_client=False), famille="MONTURES")
    file_io = io.BytesIO()

    result = export_csv_achats.get_achats(file_io, "achats.csv", *PERIOD)

    assert "OK" in result
    header, line = file_io.getvalue().decode().strip().split("\n")
    assert header.startswith("supplier;invoice_number;cct;code_maison")
    assert line.startswith(f"Fournisseur;{invoice.invoice_number};AF0001")
    assert "MONTURES" in line


def test_get_achats_hors_periode(make_invoice, make_purchase_detail, make_cct, make_article, make_society):
    make_purchase_detail(make_invoice(), make_cct("AF0001"))
    make_article(reference="ART-1", society=make_society("FOUR001", is_client=False))
    file_io = io.BytesIO()

    export_csv_achats.get_achats(file_io, "achats.csv", pendulum.parse("2025-01-01"), pendulum.parse("2025-01-31"))

    assert len(file_io.getvalue().decode().strip().split("\n")) == 1  # entête seule


def test_get_achats_erreur(monkeypatch, caplog):
    class _Connection:
        def cursor(self):
            raise RuntimeError("base indisponible")

    monkeypatch.setattr(export_csv_achats, "connection", _Connection())

    with caplog.at_level(logging.ERROR):
        result = export_csv_achats.get_achats(io.BytesIO(), "achats.csv", *PERIOD)

    assert result == {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}
    assert "achats.csv" in caplog.text


@pytest.mark.parametrize(("node", "expected"), [("MSI", r"C:\SitesWeb\heron"), ("serveur", "/home/paulo/heron")])
def test_base_dir_selon_la_machine(monkeypatch, node, expected):
    assert reload_with_node(monkeypatch, export_csv_achats, node) == expected
