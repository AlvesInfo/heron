# pylint: disable=E0401,W0621,W0212
"""FR : Tests de l'app od : OD à passer depuis un fichier csv (modèle, schéma, import, validations,


     numérotation Sage) et export X3 sur le journal ODINV
EN : Tests for od app: OD to post from a csv file and X3 export on ODINV journal

created at: 2026-10-11
created by: Paulo ALVES
"""

import csv
import datetime
import importlib
from decimal import Decimal
from pathlib import Path

import pytest
from django.apps import apps as django_apps
from pydantic import ValidationError

from apps.od.apps import OdConfig
from apps.od.bin import export_od_inv
from apps.od.bin.export_od_inv import write_odinv
from apps.od.forms import OdSchema
from apps.od.imports import od_a_passer
from apps.od.imports.od_a_passer import (
    import_od_a_passer,
    import_od_files,
    set_base_sage_invoice_number,
    update_blank_account,
    update_blank_facture_heron,
    validation_accounts,
    validation_amounts,
    validation_axes,
    validation_cct,
    validation_third_party_num,
)
from apps.od.models import ModelOd
from apps.parameters.models import Counter, CounterNums
from conftest import patched_attrs

pytestmark = pytest.mark.django_db

COLUMNS = list(ModelOd.get_columns_import())


@pytest.fixture
def od_env(settings, tmp_path, monkeypatch):
    """Répertoires de processing et d'export redirigés, compteurs generic et gaspar_num"""
    processing = tmp_path / "processing"
    export = tmp_path / "export"
    processing.mkdir()
    export.mkdir()
    settings.EXPORT_DIR = export
    monkeypatch.setattr(od_a_passer, "proccessing_dir", processing)

    for name, lpad in (("generic", 5), ("gaspar_num", 3)):
        counter = Counter.objects.create(name=name, lpad_num=lpad, separateur="")
        CounterNums.objects.create(counter=counter, num=1)

    return {"processing": processing, "export": export}


@pytest.fixture
def make_od():
    """Fabrique de lignes d'OD à passer"""

    def _factory(**kwargs):
        defaults = {
            "date_od": datetime.date(2025, 3, 31),
            "libelle_od": "OD mars",
            "date_extourne": datetime.date(2025, 4, 1),
            "libelle_extourne": "Extourne avril",
            "compte_produit": "707000",
            "compte_tva": "445710",
            "compte_collectif": "411000",
            "code_plan": "FRA",
            "journal": "ODINV",
            "type_ecriture": "OD",
            "facture_heron": "FAC000000001234",
            "libelle": "Abonnement",
            "third_party_num": "TIERS01",
            "axe_bu": "CAHA",
            "cct": "AF0001",
            "axe_pro": "OPT",
            "axe_prj": "NAF",
            "axe_pys": "FR",
            "axe_rfa": "NAF",
            "montant_ht": Decimal(100),
            "vat": "001",
            "montant_tva": Decimal(20),
            "montant_ttc": Decimal(120),
        }
        defaults.update(kwargs)
        return ModelOd.objects.create(**defaults)

    return _factory


@pytest.fixture
def referentiel(make_account, make_section, make_cct, make_society):
    """Comptes, axes, cct et tiers Sage auxquels les OD doivent correspondre"""
    make_account("FRA", "707000", nb_axes=2, call_code="")
    make_account("FRA", "445710", nb_axes=0)
    make_account("FRA", "411000", nb_axes=2, call_code="411000")
    for axe, section in (
        ("BU", "CAHA"),
        ("CCT", "AF0001"),
        ("PRO", "OPT"),
        ("PRJ", "NAF"),
        ("PYS", "FR"),
        ("RFA", "NAF"),
    ):
        make_section(axe, section)
    make_cct("AF0001")
    make_society("TIERS01")


def _write_csv(path, rows):
    with path.open("w", encoding="utf8", newline="") as file:
        writer = csv.writer(file, delimiter=";", quotechar='"', lineterminator="\n")
        writer.writerow(COLUMNS)
        writer.writerows(rows)

    return path


