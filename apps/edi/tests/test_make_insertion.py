"""Tests du module d'insertion des fichiers fournisseurs (apps/edi/bin/make_insertion_suppliers_invoices.py)

- Cache fournisseur : repli dict, faux redis (bytes), redis injoignable.
- make_insert_edi_files : chaîne data_flux réelle (marqueur integration) et chaque branche except.

created at: 2026-10-10
created by: Paulo ALVES
"""

import datetime
import importlib
import io
import types
from decimal import Decimal

import pytest
import redis
from django.db.utils import IntegrityError

from apps.data_flux import exceptions as flux_exceptions
from apps.data_flux.postgres_save import PostgresKeyError, PostgresTypeError
from apps.edi.bin import make_insertion_suppliers_invoices as module
from apps.edi.forms.forms_djantic import forms_invoices
from apps.edi.models import EdiImport
from conftest import patched_attrs


class FakeRedis:
    """Faux redis : stocke et renvoie des bytes comme le vrai client"""

    def __init__(self, fail: bool = False):
        self.data: dict = {}
        self.fail = fail

    def get(self, key):
        if self.fail:
            raise redis.exceptions.ConnectionError("redis injoignable")

        value = self.data.get(key)
        return value.encode() if isinstance(value, str) else value

    def set(self, key, value):
        self.data[key] = value


@pytest.fixture
def cleared_caches():
    """Vide les lru_cache des fonctions fournisseur avant et après le test"""
    functions = [
        module.get_suppliers,
        module.get_supplier_name,
        module.get_supplier_ident,
        module.get_supplier,
        module.get_ident,
    ]

    for function in functions:
        function.cache_clear()

    yield

    for function in functions:
        function.cache_clear()


@pytest.fixture
def dict_cache(monkeypatch, cleared_caches):  # pylint: disable=W0613
    """Cache de repli : un dict"""
    with patched_attrs(monkeypatch, module, cache={}) as patched:
        yield patched.cache


@pytest.fixture
def redis_cache(monkeypatch, cleared_caches):  # pylint: disable=W0613
    """Faux client redis"""
    with patched_attrs(monkeypatch, module, cache=FakeRedis()) as patched:
        yield patched.cache


# CACHE FOURNISSEUR ================================================================================


@pytest.mark.usefixtures("cleared_caches")
def test_get_suppliers(make_supplier_definition):
    make_supplier_definition("Widex", supplier="WIDEX", supplier_ident="Widex")

    assert module.get_suppliers("Widex") == ("WIDEX", "Widex")
    assert module.get_suppliers("Inconnu") == ("", "")


def test_get_supplier_name_et_ident_remplissent_le_dict(make_supplier_definition, dict_cache):
    make_supplier_definition("Lmc", supplier="LMC", supplier_ident="Lmc")

    assert module.get_supplier_name("Lmc") == "LMC"
    assert module.get_supplier_ident("Lmc") == "Lmc"
    assert dict_cache == {"Lmc_supplier": "LMC", "Lmc_ident": "Lmc"}


def test_get_supplier_name_et_ident_remplissent_redis(make_supplier_definition, redis_cache):
    make_supplier_definition("Lmc", supplier="LMC", supplier_ident="Lmc")

    assert module.get_supplier_ident("Lmc") == "Lmc"
    assert module.get_supplier_name("Lmc") == "LMC"
    assert redis_cache.data == {"Lmc_supplier": "LMC", "Lmc_ident": "Lmc"}


def test_get_cached_decode_les_bytes_et_ignore_le_vide(redis_cache):
    redis_cache.set("Widex_supplier", "WIDEX")
    redis_cache.set("Vide_supplier", "")

    assert module.get_cached("Widex_supplier") == "WIDEX"
    assert module.get_cached("Vide_supplier") is None
    assert module.get_cached("Absent") is None


@pytest.mark.usefixtures("cleared_caches")
def test_get_cached_redis_injoignable(monkeypatch):
    with patched_attrs(monkeypatch, module, cache=FakeRedis(fail=True)):
        assert module.get_cached("Widex_supplier") is None


@pytest.mark.usefixtures("db")
def test_get_supplier_depuis_le_cache_sans_base(redis_cache):
    """Valeur en cache : aucune lecture de SupplierDefinition"""
    redis_cache.set("Widex_supplier", "WIDEX CACHE")
    redis_cache.set("Widex_ident", "widex-cache")

    assert module.get_supplier("Widex") == "WIDEX CACHE"
    assert module.get_ident("Widex") == "widex-cache"


def test_get_supplier_depuis_la_base_puis_cache(make_supplier_definition, dict_cache):
    make_supplier_definition("Widex", supplier="WIDEX", supplier_ident="Widex")

    assert module.get_supplier("Widex") == "WIDEX"
    assert module.get_ident("Widex") == "Widex"
    assert dict_cache["Widex_supplier"] == "WIDEX"


