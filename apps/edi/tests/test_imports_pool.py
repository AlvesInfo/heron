"""Tests du pool d'import des factures fournisseurs (apps/edi/imports/imports_suppliers_invoices_pool.py)

L'insertion (make_insert_edi_files), les pré-traitements de fichiers et les post-traitements SQL
sont remplacés par des enregistreurs : on vérifie la trace créée, le schéma demandé, les champs
ajoutés par le loader et l'enchaînement des appels, ainsi que chaque branche d'erreur.

created at: 2026-10-10
created by: Paulo ALVES
"""

from pathlib import Path

import pytest

from apps.data_flux.models import Trace
from apps.edi.exceptions import EdiException
from apps.edi.imports import imports_suppliers_invoices_pool as pool
from apps.edi.models import EdiImport
from conftest import patched_attrs

# (fonction du pool, flow_name, nom du schéma, post_insert patché, pré-traitement patché)
FILE_FLOWS = [
    ("bbgr_bulk", "BbgrBulk", "BbgrBulkSchema", "bulk_post_insert", "bulk_translate_file"),
    ("cosium", "Cosium", "CosiumSchema", "cosium_post_insert", None),
    ("cosium_achats", "CosiumAchats", "CosiumSchema", "cosium_achats_post_insert", None),
    (
        "transfert_cosium",
        "Transfert",
        "CosiumTransfertSchema",
        "tansferts_cosium_post_insert",
        "transferts_cosium_file",
    ),
    ("edi", "Edi", "EdiSchema", "edi_post_insert", None),
    ("eye_confort", "EyeConfort", "EyeConfortSchema", "eye_confort_post_insert", None),
    ("generique", "Generique", "GeneriqueSchema", "generique_post_insert", None),
    ("hearing", "Hearing", "HearingSchema", "hearing_post_insert", None),
    ("interson", "Interson", "IntersonSchema", "interson_post_insert", "interson_translate_file"),
    ("johnson", "Johnson", "JohnsonSchema", "johnson_post_insert", "johnson_file"),
    ("lmc", "Lmc", "LmcSchema", "lmc_post_insert", None),
    ("newson", "Newson", "NewsonSchema", "newson_post_insert", None),
    ("phonak", "Phonak", "PhonakSchema", "phonak_post_insert", None),
    ("hansaton", "Hansaton", "HansatonSchema", "phonak_post_insert", None),
    ("prodition", "Prodition", "ProditionSchema", "prodition_post_insert", None),
    ("signia", "Signia", "SigniaSchema", "signia_post_insert", None),
    ("starkey", "Starkey", "StarkeySchema", "starkey_post_insert", None),
    ("technidis", "Technidis", "TechnidisSchema", "technidis_post_insert", None),
    ("unitron", "Unitron", "UnitronSchema", "unitron_post_insert", None),
    ("widex", "Widex", "WidexSchema", "widex_post_insert", None),
    ("wsau", "Wsau", "WsauSchema", "widex_post_insert", "wsau_file"),
    ("widex_ga", "WidexGa", "WidexGaSchema", "widexga_post_insert", None),
    ("z_bu_refac", "Zburefac", "ZBuRefacSageSchema", "z_bu_refac_post_insert", "z_bu_refac_file"),
]

# Flux qui ne renseignent pas supplier_ident via le loader
WITHOUT_IDENT = {
    "Cosium",
    "CosiumAchats",
    "Transfert",
    "Edi",
    "Generique",
    "Generique_internal",
    "Wsau",
}
# Flux qui ne renseignent pas non plus supplier via le loader
WITHOUT_SUPPLIER = {"Edi", "Generique", "Generique_internal"}


class FakeSchema:
    """Schéma factice renvoyé par get_schema"""

    def __init__(self, name):
        self.name = name


@pytest.fixture
def pool_recorder(monkeypatch, db):  # pylint: disable=W0613
    """Remplace dans le pool : get_schema, get_supplier/get_ident, make_insert_edi_files,

    tous les *_post_insert, tous les pré-traitements et les insert_bbgr_*_file,
    par des enregistreurs. Renvoie le dict des appels.
    """
    calls = {"schema": [], "insert": [], "post": [], "pre": [], "bbgr": []}

    def _make_insert(model, flow_name, source, trace, validator, params_dict_loader):
        calls["insert"].append(
            {
                "model": model,
                "flow_name": flow_name,
                "source": source,
                "trace": trace,
                "validator": validator,
                "params": params_dict_loader,
            }
        )
        return f"Import : {flow_name}\n\nPas d'erreurs\n"

    def _post(name):
        def _call(uuid_identification, *args, **kwargs):
            calls["post"].append((name, uuid_identification, args, kwargs))

        return _call

    def _pre(name):
        def _call(file):
            calls["pre"].append((name, file))
            return file.with_suffix(".pre") if name != "wsau_file" else None

        return _call

    def _bbgr(name):
        def _call(uuid_identification):
            calls["bbgr"].append((name, uuid_identification))

        return _call

    patches = {
        "get_schema": lambda name: calls["schema"].append(name) or FakeSchema(name),
        "get_supplier": lambda flow: f"SUP-{flow}",
        "get_ident": lambda flow: f"ID-{flow}",
        "make_insert_edi_files": _make_insert,
    }

    for name in dir(pool):
        if name.endswith("_post_insert") or name == "generique_post_insert_internal":
            patches[name] = _post(name)

    for name in [
        "bulk_translate_file",
        "transferts_cosium_file",
        "interson_translate_file",
        "johnson_file",
        "wsau_file",
        "z_bu_refac_file",
    ]:
        patches[name] = _pre(name)

    for name in [
        "insert_bbgr_stament_file",
        "insert_bbgr_monthly_file",
        "insert_bbgr_retours_file",
        "insert_bbgr_receptions_file",
    ]:
        patches[name] = _bbgr(name)

    with patched_attrs(monkeypatch, pool, **patches):
        yield calls


