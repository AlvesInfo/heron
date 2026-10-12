# pylint: disable=E0401,W0621
"""FR : Tests de l'import des maisons depuis la B.I (imports/import_maisons_bi.py)


EN : Tests for shops import from B.I

Commentaire:

En production heron_bi_maisons et heron_directbi_maisons sont des tables distantes (FDW).
Les tests les créent comme tables ordinaires dans la transaction de test.

created at: 2026-10-10
created by: Paulo ALVES
"""

import datetime

import pytest
from django.db import connection

from apps.centers_clients.imports.import_maisons_bi import import_maisons_bi
from apps.centers_clients.models import MaisonBi

pytestmark = pytest.mark.django_db

COLUMNS = (
    "code_maison, intitule, affaire, intitule_court, code_cosium, reference_cosium, compte_bbgr, "
    "date_ouverture, date_fermeture, immeuble, adresse, code_postal, ville, pays_x3, telephone, email"
)
DDL = "({cols})".format(
    cols=", ".join(
        f"{name} {'date' if name.startswith('date_') else 'text'}" for name in COLUMNS.split(", ")
    )
)


@pytest.fixture
def bi_tables(make_country):
    """Crée les deux tables B.I vides et retourne une fonction d'insertion"""
    make_country("FR", "France")
    make_country("BE", "Belgique")

    with connection.cursor() as cursor:
        cursor.execute(f"create table heron_bi_maisons {DDL}")
        cursor.execute(f"create table heron_directbi_maisons {DDL}")

    def _insert(table, **values):
        row = {
            "code_maison": "M001",
            "intitule": "Maison Un",
            "affaire": "",
            "intitule_court": "MU",
            "code_cosium": "C1",
            "reference_cosium": "R1",
            "compte_bbgr": "B1",
            "date_ouverture": datetime.date(2020, 1, 1),
            "date_fermeture": None,
            "immeuble": "",
            "adresse": "1 rue",
            "code_postal": "75001",
            "ville": "Paris",
            "pays_x3": "FR",
            "telephone": "01",
            "email": "un@heron.local",
        }
        row.update(values)
        placeholders = ", ".join(f"%({name})s" for name in row)

        with connection.cursor() as cursor:
            cursor.execute(f"insert into {table} ({', '.join(row)}) values ({placeholders})", row)

    return _insert


def test_import_cree_les_maisons(bi_tables):
    """Création depuis les deux sources, préfixe DO pour Direct Optic, affaire prioritaire"""
    bi_tables("heron_bi_maisons", code_maison="M001", affaire="Affaire Un")
    bi_tables("heron_bi_maisons", code_maison="M002", pays_x3="BE")
    bi_tables("heron_directbi_maisons", code_maison="DO123", reference_cosium="ignorée")
    bi_tables("heron_directbi_maisons", code_maison="456")

    result = import_maisons_bi()

    assert result == "4 maisons importées ou mises à jour"
    maisons = {m.code_maison: m for m in MaisonBi.objects.all()}
    assert set(maisons) == {"M001", "M002", "DO123", "DO456"}
    assert maisons["M001"].intitule_court == "Affaire Un"
    assert maisons["M001"].pays.country == "FR"
    assert maisons["M002"].pays.country == "BE"
    assert maisons["DO123"].reference_cosium == ""
    assert maisons["DO456"].code_bbgr == "B1"
    assert all(m.is_new and not m.is_modify for m in maisons.values())


def test_import_pays_inconnu_bascule_sur_fr(bi_tables):
    """Un pays X3 inconnu est remplacé par FR"""
    bi_tables("heron_bi_maisons", code_maison="M001", pays_x3="ZZ")

    import_maisons_bi()

    assert MaisonBi.objects.get(code_maison="M001").pays.country == "FR"


def test_import_inchange_puis_modifie(bi_tables):
    """Un second import identique ne marque rien ; une modification en B.I est répercutée"""
    bi_tables("heron_bi_maisons", code_maison="M001")
    import_maisons_bi()

    import_maisons_bi()
    assert MaisonBi.objects.get(code_maison="M001").is_modify is False

    with connection.cursor() as cursor:
        cursor.execute("update heron_bi_maisons set ville = 'Lyon', code_postal = '69000'")

    import_maisons_bi()

    maison = MaisonBi.objects.get(code_maison="M001")
    assert maison.is_modify is True
    assert maison.ville == "Lyon"
    assert maison.code_postal == "69000"


@pytest.mark.usefixtures("bi_tables")
def test_import_sans_lignes():
    """Tables vides : zéro maison"""
    assert import_maisons_bi() == "0 maisons importées ou mises à jour"
    assert not MaisonBi.objects.exists()
