# pylint: disable=E0401,W0621
"""
FR : Tests de la mise à jour des identifiants Cosium par cct (bin/gestion_cct.py)
EN : Tests for Cosium cct identifiers update

Commentaire:

La fonction retire d'abord la référence passée de tous les identifiants du tiers COSI001,
puis ajoute à chaque cct de COSI001 la référence Cosium de sa maison si elle n'y figure pas.

created at: 2026-10-10
created by: Paulo ALVES
"""
import pytest

from apps.book.models import SupplierCct
from apps.centers_clients.bin.gestion_cct import update_supplier_cct_reference_cosium

pytestmark = pytest.mark.django_db


@pytest.fixture
def cosium_rows(make_society, make_maison, make_supplier_cct):
    """Jeu d'identifiants fournisseur Cosium et d'un autre tiers"""
    cosium = make_society("COSI001", is_client=False)
    other = make_society("AUTRE001", is_client=False)
    maisons = {
        "ref1_vide": make_maison("AF0001", reference_cosium="REF1"),
        "ref2_pipe": make_maison("AF0002", reference_cosium="REF2"),
        "sans_ref": make_maison("AF0003", reference_cosium=None),
        "ref4_sans_pipe": make_maison("AF0004", reference_cosium="REF4"),
        "ref5_imbrique": make_maison("AF0005", reference_cosium="REF5"),
        "deja_present": make_maison("AF0006", reference_cosium="REF6"),
    }
    return {
        "ref1_vide": make_supplier_cct(cosium, maisons["ref1_vide"].cct, None),
        "ref2_pipe": make_supplier_cct(cosium, maisons["ref2_pipe"].cct, "OLD|"),
        "sans_ref": make_supplier_cct(cosium, maisons["sans_ref"].cct, "X|REF1|Y|"),
        "ref4_sans_pipe": make_supplier_cct(cosium, maisons["ref4_sans_pipe"].cct, "ABC"),
        "ref5_imbrique": make_supplier_cct(cosium, maisons["ref5_imbrique"].cct, "ZREF1Z"),
        "deja_present": make_supplier_cct(cosium, maisons["deja_present"].cct, "REF6|"),
        "autre_tiers": make_supplier_cct(other, maisons["ref1_vide"].cct, "REF1|"),
    }


def _identifiers(rows):
    return {key: SupplierCct.objects.get(pk=row.pk).cct_identifier for key, row in rows.items()}


def test_update_supplier_cct_reference_cosium(cosium_rows):
    """Retrait de REF1 chez COSI001 puis ajout des références manquantes, autre tiers intact"""
    update_supplier_cct_reference_cosium("REF1")

    assert _identifiers(cosium_rows) == {
        "ref1_vide": "REF1|",
        "ref2_pipe": "OLD|REF2|",
        "sans_ref": "X|Y|",
        "ref4_sans_pipe": "ABC|REF4|",
        "ref5_imbrique": "ZZ|REF5|",
        "deja_present": "REF6|",
        "autre_tiers": "REF1|",
    }


def test_update_est_idempotent(cosium_rows):
    """Un second passage ne modifie plus rien"""
    update_supplier_cct_reference_cosium("REF1")
    first = _identifiers(cosium_rows)

    update_supplier_cct_reference_cosium("REF1")

    assert _identifiers(cosium_rows) == first


def test_update_sans_lignes_cosium(make_supplier_cct, make_society):
    """Sans identifiant COSI001, rien ne change pour les autres tiers"""
    row = make_supplier_cct(make_society("AUTRE001", is_client=False), None, "REF1|")

    update_supplier_cct_reference_cosium("REF1")

    assert SupplierCct.objects.get(pk=row.pk).cct_identifier == "REF1|"