@pytest.fixture
def source_file(tmp_path) -> Path:
    file = tmp_path / "facture.csv"
    file.write_text("a;b;c\n", encoding="utf8")
    return file


# FLUX FICHIERS ====================================================================================


@pytest.mark.parametrize(
    ("function_name", "flow_name", "schema_name", "post_insert", "pre_processing"), FILE_FLOWS
)
def test_import_fichier_fournisseur(
    function_name, flow_name, schema_name, post_insert, pre_processing, pool_recorder, source_file
):
    """Chaque import : trace créée, schéma demandé, champs du loader, insertion puis post-traitement"""
    function = getattr(pool, function_name)
    pre_file = source_file.with_suffix(".pre")

    if pre_processing in {"bulk_translate_file", "z_bu_refac_file"}:
        pre_file.write_text("x", encoding="utf8")  # le pool supprime le fichier pré-traité

    trace, to_print = function(source_file)

    assert isinstance(trace, Trace)
    assert trace.flow_name == flow_name
    assert trace.file_name == source_file.name
    assert trace.application_name == "edi_imports_suppliers_invoices_pool"
    assert to_print == f"Import : {flow_name}\n\nPas d'erreurs\n"
    assert pool_recorder["schema"] == [schema_name]

    insert = pool_recorder["insert"][0]
    assert insert["model"] is EdiImport
    assert insert["flow_name"] == flow_name
    assert insert["trace"] is trace
    assert insert["validator"].name == schema_name

    added = insert["params"]["add_fields_dict"]
    assert added["flow_name"] == flow_name
    assert added["uuid_identification"] == trace.uuid_identification
    assert ("supplier" in added) is (flow_name not in WITHOUT_SUPPLIER)
    assert ("supplier_ident" in added) is (flow_name not in WITHOUT_IDENT)

    if "supplier" in added:
        assert added["supplier"] == f"SUP-{flow_name}"

    if "supplier_ident" in added:
        assert added["supplier_ident"] == f"ID-{flow_name}"

    expected_source = source_file

    if pre_processing:
        assert pool_recorder["pre"] == [(pre_processing, source_file)]

        if pre_processing != "wsau_file":
            expected_source = pre_file

    assert insert["source"] == expected_source
    assert [(name, ident) for name, ident, _, _ in pool_recorder["post"]] == [
        (post_insert, trace.uuid_identification)
    ]

    if pre_processing in {"bulk_translate_file", "z_bu_refac_file"}:
        assert not pre_file.exists()


def test_johnson_exclut_les_lignes_total(pool_recorder, source_file):
    pool.johnson(source_file)

    assert pool_recorder["insert"][0]["params"]["exclude_rows_dict"] == {1: "Total"}


def test_generique_internal_enchaine_les_deux_post_traitements(pool_recorder, source_file):
    trace, to_print = pool.generique_internal(source_file)

    assert trace.flow_name == "Generique_internal"
    assert "Pas d'erreurs" in to_print
    assert pool_recorder["schema"] == ["GeneriqueSchema"]
    assert [(name, kwargs) for name, _, _, kwargs in pool_recorder["post"]] == [
        ("generique_post_insert", {"post": False}),
        ("generique_post_insert_internal", {}),
    ]


def test_edi_sauvegarde_la_trace_avant_insertion(pool_recorder, source_file):
    trace, _ = pool.edi(source_file)

    assert Trace.objects.filter(pk=trace.pk, trace_name="Import Edi - tiers : ").exists()
    assert "supplier" not in pool_recorder["insert"][0]["params"]["add_fields_dict"]


# BRANCHES D'ERREUR ================================================================================


def test_transfert_cosium_erreur_leve_edi_exception(pool_recorder, source_file, monkeypatch):
    def _boom(_file):
        raise ValueError("fichier illisible")

    with patched_attrs(monkeypatch, pool, transferts_cosium_file=_boom):
        with pytest.raises(EdiException, match="transfert_cosium") as excinfo:
            pool.transfert_cosium(source_file)

    assert isinstance(excinfo.value.__cause__, ValueError)
    trace = Trace.objects.get(flow_name="Transfert")
    assert trace.errors is True
    assert trace.invoices is True
    assert "ValueError('fichier illisible')" in trace.comment
    assert pool_recorder["insert"] == []


