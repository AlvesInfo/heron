# pylint: disable=E0401,W0621,R0913
"""
FR : Tests des scripts de fixtures (data_fixtures/insert_fixtures.py, import_clients_from_bi_file.py)
EN : Tests for fixtures scripts

created at: 2026-10-10
created by: Paulo ALVES
"""
import csv
import datetime
from pathlib import Path

import logging

import pytest

from apps.centers_clients.data_fixtures import import_clients_from_bi_file, insert_fixtures
from apps.centers_clients.models import ClientFamilly, Maison

pytestmark = pytest.mark.django_db


# FAMILLES =========================================================================================


def test_fixtures_famillies_depuis_le_csv_du_depot():
    """Le csv livré crée Franchise et Succursale, de façon idempotente"""
    insert_fixtures.fixtures()
    insert_fixtures.fixtures()

    assert list(ClientFamilly.objects.values_list("name", flat=True)) == ["Franchise", "Succursale"]


def test_fixtures_famillies_doublon_de_casse(tmp_path, settings):
    """Un doublon à la casse près lève une IntegrityError à la sauvegarde, avalée par le script"""
    csv_dir = tmp_path / "centers_clients" / "data_fixtures"
    csv_dir.mkdir(parents=True)
    (csv_dir / "famillies.csv").write_text('"franchise"\n"FRANCHISE"\n', encoding="utf8")

    settings.APPS_DIR = tmp_path
    insert_fixtures.fixtures()

    assert list(ClientFamilly.objects.values_list("name", flat=True)) == ["Franchise"]


# IMPORT DEPUIS FICHIER B.I ========================================================================

HEADER = [
    "code_maison", "cct", "third_party_num", "sage_vat_by_default", "center_purchase", "sign_board", "integrable",
    "chargeable", "credit_account", "debit_account", "opening_date", "immeuble", "adresse", "code_postal", "ville",
    "email", "PAYSX3", "Intitulé Compta", "IntituleCourt", "Type Affaire",
]


@pytest.fixture
def import_referentiel(
    make_code_plan, make_account, make_society, make_cct, make_maison_bi, make_child_center, make_signboard,
    make_vat, make_country, make_client_familly, make_type_vente, make_country_currency, make_language,
):
    """Référentiel complet pour l'import csv"""
    make_code_plan("FRA")
    make_account("FRA", "411000", collective=True)
    make_account("FRA", "401000", collective=True)
    make_society("CLI001", is_client=True)
    make_cct("AF0001")
    make_cct("AF0002")
    make_cct("AF0003")
    make_maison_bi("M001", intitule="Maison BI", intitule_court="", adresse="", code_postal="", ville="")
    make_maison_bi("M002", opening_date=None)
    make_child_center("ACF")
    make_signboard("ACF")
    make_vat("001")
    make_country("FR")
    make_client_familly("franchise")
    make_type_vente(0)
    make_country_currency("EUR")
    make_language("FRA")


def _csv(path: Path, rows):
    with path.open("w", encoding="utf8", newline="") as file:
        writer = csv.writer(file, delimiter=";", quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(HEADER)
        writer.writerows(rows)

    return path


@pytest.mark.usefixtures('import_referentiel')
def test_import_file_bi_et_direct(tmp_path, caplog):
    """Ligne avec code B.I (données prises en B.I) et ligne directe (données du csv)"""
    caplog.set_level(logging.INFO, logger="imports")
    file = _csv(
        tmp_path / "import.csv",
        [
            ["M001", "AF0001", "CLI001", "001", "ACF", "ACF", "True", "True", "411000", "401000", "2020-01-01", "", "", "", "", "", "FR", "", "", "Franchise"],
            ["", "AF0002", "CLI001", "001", "ACF", "ACF", "True", "False", "411000", "401000", "2019-05-01", "Bât. B", "2 rue", "69000", "Lyon", "lyon@heron.local;autre@heron.local", "FR", "Maison Lyon", "LYON", "Franchise"],
        ],
    )

    import_clients_from_bi_file.import_file(file)

    maisons = {m.cct.cct: m for m in Maison.objects.all()}
    assert set(maisons) == {"AF0001", "AF0002"}
    assert maisons["AF0001"].intitule == "Maison BI"
    assert maisons["AF0001"].intitule_court == "Maison BI"[:12]
    assert maisons["AF0001"].adresse == "_"
    assert maisons["AF0001"].code_maison == "M001"
    assert maisons["AF0001"].signature_franchise_date == datetime.date(2021, 6, 1)
    assert maisons["AF0002"].intitule == "Maison Lyon"
    assert maisons["AF0002"].email == "lyon@heron.local"
    assert maisons["AF0002"].chargeable is False
    assert maisons["AF0002"].opening_date == datetime.date(2019, 5, 1)
    assert maisons["AF0002"].credit_account.account == "411000"
    assert caplog.text.count("initials dans bi") == 2


@pytest.mark.usefixtures('import_referentiel')
def test_import_file_lignes_invalides(tmp_path, caplog):
    """Formulaires invalides : rien n'est créé, les erreurs sont affichées"""
    caplog.set_level(logging.INFO, logger="imports")
    file = _csv(
        tmp_path / "import.csv",
        [
            # code B.I inconnu : ImportMaisonBiForm invalide, silencieux
            ["ZZZ", "AF0001", "CLI001", "001", "ACF", "ACF", "True", "True", "411000", "401000", "2020-01-01", "", "", "", "", "", "FR", "", "", "Franchise"],
            # maison B.I sans date d'ouverture : MaisonImportForm invalide
            ["M002", "AF0003", "CLI001", "001", "ACF", "ACF", "True", "True", "411000", "401000", "2020-01-01", "", "", "", "", "", "FR", "", "", "Franchise"],
            # directe sans intitulé
            ["", "AF0002", "CLI001", "001", "ACF", "ACF", "True", "True", "411000", "401000", "2019-05-01", "", "2 rue", "69000", "Lyon", "a@b.c", "FR", "", "", "Franchise"],
        ],
    )

    import_clients_from_bi_file.import_file(file)

    out = caplog.text
    assert not Maison.objects.exists()
    assert "depuis B.I :  AF0003  - form_bi :" in out
    assert "opening_date" in out
    assert "direct     :  AF0002  - from :" in out
    assert "intitule" in out
