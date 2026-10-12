# pylint: disable=E0401,W0621,W0212
"""FR : Tests des modèles Sage X3 (apps/accountancy/models/sage.py)


EN : Tests for Sage X3 models

created at: 2026-10-10
created by: Paulo ALVES
"""

import datetime
import uuid
from decimal import Decimal

import pytest
from django.db import IntegrityError, transaction
from django.db.models import Manager, ProtectedError

from apps.accountancy.models import (
    AccountSage,
    CategorySage,
    CctSage,
    CodePlanSage,
    CurrencySage,
    ModeReglement,
    PaymentCondition,
    TabDivSage,
    VatRatSage,
    VatRegimeSage,
    VatSage,
)
from apps.accountancy.models.sage import AccountingTypeSage, TabDivQuerySet

pytestmark = pytest.mark.django_db

IMPORT_METADATA = [
    (AccountSage, "ZBIACCOUNT_journalier.heron", {"code_plan_sage", "account"}, 31),
    (VatRegimeSage, "ZBIREG_journalier.heron", {"vat_regime", "legislation"}, 8),
    (VatSage, "ZBIVAT_journalier.heron", {"vat"}, 5),
    (VatRatSage, "ZBIRATVAT_journalier.heron", {"auuid"}, 6),
    (ModeReglement, "ZBIMODREG_journalier.heron", {"uuid_identification"}, 5),
    (PaymentCondition, "ZBIPTE_journalier.heron", {"auuid"}, 11),
    (TabDivSage, "ZBIDIV_journalier.heron", {"num_table", "code"}, 35),
    (
        CategorySage,
        ("ZBICATC_journalier.heron", "ZBICATS_journalier.heron"),
        {"initial", "code"},
        5,
    ),
    (
        CurrencySage,
        "ZBICUR_journalier.heron",
        {"currency_current", "currency_change", "exchange_date"},
        8,
    ),
]


@pytest.mark.parametrize(("model", "file_name", "uniques", "nb_columns"), IMPORT_METADATA)
def test_metadonnees_import_des_modeles(model, file_name, uniques, nb_columns):
    """Pour chaque modèle importé depuis Sage : nom de fichier, positions de colonnes contiguës

    à partir de 0, clés d'unicité incluses dans les colonnes, et champs existants sur le modèle
    """
    columns = model.get_columns_import()
    model_fields = {field.name for field in model._meta.get_fields()}

    assert model.file_import_sage() == file_name
    assert list(columns.values()) == list(range(nb_columns))
    assert model.get_uniques() == uniques
    assert uniques <= set(columns)
    assert set(columns) <= model_fields
    assert model().get_import == "methode d'import à retourner"


def test_accounting_type_sage_est_une_classe_vide():
    """AccountingTypeSage est un simple conteneur sans attribut"""
    assert isinstance(AccountingTypeSage(), AccountingTypeSage)
    assert not vars(AccountingTypeSage())


# __str__ ==========================================================================================


def test_str_des_modeles(
    make_account,
    make_cct,
    make_vat_regime,
    make_vat,
    make_vat_rat,
    make_mode_reglement,
    make_payment_condition,
    make_tab_div,
    make_category,
    make_currency,
    make_code_plan,
):
    """Texte affiché dans les selects pour chaque modèle"""
    assert str(make_account("FRA", "411000")) == "411000 - FRA"
    assert str(make_cct("AF0001")) == "AF0001"
    assert str(make_vat_regime("FRA", "FRA")) == "FRA - FRA"
    assert str(make_vat_regime("EXP", None)) == "EXP - "
    assert str(make_vat("001", "FRA")) == "001 - FRA"
    rate = make_vat_rat("001", datetime.date(2014, 1, 1), "20")
    rate.refresh_from_db()
    assert str(rate) == "001 - FRA - 2014-01-01 - 20.00000"
    assert str(make_mode_reglement("CHQ", name="Chèque")) == "CHQ - Chèque"
    assert str(make_payment_condition("30J", name="30 jours")) == "30J - 30 jours"
    assert str(make_tab_div(6100, "B01", name="Budget 1")) == "B01 - Budget 1"
    assert str(make_category("C", "CLI", name="Clients")) == "CLI - Clients"
    assert str(make_code_plan("FRA")) == "FRA"
    assert str(make_currency("EUR", "USD")) == "EUR - USD"


# CONTRAINTES ======================================================================================


