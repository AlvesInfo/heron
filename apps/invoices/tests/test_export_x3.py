# pylint: disable=E0401,W0621,W0611,R0913
"""Tests des exports X3 (fichiers texte Sage) : fonctions de base, exports par type, dispatch"""

import datetime
import logging
from decimal import Decimal
from pathlib import Path

import pytest
from django.db import connection

from apps.invoices.bin import (
    base_export_x3_functions as base,
    export_x3,
    export_x3_odana_invoices as odana,
    export_x3_purchase_do_invoices as do_,
    export_x3_purchase_gdaud_invoices as gdaud,
    export_x3_purchase_invoices as purchase,
    export_x3_purchase_sdoa_invoices as sdoa,
    export_x3_sale_invoices as sale,
)
from apps.invoices.tests.helpers_external import reload_with_node

pytestmark = pytest.mark.django_db
EXPORT_MODULES = [sale, purchase, sdoa, gdaud, do_, odana]


@pytest.fixture
def x3_env(monkeypatch, email_dirs, make_counter):
    """Connexion 'heron' redirigée vers la connexion de test, compteurs des fichiers, répertoire export"""
    for module in EXPORT_MODULES:
        monkeypatch.setattr(module, "connections", {"heron": connection})

    # Compteurs distincts : les exports odana / sale / purchase nomment tous leurs fichiers
    # <fcy>_<num>.txt, un même numéro écraserait le fichier d'un autre export
    for name, start in (("bicpar_num", 1), ("bispar_num", 101), ("gaspar_num", 201)):
        make_counter(name, num=start, lpad_num=3, separateur="")

    return email_dirs.export


def read_lines(path: Path):
    """Lignes du fichier X3 (fins de ligne \\r\\n conservées à la lecture)"""
    with path.open(encoding="iso8859_1", newline="") as handle:
        return handle.read().split("\r\n")[:-1]


# FONCTIONS DE BASE ================================================================================
def test_get_clean_line_et_ecritures(tmp_path):
    assert base.get_clean_line([Decimal("1.5"), None, "a;b", 3]) == "1,5;;a.b;3\r\n"
    file = tmp_path / "x.txt"

    with file.open("w", newline="") as handle:
        base.get_t(handle, ["T", "x"])
        base.get_d_invoices(handle, ["D", 0, "y"], idtlin=2)
        base.get_d_od_ana(handle, ["D", 0, "z", 0], idtlin=3)
        base.get_a(handle, ["A", 0], idtlin=4)
        base.get_e(handle, ["E", 0], idtlin=5)

    assert read_lines(file) == ["T;x", "D;2;y", "D;3;z;3", "A;4", "E;5"]
    assert base.split_line([1, 2, 3], lambda line: (line[:1], line[1:])) == ([1], [2, 3])


def test_get_file_numerote_les_fichiers(x3_env):
    from apps.invoices.bin.invoives_nums import get_bicpar_num

    with base.get_file(x3_env, "AC00", get_bicpar_num) as handle:
        handle.write("ok")

    assert (x3_env / "AC00_001.txt").read_text() == "ok"


@pytest.mark.usefixtures("x3_env")
def test_get_rows_sql_reel():
    rows = list(
        base.get_rows(
            connection,
            __import__("heron.settings", fromlist=["x"]).APPS_DIR,
            "AC00",
            "sql_export_x3_sale_invoices",
        )
    )

    assert rows == []


# EXPORT RÉEL DES VENTES ===========================================================================
def test_write_bicpar_sql_reel(x3_env, make_sale_invoice, make_sale_detail_external, make_account):
    """Deux factures AC00 : lignes T/D/A, compte sans axe (pas de A), écart TTC -> ligne 445710"""
    make_account("FRA", "707000", nb_axes=6, call_code="")
    make_account("FRA", "708000", nb_axes=0)
    first = make_sale_invoice(
        cct="AF0001",
        fcy="AC00",
        code_plan_sage="FRA",
        code_signboard="ACF",
        invoice_amount_with_tax=Decimal(120),
    )
    make_sale_detail_external(first, net_amount=Decimal(100), account="707000")
    second = make_sale_invoice(
        cct="AF0002",
        fcy="AC00",
        code_plan_sage="FRA",
        invoice_type_name="Avoir",
        invoice_amount_with_tax=Decimal(121),
    )
    make_sale_detail_external(second, net_amount=Decimal(100), account="708000")
    make_sale_invoice(cct="AF0003", fcy="GA00")  # autre site : ignoré
    make_sale_invoice(cct="AF0004", fcy="AC00", export=True)  # déjà exporté

    sale.write_bicpar("AC00", file_name="ventes.txt")

    lines = read_lines(x3_env / "ventes.txt")
    kinds = [line[0] for line in lines]
    assert kinds.count("T") == 2
    assert "A" in kinds  # analytique sur le compte à 6 axes
    assert any(
        line.startswith("D;") and "445710" in line for line in lines
    )  # écart de TVA de l'avoir
    assert any("707000" in line and "100" in line for line in lines if line.startswith("D;"))
    assert all(";" in line for line in lines)


