# pylint: disable=E0401,W0621,C0415,W0611
"""FR : Fixtures du chantier "noyau" de apps/invoices (insertions, contrôles, finalisation).


     Importées explicitement par les modules de tests : `from apps.invoices.tests.helpers_core import *`
EN : Core fixtures for invoices tests

created at: 2026-10-10
created by: Paulo ALVES
"""

import datetime
import types
import uuid
from collections.abc import Callable
from decimal import Decimal
from typing import Any

import pytest

PURCHASE_COUNTER_UUID = uuid.UUID("ad95c27f-9800-46d4-8e63-55191023f0a4")
SALES_COUNTER_UUID = uuid.UUID("8aad17a2-90a8-4a72-a8c6-caccdadf5a8b")
BILLING_DATE = datetime.date(2026, 1, 31)


@pytest.fixture
def make_counter(db) -> Callable[..., Any]:  # pylint: disable=W0613
    """Fabrique de compteurs parameters.Counter (+ CounterNums initialisé)"""
    from apps.parameters.models import Counter, CounterNums

    def _factory(name: str, num: int = 1, **kwargs: Any):
        defaults = {"lpad_num": 5, "separateur": ""}
        defaults.update(kwargs)
        counter, _ = Counter.objects.get_or_create(name=name, defaults=defaults)
        CounterNums.objects.get_or_create(counter=counter, defaults={"num": num})
        return counter

    return _factory


@pytest.fixture
def invoice_counters(make_counter) -> types.SimpleNamespace:
    """Les compteurs utilisés par la facturation (achats, ventes, générique)"""
    return types.SimpleNamespace(
        purchase=make_counter(
            "purchase_num", uuid_identification=PURCHASE_COUNTER_UUID, lpad_num=5
        ),
        sales=make_counter(
            "invoices_num", uuid_identification=SALES_COUNTER_UUID, prefix="AAAAMM", lpad_num=5
        ),
        generic=make_counter("generic", lpad_num=4),
    )


@pytest.fixture
def make_payment_condition(db) -> Callable[..., Any]:  # pylint: disable=W0613
    """Fabrique de accountancy.PaymentCondition (condition de paiement Sage)"""
    from apps.accountancy.models import PaymentCondition

    def _factory(
        code: str = "30FDM",
        end_month: str = "2",
        offset_days: int = 0,
        offset_month: int = 1,
        **kwargs: Any,
    ):
        defaults = {
            "name": f"Condition {code}",
            "mode": "VIR",
            "end_month": end_month,
            "offset_days": offset_days,
            "offset_month": offset_month,
            "auuid": str(uuid.uuid4()),
        }
        defaults.update(kwargs)
        return PaymentCondition.objects.get_or_create(code=code, defaults=defaults)[0]

    return _factory


@pytest.fixture
def make_type_facture(make_child_center) -> Callable[..., Any]:
    """Fabrique de centers_purchasing.TypeFacture (types de pièces X3 par centrale)"""
    from apps.centers_purchasing.models import TypeFacture

    def _factory(
        child_center: str = "ACF",
        invoice_type: str = "380",
        purchase: str = "FAF",
        sale: str = "FAC",
    ):
        return TypeFacture.objects.get_or_create(
            child_center=make_child_center(child_center),
            invoice_type=invoice_type,
            defaults={
                "purchase_type_facture": purchase,
                "sale_type_facture": sale,
                "invoice_name": "Facture" if invoice_type == "380" else "Avoir",
            },
        )[0]

    return _factory


@pytest.fixture
def make_grouping(make_section) -> Callable[..., Any]:
    """Fabrique du regroupement de facturation d'un axe pro (GroupingGoods + AxeProGroupingGoods)"""
    from apps.centers_purchasing.models import AxeProGroupingGoods, GroupingGoods

    def _factory(
        section: str = "OPT",
        base: str = "607 - MARCHANDISES",
        grouping_goods: str = "MONTURES",
        ranking: int = 1,
    ):
        grouping = GroupingGoods.objects.get_or_create(
            grouping_goods=grouping_goods, defaults={"base": base, "ranking": ranking}
        )[0]
        return AxeProGroupingGoods.objects.get_or_create(
            axe_pro=make_section("PRO", section), defaults={"grouping_goods": grouping}
        )[0]

    return _factory


@pytest.fixture
def make_article_account(make_article, make_child_center, make_vat) -> Callable[..., Any]:
    """Fabrique de comptes achat/vente par article, centrale et tva"""
    from apps.articles.models import ArticleAccount

    def _factory(
        article=None,
        child_center: str = "ACF",
        vat: str = "001",
        purchase_account: str = "607000",
        sale_account: str = "707000",
    ):
        return ArticleAccount.objects.get_or_create(
            article=article or make_article(),
            child_center=make_child_center(child_center),
            vat=make_vat(vat),
            defaults={"purchase_account": purchase_account, "sale_account": sale_account},
        )[0]

    return _factory


