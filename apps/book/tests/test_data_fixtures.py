# pylint: disable=E0401,W0621
"""FR : Tests des fixtures de données de book (natures, copie des adresses clients)


EN : Tests for book data fixtures

created at: 2026-10-11
created by: Paulo ALVES
"""

import pytest

from apps.book.data_fixtures.insert_fixtures import copy_client, fixtures_nature
from apps.parameters.models import Nature

pytestmark = pytest.mark.django_db


def test_fixtures_nature_charge_le_fichier_csv():
    """Les natures du fichier sont créées, un second passage ne crée pas de doublon"""
    fixtures_nature()

    count = Nature.objects.count()
    assert count > 20
    assert Nature.objects.get(name="Monsieur").to_display == "M."
    assert Nature.objects.filter(name="").exists()

    fixtures_nature()

    assert Nature.objects.count() == count


def test_fixtures_nature_ignore_les_conflits(make_nature):
    """Une nature déjà présente avec un autre affichage provoque un conflit d'unicité ignoré"""
    make_nature("Monsieur", to_display="Mr")

    fixtures_nature()

    assert Nature.objects.get(name="Monsieur").to_display == "Mr"
    assert Nature.objects.filter(name="Madame").exists()


def test_copy_client(make_society, make_address, make_country):
    """L'adresse par défaut des clients est recopiée, les tiers sans adresse ou non clients ignorés"""
    france = make_country("FR")
    client = make_society("CLI001", is_client=True)
    make_address(client, "2", line_01="Autre")
    make_address(
        client,
        "1",
        default_adress=True,
        line_01="Immeuble",
        line_02="12 rue",
        postal_code="75001",
        city="Paris",
        country=france,
        phone_number_01="01",
        mobile_number="06",
        email_01="cli@acuitis.com",
    )
    without = make_society("CLI002", is_client=True)
    supplier = make_society("FOUR001", is_client=False)
    make_address(supplier, "1", default_adress=True, line_01="Fournisseur")

    copy_client()

    client.refresh_from_db()
    without.refresh_from_db()
    supplier.refresh_from_db()
    assert (client.immeuble, client.adresse, client.code_postal, client.ville) == (
        "Immeuble",
        "12 rue",
        "75001",
        "Paris",
    )
    assert (client.pays, client.telephone, client.mobile, client.email) == (
        france,
        "01",
        "06",
        "cli@acuitis.com",
    )
    assert without.immeuble is None
    assert supplier.immeuble is None
