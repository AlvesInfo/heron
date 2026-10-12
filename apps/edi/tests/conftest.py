"""Fabriques propres aux tests de l'app edi"""

import csv
import datetime
import types
import uuid
from collections.abc import Callable, Iterable
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from django.db import connection

from conftest import next_code


@pytest.fixture
def make_supplier_definition(db):
    """Fabrique idempotente de edi.SupplierDefinition"""
    from apps.edi.models import SupplierDefinition  # pylint: disable=C0415

    def _make(flow_name, **kwargs):
        defaults = {
            "supplier": kwargs.pop("supplier", flow_name.upper()),
            "supplier_ident": kwargs.pop("supplier_ident", flow_name),
            "directory": kwargs.pop("directory", flow_name.upper()),
            **kwargs,
        }
        supplier, _ = SupplierDefinition.objects.get_or_create(
            flow_name=flow_name, defaults=defaults
        )
        return supplier

    return _make


@pytest.fixture
def make_column_definitions(make_supplier_definition):
    """Fabrique des edi.ColumnDefinition d'un flux : `columns` est la liste ordonnée des

    (attr_name, file_column), le rang étant la position dans la liste. Les définitions
    existantes du flux (instantané de production éventuellement chargé) sont remplacées pour la
    durée du test.
    """
    from apps.edi.models import ColumnDefinition  # pylint: disable=C0415

    def _make(flow_name, columns):
        supplier = make_supplier_definition(flow_name)
        ColumnDefinition.objects.filter(flow_name=supplier).delete()
        return [
            ColumnDefinition.objects.create(
                flow_name=supplier, ranking=ranking, attr_name=attr_name, file_column=file_column
            )
            for ranking, (attr_name, file_column) in enumerate(columns)
        ]

    return _make


@pytest.fixture
def schema_cache_cleared():
    """Vide le cache des schémas djantic avant et après le test"""
    from apps.edi.forms.forms_djantic.forms_invoices import get_schema  # pylint: disable=C0415

    get_schema.cache_clear()
    yield
    get_schema.cache_clear()


# ==================================================================================================
# RÉPERTOIRES, TABLES B.I ET FABRIQUES PROPRES À L'APP EDI
# ==================================================================================================

# Répertoires de dépôt des fichiers fournisseurs (clés de processing_dict du pool / des loops)
SUPPLIER_DIRECTORIES = [
    "BBGR_BULK",
    "COSIUM",
    "COSIUM_ACHATS",
    "EDI",
    "EYE_CONFORT",
    "GENERIQUE",
    "GENERIQUE_INTERNAL",
    "HANSATON",
    "HEARING",
    "INTERSON",
    "JOHNSON",
    "LMC",
    "NEWSON",
    "PHONAK",
    "PRODITION",
    "SIGNIA",
    "STARKEY",
    "TECHNIDIS",
    "TRANSFERTS",
    "UNITRON",
    "WIDEX",
    "WSAU",
    "WIDEX_GA",
    "SAGE_YOOZ_REFAC0",
]

# Tables B.I (FDW en production), créées en DDL dans la transaction de test
BI_TABLES = {
    "heron_bi_factures_billstatement": {
        "id": "integer",
        "boutique_bbgr": "text",
        "boutique_acuitis": "text",
        "nom_boutique": "text",
        "ref_cde_acuitis": "text",
        "livraison": "text",
        "date_livraison": "date",
        "transaction": "text",
        "date_transaction": "date",
        "type_transaction": "text",
        "article": "text",
        "article_facturation": "text",
        "famille": "text",
        "qte_facturee": "numeric",
        "prix_unitaire": "numeric",
        "montant_ht": "numeric",
        "code_tva": "numeric",
        "montant_tva": "numeric",
        "montant_ttc": "numeric",
        "statistique": "text",
    },
    "heron_bi_factures_monthlydelivery": {
        "id": "integer",
        "type_article": "text",
        "boutique_bbgr": "text",
        "boutique_acuitis": "text",
        "nom_boutique": "text",
        "customer_po_number": "text",
        "livraison": "text",
        "date_livraison": "date",
        "no_facture_acuitis": "text",
        "date_mouvement": "date",
        "qte_expediee": "numeric",
        "article": "text",
        "description": "text",
        "famille": "text",
        "prix_unitaire": "numeric",
        "montant_ht": "numeric",
        "taux_tva": "numeric",
        "montant_tva": "numeric",
        "montant_ttc": "numeric",
        "statistique": "text",
    },
    "heron_bi_receptions_bbgr": {
        "id": "integer",
        "entered_date": "date",
        "entered_valorise": "numeric",
        "type_article": "text",
        "famille": "text",
    },
    # Table de la base B.I (alias bi_bdd, miroir de default en test)
    "factures_monthlyretours": {"id": "integer", "validation": "boolean"},
}

