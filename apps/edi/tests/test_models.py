"""
Tests des modèles de l'app edi
"""
import datetime
import uuid
from decimal import Decimal

import pytest
from django.db import IntegrityError

from apps.edi.models import (
    ChronoDirect,
    EdiControlRebilling,
    EdiImport,
    StarkeyDepot,
)


@pytest.mark.parametrize("model", [EdiImport, StarkeyDepot])
@pytest.mark.usefixtures('db')
def test_save_computes_invoice_month_and_year(model):
    """Sans mois ni année renseignés, ils sont déduits de la date de facture"""
    row = model.objects.create(invoice_date=datetime.date(2026, 3, 17), invoice_number="F1")

    row.refresh_from_db()
    assert row.invoice_month == datetime.date(2026, 3, 1)
    assert row.invoice_year == 2026


@pytest.mark.parametrize("model", [EdiImport, StarkeyDepot])
@pytest.mark.usefixtures('db')
def test_save_keeps_given_invoice_month_and_year(model):
    row = model.objects.create(
        invoice_date=datetime.date(2026, 3, 17),
        invoice_month=datetime.date(2025, 12, 1),
        invoice_year=2025,
    )

    row.refresh_from_db()
    assert row.invoice_month == datetime.date(2025, 12, 1)
    assert row.invoice_year == 2025


@pytest.mark.usefixtures('db')
def test_edi_import_defaults():
    row = EdiImport.objects.create(invoice_date=datetime.date(2026, 1, 1))

    assert isinstance(row.uuid_identification, uuid.UUID)
    assert isinstance(row.import_uuid_identification, uuid.UUID)
    assert row.packaging_qty == 1
    assert row.valid is False
    assert row.is_multi_store is None


def test_edi_import_control_defaults(make_edi_import_control):
    control = make_edi_import_control()

    assert control.statement_without_tax == Decimal("100")
    assert control.final is False
    assert isinstance(control.uuid_identification, uuid.UUID)


def test_edi_validation_defaults(make_edi_validation):
    validation = make_edi_validation(billing_period=datetime.date(2026, 2, 1))

    assert validation.billing_period == datetime.date(2026, 2, 1)
    assert validation.billing_date is None
    assert validation.final is False
    assert validation.articles_news is False
    assert validation.validation_ca is False


def test_edi_control_rebilling_unique_together(make_edi_validation):
    from apps.parameters.models import ControlRebilling  # pylint: disable=C0415

    control = ControlRebilling.objects.create(name="Contrôle test")
    validation = make_edi_validation()
    EdiControlRebilling.objects.create(
        control_rebilling=control, uuid_edi_validation=validation, comment="ok"
    )

    assert EdiControlRebilling.objects.filter(control_rebilling__name="Contrôle test").count() == 1

    with pytest.raises(IntegrityError):
        EdiControlRebilling.objects.create(control_rebilling=control, uuid_edi_validation=validation)


@pytest.mark.usefixtures('db')
def test_chrono_direct():
    row = ChronoDirect.objects.create(
        reference_cosium="COS1",
        libelle="Courrier",
        qty=3,
        montant_achat=Decimal("1.50"),
        montant_cession=Decimal("2.25"),
    )

    assert ChronoDirect.objects.get(pk=row.pk).montant_cession == Decimal("2.25")
