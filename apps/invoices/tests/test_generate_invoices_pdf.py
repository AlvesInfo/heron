# pylint: disable=E0401,W0621,W0611
"""FR : Tests de l'orchestrateur de génération des PDF de factures (sommaire + factures fusionnés)


EN : Tests for the invoice PDF generation orchestrator

created at: 2026-10-10
created by: Paulo ALVES
"""

import importlib
import logging
import platform
import sys
import types
from pathlib import Path

import pytest
from django_celery_results.models import TaskResult

from apps.data_flux.models import Trace
from apps.invoices.bin import generate_invoices_pdf
from apps.invoices.bin.generate_invoices_pdf import (
    get_invoices_in_progress,
    invoices_pdf_generation,
)
from apps.invoices.models import SaleInvoice
from apps.invoices.tests.helpers_pdf import page_count, write_minimal_pdf
from conftest import patched_attrs

pytestmark = pytest.mark.django_db

FULL = "AF0001_000000000001_full.pdf"


@pytest.fixture
def fake_generators(monkeypatch):
    """Remplace les générateurs par catégorie par des écrivains de PDF minimal et journalise"""
    calls = []

    def generator(name):
        def _generate(uuid_invoice, pdf_path):
            calls.append((name, uuid_invoice, Path(pdf_path).name))
            write_minimal_pdf(pdf_path, name)

        return _generate

    def summary(cct, pdf_path):
        calls.append(("summary", cct, Path(pdf_path).name))
        write_minimal_pdf(pdf_path, "summary")

    names = [
        "invoice_marchandise_pdf",
        "rfa_invoice_pdf",
        "invoice_royalties_pdf",
        "invoice_publicity_pdf",
        "invoice_prestation_pdf",
        "invoice_formation_pdf",
        "invoice_staff_pdf",
        "invoice_material_pdf",
        "invoice_various_pdf",
    ]
    with patched_attrs(
        monkeypatch,
        generate_invoices_pdf,
        summary_invoice_pdf=summary,
        **{name: generator(name) for name in names},
    ):
        yield calls


def test_invoices_pdf_generation(sales_dir, fake_generators, make_sale_invoice):
    """Sommaire + une facture par catégorie connue, fusion, nettoyage et flag printed"""
    marchandises = make_sale_invoice(
        global_invoice_file=FULL, big_category_slug_name="marchandises", big_category_ranking=1
    )
    rfa = make_sale_invoice(
        global_invoice_file=FULL, big_category_slug_name="rfa", big_category_ranking=2
    )
    inconnue = make_sale_invoice(
        global_invoice_file=FULL, big_category_slug_name="inconnue", big_category_ranking=3
    )
    deja_imprimee = make_sale_invoice(global_invoice_file=FULL, printed=True)
    autre_fichier = make_sale_invoice(global_invoice_file="AUTRE_full.pdf")

    trace, to_print = invoices_pdf_generation("AF0001", FULL)

    assert trace.errors is False
    assert trace.file_name == f"Generate pdf : {FULL}"
    assert to_print == f"have generate pdf : {FULL} - "
    assert [call[0] for call in fake_generators] == [
        "summary",
        "invoice_marchandise_pdf",
        "rfa_invoice_pdf",
    ]
    assert fake_generators[1][1] == marchandises.uuid_identification
    assert fake_generators[1][2] == f"AF0001_marchandises_{marchandises.invoice_number}.pdf"
    merged = sales_dir / FULL
    assert page_count(merged) == 3
    assert sorted(path.name for path in sales_dir.iterdir() if path.is_file()) == [FULL]
    printed = dict(SaleInvoice.objects.values_list("pk", "printed"))
    assert printed[marchandises.pk]
    assert printed[rfa.pk]
    assert printed[inconnue.pk]
    assert printed[deja_imprimee.pk] is True
    assert printed[autre_fichier.pk] is False


@pytest.mark.usefixtures("sales_dir", "fake_generators")
def test_invoices_pdf_generation_erreur(make_sale_invoice, monkeypatch, caplog):
    """Une exception trace l'erreur et ne marque rien comme imprimé"""
    sale = make_sale_invoice(global_invoice_file=FULL)

    def boom(cct, pdf_path):
        raise RuntimeError("summary KO")

    with (
        patched_attrs(monkeypatch, generate_invoices_pdf, summary_invoice_pdf=boom),
        caplog.at_level(logging.ERROR),
    ):
        trace, to_print = invoices_pdf_generation("AF0001", FULL)

    assert trace.errors is True
    assert "Une erreur c'est produite" in trace.comment
    assert to_print == ""
    assert "summary KO" in caplog.text
    sale.refresh_from_db()
    assert sale.printed is False
    assert Trace.objects.count() == 1


@pytest.mark.usefixtures("make_user")
def test_get_invoices_in_progress():
    for task_name, status in [
        ("invoices_insertions_launch", "STARTED"),
        ("launch_generate_pdf_invoices", "SUCCESS"),
        ("send_invoice_email", "STARTED"),
    ]:
        TaskResult.objects.create(
            task_id=f"{task_name}-{status}", task_name=task_name, status=status
        )

    assert get_invoices_in_progress() == (True, False, True)


@pytest.mark.parametrize(("node", "expected"), [("MSI", "/"), ("serveur", "/home/paulo/heron")])
def test_base_dir_selon_la_machine(monkeypatch, node, expected):
    monkeypatch.setattr(sys, "path", list(sys.path))

    try:
        with patched_attrs(monkeypatch, platform, uname=lambda: types.SimpleNamespace(node=node)):
            assert expected == importlib.reload(generate_invoices_pdf).BASE_DIR
    finally:
        importlib.reload(generate_invoices_pdf)


@pytest.mark.integration
@pytest.mark.usefixtures("pdf_domain")
def test_invoices_pdf_generation_reelle(sales_dir, make_sale_with_lines):
    """Chaîne réelle WeasyPrint : sommaire + facture de marchandises fusionnés"""
    sale = make_sale_with_lines(
        [{"vat": "001"}, {"vat": "002", "axe": "VER"}], global_invoice_file=FULL
    )

    trace, _ = invoices_pdf_generation(sale.cct_id, FULL)

    assert trace.errors is False
    assert page_count(sales_dir / FULL) >= 5
