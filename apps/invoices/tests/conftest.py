# pylint: disable=E0401,W0621,C0415
"""FR : Fabriques et fixtures propres aux tests de l'app invoices (factures achats / ventes,


     éléments de facturation, exports X3, répertoires de fichiers)
EN : Fixtures for invoices app tests

created at: 2026-10-10
created by: Paulo ALVES
"""

import datetime
import types
from collections.abc import Callable
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest

from conftest import next_code

INVOICE_DATE = datetime.date(2026, 1, 31)


@pytest.fixture
def invoices_dirs(tmp_path: Path, settings) -> types.SimpleNamespace:
    """Redirige les répertoires de l'app invoices (pdf des ventes, Factur-X, exports X3, media)

    vers tmp_path : les FileField (upload_to) et les générateurs n'écrivent jamais dans files/.
    """
    dirs = types.SimpleNamespace(
        media=tmp_path / "media",
        sales=tmp_path / "media" / "sales_invoices",
        facturx=tmp_path / "media" / "sales_invoices" / "facturx",
        processing_facturx=tmp_path / "processing" / "facturx",
        export=tmp_path / "media" / "export",
    )

    for directory in vars(dirs).values():
        directory.mkdir(parents=True, exist_ok=True)

    settings.MEDIA_ROOT = str(dirs.media)
    settings.SALES_INVOICES_FILES_DIR = dirs.sales
    settings.SALES_INVOICES_FACTURX_DIR = dirs.facturx
    settings.PROCESSING_FACTURX_DIR = dirs.processing_facturx
    settings.EXPORT_DIR = dirs.export
    return dirs


@pytest.fixture
def make_invoice(make_society) -> Callable[..., Any]:
    """Fabrique de factures d'achat invoices.Invoice"""
    from apps.invoices.models import Invoice

    def _factory(third_party_num: str = "FOUR001", **kwargs: Any):
        defaults = {
            "invoice_sage_number": next_code("ACH"),
            "invoice_number": next_code("FAC"),
            "invoice_date": INVOICE_DATE,
            "invoice_month": INVOICE_DATE.replace(day=1),
            "invoice_year": INVOICE_DATE.year,
            "invoice_type": "380",
            "invoice_type_name": "Facture",
            "devise": "EUR",
            "invoice_amount_without_tax": Decimal(100),
            "invoice_amount_tax": Decimal(20),
            "invoice_amount_with_tax": Decimal(120),
            "vat_regime": "FRA",
            "cpy": "ACF",
            "fcy": "ACF",
        }
        defaults.update(kwargs)
        return Invoice.objects.create(
            third_party_num=make_society(third_party_num, is_client=False), **defaults
        )

    return _factory


@pytest.fixture
def make_invoice_detail(make_invoice) -> Callable[..., Any]:
    """Fabrique de lignes invoices.InvoiceDetail"""
    from apps.invoices.models import InvoiceDetail

    def _factory(invoice=None, **kwargs: Any):
        defaults = {
            "import_uuid_identification": uuid4(),
            "axe_bu": "CAHA",
            "axe_prj": "NAF",
            "axe_pro": "OPT",
            "axe_rfa": "NAF",
            "axe_pys": "FR",
            "vat": "001",
            "vat_rate": Decimal("0.2"),
            "vat_regime": "FRA",
            "big_category": "Marchandises",
            "account": "607000",
            "flow_name": "Widex",
            "gross_unit_price": Decimal(100),
            "net_unit_price": Decimal(100),
            "gross_amount": Decimal(100),
            "net_amount": Decimal(100),
            "vat_amount": Decimal(20),
            "amount_with_vat": Decimal(120),
        }
        defaults.update(kwargs)
        return InvoiceDetail.objects.create(uuid_invoice=invoice or make_invoice(), **defaults)

    return _factory


@pytest.fixture
def make_entete_details(db) -> Callable[..., Any]:  # pylint: disable=W0613
    """Fabrique idempotente de invoices.EnteteDetails (entêtes de regroupement des détails)"""
    from apps.invoices.models import EnteteDetails

    def _factory(column_name: str = "Montures", ranking: int = 1):
        return EnteteDetails.objects.get_or_create(
            column_name=column_name, defaults={"ranking": ranking}
        )[0]

    return _factory


@pytest.fixture
def make_axes_details(make_entete_details, make_section) -> Callable[..., Any]:
    """Fabrique de invoices.AxesDetails (axe pro -> entête de détail)"""
    from apps.invoices.models import AxesDetails

    def _factory(section: str = "OPT", column_name: str = "Montures"):
        return AxesDetails.objects.create(
            axe_pro=make_section("PRO", section), column_name=make_entete_details(column_name)
        )

    return _factory


@pytest.fixture
def make_export_x3(make_edi_validation) -> Callable[..., Any]:
    """Fabrique de invoices.ExportX3 (fichiers d'export d'une période)"""
    from apps.invoices.models import ExportX3

    def _factory(validation=None, **kwargs: Any):
        return ExportX3.objects.create(
            uuid_edi_validation=validation or make_edi_validation(), **kwargs
        )

    return _factory


@pytest.fixture
def thread_recorder(monkeypatch) -> Callable[[types.ModuleType], list]:
    """Remplace threading.Thread d'un module : enregistre (target, args, daemon) sans lancer"""

    def _patch(module) -> list:
        started = []

        class _Thread:
            def __init__(self, target, args=(), kwargs=None, daemon=None):
                self.target, self.args, self.kwargs, self.daemon = (
                    target,
                    args,
                    kwargs or {},
                    daemon,
                )

            def start(self):
                started.append((self.target, self.args, self.daemon))

        monkeypatch.setattr(module, "threading", types.SimpleNamespace(Thread=_Thread))
        return started

    return _patch


# Fixtures des modules d'aide de l'app (collectées ici, plus d'import dans les tests)
# Fixtures edi partagées (lignes edi_ediimport, unités, taux de TVA)
from apps.edi.tests.helpers_post import (  # noqa: E402,F401  pylint: disable=W0611,C0413
    edi_batch,
    make_vat_rat,
    units,
)
from apps.invoices.tests.helpers_core import (  # noqa: E402,F401  pylint: disable=W0611,C0413
    billing_dataset,
    invoice_counters,
    keep_connection,
    make_accounts_axe_pro_category,
    make_article_account,
    make_counter,
    make_detail,
    make_grouping,
    make_payment_condition,
    make_sale_detail,
    make_sse_progress_core,
    make_type_facture,
    sync_controls,
)
from apps.invoices.tests.helpers_external import (  # noqa: E402,F401  pylint: disable=W0611,C0413
    email_dirs,
    email_template,
    fake_sender_module,
    fake_tracker,
    gmail_config_file,
    make_purchase_detail,
    make_sale_detail_external,
    sale_for_email,
)
from apps.invoices.tests.helpers_pdf import (  # noqa: E402,F401  pylint: disable=W0611,C0413
    make_sale_with_lines,
    pdf_domain,
    sales_dir,
)
from apps.invoices.tests.helpers_views import (  # noqa: E402,F401  pylint: disable=W0611,C0413
    celery_recorder,
    export_counters,
    make_action,
    make_counter_views,
    make_email,
    make_sse_progress,
    month_period,
)