@pytest.mark.usefixtures("cleared_caches")
def test_get_supplier_redis_injoignable_retombe_sur_la_base(make_supplier_definition, monkeypatch):
    make_supplier_definition("Widex", supplier="WIDEX", supplier_ident="Widex")

    with patched_attrs(monkeypatch, module, cache=FakeRedis(fail=True)):
        assert module.get_supplier("Widex") == "WIDEX"


def test_import_sans_redis_bascule_sur_le_dict(monkeypatch):
    """Si la construction du client redis échoue, le cache de repli est un dict"""

    def _boom(**_kwargs):
        raise redis.exceptions.ConnectionError("pas de redis")

    with patched_attrs(monkeypatch, redis, StrictRedis=_boom):
        reloaded = importlib.reload(module)
        assert reloaded.cache == {}

    importlib.reload(module)
    assert isinstance(module.cache, redis.StrictRedis)


# MAKE INSERT EDI FILES ============================================================================


@pytest.fixture
def widex_context(column_definitions_data, make_trace, schema_cache_cleared):  # pylint: disable=W0613
    """Trace + paramètres du loader pour le flux Widex (colonnes de l'instantané de production)"""
    from django.utils import timezone  # pylint: disable=C0415

    trace = make_trace(flow_name="Widex", comment="")
    params = {
        "trace": trace,
        "add_fields_dict": {
            "flow_name": "Widex",
            "supplier": "WIDEX",
            "supplier_ident": "Widex",
            "uuid_identification": trace.uuid_identification,
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
        },
    }
    return trace, params


WIDEX_ROW = {
    "code_fournisseur": "AF0001",
    "invoice_type": "380",
    "invoice_number": "WX-1",
    "invoice_date": "15/01/2026",
    "famille": "APPAREILS",
    "reference_article": "ART-WX",
    "libelle": "Appareil auditif",
    "qty": "2",
    "vat_rate": "0.2",
    "net_unit_price": "100",
    "net_amount": "200",
    "amount_with_vat": "240",
    "serial_number": "SN1",
}


@pytest.mark.integration
def test_make_insert_edi_files_insertion_reelle(widex_context, supplier_csv):
    """Lecture csv, validation djantic et insertion réelles d'un fichier Widex"""
    trace, params = widex_context
    file = supplier_csv(
        "Widex", [WIDEX_ROW, {**WIDEX_ROW, "reference_article": "ART-WX2"}], headers=False
    )

    to_print = module.make_insert_edi_files(
        EdiImport, "Widex", file, trace, forms_invoices.get_schema("WidexSchema"), params
    )

    trace.refresh_from_db()
    assert "Import : Widex" in to_print
    assert "Pas d'erreurs" in to_print
    assert trace.errors is False
    assert trace.time_to_process is not None
    rows = EdiImport.objects.filter(uuid_identification=trace.uuid_identification).order_by(
        "reference_article"
    )
    assert [row.reference_article for row in rows] == ["ART-WX", "ART-WX2"]
    first = rows.first()
    assert first.invoice_date == datetime.date(2026, 1, 15)
    assert first.qty == Decimal(2)
    assert first.net_amount == Decimal(200)
    assert (first.supplier, first.supplier_ident, first.flow_name) == ("WIDEX", "Widex", "Widex")


@pytest.mark.integration
def test_make_insert_edi_files_lignes_en_erreur(widex_context, supplier_csv):
    """Une date invalide est rejetée par la validation : trace en erreur, rien d'inséré"""
    trace, params = widex_context
    file = supplier_csv("Widex", [{**WIDEX_ROW, "invoice_date": "pas une date"}], headers=False)

    to_print = module.make_insert_edi_files(
        EdiImport, "Widex", file, trace, forms_invoices.get_schema("WidexSchema"), params
    )

    trace.refresh_from_db()
    assert "Lignes en erreur" in to_print
    assert trace.errors is True
    assert "consulter les logs" in trace.comment
    assert not EdiImport.objects.filter(uuid_identification=trace.uuid_identification).exists()


@pytest.mark.usefixtures("db")
def test_make_insert_edi_files_sans_colonnes(make_trace, tmp_path):
    """Flux sans ColumnDefinition : TypeError attrapée en exception générale"""
    trace = make_trace(flow_name="Inconnu", comment="")

    to_print = module.make_insert_edi_files(
        EdiImport, "Inconnu", tmp_path / "f.csv", trace, None, {"trace": trace}
    )

    trace.refresh_from_db()
    assert to_print == "Import : Inconnu\n"
    assert trace.errors is True