BI_DEFAULTS: dict[str, dict] = {
    "heron_bi_factures_billstatement": {
        "boutique_bbgr": "BB001",
        "boutique_acuitis": "AF0001",
        "nom_boutique": "Maison test",
        "ref_cde_acuitis": "CDE1",
        "livraison": "BL1",
        "date_livraison": datetime.date(2026, 1, 10),
        "transaction": "TR1",
        "date_transaction": datetime.date(2026, 1, 15),
        "type_transaction": "INV",
        "article": "ART-1",
        "article_facturation": "Verre unifocal",
        "famille": "VERRES",
        "qte_facturee": Decimal(1),
        "prix_unitaire": Decimal(10),
        "montant_ht": Decimal(10),
        "code_tva": Decimal("0.2"),
        "montant_tva": Decimal(2),
        "montant_ttc": Decimal(12),
        "statistique": "VER",
    },
    "heron_bi_factures_monthlydelivery": {
        "type_article": "MONTURE",
        "boutique_bbgr": "BB001",
        "boutique_acuitis": "AF0001",
        "nom_boutique": "Maison test",
        "customer_po_number": "PO1",
        "livraison": "BL1",
        "date_livraison": datetime.date(2026, 1, 10),
        "no_facture_acuitis": "FA1",
        "date_mouvement": datetime.date(2026, 1, 15),
        "qte_expediee": Decimal(1),
        "article": "ART-1",
        "description": "Monture",
        "famille": "MONTURES",
        "prix_unitaire": Decimal(10),
        "montant_ht": Decimal(10),
        "taux_tva": Decimal("0.2"),
        "montant_tva": Decimal(2),
        "montant_ttc": Decimal(12),
        "statistique": "MON",
    },
    "heron_bi_receptions_bbgr": {
        "entered_date": datetime.date(2026, 1, 15),
        "entered_valorise": Decimal(100),
        "type_article": "VERRE",
        "famille": "VERRES",
    },
    "factures_monthlyretours": {"validation": True},
}


@pytest.fixture
def edi_dirs(tmp_path: Path, settings) -> types.SimpleNamespace:
    """Redirige les répertoires des fichiers fournisseurs (processing, backup, pré-traitement,

    Interson) vers tmp_path, avec un sous-répertoire par flux, pour ne jamais écrire dans files/.
    """
    dirs = types.SimpleNamespace(
        processing=tmp_path / "processing",
        backup=tmp_path / "backup",
        pre_processing=tmp_path / "processing" / "PRE_PROCESSING",
        interson=tmp_path / "processing" / "INTERSON",
    )

    for name in SUPPLIER_DIRECTORIES:
        (dirs.processing / name).mkdir(parents=True, exist_ok=True)
        (dirs.backup / name).mkdir(parents=True, exist_ok=True)

    dirs.pre_processing.mkdir(parents=True, exist_ok=True)

    settings.PROCESSING_SUPPLIERS_DIR = dirs.processing
    settings.BACKUP_SUPPLIERS_DIR = dirs.backup
    settings.PRE_PROCESSING = dirs.pre_processing
    settings.INTERSON = dirs.interson
    return dirs


@pytest.fixture
def bi_tables(db) -> Callable[..., int]:  # pylint: disable=W0613
    """Crée les tables B.I BBGR (statment, monthly/retours, réceptions) et la table de validation

    des retours de la base B.I, puis renvoie une fonction d'insertion :
    `insert_bi("heron_bi_factures_billstatement", id=5, montant_ht=12)` -> id inséré.
    """
    with connection.cursor() as cursor:
        for table, columns in BI_TABLES.items():
            ddl = ", ".join(f'"{name}" {kind}' for name, kind in columns.items())
            cursor.execute(f'create table if not exists "{table}" ({ddl})')

    counters = dict.fromkeys(BI_TABLES, 0)

    def _insert(table: str, **values: Any) -> int:
        counters[table] += 1
        row = {"id": counters[table], **BI_DEFAULTS[table]}
        row.update(values)
        columns = ", ".join(f'"{name}"' for name in row)
        placeholders = ", ".join(f"%({name})s" for name in row)

        with connection.cursor() as cursor:
            cursor.execute(f'insert into "{table}" ({columns}) values ({placeholders})', row)

        return row["id"]

    return _insert


