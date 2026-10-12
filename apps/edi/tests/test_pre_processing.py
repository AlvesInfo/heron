"""
Tests des pré-traitements de fichiers fournisseurs (apps/edi/bin/edi_pre_processing_pool.py),
sur de vrais fichiers temporaires.

created at: 2026-10-10
created by: Paulo ALVES
"""
import csv
from pathlib import Path

import openpyxl
import pytest

from apps.core.bin import get_sage_elements
from apps.edi.bin import edi_pre_processing_pool as module
from conftest import patched_attrs


def read_csv(path: Path, encoding: str = "utf8") -> list[list[str]]:
    with path.open("r", encoding=encoding, newline="") as file:
        return [row for row in csv.reader(file, delimiter=";", quotechar='"')]


@pytest.fixture
def random_names(monkeypatch):
    """Noms "aléatoires" prévisibles : la première valeur peut déjà exister (boucle de collision)"""
    names = iter(["existant", "libre", "libre2", "libre3"])

    with patched_attrs(monkeypatch, module, get_random_name=lambda: next(names)):
        yield names


# BBGR BULK ========================================================================================


@pytest.mark.usefixtures('random_names')
def test_bulk_translate_file(edi_dirs, tmp_path):
    """Les lignes G21 sont préfixées par la dernière entête E20 ; les lignes vides sont ignorées"""
    (edi_dirs.pre_processing / "existant.csv").write_text("occupé", encoding="utf8")
    source = tmp_path / "bulk.csv"
    source.write_text(
        'E20;"F001 ";AF0001\nG21;ART-1 ;2\n\nG21;ART-2;1\nE20;F002;AF0002\nG21;ART-3;5\nX99;ignore\n',
        encoding="utf8",
    )

    new_file = module.bulk_translate_file(source)

    assert new_file == edi_dirs.pre_processing / "libre.csv"
    assert read_csv(new_file) == [
        ["E20", "F001", "AF0001", "G21", "ART-1", "2"],
        ["E20", "F001", "AF0001", "G21", "ART-2", "1"],
        ["E20", "F002", "AF0002", "G21", "ART-3", "5"],
    ]
    assert source.exists()


# INTERSON =========================================================================================


@pytest.mark.usefixtures('random_names')
def test_interson_translate_file(edi_dirs, tmp_path):
    """Les lignes tabulées sont converties en ; (les ; parasites supprimés), les autres recopiées"""
    (edi_dirs.interson / "existant.csv").write_text("occupé", encoding="utf8")
    source = tmp_path / "interson.csv"
    source.write_bytes(b"a\tb;x\tc\r\nd;e;f\n")

    result = module.interson_translate_file(source)

    assert result == source
    assert read_csv(source) == [["a", "bx", "c"], ["d", "e", "f"]]
    assert [path.name for path in edi_dirs.interson.iterdir()] == ["existant.csv"]


# TRANSFERTS COSIUM ================================================================================


def transfert_line(date: str, qty: str, sender: str = "AF0001", receiver: str = "AF0002") -> list[str]:
    """Ligne du fichier des transferts Cosium : 10 colonnes, envoyeur, receveur, qté, 4 colonnes"""
    return (
        [date, "F-TS", "2026-01-15", "380", "EUR", "PROD1", "Monture", "MONTURES", "OPT", "SN1", sender, receiver, qty, "12.5", "commentaire\r\nmultiligne", "RET1", "2026-01-10"]
    )