def test_write_bicpar_sans_lignes(x3_env):
    assert sale.write_bicpar("AC00") is None
    assert list(x3_env.iterdir()) == []


# EXPORT RÉEL DES ACHATS ===========================================================================
def test_write_bispar_et_bispard_sql_reel(
    x3_env, make_invoice, make_purchase_detail, make_account, make_cct
):
    make_account("FRA", "607000", nb_axes=6, call_code="401")
    make_account("FRA", "608000", nb_axes=0)
    cct = make_cct("AF0001")
    first = make_invoice(
        fcy="AC00",
        code_plan_sage="FRA",
        code_signboard="ACF",
        mode_reglement="VIR",
        date_echeance=datetime.date(2026, 2, 28),
        integration_month=datetime.date(2026, 2, 1),
    )
    make_purchase_detail(first, cct, account="607000")
    make_purchase_detail(first, cct, account="607000", vat="002")
    second = make_invoice(
        third_party_num="FOUR002", fcy="AC00", code_plan_sage="FRA", invoice_type_name="Avoir"
    )
    make_purchase_detail(second, cct, account="608000")
    make_invoice(fcy="AC00", export=True)

    purchase.write_bispar("AC00", file_name="achats.txt")
    purchase.write_bispard("AC00", file_name="achats_d.txt")

    for name in ("achats.txt", "achats_d.txt"):
        lines = read_lines(x3_env / name)
        kinds = [line[0] for line in lines]
        assert kinds.count("T") == 2
        assert kinds.count("E") == 2
        assert kinds.count("L") == 3  # deux taux de TVA sur la première facture
        assert "A" in kinds

    assert purchase.write_bispar("GA00") is None
    assert purchase.write_bispard("GA00") is None


# EXPORTS DES CENTRALES / OD ANA : SQL exécutées (sans données) ===================================
@pytest.mark.parametrize(
    ("function", "fcy"),
    [
        (sdoa.write_bispar_sdoa, "SD00"),
        (gdaud.write_bispar_gdaud, "GA00"),
        (do_.write_bispar_do, "DO00"),
        (odana.write_odana, "AC00"),
    ],
)
@pytest.mark.usefixtures("x3_env")
def test_exports_centrales_sql_sans_lignes(function, fcy):
    assert function(fcy) is None


# BOUCLES D'ÉCRITURE SUR DES LIGNES SIMULÉES ======================================================
def rows_for(kind: str, invoices, with_a=True):
    """Lignes de requête simulées pour chaque type d'export (tailles des tranches T/D/A/E)"""
    sizes = {
        "sale": (16, 14, 16, 0),
        "purchase": (17, 13, 16, 7),
        "purchase_d": (18, 13, 16, 7),
        "sdoa": (17, 13, 16, 7),
        "odana": (11, 16, 16, 0),
    }[kind]
    rows = []

    for number, d_values in invoices:
        for index, d_value in enumerate(d_values):
            t = ["T", number] + ["t"] * (sizes[0] - 2)
            d = ["D", 0, d_value] + ["d"] * (sizes[1] - 3)
            a = ["A", 0, f"a{index}"] + ["a"] * (sizes[2] - 3)
            e = (["E", 0] + ["e"] * (sizes[3] - 2)) if sizes[3] else []
            rows.append([number, *t, *d, *a, *e, with_a])

    return rows


def fake_rows(monkeypatch, module, rows):
    monkeypatch.setattr(module, "get_rows", lambda *args, **kwargs: iter(list(rows)))