@pytest.mark.parametrize(
    "exception",
    [
        flux_exceptions.GetAddDictError("add"),
        flux_exceptions.IterFileToInsertError("iter"),
        flux_exceptions.ExcelToCsvError("excel"),
        flux_exceptions.FileToCsvError("file"),
        flux_exceptions.OptoDateError("date"),
        flux_exceptions.OptoLinesError("lines"),
        flux_exceptions.OptoQualifierError("qualifier"),
        flux_exceptions.OptoIdError("id"),
        flux_exceptions.OptoNumberError("number"),
        flux_exceptions.OptoParserError("parser"),
        flux_exceptions.PathTypeError("path type"),
        flux_exceptions.PathFileError("path file"),
        PostgresKeyError("key"),
        PostgresTypeError("type"),
        IntegrityError("integrity"),
        RuntimeError("générale"),
    ],
    ids=lambda exc: type(exc).__name__,
)
def test_make_insert_edi_files_chaque_exception(
    exception, widex_context, monkeypatch, tmp_path, caplog
):
    """Chaque exception du loader/validation/upsert est journalisée et met la trace en erreur"""
    trace, params = widex_context

    class _Loader:
        def __init__(self, **_kwargs):
            raise exception

    with patched_attrs(monkeypatch, module, FileLoader=_Loader):
        to_print = module.make_insert_edi_files(
            EdiImport,
            "Widex",
            tmp_path / "f.csv",
            trace,
            forms_invoices.get_schema("WidexSchema"),
            params,
        )

    trace.refresh_from_db()
    assert to_print == "Import : Widex\n"
    assert trace.errors is True
    assert type(exception).__name__ in caplog.text or "Générale" in caplog.text


def test_make_insert_edi_files_flux_edi_utilise_opto33(widex_context, monkeypatch, tmp_path):
    """Le flux Edi passe par Opto33Loader (ici remplacé par un loader qui échoue)"""
    trace, params = widex_context
    seen = {}

    class _Loader:
        def __init__(self, **kwargs):
            seen.update(kwargs)
            raise flux_exceptions.OptoParserError("parser")

    with patched_attrs(monkeypatch, module, Opto33Loader=_Loader):
        module.make_insert_edi_files(
            EdiImport,
            "Edi",
            tmp_path / "f.edi",
            trace,
            forms_invoices.get_schema("EdiSchema"),
            params,
        )

    assert seen["source"] == tmp_path / "f.edi"
    assert "supplier" in seen["columns_dict"]


def test_make_insert_edi_files_trace_deja_en_erreur(widex_context, monkeypatch, tmp_path):
    """Trace déjà en erreur (lignes rejetées en amont) : commentaire complété même sans exception"""
    trace, params = widex_context
    trace.errors = True
    trace.save()

    class _Loader:
        def __init__(self, **_kwargs):
            raise flux_exceptions.PathFileError("fichier")

    with patched_attrs(monkeypatch, module, FileLoader=_Loader):
        module.make_insert_edi_files(
            EdiImport,
            "Widex",
            tmp_path / "f.csv",
            trace,
            forms_invoices.get_schema("WidexSchema"),
            params,
        )

    trace.refresh_from_db()
    assert trace.comment.endswith("Une erreur c'est produite veuillez consulter les logs")


def test_make_insert_edi_files_fermeture_io_deja_fermee(widex_context, monkeypatch, tmp_path):
    """Le buffer de validation fermé par un tiers ne lève pas d'erreur en finally"""
    trace, params = widex_context

    class _ClosedIO:
        """Buffer dont l'état n'est plus interrogeable (AttributeError sur closed)"""

        @property
        def closed(self):
            raise AttributeError("buffer détruit")

    class _Loader:
        def __init__(self, **_kwargs):
            raise flux_exceptions.PathFileError("fichier")

    with (
        patched_attrs(monkeypatch, module, FileLoader=_Loader),
        patched_attrs(monkeypatch, module, io=types.SimpleNamespace(StringIO=_ClosedIO)),
    ):
        to_print = module.make_insert_edi_files(
            EdiImport,
            "Widex",
            tmp_path / "f.csv",
            trace,
            forms_invoices.get_schema("WidexSchema"),
            params,
        )

    assert to_print == "Import : Widex\n"


def test_make_insert_edi_files_buffer_deja_ferme(widex_context, monkeypatch, tmp_path):
    """Buffer déjà fermé : pas de seconde fermeture"""
    trace, params = widex_context

    def _closed_io():
        buffer = io.StringIO()
        buffer.close()
        return buffer

    class _Loader:
        def __init__(self, **_kwargs):
            raise flux_exceptions.PathFileError("fichier")

    with (
        patched_attrs(monkeypatch, module, FileLoader=_Loader),
        patched_attrs(monkeypatch, module, io=types.SimpleNamespace(StringIO=_closed_io)),
    ):
        assert (
            module.make_insert_edi_files(
                EdiImport,
                "Widex",
                tmp_path / "f.csv",
                trace,
                forms_invoices.get_schema("WidexSchema"),
                params,
            )
            == "Import : Widex\n"
        )
