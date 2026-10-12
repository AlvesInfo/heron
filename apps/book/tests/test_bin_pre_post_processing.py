# pylint: disable=E0401,W0621
"""
FR : Tests des pré/post-traitements des imports Sage de book (bin/book_pre_processing.py,
     bin/book_post_processing.py) et du script de migration GA0000 -> LAB0001
EN : Tests for book Sage imports pre/post processing and the GA0000 -> LAB0001 migration script

created at: 2026-10-11
created by: Paulo ALVES
"""
import csv
import logging

import pytest

from apps.book.bin import book_pre_processing
from apps.book.bin.book_post_processing import adress_sage_post_processing, bpr_book_post_processing
from apps.book.bin.book_pre_processing import (
    bank_book_pre_processing,
    bp_book_pre_processing,
    society_book_pre_processing,
)
from apps.book.bin.migrate_ga000_to_lab0001 import migrate_ga000_to_lab0001
from apps.book.models import Address, Society, SupplierCct
from conftest import csv_file, patched_attrs

pytestmark = pytest.mark.django_db


def _read_rows(path):
    with path.open("r", encoding="utf8", newline="") as file:
        return list(csv.reader(file, delimiter=";", quotechar='"'))


# PRÉ-TRAITEMENT TIERS FOURNISSEURS / CLIENTS ======================================================


@pytest.fixture
def societies(make_society):
    make_society("FOUR001", is_client=False, is_supplier=True, is_physical_person=True)
    make_society("CLI001", is_client=True)


def test_bp_book_pre_processing(societies, make_payment_condition, tmp_path):
    """Condition de paiement remplacée par son auuid (COMPTANT par défaut), types du tiers ajoutés"""
    thirty = make_payment_condition("30J")
    cash = make_payment_condition("COMPTANT")

    with csv_file(
        tmp_path / "ZBIBPS_journalier.heron",
        [["FOUR001", "30J", "FRA", "FOU"], ["CLI001", "INCONNU", "FRA", "CLI"], [], ["ABSENT", "30J", "FRA", "X"]],
        quoting=csv.QUOTE_MINIMAL,
    ) as file:
        bp_book_pre_processing(tmp_path, file)
        rows = _read_rows(file)

    assert rows == [
        ["FOUR001", thirty.auuid, "FRA", "FOU", "1", "1", "1", "2", "1", "1", "1", "1", "2"],
        ["CLI001", cash.auuid, "FRA", "CLI", "2", "1", "1", "1", "1", "1", "1", "1", "1"],
    ]
    assert [path.name for path in tmp_path.iterdir()] == []


def test_bp_book_pre_processing_sans_condition_comptant(societies, tmp_path):
    """Sans condition COMPTANT ni code connu, la colonne reste vide"""
    with csv_file(tmp_path / "ZBIBPC_journalier.heron", [["CLI001", "INCONNU", "FRA", "CLI"]]) as file:
        bp_book_pre_processing(tmp_path, file)
        rows = _read_rows(file)

    assert rows[0][:4] == ["CLI001", "", "FRA", "CLI"]


def test_bp_book_pre_processing_evite_les_collisions_de_nom_temporaire(societies, tmp_path, monkeypatch):
    """Si le nom aléatoire existe déjà, un autre nom est tiré"""
    (tmp_path / "occupe.csv").write_text("déjà là", encoding="utf8")
    names = iter(["occupe", "libre"])

    with patched_attrs(monkeypatch, book_pre_processing, get_random_name=lambda: next(names)), csv_file(
        tmp_path / "ZBIBPS_journalier.heron", [["FOUR001", "30J", "FRA", "FOU"]]
    ) as file:
        bp_book_pre_processing(tmp_path, file)
        rows = _read_rows(file)

    assert rows[0][0] == "FOUR001"
    assert (tmp_path / "occupe.csv").read_text(encoding="utf8") == "déjà là"
    assert not (tmp_path / "libre.csv").exists()


