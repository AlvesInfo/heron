"""
Tests de la mise à jour des cct depuis les identifiants fournisseurs (apps.edi.bin.cct_update)
et de la remise à zéro des imports (apps.edi.bin.reset_import).

created at: 2026-10-10
created by: Paulo ALVES
"""
import pytest

from apps.edi.bin import cct_update, reset_import
from apps.edi.models import EdiImport
from apps.edi.tests.helpers_post import refresh

pytestmark = pytest.mark.django_db


def test_update_cct_edi_import(edi_batch, make_maison, make_cct, make_supplier_cct, make_society):
    make_cct("AF0001", active=True)
    make_cct("AF0002", active=False)
    active = make_maison("AF0001")
    inactive = make_maison("AF0002")
    society = make_society("FOUR001", is_client=False)
    make_supplier_cct(society, active.cct, "MAG01|")
    make_supplier_cct(society, inactive.cct, "MAG02")
    _, rows = edi_batch(
        [
            {"code_maison": "MAG01", "cct_uuid_identification": None, "code_signboard": None},
            {"code_maison": "MAG02", "cct_uuid_identification": None},
            {"code_maison": "MAG01", "cct_uuid_identification": inactive, "code_signboard": "X"},
        ],
        third_party_num="FOUR001",
    )

    cct_update.update_cct_edi_import()

    first, second, third = refresh(*rows)
    assert (first.cct_uuid_identification, first.code_signboard) == (active, "ACF")
    # cct inactif : non rattaché
    assert second.cct_uuid_identification is None
    # déjà renseigné : conservé, enseigne réalignée sur la maison
    assert (third.cct_uuid_identification, third.code_signboard) == (inactive, "ACF")


def test_reset_all_imports(edi_batch):
    edi_batch([{}, {}])
    edi_batch([{"valid": True}])

    reset_import.reset_all_imports()

    assert EdiImport.objects.count() == 0