def _csv_row(**overrides):
    row = {
        "date_od": "31/03/2025",
        "libelle_od": "OD mars",
        "date_extourne": "01/04/2025",
        "libelle_extourne": "Extourne",
        "compte_produit": "707000",
        "compte_tva": "445710",
        "compte_collectif": "411000",
        "journal": "ODINV",
        "type_ecriture": "OD",
        "facture_heron": "FAC000000001234",
        "libelle": "Abonnement",
        "third_party_num": "TIERS01",
        "code_plan": "FRA",
        "axe_bu": "CAHA",
        "cct": "AF0001",
        "axe_pro": "OPT",
        "axe_prj": "NAF",
        "axe_pys": "FR",
        "axe_rfa": "NAF",
        "montant_ht": "100",
        "vat": "001",
        "montant_tva": "20",
        "montant_ttc": "120",
    }
    row.update(overrides)
    return [row[column] for column in COLUMNS]


# CONFIGURATION, MODÈLE ET SCHÉMA ==================================================================


def test_app_config_et_modele(make_od):
    config = django_apps.get_app_config("od")
    od_line = make_od()

    assert isinstance(config, OdConfig)
    assert config.name == "apps.od"
    assert [model.__name__ for model in config.get_models()] == ["ModelOd"]
    assert str(od_line) == "OD mars - ODINV"
    assert set(COLUMNS) <= {field.name for field in ModelOd._meta.fields}
    assert all(key == value for key, value in ModelOd.get_columns_import().items())
    assert ModelOd.get_uniques() == {}
    assert od_line.get_import == "methode d'import à retourner"
    assert od_line.base_sage_invoice_number is None


@pytest.mark.parametrize(
    "module_name",
    ["apps.od.admin", "apps.od.bin", "apps.od.forms", "apps.od.imports", "apps.od.sql_files"],
)
def test_packages_importables(module_name):
    assert importlib.import_module(module_name) is not None


def test_schema_dates_excel_et_troncature():
    """Dates jj/mm/aaaa, textes tronqués au max_length, montants décimaux, dates techniques posées"""
    validated = OdSchema(
        date_od="31/03/2025",
        date_extourne="01/04/2025",
        code_plan="FRA",
        journal="ODINV",
        type_ecriture="OD",
        libelle="L" * 40,
        third_party_num="TIERS01",
        axe_bu="CAHA",
        cct="AF0001",
        axe_pro="OPT",
        axe_prj="NAF",
        axe_pys="FR",
        axe_rfa="NAF",
        montant_ht="100.5",
        vat="001",
        montant_tva="20.1",
        montant_ttc="120.6",
    ).dict()

    assert OdSchema.model_config["model"] is ModelOd
    assert OdSchema.model_config["include"] == [*COLUMNS, "created_at", "modified_at"]
    assert validated["date_od"] == datetime.date(2025, 3, 31)
    assert validated["date_extourne"] == datetime.date(2025, 4, 1)
    assert len(validated["libelle"]) == 30
    assert validated["montant_ttc"] == Decimal("120.6")
    assert validated["compte_produit"] is None
    assert isinstance(validated["created_at"], datetime.datetime)


def test_schema_date_obligatoire():
    with pytest.raises(ValidationError) as excinfo:
        OdSchema(
            date_od="",
            date_extourne="01/04/2025",
            code_plan="FRA",
            journal="ODINV",
            type_ecriture="OD",
            libelle="x",
            third_party_num="T",
            axe_bu="B",
            cct="C",
            axe_pro="P",
            axe_prj="J",
            axe_pys="Y",
            axe_rfa="R",
            vat="001",
        )

    assert {error["loc"][0] for error in excinfo.value.errors()} == {"date_od"}


# IMPORT D'UN FICHIER ==============================================================================


