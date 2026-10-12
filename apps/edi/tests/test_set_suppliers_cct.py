"""
Tests des identifiants de maisons par fournisseur (apps.edi.bin.set_suppliers_cct) :
création des book_suppliercct manquants, mise à jour des cct et enseignes des imports.

created at: 2026-10-10
created by: Paulo ALVES
"""
import datetime

import pytest

from apps.book.models import SupplierCct
from apps.edi.bin import set_suppliers_cct
from apps.edi.tests.helpers_post import refresh

pytestmark = pytest.mark.django_db


@pytest.fixture
def automate(make_user):
    """Utilisateur automate, créateur des identifiants générés"""
    return make_user(email="automate@acuitis.com", username="automate")


@pytest.fixture
def maisons(make_maison, make_cct):
    """Deux maisons ouvertes et une fermée, avec leurs cct Sage actifs"""
    for cct in ("AF0001", "AF0002", "AF0009"):
        make_cct(cct, active=True)

    opened = [make_maison(cct) for cct in ("AF0001", "AF0002")]
    closed = make_maison("AF0009", closing_date=datetime.date(2025, 1, 1))
    return [*opened, closed]


def identifiers(third_party_num):
    return dict(
        SupplierCct.objects.filter(third_party_num=third_party_num).values_list(
            "cct_uuid_identification__cct", "cct_identifier"
        )
    )


def test_add_news_cct_sage_pour_les_tiers_importes(edi_batch, automate, maisons, make_supplier_cct, make_society):
    edi_batch([{}], third_party_num="FOUR001")
    edi_batch([{}], third_party_num="FOUR002")
    # identifiant déjà renseigné pour AF0001 chez FOUR001 : conservé
    make_supplier_cct(make_society("FOUR001", is_client=False), maisons[0].cct, "MAG01|")

    set_suppliers_cct.add_news_cct_sage()

    assert identifiers("FOUR001") == {"AF0001": "MAG01|", "AF0002": "AF0002|"}
    assert identifiers("FOUR002") == {"AF0001": "AF0001|", "AF0002": "AF0002|"}
    assert SupplierCct.objects.filter(created_by=automate, third_party_num__in=["FOUR001", "FOUR002"]).count() == 3
    # le tiers propriétaire des maisons (CLI001) reçoit aussi ses identifiants
    assert set(identifiers("CLI001")) == {"AF0001", "AF0002"}


@pytest.mark.usefixtures('automate', 'maisons')
def test_add_news_cct_sage_pour_un_tiers(edi_batch):
    edi_batch([{}], third_party_num="FOUR001")
    edi_batch([{}], third_party_num="FOUR002")

    set_suppliers_cct.add_news_cct_sage("FOUR001")

    assert set(identifiers("FOUR001")) == {"AF0001", "AF0002"}
    assert identifiers("FOUR002") == {}


@pytest.mark.usefixtures('automate', 'maisons')
def test_add_news_cct_sage_force_add(make_society):
    make_society("NEWS001", is_client=False)

    set_suppliers_cct.add_news_cct_sage("NEWS001")
    assert identifiers("NEWS001") == {}

    set_suppliers_cct.add_news_cct_sage("NEWS001", force_add=True)
    assert set(identifiers("NEWS001")) == {"AF0001", "AF0002"}


@pytest.mark.usefixtures('maisons')
def test_add_news_cct_sage_sans_automate(edi_batch):
    edi_batch([{}], third_party_num="FOUR001")

    set_suppliers_cct.add_news_cct_sage()

    assert identifiers("FOUR001") == {}


@pytest.fixture
def imports_a_rattacher(edi_batch, maisons, make_supplier_cct, make_society):
    """Lignes validées dont le code maison correspond à un identifiant fournisseur"""
    society = make_society("FOUR001", is_client=False)
    make_supplier_cct(society, maisons[0].cct, "MAG01|MAG02|")
    make_supplier_cct(make_society("FOUR002", is_client=False), maisons[1].cct, "X2")
    _, rows = edi_batch(
        [
            {"code_maison": "MAG01", "valid": True, "code_signboard": None},
            {"code_maison": "MAG02", "valid": True, "cct_uuid_identification": maisons[1], "code_signboard": "OLD"},
            {"code_maison": "MAG01", "valid": False},
            {"code_maison": "X2", "valid": True, "third_party_num": "FOUR002", "code_signboard": "ACF"},
        ],
        third_party_num="FOUR001",
    )
    return rows


def test_update_edi_import_cct_tous_les_tiers(imports_a_rattacher, maisons):
    set_suppliers_cct.update_edi_import_cct_uui_identification()

    first, second, invalid, other = refresh(*imports_a_rattacher)
    assert first.cct_uuid_identification == maisons[0]
    # force_update=False : toutes les lignes validées sont réalignées, même déjà renseignées
    assert second.cct_uuid_identification == maisons[0]
    assert invalid.cct_uuid_identification is None
    assert other.cct_uuid_identification == maisons[1]
    assert (first.code_signboard, second.code_signboard, other.code_signboard) == ("ACF", "ACF", "ACF")


def test_update_edi_import_cct_seulement_les_vides(imports_a_rattacher, maisons):
    set_suppliers_cct.update_edi_import_cct_uui_identification(force_update=True)

    first, second, _, _ = refresh(*imports_a_rattacher)
    assert first.cct_uuid_identification == maisons[0]
    assert second.cct_uuid_identification == maisons[1]


def test_update_edi_import_cct_pour_un_tiers(imports_a_rattacher, maisons):
    set_suppliers_cct.update_edi_import_cct_uui_identification(third_party_num="FOUR002")

    first, _, _, other = refresh(*imports_a_rattacher)
    assert first.cct_uuid_identification is None
    assert other.cct_uuid_identification == maisons[1]


def test_set_signboard(edi_batch, make_maison, make_child_center, make_signboard):
    maison = make_maison("AF0001", center_purchase=make_child_center("GAF"), sign_board=make_signboard("GAF"))
    _, rows = edi_batch(
        [
            {"cct_uuid_identification": maison, "code_center": None, "code_signboard": None},
            {"cct_uuid_identification": maison, "code_center": "ACF", "code_signboard": "GAF"},
            {"cct_uuid_identification": maison, "code_center": "GAF", "code_signboard": "GAF"},
            {"cct_uuid_identification": None, "code_center": None, "code_signboard": None},
        ]
    )

    set_suppliers_cct.set_signboard()

    null_row, center_row, same, no_cct = refresh(*rows)
    # Régression : les lignes à centrale NULL n'étaient jamais mises à jour (NULL != x est NULL)
    assert (null_row.code_center, null_row.code_signboard) == ("GAF", "GAF")
    assert (center_row.code_center, center_row.code_signboard) == ("GAF", "GAF")
    assert (same.code_center, same.code_signboard) == ("GAF", "GAF")
    assert (no_cct.code_center, no_cct.code_signboard) == (None, None)