@pytest.fixture
def make_accounts_axe_pro_category(
    make_child_center, make_big_category, make_section, make_vat, make_account
) -> Callable[..., Any]:
    """Fabrique du paramétrage des comptes par axe pro / catégorie / tva / centrale"""
    from apps.centers_purchasing.models import AccountsAxeProCategory

    def _factory(
        axe_pro=None,
        big_category=None,
        sub_category=None,
        child_center: str = "ACF",
        vat: str = "001",
        purchase: str = "607000",
        sale: str = "707000",
    ):
        return AccountsAxeProCategory.objects.create(
            child_center=make_child_center(child_center),
            big_category=big_category or make_big_category(),
            sub_category=sub_category,
            axe_pro=axe_pro or make_section("PRO", "OPT"),
            vat=make_vat(vat),
            purchase_account=make_account("FRA", purchase),
            sale_account=make_account("FRA", sale),
        )

    return _factory


@pytest.fixture
def billing_dataset(
    db,
    make_user,
    make_edi_validation,
    make_society,
    make_maison,
    make_section,
    make_big_category,
    make_article,
    make_article_account,
    make_vat_rat,
    units,
    make_type_facture,
    make_grouping,
    make_payment_condition,
    make_account,
    make_edi_import,
    invoice_counters,
    make_sse_progress_core,
) -> types.SimpleNamespace:  # pylint: disable=W0613
    """Jeu de données complet pour une facturation : période ouverte, tiers fournisseur et client,

    maison AF0001 (centrale ACF, enseigne ACF), article avec comptes, TVA 001 à 20 %, types de
    pièces, regroupement, compteurs, jauge SSE, et une facture edi validée de deux lignes
    (achat + vente, 100 € HT + 50 € HT).
    """
    user = make_user()
    validation = make_edi_validation(billing_period=datetime.date(2026, 1, 1))
    condition = make_payment_condition()
    supplier = make_society(
        "FOUR001",
        is_client=False,
        is_supplier=True,
        vat_sheme_supplier="FRA",
        payment_condition_supplier=condition,
        payment_condition_client=condition,
    )
    client = make_society(
        "CLI001", is_client=True, payment_condition_client=condition, vat_sheme_client="FRA"
    )
    axes = {
        "BU": make_section("BU", "CAHA"),
        "PRJ": make_section("PRJ", "NAF"),
        "PRO": make_section("PRO", "OPT"),
        "PYS": make_section("PYS", "FR"),
        "RFA": make_section("RFA", "NAF"),
    }
    category = make_big_category("Marchandises")
    debit, credit = (
        make_account("FRA", "411000", call_code="411"),
        make_account("FRA", "707000", call_code="707"),
    )
    make_account("FRA", "607000", call_code="607")
    maison = make_maison(
        "AF0001",
        third_party_num=client,
        type_x3=1,
        debit_account=debit,
        credit_account=credit,
        axe_bu=axes["BU"],
        code_maison="AF0001",
    )
    make_vat_rat("001", "20")
    make_type_facture("ACF", "380", "FAF", "FAC")
    make_type_facture("ACF", "381", "AVO", "AVO")
    make_grouping("OPT")
    article = make_article(
        "ART-1",
        society=supplier,
        big_category=category,
        axe_bu=axes["BU"],
        axe_prj=axes["PRJ"],
        axe_pro=axes["PRO"],
        axe_pys=axes["PYS"],
        axe_rfa=axes["RFA"],
        new_article=False,
    )
    make_article_account(article, "ACF", "001", "607000", "707000")
    progress = make_sse_progress_core(user)

    common = {
        "third_party_num": "FOUR001",
        "reference_article": "ART-1",
        "flow_name": "Widex",
        "invoice_number": "F2026-001",
        "invoice_date": datetime.date(2026, 1, 15),
        "invoice_year": 2026,
        "invoice_month": datetime.date(2026, 1, 1),
        "invoice_type": "380",
        "devise": "EUR",
        "cct_uuid_identification": maison,
        "code_center": "ACF",
        "code_signboard": "ACF",
        "axe_bu": axes["BU"],
        "axe_prj": axes["PRJ"],
        "axe_pro": axes["PRO"],
        "axe_pys": axes["PYS"],
        "axe_rfa": axes["RFA"],
        "big_category": category,
        "vat": __import__("apps.accountancy.models", fromlist=["VatSage"]).VatSage.objects.get(
            vat="001"
        ),
        "vat_rate": Decimal("0.2"),
        "vat_regime": "FRA",
        "purchase_invoice": True,
        "sale_invoice": True,
        "valid": True,
        "unit_weight": units_unit(1),
        "supplier": "WIDEX",
        "supplier_ident": "Widex",
        "invoice_amount_without_tax": Decimal(150),
        "invoice_amount_tax": Decimal(30),
        "invoice_amount_with_tax": Decimal(180),
        "import_uuid_identification": None,
    }
    lines = [
        make_edi_import(
            **{
                **common,
                "qty": Decimal(1),
                "net_unit_price": Decimal(100),
                "net_amount": Decimal(100),
                "vat_amount": Decimal(20),
                "amount_with_vat": Decimal(120),
                "libelle": "Monture",
            }
        ),
        make_edi_import(
            **{
                **common,
                "qty": Decimal(1),
                "net_unit_price": Decimal(50),
                "net_amount": Decimal(50),
                "vat_amount": Decimal(10),
                "amount_with_vat": Decimal(60),
                "libelle": "Etui",
            }
        ),
    ]
    return types.SimpleNamespace(
        user=user,
        validation=validation,
        supplier=supplier,
        client=client,
        maison=maison,
        axes=axes,
        category=category,
        article=article,
        lines=lines,
        progress=progress,
        condition=condition,
    )


