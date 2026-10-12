"""Tests de la numérotation des factures saisies manuellement"""

import pytest

from apps.edi.bin.data_edi_invoices_nums import get_invoices_manual_entries_nums


def test_numbering_increments_with_third_party_prefix(make_counter, make_society):
    make_society("FOUR001")
    make_counter("invoices_manual_entries_nums", num=1, lpad_num=5, separateur="-")

    first = get_invoices_manual_entries_nums("FOUR001")
    second = get_invoices_manual_entries_nums("FOUR001")

    assert first == "FOUR001-00001"
    assert second == "FOUR001-00002"


@pytest.mark.usefixtures("db")
def test_numbering_requires_counter():
    from apps.parameters.models import Counter  # pylint: disable=C0415

    with pytest.raises(Counter.DoesNotExist):
        get_invoices_manual_entries_nums("FOUR001")
