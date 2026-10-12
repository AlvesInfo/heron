# pylint: disable=E0401,W0621,C0415,R0903
"""FR : Aides des tests des services externes de l'app invoices : faux service Gmail, fausses


     réponses HTTP (serveur Factur-X), configuration Gmail temporaire, factures prêtes à être
     envoyées par email. Importées explicitement : `from apps.invoices.tests.helpers_external import *`
EN : Test helpers for the invoices app external services (Gmail, Factur-X server)

created at: 2026-10-10
created by: Paulo ALVES
"""

import datetime
import types
from collections.abc import Callable
from decimal import Decimal
from pathlib import Path
from typing import Any, ClassVar
from uuid import uuid4

import httplib2
import pytest
import requests
import yaml
from googleapiclient.errors import HttpError

INVOICE_MONTH = datetime.date(2026, 1, 1)
PDF_BYTES = b"%PDF-1.4\n%fake\n"


# FAUX SERVICE GMAIL ===============================================================================
class FakeGmailService:
    """Service Gmail simulé : users().messages().send(userId, body).execute()"""

    def __init__(self, outcomes=None):
        """Outcomes : liste d'exceptions ou de dicts renvoyés successivement par execute()"""
        self.outcomes = list(outcomes or [])
        self.sent = []

    def users(self):
        return self

    def messages(self):
        return self

    def send(self, userId, body):  # pylint: disable=C0103  # noqa: N803
        self.sent.append((userId, body))
        return self

    def execute(self):
        outcome = self.outcomes.pop(0) if self.outcomes else {"id": f"msg-{len(self.sent)}"}

        if isinstance(outcome, BaseException):
            raise outcome

        return outcome


def http_error(status: int) -> HttpError:
    """Erreur HTTP googleapiclient avec le statut voulu"""
    return HttpError(httplib2.Response({"status": status, "reason": "err"}), b'{"error": "x"}')


def gmail_settings(**overrides) -> types.SimpleNamespace:
    """Configuration Gmail simulée (valeurs sans attente)"""
    values: dict = {
        "sender_email": "factures@heron.local",
        "max_per_second": 1000,
        "max_retries": 3,
        "retry_delay": 0,
        "retry_backoff": 2,
        "max_retry_delay": 0,
    }
    values.update(overrides)
    return types.SimpleNamespace(**values)


@pytest.fixture
def gmail_config_file(tmp_path: Path) -> Callable[..., Path]:
    """Écrit un fichier yaml de configuration Gmail et renvoie son chemin"""

    def _write(data=None, name: str = "gmail_api_config.yaml") -> Path:
        path = tmp_path / name
        content = {
            "oauth2": {"client_id": "id", "client_secret": "secret"},
            "sender": {"email": "factures@heron.local", "name": "Heron"},
            "rate_limiting": {"max_per_second": 2},
        }
        if data is not None:
            content = data
        path.write_text(yaml.safe_dump(content), encoding="utf-8")
        return path

    return _write


@pytest.fixture
def fake_sender_module(monkeypatch) -> Callable[..., Any]:
    """Construit un GmailSender réel sur un faux service Gmail et une fausse configuration

    (authenticator et config patchés sur le module sender) : `sender, service = make_sender()`
    """
    from apps.invoices.bin.api_gmail import sender as sender_module

    def _make(outcomes=None, **config_overrides):
        service = FakeGmailService(outcomes)
        fake_auth = types.SimpleNamespace(service=service, get_gmail_service=lambda: service)
        monkeypatch.setattr(sender_module, "authenticator", fake_auth)
        monkeypatch.setattr(sender_module, "config", gmail_settings(**config_overrides))
        monkeypatch.setattr(sender_module.time, "sleep", lambda seconds: None)
        return sender_module.GmailSender(), service

    return _make


# FAUSSES RÉPONSES HTTP (serveur Factur-X) =========================================================
class FakeResponse:
    """Réponse requests simulée"""

    def __init__(self, status_code=200, payload=None, content=b"", json_error=False):
        self.status_code = status_code
        self.ok = 200 <= status_code < 300
        self._payload = payload
        self.content = content
        self._json_error = json_error

    def json(self):
        if self._json_error:
            raise ValueError("pas du json")
        return self._payload