def units_unit(num: int):
    """Instance UnitChoices par numéro (créée par la fixture units)"""
    from apps.parameters.models import UnitChoices

    return UnitChoices.objects.get(num=num)


@pytest.fixture
def make_sse_progress_core(db) -> Callable[..., Any]:  # pylint: disable=W0613
    """Fabrique de core.SSEProgress (jauge des insertions)"""
    from apps.core.models import SSEProgress

    def _factory(user, job_id: str | None = None, total_items: int = 20):
        return SSEProgress.objects.create(
            job_id=job_id or str(uuid.uuid4()),
            user=user,
            task_type="invoices_insertion",
            total_items=total_items,
            metadata={"success": [], "failed": []},
        )

    return _factory


@pytest.fixture
def keep_connection(monkeypatch):
    """invoices_insertion ferme la connexion Django en fin de traitement (threads) : dans la

    transaction de test, la fermeture casserait le test. close() devient un no-op.
    """
    from django.db import connections

    monkeypatch.setattr(connections["default"], "close", lambda: None)


@pytest.fixture
def sync_controls(monkeypatch):
    """control_alls_missings exécute ses requêtes dans un pool de threads (autres connexions,

    invisibles depuis la transaction de test) : exécution synchrone dans le thread de test.
    """
    from apps.invoices.bin import pre_controls

    class _Future:
        def __init__(self, result):
            self._result = result

        def result(self):
            return self._result

    class _Executor:
        def __init__(self, max_workers=None):
            self.max_workers = max_workers

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def submit(self, function, *args, **kwargs):
            return _Future(function(*args, **kwargs))

    monkeypatch.setattr(pre_controls, "ThreadPoolExecutor", _Executor)
    monkeypatch.setattr(pre_controls, "as_completed", lambda futures: list(futures))
    monkeypatch.setattr(pre_controls, "close_old_connections", lambda: None)


@pytest.fixture
def make_detail(make_invoice, make_unit) -> Callable[..., Any]:
    """Fabrique de lignes invoices.InvoiceDetail (champs de BaseInvoiceDetailsTable uniquement)"""
    from apps.invoices.models import InvoiceDetail

    def _factory(invoice=None, **kwargs: Any):
        defaults = {
            "import_uuid_identification": uuid.uuid4(),
            "axe_bu": "CAHA",
            "axe_prj": "NAF",
            "axe_pro": "OPT",
            "axe_rfa": "NAF",
            "axe_pys": "FR",
            "vat": "001",
            "vat_rate": Decimal("0.2"),
            "vat_regime": "FRA",
            "big_category": "marchandises",
            "account": "607000",
            "flow_name": "Widex",
            "unit_weight": make_unit(1, "U"),
            "net_unit_price": Decimal(100),
            "net_amount": Decimal(100),
            "vat_amount": Decimal(20),
            "amount_with_vat": Decimal(120),
        }
        defaults.update(kwargs)
        return InvoiceDetail.objects.create(uuid_invoice=invoice or make_invoice(), **defaults)

    return _factory


@pytest.fixture
def make_sale_detail(make_sale_invoice, make_unit) -> Callable[..., Any]:
    """Fabrique de lignes invoices.SaleInvoiceDetail (champs de BaseInvoiceDetailsTable uniquement)"""
    from apps.invoices.models import SaleInvoiceDetail

    def _factory(sale_invoice=None, **kwargs: Any):
        defaults = {
            "import_uuid_identification": uuid.uuid4(),
            "axe_bu": "CAHA",
            "axe_prj": "NAF",
            "axe_pro": "OPT",
            "axe_rfa": "NAF",
            "axe_pys": "FR",
            "vat": "001",
            "vat_rate": Decimal("0.2"),
            "vat_regime": "FRA",
            "big_category": "marchandises",
            "base": "607 - MARCHANDISES",
            "grouping_goods": "MONTURES",
            "account": "707000",
            "account_od_600": "607000",
            "ranking": 1,
            "unit_weight": make_unit(1, "U"),
            "net_unit_price": Decimal(100),
            "net_amount": Decimal(100),
            "vat_amount": Decimal(20),
            "amount_with_vat": Decimal(120),
        }
        defaults.update(kwargs)
        return SaleInvoiceDetail.objects.create(
            uuid_invoice=sale_invoice or make_sale_invoice(), **defaults
        )

    return _factory