# PRÉ-TRAITEMENT ADRESSES ET BANQUES ===============================================================


def test_society_book_pre_processing_garde_les_tiers_connus(societies, tmp_path):
    with csv_file(
        tmp_path / "ZBIADDR_journalier.heron",
        [["FOUR001", "2", "1"], [], ["ABSENT", "2", "1"], ["CLI001", "1", "2"]],
        quoting=csv.QUOTE_MINIMAL,
    ) as file:
        society_book_pre_processing(tmp_path, file)
        rows = _read_rows(file)

    assert rows == [["FOUR001", "2", "1"], ["CLI001", "1", "2"]]
    assert [path.name for path in tmp_path.iterdir()] == []


def test_society_book_pre_processing_collision_de_nom(societies, tmp_path, monkeypatch):
    (tmp_path / "occupe.csv").write_text("déjà là", encoding="utf8")
    names = iter(["occupe", "libre"])

    with patched_attrs(monkeypatch, book_pre_processing, get_random_name=lambda: next(names)), csv_file(
        tmp_path / "ZBIADDR_journalier.heron", [["FOUR001", "2", "1"]]
    ) as file:
        society_book_pre_processing(tmp_path, file)
        rows = _read_rows(file)

    assert rows == [["FOUR001", "2", "1"]]


def test_bank_book_pre_processing_dedoublonne(societies, tmp_path):
    """Une banque par couple tiers / compte, tiers inconnus et lignes vides ignorés"""
    with csv_file(
        tmp_path / "ZBIBANK_journalier.heron",
        [["FOUR001", "FR01", "a"], ["FOUR001", "FR01", "b"], [], ["ABSENT", "FR01", "c"], ["FOUR001", "FR02", "d"]],
        quoting=csv.QUOTE_MINIMAL,
    ) as file:
        bank_book_pre_processing(tmp_path, file)
        rows = _read_rows(file)

    assert rows == [["FOUR001", "FR01", "a"], ["FOUR001", "FR02", "d"]]


def test_bank_book_pre_processing_collision_de_nom(societies, tmp_path, monkeypatch):
    (tmp_path / "occupe.csv").write_text("déjà là", encoding="utf8")
    names = iter(["occupe", "libre"])

    with patched_attrs(monkeypatch, book_pre_processing, get_random_name=lambda: next(names)), csv_file(
        tmp_path / "ZBIBANK_journalier.heron", [["FOUR001", "FR01", "a"]]
    ) as file:
        bank_book_pre_processing(tmp_path, file)
        rows = _read_rows(file)

    assert rows == [["FOUR001", "FR01", "a"]]


# POST-TRAITEMENT TIERS ============================================================================


def test_bpr_book_post_processing(make_society):
    """Drapeaux null remis aux défauts du modèle, nom et nom court complétés"""
    make_society("TIERS01", name=None, short_name=None, integrable=None, chargeable=None, od_ana=None)
    make_society("TIERS02", name="Un nom de tiers de plus de vingt caractères", short_name="", integrable=False, od_ana=True)

    bpr_book_post_processing()

    first = Society.objects.get(third_party_num="TIERS01")
    second = Society.objects.get(third_party_num="TIERS02")
    assert (first.integrable, first.chargeable, first.od_ana) == (True, True, False)
    assert (first.name, first.short_name) == ("TIERS01", "TIERS01")
    assert (second.integrable, second.od_ana) == (False, True)
    assert second.short_name == "Un nom de tiers de p"


def test_bpr_book_post_processing_sans_defaut_de_modele(monkeypatch):
    """Un champ sans valeur par défaut déclarée est remis à False"""
    from django.db.models.fields import NOT_PROVIDED  # pylint: disable=C0415

    with patched_attrs(monkeypatch, Society._meta.get_field("integrable"), default=NOT_PROVIDED):  # pylint: disable=W0212
        bpr_book_post_processing()