@pytest.mark.usefixtures('random_names')
def test_transferts_cosium_file(edi_dirs, tmp_path):
    """Chaque transfert devient deux lignes (envoyeur en négatif, receveur en positif)"""
    (edi_dirs.pre_processing / "existant.csv").write_text("occupé", encoding="utf8")
    source = tmp_path / "transferts.csv"

    with source.open("w", encoding="utf8", newline="") as file:
        writer = csv.writer(file, delimiter=";", quotechar='"')
        writer.writerow(["titre"])
        writer.writerow(["sous-titre"])
        writer.writerow(
            ["date", "n°", "date_fac", "type", "devise", "code_prod.", "libellé", "famille", "type_famille", "num._série", "envoyeur", "receveur", "qté", "prix_achat", "comm.", "rétrocession", "date_facture"]
        )
        writer.writerow(transfert_line("12/01/2026", "3"))
        writer.writerow(transfert_line("2026-01-20", "0"))
        writer.writerow([])
        writer.writerow(transfert_line("2026-01-25", "1"))

    result = module.transferts_cosium_file(source)

    rows = read_csv(result)
    assert result == source
    assert rows[0][:6] == ["third_party_num", "invoice_number", "invoice_date", "invoice_type", "devise", "vat_rate"]
    assert rows[0][6:16] == ["date", "n°", "date_fac", "type", "devise", "code_prod.", "libellé", "famille", "type_famille", "num._série"]
    assert rows[0][16:] == ["code_fournisseur", "code_maison", "qté", "prix_achat", "comm.", "rétrocession", "date_facture"]
    # qté nulle ignorée, ligne vide = fin de fichier : un seul transfert, deux lignes
    assert len(rows) == 3
    sender, receiver = rows[1], rows[2]
    assert sender[:6] == ["ZTRANSFERT", "TS-2026-01-31", "31/01/2026", "380", "EUR", ".2"]
    assert sender[16:19] == ["AF0001", "AF0001", "-3"]
    assert receiver[16:19] == ["AF0002", "AF0002", "3"]
    assert receiver[20] == "commentaire multiligne"


@pytest.mark.usefixtures('edi_dirs', 'random_names')
def test_transferts_cosium_file_sans_ligne_vide(tmp_path):
    """Fichier sans ligne vide finale : toutes les lignes sont traitées"""
    source = tmp_path / "transferts.csv"

    with source.open("w", encoding="utf8", newline="") as file:
        writer = csv.writer(file, delimiter=";", quotechar='"')
        writer.writerow(["titre"])
        writer.writerow(["sous-titre"])
        writer.writerow([f"c{i}" for i in range(17)])
        writer.writerow(transfert_line("12/01/2026", "2"))
        writer.writerow(transfert_line("13/01/2026", "1"))

    module.transferts_cosium_file(source)

    assert len(read_csv(source)) == 5


# JOHNSON ==========================================================================================


def test_johnson_file(tmp_path, make_supplier_definition):
    """Le xlsx est converti en csv, les sous-totaux (*) et lignes sans n° de facture sont supprimés"""
    make_supplier_definition("FluxJohnsonTest")
    supplier = make_supplier_definition("Johnson")
    supplier.first_line = 2
    supplier.save()

    source = tmp_path / "johnson.xlsx"
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.append(["payer", "customer", "billing_nu", "net"])
    sheet.append(["P1", "C1", "F001", 10])
    sheet.append(["P1", "*", "F001", 10])
    sheet.append(["P1", "C1", None, 20])
    sheet.append(["P1", "C2", "F002", 30])
    workbook.save(source)

    new_file = module.johnson_file(source)

    assert new_file == tmp_path / "johnson.csv"
    assert not source.exists()
    assert read_csv(new_file) == [
        ["payer", "customer", "billing_nu", "net"],
        ["P1", "C1", "F001", "10"],
        ["P1", "C2", "F002", "30"],
    ]


# WSAU =============================================================================================


def wsau_line(ident: str, delivery_date: str) -> list[str]:
    line = [f"c{i}" for i in range(19)]
    line[1] = ident
    line[17] = delivery_date
    return line


