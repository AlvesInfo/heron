# pylint: disable=E0401,W0621,C0415
"""FR : Aides pour les tests des vues de validation_purchases : encodage des paramètres,


     jeu de données d'intégration, remplaçant des exports Excel, action en cours
EN : Helpers for validation_purchases views tests

Importées explicitement par les modules de tests : `from ...helpers_views import ...`
"""

import datetime
import types
from collections.abc import Callable
from decimal import Decimal
from typing import Any

import pytest

from apps.core.bin.encoders import set_base_64_list

MONTH = datetime.date(2026, 1, 1)
INVOICE_DATE = datetime.date(2026, 1, 15)


def encode(*values: Any) -> str:
    """Encode les paramètres d'URL en base64 comme les templates (séparateur ||)"""
    return set_base_64_list([str(value) for value in values])


@pytest.fixture
def stub_excel(monkeypatch) -> Callable[..., list]:
    """Remplace une fonction d'export Excel d'un module de vue par un enregistreur qui écrit

    quelques octets : `calls = stub_excel(module, "excel_x")` ; `stub_excel(module, "excel_x",
    error=ValueError("boom"))` fait échouer l'export.
    """

    def _patch(module, name: str, error: Exception | None = None) -> list:
        calls = []

        def _fake(file_io, file_name, *args, **kwargs):
            calls.append((file_name, args, kwargs))

            if error is not None:
                raise error

            file_io.write(b"xlsx")
            return {"OK": file_name}

        monkeypatch.setattr(module, name, _fake)
        return calls

    return _patch


@pytest.fixture
def make_action(db) -> Callable[..., Any]:  # pylint: disable=W0613
    """Fabrique idempotente de parameters.ActionInProgress"""
    from apps.parameters.models import ActionInProgress

    def _factory(action: str = "import_edi_invoices", in_progress: bool = False):
        obj, _ = ActionInProgress.objects.get_or_create(action=action, defaults={"comment": action})
        obj.in_progress = in_progress
        obj.save()
        return obj

    return _factory


@pytest.fixture
def integration_data(
    make_edi_import,
    make_maison,
    make_edi_import_control,
    make_icon_origin,
    make_section,
    make_society,
    validation_period,
):
    """Jeu de données de l'écran 2.1 : un fournisseur FOUR001 (WIDEX, flux Widex) avec deux factures

    validées de janvier 2026 rattachées à une maison, un relevé (contrôle) lié, une origine.
    """
    make_icon_origin(1, "Import EDI", "upload")
    maison = make_maison("AF0001", code_maison="AF0001")
    society = make_society("FOUR001", is_client=False, is_supplier=True, name="WIDEX SAS")
    control = make_edi_import_control(
        statement_without_tax=Decimal(30), statement_with_tax=Decimal(36)
    )
    axe_rfa = make_section("RFA", "RFA01")
    common = {
        "supplier": "WIDEX",
        "supplier_ident": "widex",
        "flow_name": "Widex",
        "invoice_date": INVOICE_DATE,
        "invoice_month": MONTH,
        "invoice_year": 2026,
        "cct_uuid_identification": maison,
        "code_maison": "AF0001",
        "maison": "Maison AF0001",
        "purchase_invoice": True,
        "sale_invoice": False,
        "valid": True,
        "is_multi_store": False,
        "origin_id": 1,
        "uuid_control": control,
        "axe_rfa": axe_rfa,
        "invoice_type": "380",
    }
    rows = [
        make_edi_import(
            invoice_number="F001",
            reference_article="ART-1",
            net_amount=Decimal(10),
            amount_with_vat=Decimal(12),
            invoice_amount_without_tax=Decimal(10),
            invoice_amount_with_tax=Decimal(12),
            **common,
        ),
        make_edi_import(
            invoice_number="F002",
            reference_article="ART-2",
            net_amount=Decimal(20),
            amount_with_vat=Decimal(24),
            invoice_amount_without_tax=Decimal(20),
            invoice_amount_with_tax=Decimal(24),
            **common,
        ),
    ]
    rows[1].uuid_identification = rows[0].uuid_identification
    rows[1].save()

    return types.SimpleNamespace(
        rows=rows,
        maison=maison,
        society=society,
        control=control,
        validation=validation_period,
        third_party_num="FOUR001",
        supplier="WIDEX",
        flow_name="Widex",
        month=MONTH,
        enc_param=encode("FOUR001", "WIDEX", MONTH.isoformat(), "Widex"),
        enc_invoice=encode("FOUR001", "WIDEX", MONTH.isoformat(), "F001"),
    )


def messages_of(response) -> list[str]:
    """Textes des messages Django posés pendant la requête (fonctionne aussi pour un JsonResponse)"""
    from django.contrib.messages import get_messages

    return [str(message) for message in get_messages(response.wsgi_request)]
