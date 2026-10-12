"""Tests du contrôle des doublons de factures (apps.edi.bin.duplicates_check) : doublons entre imports,


doublons avec les factures définitives, existence d'une facture.

created at: 2026-10-10
created by: Paulo ALVES
"""

import datetime

import pytest

from apps.edi.bin import duplicates_check
from apps.edi.models import EdiImport
from apps.edi.tests.helpers_post import refresh

pytestmark = pytest.mark.django_db


def set_created_at(rows, created_at):
    """Force created_at (auto_now_add) des lignes"""
    EdiImport.objects.filter(pk__in=[row.pk for row in rows]).update(created_at=created_at)


def test_edi_import_duplicate_check_un_doublon(edi_batch, make_trace):
    """La facture déjà importée est signalée sur la trace la plus récente, l'ancien import est purgé"""
    old_uuid, old_rows = edi_batch(
        [{"invoice_number": "F1"}, {"invoice_number": "F1"}], third_party_num="WIDE001"
    )
    new_uuid, new_rows = edi_batch([{"invoice_number": "F1"}], third_party_num="WIDE001")
    other_uuid, _ = edi_batch([{"invoice_number": "F9"}], third_party_num="WIDE001")
    set_created_at(old_rows, datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC))
    set_created_at(new_rows, datetime.datetime(2026, 1, 2, tzinfo=datetime.UTC))
    old_trace = make_trace(uuid_identification=old_uuid, comment="")
    new_trace = make_trace(uuid_identification=new_uuid, comment=None)

    duplicates_check.edi_import_duplicate_check()

    new_trace.refresh_from_db()
    assert new_trace.errors is True
    assert new_trace.comment.startswith("L'ensemble (")
    assert "(Tiers : WIDE001 - Fac. N° : F1 - Année : 2026)" in new_trace.comment
    assert "Cette facture à été supprimée" in new_trace.comment
    assert refresh(old_trace).errors is False
    assert not EdiImport.objects.filter(uuid_identification=old_uuid).exists()
    assert EdiImport.objects.filter(uuid_identification=new_uuid).count() == 1
    assert EdiImport.objects.filter(uuid_identification=other_uuid).count() == 1


def test_edi_import_duplicate_check_plusieurs_doublons(edi_batch, make_trace):
    old_uuid, old_rows = edi_batch([{"invoice_number": "F1"}, {"invoice_number": "F2"}])
    new_uuid, new_rows = edi_batch([{"invoice_number": "F1"}, {"invoice_number": "F2"}])
    set_created_at(old_rows, datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC))
    set_created_at(new_rows, datetime.datetime(2026, 1, 2, tzinfo=datetime.UTC))
    trace = make_trace(uuid_identification=new_uuid, comment="Import")

    duplicates_check.edi_import_duplicate_check()

    trace.refresh_from_db()
    assert trace.comment.startswith("ImportLes ensembles (")
    assert "F1" in trace.comment
    assert "F2" in trace.comment
    assert "Ces factures ont été supprimées" in trace.comment
    assert not EdiImport.objects.filter(uuid_identification=old_uuid).exists()


def test_edi_import_duplicate_check_sans_doublon(edi_batch, make_trace):
    uuid_identification, _ = edi_batch([{"invoice_number": "F1"}])
    trace = make_trace(uuid_identification=uuid_identification)

    duplicates_check.edi_import_duplicate_check()

    assert refresh(trace).errors is False
    assert EdiImport.objects.filter(uuid_identification=uuid_identification).count() == 1


def test_suppliers_invoices_duplicate_check(edi_batch, make_trace, make_invoice_common_details):
    make_invoice_common_details("FOUR001", "F1")
    make_invoice_common_details("FOUR001", "F2")
    make_invoice_common_details("FOUR001", "F3", final=False)
    uuid_identification, _ = edi_batch(
        [{"invoice_number": "F1"}, {"invoice_number": "F2"}, {"invoice_number": "F3"}]
    )
    trace = make_trace(uuid_identification=uuid_identification, comment=None)
    uuid_single, _ = edi_batch([{"invoice_number": "F1"}])
    single_trace = make_trace(uuid_identification=uuid_single, comment="Import")

    duplicates_check.suppliers_invoices_duplicate_check()

    trace.refresh_from_db()
    assert trace.errors is True
    assert trace.comment.startswith("Les ensembles (")
    assert "Ces factures ont été supprimées" in trace.comment
    assert refresh(single_trace).comment.startswith("ImportL'ensemble (")
    # F3 n'est pas finalisée : conservée
    assert list(
        EdiImport.objects.filter(uuid_identification=uuid_identification).values_list(
            "invoice_number", flat=True
        )
    ) == ["F3"]
    assert not EdiImport.objects.filter(uuid_identification=uuid_single).exists()


def test_suppliers_invoices_duplicate_check_sans_trace(edi_batch, make_invoice_common_details):
    make_invoice_common_details("FOUR001", "F1")
    uuid_identification, _ = edi_batch([{"invoice_number": "F1"}])

    duplicates_check.suppliers_invoices_duplicate_check()

    assert not EdiImport.objects.filter(uuid_identification=uuid_identification).exists()


def test_check_invoice_exists(edi_batch, make_invoice_common_details):
    edi_batch([{"invoice_number": "F1"}], third_party_num="FOUR001")
    make_invoice_common_details("FOUR001", "F2")
    make_invoice_common_details("FOUR001", "F3", final=False)

    assert duplicates_check.check_invoice_exists("FOUR001", "F1", 2026) is True
    assert duplicates_check.check_invoice_exists("FOUR001", "F2", 2026) is True
    assert duplicates_check.check_invoice_exists("FOUR001", "F3", 2026) is False
    assert duplicates_check.check_invoice_exists("FOUR001", "F1", 2025) is False
    assert duplicates_check.check_invoice_exists("AUTRE", "F1", 2026) is False