@pytest.fixture
def make_action(db) -> Callable[..., Any]:  # pylint: disable=W0613
    """Fabrique idempotente de parameters.ActionInProgress"""
    from apps.parameters.models import ActionInProgress  # pylint: disable=C0415

    def _factory(action: str = "import_edi_invoices", in_progress: bool = False, **kwargs: Any):
        obj, _ = ActionInProgress.objects.get_or_create(
            action=action, defaults={"in_progress": in_progress, "comment": action, **kwargs}
        )

        if obj.in_progress != in_progress:
            obj.in_progress = in_progress
            obj.save()

        return obj

    return _factory


@pytest.fixture
def make_counter(db) -> Callable[..., Any]:  # pylint: disable=W0613
    """Fabrique de compteurs parameters.Counter (+ CounterNums initialisé)"""
    from apps.parameters.models import Counter, CounterNums  # pylint: disable=C0415

    def _factory(name: str = "invoices_manual_entries_nums", num: int = 1, **kwargs: Any):
        defaults = {"lpad_num": 5, "separateur": "-"}
        defaults.update(kwargs)
        counter, _ = Counter.objects.get_or_create(name=name, defaults=defaults)
        CounterNums.objects.get_or_create(counter=counter, defaults={"num": num})
        return counter

    return _factory


@pytest.fixture
def make_sse_progress(make_user) -> Callable[..., Any]:
    """Fabrique de core.SSEProgress (jauge de progression des tâches)"""
    from apps.core.models import SSEProgress  # pylint: disable=C0415

    def _factory(job_id: str | None = None, user=None, **kwargs: Any):
        defaults = {
            "task_type": "edi_import",
            "total_items": 1,
            "metadata": {"success": [], "failed": []},
        }
        defaults.update(kwargs)
        return SSEProgress.objects.create(
            job_id=job_id or str(uuid.uuid4()), user=user or make_user(), **defaults
        )

    return _factory


def _positional_line(positions: dict[str, int], width: int, values: dict[str, Any]) -> list[str]:
    """Ligne csv de `width` colonnes : chaque valeur placée à la position de son attribut"""
    line = [""] * width

    for attr, value in values.items():
        line[positions[attr]] = "" if value is None else str(value)

    return line


@pytest.fixture
def supplier_csv(tmp_path: Path) -> Callable[..., Path]:
    """Écrit un fichier fournisseur csv à partir des edi.ColumnDefinition du flux (instantané ou

    fabriques) : chaque ligne est un dict attr_name -> valeur, placée dans la colonne
    `file_column` (index numérique) ; les colonnes non renseignées sont vides.
    `supplier_csv("Widex", [{"invoice_number": "F1", ...}], first_line=1, delimiter=";")`
    """
    from apps.edi.models import ColumnDefinition  # pylint: disable=C0415

    def _factory(
        flow_name: str,
        rows: Iterable[dict[str, Any]],
        directory: Path | None = None,
        name: str | None = None,
        headers: bool = True,
        delimiter: str = ";",
        encoding: str = "utf8",
    ) -> Path:
        columns = (
            ColumnDefinition.objects.filter(flow_name=flow_name)  # type: ignore[misc]
            .order_by("ranking")
            .values_list("attr_name", "file_column")
        )
        positions = {
            attr: int(col) for attr, col in columns if col is not None and str(col).isnumeric()
        }
        width = max(positions.values(), default=0) + 1
        path = (directory or tmp_path) / (name or f"{flow_name.lower()}_{next_code('F')}.csv")
        header = (
            [_positional_line(positions, width, {attr: attr for attr in positions})]
            if headers
            else []
        )

        with path.open("w", encoding=encoding, newline="") as file:
            writer = csv.writer(file, delimiter=delimiter, quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writerows(header + [_positional_line(positions, width, row) for row in rows])

        return path

    return _factory


# Fixtures des modules d'aide de l'app (collectées ici, plus d'import dans les tests)
from apps.edi.tests.helpers_post import (  # noqa: E402,F401  pylint: disable=W0611,C0413
    edi_batch,
    icon_origins,
    make_vat_rat,
    pg_is_date,
    units,
)
