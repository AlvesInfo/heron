# pylint: disable=E0401,W0621,W0212
"""FR : Tests des modèles du répertoire des tiers (apps/book/models)


EN : Tests for directory models

created at: 2026-10-11
created by: Paulo ALVES
"""

import pytest
from django.db import IntegrityError, transaction
from django.urls import reverse

from apps.book.models import (
    Address,
    BookAdressesSage,
    BookBanksSage,
    BookContactsSage,
    BpcBookSage,
    BprBookSage,
    BpsBookSage,
    CodeContactsSage,
    Contact,
    Society,
    SocietyBank,
    SupplierCct,
    SupplierFamilyAxes,
)

pytestmark = pytest.mark.django_db


# SOCIÉTÉS, ADRESSES, CONTACTS, BANQUES ============================================================


def test_society_str_et_url(make_society):
    society = make_society("FOUR001", name="Fournisseur")

    assert str(society) == "FOUR001 - Fournisseur"
    assert Society.get_absolute_url() == reverse("book:societies_list")
    assert society.currency == "EUR"
    assert society.rfa_frequence == Society.Frequence.AUCUNE
    assert society.rfa_remise == Society.Remise.AUCUNE


def test_society_choix_rfa():
    assert [choice.label for choice in Society.Frequence] == [
        "---------",
        "Mensuel",
        "Trimestriel",
        "Semestriel",
        "Annuel",
    ]
    assert [choice.label for choice in Society.Remise] == [
        "---------",
        "Fournisseur Total",
        "Famille Article",
        "Article",
    ]


def test_society_third_party_num_unique(make_society):
    make_society("DOUBLE")

    with pytest.raises(IntegrityError), transaction.atomic():
        Society.objects.create(third_party_num="DOUBLE")


def test_address_str_et_adresse_par_defaut_unique(make_society, make_address):
    """La sauvegarde d'une adresse par défaut retire le drapeau des autres adresses du tiers"""
    society = make_society("TIERS01")
    first = make_address(society, "1", default_adress=True)
    second = make_address(society, "2", default_adress=True)

    first.refresh_from_db()
    assert str(second) == f"{society} - 2"
    assert first.default_adress is False
    assert second.default_adress is True

    second.default_adress = False
    second.save()
    first.refresh_from_db()
    assert first.default_adress is False


def test_address_unique_par_tiers_et_code(make_society, make_address):
    society = make_society("TIERS01")
    make_address(society, "1")

    with pytest.raises(IntegrityError), transaction.atomic():
        Address.objects.create(society=society, address_code="1")


def test_contact_str(make_contact):
    assert str(make_contact(code="C1", first_name="Jean", last_name="Dupont")) == "Jean - Dupont"
    assert str(make_contact(code="C2", last_name="Durand")) == "Durand"


def test_contact_unique_par_tiers_et_code(make_society, make_contact):
    society = make_society("TIERS01")
    make_contact(society, "C01")

    with pytest.raises(IntegrityError), transaction.atomic():
        Contact.objects.create(society=society, code="C01")


def test_society_bank_str_et_tri(make_society, make_society_bank):
    society = make_society("TIERS01")
    secondary = make_society_bank(society, "FR01")
    default = make_society_bank(society, "FR02", is_default=True)

    assert str(default) == f"{society} - FR02"
    assert list(SocietyBank.objects.filter(society=society)) == [default, secondary]
    assert society.bank_society.filter(is_default=True).first() == default


# STATISTIQUES ET IDENTIFIANTS =====================================================================


def test_stat_familly_axes_str_et_url(make_stat_familly):
    stat = make_stat_familly("ACUITIS")

    assert str(stat) == "ACUITIS"
    assert stat.get_absolute_url() == reverse("book:statistique_update", args=["ACUITIS"])
    assert stat.uuid_identification is not None


def test_supplier_family_axes_str_tri_et_unicite(make_supplier_family_axes):
    """Tri par statistique / colonne / regex, unicité du quadruplet"""
    first = make_supplier_family_axes("VERRES", stat_name="ACUITIS", description="verres")
    second = make_supplier_family_axes("LUNETTES", stat_name="ACUITIS")

    assert str(second) == "ACUITIS - famille - LUNETTES"
    assert list(SupplierFamilyAxes.objects.all()) == [second, first]
    assert SupplierFamilyAxes.Unit.KG.label == "Kilo"
    assert first.item_weight == 0

    with pytest.raises(IntegrityError), transaction.atomic():
        SupplierFamilyAxes.objects.create(
            stat_name=first.stat_name,
            invoice_column="famille",
            regex_match="VERRES",
            expected_result="VERRES",
            axe_pro=first.axe_pro,
            big_category=first.big_category,
        )


def test_supplier_cct_str_url_et_unicite(make_society, make_cct, make_supplier_cct):
    """L'url de retour cible la fiche du tiers dans la liste complète (route avec in_use)"""
    society = make_society("FOUR001", name="Fournisseur", is_client=False)
    cct = make_cct("AF0001", name="Paris")
    supplier_cct = make_supplier_cct(society, cct, "PAR|")

    assert str(supplier_cct) == "FOUR001 - Fournisseur - Paris - PAR|"
    assert supplier_cct.get_absolute_url() == reverse(
        "book:society_update", args=[society.pk, "alls"]
    )

    with pytest.raises(IntegrityError), transaction.atomic():
        SupplierCct.objects.create(third_party_num=society, cct_uuid_identification=cct)


# MÉTADONNÉES D'IMPORT SAGE ========================================================================

IMPORT_METADATA = [
    (BprBookSage, Society, "ZBIBPR_journalier.heron", {"third_party_num"}, 22),
    (BpsBookSage, Society, "ZBIBPS_journalier.heron", {"third_party_num"}, 13),
    (BpcBookSage, Society, "ZBIBPC_journalier.heron", {"third_party_num"}, 13),
    (BookAdressesSage, Address, "ZBIADDR_journalier.heron", {"society", "address_code"}, 22),
    (CodeContactsSage, Contact, "ZBICONTACT_journalier.heron", {"society", "code"}, 4),
    (BookContactsSage, Contact, "ZBICONTCRM_journalier.heron", {"society", "code"}, 17),
    (BookBanksSage, SocietyBank, "ZBIBANK_journalier.heron", {"society", "account_number"}, 13),
]


@pytest.mark.parametrize(
    ("sage_class", "model", "file_name", "uniques", "nb_columns"), IMPORT_METADATA
)
def test_metadonnees_import_sage(sage_class, model, file_name, uniques, nb_columns):
    """Pour chaque fichier Sage : modèle cible, nom de fichier, clés uniques, colonnes du fichier

    existant dans le modèle, positions croissantes et distinctes
    """
    columns = sage_class.get_columns_import()
    model_fields = {field.name for field in model._meta.fields}

    assert sage_class.model is model
    assert sage_class.file_import_sage() == file_name
    assert set(sage_class.get_uniques()) == uniques
    assert uniques <= set(columns)
    assert set(columns) <= model_fields
    assert len(columns) == nb_columns
    assert list(columns.values()) == sorted(set(columns.values()))
    assert sage_class().get_import == "methode d'import à retourner"


def test_colonnes_adresses_sage_sautent_la_colonne_4():
    """Le fichier des adresses a une colonne inutilisée en position 4"""
    positions = list(BookAdressesSage.get_columns_import().values())

    assert 4 not in positions
    assert positions[:5] == [0, 1, 2, 3, 5]