class FakeSession:
    """Session requests simulée : renvoie les réponses programmées ou lève l'exception donnée"""

    def __init__(self, responses=None):
        self.responses = list(responses or [])
        self.calls = []

    def _next(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        outcome = self.responses.pop(0) if self.responses else FakeResponse()

        if isinstance(outcome, BaseException):
            raise outcome

        return outcome

    def get(self, url, **kwargs):
        return self._next("get", url, **kwargs)

    def post(self, url, **kwargs):
        return self._next("post", url, **kwargs)


def unreachable() -> requests.RequestException:
    return requests.ConnectionError("refusé")


# DONNÉES DE FACTURATION ===========================================================================
@pytest.fixture
def make_sale_detail_external(db) -> Callable[..., Any]:  # pylint: disable=W0613
    """Ligne de vente (SaleInvoiceDetail) avec sa ligne commune (InvoiceCommonDetails) optionnelle"""
    from apps.invoices.models import InvoiceCommonDetails, SaleInvoiceDetail

    def _factory(
        sale,
        common: bool = True,
        qty=Decimal(2),
        libelle="Monture Ray",
        reference="ART-1",
        **kwargs,
    ):
        import_uuid = kwargs.pop("import_uuid_identification", uuid4())
        defaults = {
            "axe_bu": "CAHA",
            "axe_prj": "NAF",
            "axe_pro": "OPT",
            "axe_rfa": "NAF",
            "axe_pys": "FR",
            "vat": "001",
            "vat_rate": Decimal("0.2"),
            "vat_regime": "FRA",
            "big_category": "Marchandises",
            "base": "Marchandises",
            "grouping_goods": "Montures",
            "account": "707000",
            "account_od_600": "607000",
            "ranking": 1,
            "net_unit_price": Decimal(50),
            "net_amount": Decimal(100),
            "vat_amount": Decimal(20),
            "amount_with_vat": Decimal(120),
        }
        defaults.update(kwargs)
        detail = SaleInvoiceDetail.objects.create(
            uuid_invoice=sale, import_uuid_identification=import_uuid, **defaults
        )

        if common:
            InvoiceCommonDetails.objects.create(
                import_uuid_identification=import_uuid,
                invoice_number=sale.invoice_number,
                invoice_date=sale.invoice_date,
                invoice_year=sale.invoice_year,
                unit_weight="U",
                cct=sale.cct,
                third_party_num=sale.third_party_num,
                qty=qty,
                libelle=libelle,
                reference_article=reference,
                acuitis_order_number="CDE-1",
                final=True,
            )

        return detail

    return _factory


@pytest.fixture
def make_purchase_detail(db) -> Callable[..., Any]:  # pylint: disable=W0613
    """Ligne d'achat (InvoiceDetail) avec sa ligne commune (InvoiceCommonDetails)"""
    from apps.invoices.models import InvoiceCommonDetails, InvoiceDetail

    def _factory(invoice, cct, **kwargs):
        import_uuid = uuid4()
        defaults = {
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
            "net_unit_price": Decimal(100),
            "net_amount": Decimal(100),
            "vat_amount": Decimal(20),
            "amount_with_vat": Decimal(120),
        }
        defaults.update(kwargs)
        detail = InvoiceDetail.objects.create(
            uuid_invoice=invoice, import_uuid_identification=import_uuid, **defaults
        )
        InvoiceCommonDetails.objects.create(
            import_uuid_identification=import_uuid,
            invoice_number=invoice.invoice_number,
            invoice_date=invoice.invoice_date,
            invoice_year=invoice.invoice_year,
            unit_weight="U",
            cct=cct,
            third_party_num=invoice.third_party_num,
            qty=Decimal(1),
            libelle="Article",
            reference_article="ART-1",
            supplier="Fournisseur",
            maison="Maison",
            final=True,
        )
        return detail

    return _factory


@pytest.fixture
def email_dirs(invoices_dirs, settings):
    """Répertoires invoices redirigés aussi dans django.conf.settings (modules qui le lisent)"""
    settings.SALES_INVOICES_FILES_DIR = invoices_dirs.sales
    settings.SALES_INVOICES_FACTURX_DIR = invoices_dirs.facturx
    settings.PROCESSING_FACTURX_DIR = invoices_dirs.processing_facturx
    settings.EXPORT_DIR = invoices_dirs.export
    return invoices_dirs


@pytest.fixture
def sale_for_email(email_dirs, make_society, make_maison, make_sale_invoice) -> Callable[..., Any]:
    """Facture de vente imprimée (pdf global présent) prête à être envoyée par email, avec la maison

    (email_06) et le tiers client (email_01) : `sale, context_dict = sale_for_email()`
    """

    def _factory(
        cct: str = "AF0001",
        emails=("client@heron.local",),
        maison_email="maison@heron.local",
        third_party_num: str = "CLI001",
        **kwargs,
    ):
        society_fields = {
            f"email_0{index}": email for index, email in enumerate(emails, 1) if email
        }
        society = make_society(third_party_num, **society_fields)
        make_maison(cct, third_party_num=society, email=maison_email)
        file_name = f"{cct}_global.pdf"
        (email_dirs.sales / file_name).write_bytes(PDF_BYTES)
        sale = make_sale_invoice(
            cct=cct,
            third_party_num=third_party_num,
            printed=True,
            global_invoice_file=file_name,
            invoice_month=INVOICE_MONTH,
            **kwargs,
        )
        context_dict = {
            "cct": cct,
            "global_invoice_file": file_name,
            "invoice_month": INVOICE_MONTH.isoformat(),
            "subject_email": "Factures {periode}",
            "email_text": "Factures {cct}",
            "email_html": "<p>{cct} {synthese} {factures} {service} {centrale}</p>",
        }
        return sale, context_dict

    return _factory


@pytest.fixture
def email_template(db) -> Any:  # pylint: disable=W0613
    """Modèle d'email de facturation (parameters.Email name=0)"""
    from apps.parameters.models import Email

    return Email.objects.create(
        name=0, description="Factures", subject="Factures {periode}", email_body="<p>{cct}</p>"
    )


class FakeTracker:
    """SSEProgressTracker simulé : enregistre les événements"""

    events: ClassVar[list] = []

    def __init__(self, channel_name, enabled=True):
        self.channel_name = channel_name

    def _record(self, kind, *args, **kwargs):
        FakeTracker.events.append((kind, args, kwargs))

    def send_start(self, *args, **kwargs):
        self._record("start", *args, **kwargs)

    def send_progress(self, *args, **kwargs):
        self._record("progress", *args, **kwargs)

    def send_complete(self, *args, **kwargs):
        self._record("complete", *args, **kwargs)

    def send_error(self, *args, **kwargs):
        self._record("error", *args, **kwargs)

    def send_warning(self, *args, **kwargs):
        self._record("warning", *args, **kwargs)


@pytest.fixture
def fake_tracker(monkeypatch):
    """Remplace SSEProgressTracker des tâches SSE par un enregistreur"""
    from apps.invoices.bin.api_gmail import tasks_gmail_sse

    FakeTracker.events = []
    monkeypatch.setattr(tasks_gmail_sse, "SSEProgressTracker", FakeTracker)
    return FakeTracker


def reload_with_node(monkeypatch, module, node):
    """Recharge un module d'amorçage Django avec un nom de machine donné, renvoie BASE_DIR"""
    import importlib
    import platform
    import sys

    from conftest import patched_attrs

    monkeypatch.setattr(sys, "path", list(sys.path))

    try:
        with patched_attrs(monkeypatch, platform, uname=lambda: types.SimpleNamespace(node=node)):
            return importlib.reload(module).BASE_DIR
    finally:
        importlib.reload(module)