def test_johnson_erreur_os_sur_la_traduction_excel(pool_recorder, source_file, monkeypatch, caplog):
    """Échec de conversion excel : trace en erreur, fichier source conservé pour le backup"""

    def _boom(_file):
        raise OSError("xls corrompu")

    with patched_attrs(monkeypatch, pool, johnson_file=_boom):
        trace, to_print = pool.johnson(source_file)

    assert to_print == "erreur"
    assert trace.errors is True
    assert "traduction du fichier excel" in trace.comment
    assert source_file.exists()
    assert "xls corrompu" in caplog.text
    assert pool_recorder["post"] == []


@pytest.mark.usefixtures("pool_recorder")
def test_johnson_erreur_generale_apres_traduction(source_file, monkeypatch):
    """Échec après traduction : le csv produit est supprimé, l'original conservé"""
    pre_file = source_file.with_suffix(".pre")
    pre_file.write_text("x", encoding="utf8")

    def _boom(*_args, **_kwargs):
        raise RuntimeError("insertion impossible")

    with patched_attrs(monkeypatch, pool, make_insert_edi_files=_boom):
        trace, to_print = pool.johnson(source_file)

    assert to_print == "erreur"
    assert trace.errors is True
    assert trace.comment == "Une erreur c'est produite veuillez consulter les logs"
    assert not pre_file.exists()
    assert source_file.exists()


@pytest.mark.usefixtures("pool_recorder")
def test_johnson_succes_supprime_le_csv_traduit(source_file):
    pre_file = source_file.with_suffix(".pre")
    pre_file.write_text("x", encoding="utf8")

    trace, _ = pool.johnson(source_file)

    assert trace.errors is False
    assert not pre_file.exists()


def test_wsau_identifiant_manquant(pool_recorder, source_file, monkeypatch, caplog):
    def _boom(_file):
        raise AttributeError("il manque l'identifiant aux lignes : 2")

    with patched_attrs(monkeypatch, pool, wsau_file=_boom):
        trace, to_print = pool.wsau(source_file)

    assert to_print == "erreur"
    assert trace.errors is True
    assert trace.comment == "error"
    assert "la colonne deux du fichier, a un manque" in caplog.text
    assert pool_recorder["insert"] == []


@pytest.mark.usefixtures("pool_recorder")
def test_wsau_erreur_generale(source_file, monkeypatch, caplog):
    def _boom(*_args, **_kwargs):
        raise RuntimeError("upsert impossible")

    with patched_attrs(monkeypatch, pool, make_insert_edi_files=_boom):
        trace, to_print = pool.wsau(source_file)

    assert to_print == "erreur"
    assert trace.errors is True
    assert trace.comment == "Une erreur c'est produite veuillez consulter les logs"
    assert "wsau_file" in caplog.text


# FLUX BBGR DEPUIS LA B.I ==========================================================================


@pytest.mark.parametrize(
    ("function_name", "flow_name", "insert_name", "post_insert"),
    [
        ("bbgr_statment", "BbgrStatment", "insert_bbgr_stament_file", "bbgr_statment_post_insert"),
        ("bbgr_monthly", "BbgrMonthly", "insert_bbgr_monthly_file", "bbgr_monthly_post_insert"),
        ("bbgr_retours", "BbgrRetours", "insert_bbgr_retours_file", "bbgr_retours_post_insert"),
        (
            "bbgr_receptions",
            "BbgrReceptions",
            "insert_bbgr_receptions_file",
            "bbgr_reception_post_insert",
        ),
    ],
)
def test_import_bbgr_depuis_la_bi(
    function_name, flow_name, insert_name, post_insert, pool_recorder
):
    trace, to_print = getattr(pool, function_name)()

    assert trace.flow_name == flow_name
    assert trace.errors is False
    assert to_print == f"Import : {flow_name}\n"
    assert pool_recorder["bbgr"] == [(insert_name, trace.uuid_identification)]
    assert [(name, ident) for name, ident, _, _ in pool_recorder["post"]] == [
        (post_insert, trace.uuid_identification)
    ]


@pytest.mark.parametrize(
    ("function_name", "insert_name"),
    [
        ("bbgr_statment", "insert_bbgr_stament_file"),
        ("bbgr_monthly", "insert_bbgr_monthly_file"),
        ("bbgr_retours", "insert_bbgr_retours_file"),
        ("bbgr_receptions", "insert_bbgr_receptions_file"),
    ],
)
def test_import_bbgr_erreur_insertion(
    function_name, insert_name, pool_recorder, monkeypatch, caplog
):
    """L'erreur d'insertion est journalisée, la trace marquée, le post-traitement exécuté quand même"""

    def _boom(uuid_identification):
        raise RuntimeError("table B.I injoignable")

    with patched_attrs(monkeypatch, pool, **{insert_name: _boom}):
        trace, _ = getattr(pool, function_name)()

    assert trace.errors is True
    assert trace.comment.endswith("Une erreur c'est produite veuillez consulter les logs")
    assert "table B.I injoignable" in caplog.text
    assert len(pool_recorder["post"]) == 1