def test_import_od_a_passer_unitaire(od_env, monkeypatch):
    """Trace nominative et insertion en mode insert (pas de clé unique)"""
    calls = []

    def _recorder(model, flow_name, source, trace, validator, params_dict_loader, **kwargs):
        calls.append((model, flow_name, source, trace, validator, params_dict_loader, kwargs))
        return "Import : ModelOd\n\nPas d'erreurs\n"

    file = _write_csv(od_env["processing"] / "od.csv", [_csv_row()])

    with patched_attrs(monkeypatch, od_a_passer, make_insert=_recorder):
        trace, to_print = import_od_a_passer(file)

    model, flow_name, source, call_trace, validator, loader, kwargs = calls[0]
    assert (trace.trace_name, trace.flow_name, trace.application_name) == (
        "Import od à passer",
        "ModelOd",
        "import_od_a_passer",
    )
    assert trace.comment == "import du fichier od.csv, des OD à passer"
    assert "Pas d'erreurs" in to_print
    assert (model, flow_name, source, call_trace, validator) == (
        ModelOd,
        "ModelOd",
        file,
        trace,
        OdSchema,
    )
    assert loader["trace"] is trace
    assert set(loader["add_fields_dict"]) == {"created_at", "modified_at"}
    assert kwargs == {"insert_mode": "insert"}


@pytest.mark.integration
def test_import_od_a_passer_integration(od_env):
    """Chaîne data_flux réelle : colonnes par nom d'entête, dates et montants convertis"""
    file = _write_csv(
        od_env["processing"] / "od.csv",
        [
            _csv_row(),
            _csv_row(
                libelle="Second",
                compte_produit="",
                montant_ht="50",
                montant_tva="10",
                montant_ttc="60",
            ),
        ],
    )

    trace, to_print = import_od_a_passer(file)

    lines = {line.libelle: line for line in ModelOd.objects.all()}
    assert "Pas d'erreurs" in to_print
    assert trace.errors is False
    assert set(lines) == {"Abonnement", "Second"}
    assert (lines["Abonnement"].date_od, lines["Abonnement"].montant_ttc) == (
        datetime.date(2025, 3, 31),
        Decimal(120),
    )
    assert lines["Second"].compte_produit is None


# VALIDATIONS ET MISES À JOUR ======================================================================


def test_validation_amounts(make_od):
    make_od(libelle="Equilibrée")
    assert validation_amounts(False, "ok") == (False, "ok")

    make_od(
        libelle="Fausse",
        montant_ht=Decimal(100),
        montant_tva=Decimal(20),
        montant_ttc=Decimal(121),
    )
    error, message = validation_amounts(False, "ok")

    assert error is True
    assert (
        message
        == '<span>- la ligne "Fausse : (100.00000 + 20.00000) - (121.00000)" est déséquilibrée</span><br>'
    )


def test_update_blank_account_et_facture(make_od):
    blank = make_od(compte_produit=None, compte_tva=None, compte_collectif=None, facture_heron=None)
    kept = make_od()

    update_blank_account()
    update_blank_facture_heron()

    blank.refresh_from_db()
    kept.refresh_from_db()
    assert (
        blank.compte_produit,
        blank.compte_tva,
        blank.compte_collectif,
        blank.facture_heron,
    ) == ("", "", "", "")
    assert (kept.compte_produit, kept.facture_heron) == ("707000", "FAC000000001234")


def test_set_base_sage_invoice_number(od_env, make_od):
    """Facture Héron longue : ses 12 derniers caractères après le préfixe ; sinon numéro du compteur generic"""
    long_one = make_od(facture_heron="FAC000000001234")
    same = make_od(facture_heron="FAC000000001234", libelle="Même facture")
    short = make_od(facture_heron="FA12")
    empty = make_od(facture_heron="")

    set_base_sage_invoice_number()

    for line in (long_one, same, short, empty):
        line.refresh_from_db()
    assert long_one.base_sage_invoice_number == "000000001234"
    assert same.base_sage_invoice_number == "000000001234"
    assert {short.base_sage_invoice_number, empty.base_sage_invoice_number} == {"00001", "00002"}
    assert CounterNums.objects.get(counter__name="generic").num == 3


