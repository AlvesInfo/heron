# pylint: disable=E0401,W0621
"""FR : Tests des pré/post-traitements des imports Sage (bin/sage_pre_processing.py, bin/sage_post_processing.py)


EN : Tests for Sage imports pre/post processing

created at: 2026-10-10
created by: Paulo ALVES
"""

import csv
import datetime
import uuid
from decimal import Decimal

import pytest

from apps.accountancy.bin import sage_pre_processing
from apps.accountancy.bin.sage_post_processing import rat_vat_correction
from apps.accountancy.bin.sage_pre_processing import mode_reglement_file
from apps.accountancy.models import ModeReglement, VatRatSage
from conftest import csv_file, patched_attrs

pytestmark = pytest.mark.django_db


# POST-PROCESSING ==================================================================================


@pytest.mark.usefixtures("vat_rates_dataset")
def test_rat_vat_correction():
    """Le taux 011 (intracommunautaire) est remis à 0, les autres sont inchangés"""
    rat_vat_correction()

    assert set(VatRatSage.objects.filter(vat="011").values_list("rate", flat=True)) == {Decimal(0)}
    assert set(VatRatSage.objects.filter(vat="001").values_list("rate", flat=True)) == {
        Decimal("19.6"),
        Decimal(20),
    }


def test_rat_vat_correction_sans_011(make_vat_rat):
    """Sans taux 011, rien ne change"""
    make_vat_rat("001", datetime.date(2014, 1, 1), "20")

    rat_vat_correction()

    assert VatRatSage.objects.get().rate == Decimal(20)


# PRE-PROCESSING ===================================================================================


def _read_rows(path):
    with path.open("r", encoding="utf8", newline="") as file:
        return list(csv.reader(file, delimiter=";", quotechar='"'))


def test_mode_reglement_file_reutilise_les_uuid_existants(sage_dirs, make_mode_reglement, tmp_path):
    """Un mode déjà connu garde son uuid, un nouveau reçoit un uuid4, les tildes sont nettoyés"""
    existing = make_mode_reglement("CHQ", name="Chèque", short_name="CHQ", legislation="FRA")
    source = tmp_path / "ZBIMODREG_journalier.heron"

    with csv_file(
        source,
        [
            ["CHQ", "Chèque~~Cheque", "CHQ~~CHQ", "FRA"],
            ["VRT", "Virement", "VRT", "FRA"],
            [],
            ["IGN", "Ignoré après ligne vide", "IGN", "FRA"],
        ],
        quoting=csv.QUOTE_MINIMAL,
    ) as file:
        result = mode_reglement_file(file)
        rows = _read_rows(result)

    assert result == source
    assert len(rows) == 2
    assert rows[0] == ["CHQ", "Chèque", "CHQ", "FRA", str(existing.uuid_identification)]
    assert rows[1][:4] == ["VRT", "Virement", "VRT", "FRA"]
    assert uuid.UUID(rows[1][4]) != existing.uuid_identification
    assert list(sage_dirs.pre_processing.iterdir()) == []
    assert ModeReglement.objects.count() == 1


@pytest.mark.usefixtures("sage_dirs")
def test_mode_reglement_file_mode_different_par_legislation(make_mode_reglement, tmp_path):
    """La recherche porte sur code + nom + nom court + législation : autre législation = nouvel uuid"""
    existing = make_mode_reglement("CHQ", name="Chèque", short_name="CHQ", legislation="FRA")

    with csv_file(tmp_path / "modes.heron", [["CHQ", "Chèque", "CHQ", "BEL"]]) as file:
        rows = _read_rows(mode_reglement_file(file))

    assert rows[0][4] != str(existing.uuid_identification)


def test_mode_reglement_file_evite_les_collisions_de_nom_temporaire(
    sage_dirs, tmp_path, monkeypatch
):
    """Si le nom aléatoire existe déjà dans PRE_PROCESSING, un autre nom est tiré"""
    (sage_dirs.pre_processing / "occupe.csv").write_text("déjà là", encoding="utf8")
    names = iter(["occupe", "libre"])

    with (
        patched_attrs(monkeypatch, sage_pre_processing, get_random_name=lambda: next(names)),
        csv_file(tmp_path / "modes.heron", [["VRT", "Virement", "VRT", "FRA"]]) as file,
    ):
        rows = _read_rows(mode_reglement_file(file))

    assert rows[0][:4] == ["VRT", "Virement", "VRT", "FRA"]
    assert (sage_dirs.pre_processing / "occupe.csv").read_text(encoding="utf8") == "déjà là"
    assert not (sage_dirs.pre_processing / "libre.csv").exists()


@pytest.mark.usefixtures("sage_dirs")
def test_mode_reglement_file_fichier_vide(tmp_path):
    """Un fichier vide produit un fichier vide"""
    with csv_file(tmp_path / "vide.heron", []) as file:
        assert _read_rows(mode_reglement_file(file)) == []