def test_wsau_file(tmp_path):
    """La date de livraison vide est remplacée, le fichier est réécrit sous son nom d'origine"""
    source = tmp_path / "wsau.csv"

    with source.open("w", encoding="utf8", newline="") as file:
        writer = csv.writer(file, delimiter=";", quotechar='"')
        writer.writerow(wsau_line("WIDE", ""))
        writer.writerow(wsau_line("SIGN", "2026-01-15"))

    assert module.wsau_file(source) is None

    rows = read_csv(source)
    assert [row[17] for row in rows] == ["1900-01-01", "2026-01-15"]
    assert not (tmp_path / "wsau_change.csv").exists()


def test_wsau_file_identifiant_manquant(tmp_path, caplog):
    source = tmp_path / "wsau.csv"

    with source.open("w", encoding="utf8", newline="") as file:
        writer = csv.writer(file, delimiter=";", quotechar='"')
        writer.writerow(wsau_line("WIDE", "2026-01-15"))
        writer.writerow(wsau_line("", "2026-01-15"))
        writer.writerow(wsau_line("", "2026-01-15"))

    with pytest.raises(AttributeError, match="aux lignes : 2, 3"):
        module.wsau_file(source)

    assert source.exists()
    assert "Erreur dans le fichier WSAU" in caplog.text


# Z BU REFAC =======================================================================================


@pytest.fixture
def sage_sections(make_section):
    """Sections Sage de chaque axe, caches des fonctions get_uuid_* vidés"""
    sections = {
        "pys": make_section("PYS", "FR"),
        "pro": make_section("PRO", "OPT"),
        "prj": make_section("PRJ", "NAF"),
        "bu": make_section("BU", "REFAC0"),
        "rfa": make_section("RFA", "NAF"),
    }

    for name in ("get_uuid_pys", "get_uuid_pro", "get_uuid_prj", "get_uuid_bu", "get_uuid_rfa"):
        getattr(get_sage_elements, name).cache_clear()

    yield sections

    for name in ("get_uuid_pys", "get_uuid_pro", "get_uuid_prj", "get_uuid_bu", "get_uuid_rfa"):
        getattr(get_sage_elements, name).cache_clear()


@pytest.mark.usefixtures('random_names')
def test_z_bu_refac_file(edi_dirs, tmp_path, sage_sections):
    """Les axes sont remplacés par leurs uuid, la tva normalisée sur 3 caractères, l'unité agrégée"""
    (edi_dirs.pre_processing / "existant.csv").write_text("occupé", encoding="utf8")
    source = tmp_path / "refac.csv"
    header = ["tiers", "bl", "n_pièce", "date_compta", "compte", "pys", "col", "cct", "prj", "bu", "rfa", "sens", "montant", "tva", "libelle", "unity", "extra"]

    with source.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file, delimiter=";", quotechar='"')
        writer.writerow(header)
        writer.writerow(["ZREFAC0", "BL1", "P1", "2026-01-15", "604000", "FR", "OPT", "AF0001", "NAF", "REFAC0", "NAF", " 1 ", "100", "2", "Refac", "U", "x"])
        writer.writerow(["ZREFAC0", "BL2", "P2", "2026-01-15", "604000", "FR", "OPT", "AF0001", "NAF", "REFAC0", "NAF", "-1", "50", "7", "Refac 2"])

    new_file = module.z_bu_refac_file(source)

    assert new_file == edi_dirs.pre_processing / "libre.csv"
    assert not source.exists()
    rows = read_csv(new_file)
    assert rows[0] == header[:16] + ["vat_regime"]
    first, second = rows[1], rows[2]
    assert first[5:7] == [str(sage_sections["pys"].uuid_identification), str(sage_sections["pro"].uuid_identification)]
    assert first[8:11] == [
        str(sage_sections["prj"].uuid_identification),
        str(sage_sections["bu"].uuid_identification),
        str(sage_sections["rfa"].uuid_identification),
    ]
    assert first[11:17] == ["1", "100", "002", "Refac", "U x", "FRA"]
    assert second[13] == "001"
    assert second[15] == ""