@pytest.mark.parametrize(
    ("validation", "overrides", "expected"),
    [
        (validation_accounts, {"compte_tva": "999999"}, '" a un compte comptable qui est erroné'),
        (validation_axes, {"axe_pro": "ZZZ"}, '" a un axe qui est erroné'),
        (validation_cct, {"cct": "AF9999"}, '" a un cct qui est erroné'),
        (validation_third_party_num, {"third_party_num": "ABSENT"}, '" a un tiers qui est erroné'),
    ],
)
def test_validations_referentiel(referentiel, make_od, validation, overrides, expected):
    """Sans écart : état inchangé ; avec une ligne hors référentiel : erreur et message détaillé"""
    make_od(libelle="Conforme")
    assert validation(False, "ok") == (False, "ok")

    make_od(libelle="Fausse", **overrides)
    error, message = validation(False, "ok")

    assert error is True
    assert message.startswith('<span>- la ligne "Fausse : (100.00000 + 20.00000) - (120.00000) : ')
    assert message.endswith(expected + "</span><br>")
    assert "Conforme" not in message


def test_validation_axes_message_complet(referentiel, make_od):
    make_od(libelle="Fausse", axe_pys="XX")

    _, message = validation_axes(False, "")

    assert " : axe_bu=CAHA : axe_pro=OPT : axe_prj=NAF : axe_pys=XX : axe_rfa=NAF" in message


# BOUCLE D'IMPORT ==================================================================================


@pytest.mark.integration
def test_import_od_files_nominal(od_env, referentiel, make_od):
    """La table est vidée, les fichiers csv intégrés, validés et numérotés"""
    make_od(libelle="Ancienne")
    _write_csv(od_env["processing"] / "od_1.csv", [_csv_row()])
    _write_csv(od_env["processing"] / "od_2.csv", [_csv_row(libelle="Second", facture_heron="")])
    (od_env["processing"] / "notes.txt").write_text("ignoré", encoding="utf8")

    error, message = import_od_files()

    lines = {line.libelle: line for line in ModelOd.objects.all()}
    assert error is False
    assert (
        message
        == "<span>- le fichier od_1.csv a été intégrer avec succes</span><br><span>- le fichier od_2.csv a été intégrer avec succes</span><br>"
    )
    assert set(lines) == {"Abonnement", "Second"}
    assert lines["Abonnement"].base_sage_invoice_number == "000000001234"
    assert lines["Second"].base_sage_invoice_number == "00001"
    assert lines["Second"].facture_heron == ""


@pytest.mark.integration
def test_import_od_files_fichier_en_erreur(od_env, referentiel):
    """Un fichier invalide vide la table et arrête l'import"""
    _write_csv(od_env["processing"] / "od_1.csv", [_csv_row(date_od="pas une date")])

    error, message = import_od_files()

    assert error is True
    assert (
        message
        == '<span>- le fichier "od_1.csv" a générer une erreur veillez consulter les traces</span><br>'
    )
    assert ModelOd.objects.count() == 0


@pytest.mark.integration
@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"montant_ttc": "121"}, "est déséquilibrée"),
        ({"compte_collectif": "999999"}, "a un compte comptable qui est erroné"),
        ({"axe_bu": "ZZZ"}, "a un axe qui est erroné"),
        ({"cct": "AF9999"}, "a un cct qui est erroné"),
        ({"third_party_num": "ABSENT"}, "a un tiers qui est erroné"),
    ],
)
def test_import_od_files_arret_sur_validation(od_env, referentiel, overrides, expected):
    _write_csv(od_env["processing"] / "od.csv", [_csv_row(**overrides)])

    error, message = import_od_files()

    assert error is True
    assert expected in message
    assert ModelOd.objects.count() == 1


# EXPORT X3 ========================================================================================


def _read_lines(path: Path):
    with path.open(encoding="iso8859_1", newline="") as handle:
        return [line.split(";") for line in handle.read().split("\r\n")[:-1]]


@pytest.mark.usefixtures("od_env")
def test_write_odinv_sans_od():
    assert write_odinv("AC00", file_name="vide.txt") is None