def test_write_bicpar_boucles(x3_env, monkeypatch):
    """Deux D par facture (A répétés), changement de facture et découpage à nb_fac"""
    fake_rows(
        monkeypatch,
        sale,
        rows_for("sale", [("F1", ["d1", "d1", "d2"]), ("F2", ["d1"]), ("F3", ["d1"])], with_a=True),
    )

    sale.write_bicpar("AC00", nb_fac=1)

    files = sorted(x3_env.iterdir())
    assert [file.name for file in files] == ["AC00_001.txt", "AC00_002.txt", "AC00_003.txt"]
    first = read_lines(files[0])
    assert [line[0] for line in first] == ["T", "D", "A", "A", "D", "A"]
    assert first[1].startswith("D;1;d1")
    assert first[4].startswith("D;2;d2")

    fake_rows(monkeypatch, sale, rows_for("sale", [("F1", ["d1"])], with_a=False))
    sale.write_bicpar("AC00", file_name="sans_a.txt")
    assert [line[0] for line in read_lines(x3_env / "sans_a.txt")] == ["T", "D"]


@pytest.mark.parametrize(
    ("module", "function", "kind"),
    [
        (purchase, purchase.write_bispar, "purchase"),
        (purchase, purchase.write_bispard, "purchase_d"),
        (sdoa, sdoa.write_bispar_sdoa, "sdoa"),
        (gdaud, gdaud.write_bispar_gdaud, "sdoa"),
        (do_, do_.write_bispar_do, "sdoa"),
    ],
)
def test_write_achats_boucles(x3_env, monkeypatch, module, function, kind):
    fake_rows(
        monkeypatch,
        module,
        rows_for(kind, [("F1", ["d1", "d1", "d2"]), ("F2", ["d1"]), ("F3", ["d1"])]),
    )

    function("AC00", nb_fac=1)

    files = sorted(x3_env.iterdir())
    assert len(files) == 3
    first = read_lines(files[0])
    assert [line[0] for line in first] == ["T", "D", "A", "A", "D", "A", "E"]

    for file in files:
        file.unlink()

    fake_rows(monkeypatch, module, rows_for(kind, [("F1", ["d1"]), ("F2", ["d1"])], with_a=False))
    function("AC00", file_name="deux.txt", nb_fac=10)
    assert [line[0] for line in read_lines(x3_env / "deux.txt")] == ["T", "D", "E", "T", "D", "E"]


def test_write_odana_boucles(x3_env, monkeypatch):
    fake_rows(
        monkeypatch,
        odana,
        rows_for("odana", [("F1", ["d1", "d1", "d2"]), ("F2", ["d1"]), ("F3", ["d1"])]),
    )

    odana.write_odana("AC00", nb_fac=1)

    files = sorted(x3_env.iterdir())
    assert len(files) == 3
    first = read_lines(files[0])
    assert [line[0] for line in first] == ["T", "D", "A", "A", "D", "A"]
    assert first[1].split(";")[1] == "1"
    assert first[1].split(";")[3] == "1"

    fake_rows(monkeypatch, odana, rows_for("odana", [("F1", ["d1"]), ("F2", ["d1"])]))
    odana.write_odana("AC00", file_name="od.txt", nb_fac=10)
    assert [line[0] for line in read_lines(x3_env / "od.txt")] == ["T", "D", "A", "T", "D", "A"]


# DISPATCH =========================================================================================
def test_export_files_x3(monkeypatch, caplog):
    calls = []
    for name in (
        "write_odana",
        "write_bicpar",
        "write_bispard",
        "write_bispar_gdaud",
        "write_bispar_sdoa",
        "write_bispar_do",
    ):
        monkeypatch.setattr(
            export_x3,
            name,
            lambda centrale, file_name, nb_fac, name=name: calls.append(
                (name, centrale, file_name, nb_fac)
            ),
        )

    for export_type in ("odana", "sale", "purchase", "gdaud", "sdoa", "do"):
        trace, to_print = export_x3.export_files_x3(export_type, "AC00", "f.txt", 10)
        assert trace.errors is False
        assert to_print == ""

    assert [call[0] for call in calls] == [
        "write_odana",
        "write_bicpar",
        "write_bispard",
        "write_bispar_gdaud",
        "write_bispar_sdoa",
        "write_bispar_do",
    ]
    assert trace.time_to_process >= 0

    with caplog.at_level(logging.ERROR, logger="export_x3"):
        trace, _ = export_x3.export_files_x3("inconnu", "AC00", "f.txt", 10)

    assert trace.errors is True
    assert trace.comment.count("Une erreur c'est produite") == 1
    assert "(inconnu)" in trace.comment
    assert "AC00" in trace.comment


@pytest.mark.parametrize(("node", "expected"), [("MSI", "/"), ("serveur", "/home/paulo/heron")])
def test_base_dir_selon_la_machine(monkeypatch, node, expected):
    assert reload_with_node(monkeypatch, export_x3, node) == expected
