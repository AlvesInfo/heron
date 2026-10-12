"""
Tests des exclusions de facturation (apps.edi.bin.exclusions) : suppression des lignes exclues par
couple tiers/maison ou tiers/pays, recalcul des totaux de factures.

created at: 2026-10-10
created by: Paulo ALVES
"""
import importlib
import platform
import sys
import types
from decimal import Decimal

import pytest

from apps.centers_clients.models import MaisonSupllierExclusion, SupllierCountryExclusion
from apps.edi.bin import exclusions
from apps.edi.models import EdiImport
from apps.edi.tests.helpers_post import refresh
from conftest import patched_attrs

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(("node", "expected"), [("PauloMSI", r"C:\SitesWeb\heron"), ("serveur-prod", "/home/paulo/heron")])
def test_base_dir_selon_la_machine(monkeypatch, node, expected):
    monkeypatch.setattr(sys, "path", list(sys.path))

    try:
        with patched_attrs(monkeypatch, platform, uname=lambda: types.SimpleNamespace(node=node)):
            assert expected == importlib.reload(exclusions).BASE_DIR
    finally:
        importlib.reload(exclusions)


def test_set_exclusions(edi_batch, make_maison, make_society, make_country):
    paris = make_maison("AF0001")
    lyon = make_maison("AF0002")
    bruxelles = make_maison("BE0001", pays=make_country("BE"))
    four = make_society("FOUR001", is_client=False)
    MaisonSupllierExclusion.objects.create(third_party_num=four, cct_uuid_identification=paris)
    SupllierCountryExclusion.objects.create(third_party_num=make_society("FOUR002", is_client=False), pays=make_country("BE"))
    _, rows = edi_batch(
        [
            {"invoice_number": "F1", "cct_uuid_identification": paris, "net_amount": Decimal("10"), "vat_amount": Decimal("2"),
             "amount_with_vat": Decimal("12")},
            {"invoice_number": "F1", "cct_uuid_identification": lyon, "net_amount": Decimal("5"), "vat_amount": Decimal("1"),
             "amount_with_vat": Decimal("6"), "invoice_amount_without_tax": Decimal("15")},
            {"invoice_number": "F2", "cct_uuid_identification": bruxelles, "third_party_num": "FOUR002"},
            {"invoice_number": "F3", "cct_uuid_identification": bruxelles, "third_party_num": "FOUR003"},
        ],
        third_party_num="FOUR001",
    )

    exclusions.set_exclusions()

    assert not EdiImport.objects.filter(pk__in=[rows[0].pk, rows[2].pk]).exists()
    kept = refresh(rows[1])
    assert (kept.invoice_amount_without_tax, kept.invoice_amount_tax, kept.invoice_amount_with_tax) == (
        Decimal("5"), Decimal("1"), Decimal("6"),
    )
    assert EdiImport.objects.filter(pk=rows[3].pk).exists()