@pytest.mark.integration
def test_write_odinv_fichier_nomme(od_env, referentiel, make_od):
    """Une OD donne une pièce OD et sa pièce d'extourne : collectif, produit et tva avec analytique"""
    make_od(base_sage_invoice_number="000000001234")

    write_odinv("AC00", file_name="odinv.txt")

    lines = _read_lines(od_env["export"] / "odinv.txt")
    kinds = [line[0] for line in lines]
    assert kinds == ["G", "D", "A", "D", "A", "D", "G", "D", "A", "D", "A", "D"]
    headers = [line for line in lines if line[0] == "G"]
    assert headers[0][1:4] == ["ODINV", "OD250331000000001234", "AC00"]
    assert headers[1][2] == "OD250401000000001234"
    assert headers[0][5] == "310325"
    collectif = lines[1]
    assert (collectif[1], collectif[3], collectif[5], collectif[8], collectif[9]) == (
        "1",
        "1",
        "411000",
        "411000",
        "TIERS01",
    )
    assert collectif[12] == "120,00"
    assert lines[2][1] == "1"
    assert lines[2][8:14] == ["CAHA", "AF0001", "OPT", "NAF", "FR", "NAF"]
    assert [line[8] for line in lines if line[0] == "D"][:3] == ["411000", "707000", "445710"]
    assert list(od_env["export"].iterdir()) == [od_env["export"] / "odinv.txt"]


@pytest.mark.integration
def test_write_odinv_fichiers_numerotes_par_lot(od_env, referentiel, make_od):
    """Sans nom de fichier : un fichier par lot de nb_fac pièces, numérotés par le compteur gaspar"""
    make_od(base_sage_invoice_number="000000000001", facture_heron="FAC000000000001")
    make_od(
        base_sage_invoice_number="000000000002",
        facture_heron="FAC000000000002",
        date_od=datetime.date(2025, 5, 31),
        date_extourne=datetime.date(2025, 6, 1),
    )

    write_odinv("AC00", nb_fac=3)

    files = sorted(path.name for path in od_env["export"].iterdir())
    assert files == ["AC00_001.txt", "AC00_002.txt"]
    first = _read_lines(od_env["export"] / "AC00_001.txt")
    second = _read_lines(od_env["export"] / "AC00_002.txt")
    assert [line[0] for line in first].count("G") == 3
    assert [line[0] for line in second].count("G") == 1


def test_write_odinv_regroupe_les_lignes_d(od_env, monkeypatch):
    """Lignes de même compte dans une pièce : une seule ligne D, autant de lignes A"""

    def _line(invoice, account, with_a=True):
        g_block = [
            "G",
            "ODINV",
            invoice,
            "AC00",
            "ODINV",
            "310325",
            "STDCO",
            "EUR",
            "lib",
            "doc",
            "ref",
        ]
        d_block = [
            "D",
            0,
            "2",
            0,
            "AC00",
            "",
            "AFR",
            "FRA",
            account,
            "TIERS01",
            1,
            "EUR",
            Decimal(10),
            "des",
            "",
            "707000",
        ]
        a_block = [
            "A",
            0,
            "BU",
            "CCT",
            "PRO",
            "PRJ",
            "PYS",
            "RFA",
            "CAHA",
            "AF0001",
            "OPT",
            "NAF",
            "FR",
            "NAF",
            Decimal(10),
            1,
        ]
        return [invoice, *g_block, *d_block, "A" if with_a else "", *a_block, 1]

    rows = [
        _line("OD1", "411000"),
        _line("OD1", "411000"),
        _line("OD1", "707000", with_a=False),
        _line("OD2", "411000"),
    ]

    with patched_attrs(monkeypatch, export_od_inv, get_rows=lambda *_args, **_kwargs: iter(rows)):
        write_odinv("AC00", file_name="regroupe.txt")

    lines = _read_lines(od_env["export"] / "regroupe.txt")
    assert [line[0] for line in lines] == ["G", "D", "A", "A", "D", "G", "D", "A"]
    assert [line[1] for line in lines if line[0] == "A"] == ["1", "2", "1"]
    assert [line[3] for line in lines if line[0] == "D"] == ["1", "2", "1"]

    rows = [_line("OD1", "445710", with_a=False), _line("OD1", "707000")]

    with patched_attrs(monkeypatch, export_od_inv, get_rows=lambda *_args, **_kwargs: iter(rows)):
        write_odinv("AC00", file_name="sans_a.txt")

    assert [line[0] for line in _read_lines(od_env["export"] / "sans_a.txt")] == [
        "G",
        "D",
        "D",
        "A",
    ]