# POST-TRAITEMENT ADRESSES =========================================================================


def test_adress_sage_post_processing(make_society, make_address, make_country):
    """Les 'None' textuels sont annulés et l'adresse 1 de Sage est recopiée sur le tiers"""
    france = make_country("FR")
    society = make_society("TIERS01", adresse="None", code_postal="NONE", ville="Vieille ville", pays=None, email="none")
    make_address(
        society,
        "1",
        line_01="Immeuble A",
        line_02="None",
        line_03="12 rue de la Paix",
        postal_code="75001",
        city="Paris",
        country=france,
        email_01="contact@acuitis.com",
        phone_number_01="None",
        phone_number_02="0102030405",
        mobile_number="0601020304",
    )
    make_address(society, "2", line_01="Autre", line_03="Ailleurs", city="Lyon")
    other = make_society("TIERS02", adresse="None", ville="Lyon")

    adress_sage_post_processing()

    society.refresh_from_db()
    other.refresh_from_db()
    address = Address.objects.get(society=society, address_code="1")
    assert address.line_02 is None
    assert address.phone_number_01 is None
    assert address.phone_number_02 == "0102030405"
    assert society.address_code == "1"
    assert society.immeuble == "Immeuble A"
    assert society.adresse == "12 rue de la Paix"
    assert (society.code_postal, society.ville, society.pays) == ("75001", "Paris", france)
    assert (society.email_01, society.phone_number_01, society.mobile_number) == ("contact@acuitis.com", None, "0601020304")
    assert society.email is None
    assert (other.adresse, other.ville) == (None, "Lyon")


def test_adress_sage_post_processing_immeuble_sur_deux_lignes(make_society, make_address):
    society = make_society("TIERS01")
    make_address(society, "1", line_01="Bât. A", line_02="Escalier 2")
    second = make_society("TIERS02")
    make_address(second, "1", line_01=None, line_02="Escalier 3")

    adress_sage_post_processing()

    society.refresh_from_db()
    second.refresh_from_db()
    assert society.immeuble == "Bât. A - Escalier 2"
    assert society.adresse == ""
    assert second.immeuble == "Escalier 3"


# MIGRATION GA0000 -> LAB0001 ======================================================================


def test_migrate_ga000_to_lab0001(make_society, make_cct, make_supplier_cct, caplog):
    """Les identifiants de GA0000 sont fusionnés dans LAB0001, GA0000 reçoit ZZZ"""
    ga0000 = make_cct("GA0000")
    lab0001 = make_cct("LAB0001")
    four1 = make_society("FOUR001", is_client=False)
    four2 = make_society("FOUR002", is_client=False)
    four3 = make_society("FOUR003", is_client=False)
    ga_1 = make_supplier_cct(four1, ga0000, "GA|COMMUN|")
    lab_1 = make_supplier_cct(four1, lab0001, " LAB|COMMUN")
    ga_2 = make_supplier_cct(four2, ga0000, None)
    lab_2 = make_supplier_cct(four2, lab0001, "ZZZ|")
    ga_3 = make_supplier_cct(four3, ga0000, "SEUL|")
    make_supplier_cct(make_society("FOUR004", is_client=False), lab0001, "RESTE|")

    with caplog.at_level(logging.ERROR, logger="imports"):
        migrate_ga000_to_lab0001()

    for supplier_cct in (ga_1, lab_1, ga_2, lab_2, ga_3):
        supplier_cct.refresh_from_db()
    assert (ga_1.cct_identifier, lab_1.cct_identifier) == ("ZZZ|", "COMMUN|GA|LAB|")
    assert (ga_2.cct_identifier, lab_2.cct_identifier) == ("ZZZ|", "")
    assert ga_3.cct_identifier == "SEUL|"
    assert "FOUR003 : pas de cct LAB0001, GA0000 conservé" in caplog.text
    assert SupplierCct.objects.get(third_party_num="FOUR004").cct_identifier == "RESTE|"