@pytest.mark.parametrize(
    ("factory_name", "first_kwargs", "duplicate_kwargs"),
    [
        (
            "make_vat_regime",
            {"vat_regime": "FRA", "legislation": "FRA"},
            {"vat_regime": "FRA", "legislation": "FRA"},
        ),
        ("make_tab_div", {"num_table": 6100, "code": "B01"}, {"num_table": 6100, "code": "B01"}),
        ("make_category", {"initial": "C", "code": "CLI"}, {"initial": "C", "code": "CLI"}),
        (
            "make_currency",
            {"currency_current": "EUR", "currency_change": "USD"},
            {"currency_current": "EUR", "currency_change": "USD"},
        ),
        (
            "make_mode_reglement",
            {"uuid_identification": uuid.UUID(int=1)},
            {"uuid_identification": uuid.UUID(int=1)},
        ),
        ("make_payment_condition", {"auuid": "PTE-1"}, {"auuid": "PTE-1"}),
        ("make_vat_rat", {"auuid": uuid.UUID(int=2)}, {"auuid": uuid.UUID(int=2)}),
    ],
)
def test_contraintes_unicite(request, factory_name, first_kwargs, duplicate_kwargs):
    """Les contraintes d'unicité (unique / unique_together) sont bien posées en base"""
    factory = request.getfixturevalue(factory_name)
    factory(**first_kwargs)

    with transaction.atomic(), pytest.raises(IntegrityError):
        factory(**duplicate_kwargs)


def test_account_sage_unique(make_account):
    """Le couple plan/compte est unique (la fabrique réutilise, la création directe échoue)"""
    make_account("FRA", "411000")

    with transaction.atomic(), pytest.raises(IntegrityError):
        AccountSage.objects.create(code_plan_sage="FRA", account="411000")


def test_cct_sage_unique(make_cct):
    """Le code cct est unique (la fabrique réutilise, la création directe échoue)"""
    make_cct("AF0001")

    with transaction.atomic(), pytest.raises(IntegrityError):
        CctSage.objects.create(cct="AF0001")


def test_vat_sage_unique_sur_vat(make_vat):
    """Le code tva est unique même avec un auuid différent"""
    make_vat("001", auuid=uuid.uuid4())
    auuid = uuid.uuid4()

    with transaction.atomic(), pytest.raises(IntegrityError):
        VatSage.objects.create(vat="001", auuid=auuid)


def test_vat_rat_sage_protege_la_tva(make_vat_rat):
    """Une taxe ayant des taux ne peut pas être supprimée (on_delete=PROTECT)"""
    rate = make_vat_rat("001")
    vat = VatSage.objects.filter(pk=rate.vat.pk)

    with pytest.raises(ProtectedError):
        vat.delete()


def test_vat_rat_sage_ordering(make_vat_rat):
    """Les taux sont triés par tva puis date de début décroissante"""
    make_vat_rat("002", datetime.date(2000, 1, 1), "5.5")
    make_vat_rat("001", datetime.date(2000, 1, 1), "19.6")
    make_vat_rat("001", datetime.date(2014, 1, 1), "20")

    assert list(VatRatSage.objects.values_list("vat_id", "vat_start_date")) == [
        ("001", datetime.date(2014, 1, 1)),
        ("001", datetime.date(2000, 1, 1)),
        ("002", datetime.date(2000, 1, 1)),
    ]


def test_account_sage_ordering_et_defauts(make_account):
    """Tri par plan puis compte, valeurs par défaut des flags"""
    make_account("FRA", "607000")
    make_account("BEL", "707000")
    account = make_account("FRA", "411000")

    assert list(AccountSage.objects.values_list("account", flat=True)) == [
        "707000",
        "411000",
        "607000",
    ]
    assert account.nb_axes == 0
    assert account.analytic is False
    assert account.chargeback_x3 is False
    assert account.collective is None


def test_valeurs_par_defaut(make_cct, make_payment_condition, make_tab_div, make_currency):
    """Valeurs par défaut des modèles (FlagsTable + champs spécifiques)"""
    cct = make_cct()
    condition = make_payment_condition()
    tab_div = make_tab_div()
    currency = make_currency()

    assert cct.chargeable is True
    assert cct.active is False
    assert cct.delete is False
    assert condition.default is None
    assert tab_div.n_01 == Decimal(0)
    assert tab_div.a_01 is None
    assert tab_div.def_val is None
    assert currency.exchange_type == 1
    assert currency.divider == Decimal(1)


# TAB DIV ==========================================================================================


def test_tab_div_queryset_budget(make_tab_div):
    """Le filtre budget ne renvoie que la table 6100"""
    make_tab_div(6100, "B01")
    make_tab_div(6100, "B02")
    make_tab_div(6200, "X01")

    budgets = TabDivSage.objects.budget()

    assert isinstance(budgets, TabDivQuerySet)
    assert list(budgets.values_list("code", flat=True)) == ["B01", "B02"]
    assert TabDivSage.objects.budget().filter(code="B02").count() == 1


def test_tab_div_managers(make_tab_div):
    """`tab_div` est un Manager standard, `objects` porte le QuerySet métier"""
    make_tab_div(6200, "X01")

    assert type(TabDivSage.tab_div) is Manager  # pylint: disable=C0123
    assert TabDivSage.tab_div.count() == 1
    assert not hasattr(TabDivSage.tab_div, "budget")


# CODE PLAN ========================================================================================


def test_code_plan_sage_cle_primaire(make_code_plan):
    """La clé primaire est le code plan lui-même"""
    plan = make_code_plan("FRA")

    assert plan.pk == "FRA"
    assert CodePlanSage.objects.get(pk="FRA") == plan
    assert make_code_plan("FRA") == plan
