# pylint: disable=E0401,W0621
"""
FR : Tests des schémas djantic de validation des imports Sage (forms/forms_djantic/sage.py)
EN : Tests for djantic validation schemas of Sage imports

created at: 2026-10-10
created by: Paulo ALVES
"""
import datetime
import uuid
from decimal import Decimal

import pytest
from pydantic import ValidationError

from apps.accountancy.forms.forms_djantic.sage import (
    AccountSageSchema,
    AxeSageSchema,
    CategorySageSchema,
    CurrencySageSchema,
    ModeReglementSchema,
    PaymentConditionSchema,
    SectionSageSchema,
    TabDivSageSchema,
    VatRatSageSchema,
    VatRegimeSageSchema,
    VatSageSchema,
)
from apps.accountancy.models import (
    AccountSage,
    AxeSage,
    CategorySage,
    CurrencySage,
    ModeReglement,
    PaymentCondition,
    SectionSage,
    TabDivSage,
    VatRatSage,
    VatRegimeSage,
    VatSage,
)

AUUID = "6fa459ea-ee8a-3ca4-894e-db77e160355e"
WITH_UUID = ["created_at", "modified_at", "uuid_identification"]
WITHOUT_UUID = ["created_at", "modified_at"]


@pytest.mark.parametrize(
    ("schema", "model", "extra"),
    [
        (AccountSageSchema, AccountSage, WITH_UUID),
        (AxeSageSchema, AxeSage, WITHOUT_UUID),
        (SectionSageSchema, SectionSage, WITH_UUID),
        (VatRegimeSageSchema, VatRegimeSage, WITH_UUID),
        (VatSageSchema, VatSage, WITHOUT_UUID),
        (VatRatSageSchema, VatRatSage, WITHOUT_UUID),
        (ModeReglementSchema, ModeReglement, WITHOUT_UUID),
        (PaymentConditionSchema, PaymentCondition, WITHOUT_UUID),
        (TabDivSageSchema, TabDivSage, WITHOUT_UUID),
        (CategorySageSchema, CategorySage, WITHOUT_UUID),
        (CurrencySageSchema, CurrencySage, WITH_UUID),
    ],
)
def test_config_des_schemas(schema, model, extra):
    """Chaque schéma cible son modèle et inclut les colonnes du fichier + les champs techniques"""
    assert schema.Config.model is model
    assert schema.Config.include == list(model.get_columns_import()) + extra
    assert set(schema.__fields__) == set(schema.Config.include)


def test_account_sage_schema_nettoyage_sage():
    """Tildes supprimés, texte tronqué au max_length, booléens Sage 2/1, dates techniques posées"""
    validated = AccountSageSchema(
        code_plan_sage="FRA",
        account="  411000  ",
        name="Clients~~Clients divers " + "x" * 50,
        short_name="Cli",
        collective="2",
        analytic="1",
        nb_axes="2",
        axe_00="BU",
        section_00="S1",
        chargeback_x3="",
    ).dict()

    assert validated["account"] == "411000"
    assert validated["name"] == "Clients"
    assert validated["collective"] is True
    assert validated["analytic"] is False
    assert validated["chargeback_x3"] is False
    assert validated["nb_axes"] == 2
    assert validated["call_code"] is None
    assert isinstance(validated["created_at"], datetime.datetime)
    assert isinstance(validated["uuid_identification"], uuid.UUID)


def test_account_sage_schema_troncature_max_length():
    """Le texte est tronqué à la longueur du champ du modèle"""
    validated = AccountSageSchema(code_plan_sage="FRA", account="4", name="N" * 40, short_name="S" * 30)

    assert len(validated.name) == 30
    assert len(validated.short_name) == 20


def test_account_sage_schema_champ_obligatoire_manquant():
    """Le compte est obligatoire"""
    with pytest.raises(ValidationError) as excinfo:
        AccountSageSchema(code_plan_sage="FRA")

    assert {error["loc"][0] for error in excinfo.value.errors()} == {"account"}


def test_axe_sage_schema():
    """Schéma minimal des axes"""
    validated = AxeSageSchema(axe="BU", name="Business~~Unit", short_name="").dict()

    assert validated["axe"] == "BU"
    assert validated["name"] == "Business"
    assert validated["short_name"] is None


def test_section_sage_schema_defauts():
    """chargeable/active absents deviennent False (SageNullFalseBoolean), cpy_fcy None"""
    validated = SectionSageSchema(axe="CCT", section="AF0001", name="Paris").dict()

    assert validated["chargeable"] is False
    assert validated["active"] is False
    assert validated["cpy_fcy"] is None
    assert validated["regroup_01"] is None


def test_section_sage_schema_valeurs_sage():
    """2 → True, 1 → False ; cpy_fcy redéclaré en str simple n'est pas tronqué (annotation explicite)"""
    validated = SectionSageSchema(
        axe="CCT", section="AF0001", chargeable="2", active="1", cpy_fcy="ACU001"
    ).dict()

    assert validated["chargeable"] is True
    assert validated["active"] is False
    assert validated["cpy_fcy"] == "ACU001"


def test_vat_regime_sage_schema_legislation_vide_par_defaut():
    """La législation absente vaut chaîne vide (clé d'unicité non nulle)"""
    validated = VatRegimeSageSchema(vat_regime="FRA", active="2").dict()

    assert validated["legislation"] == ""
    assert validated["active"] is True


def test_vat_sage_schema_auuid():
    """auuid est un uuid obligatoire"""
    assert VatSageSchema(vat="001", auuid=AUUID).auuid == uuid.UUID(AUUID)

    with pytest.raises(ValidationError):
        VatSageSchema(vat="001", auuid="pas-un-uuid")

    with pytest.raises(ValidationError):
        VatSageSchema(vat="001")


def test_vat_rat_sage_schema_date_et_decimal_par_defaut():
    """Date vide → 01/01/1900, taux vide → 0, exoneration absent → False"""
    validated = VatRatSageSchema(vat="001", vat_start_date="", rate="", auuid=AUUID).dict()

    assert validated["vat_start_date"] == datetime.date(1900, 1, 1)
    assert validated["rate"] == Decimal("0")
    assert validated["exoneration"] is False
    assert validated["vat_regime"] is None


def test_vat_rat_sage_schema_valeurs_sage():
    """Date ddmmyy, taux avec virgule, exoneration 2 → True"""
    validated = VatRatSageSchema(
        vat="001", vat_start_date="010114", rate="20,00", exoneration="2", auuid=AUUID, vat_regime="FRA"
    ).dict()

    assert validated["vat_start_date"] == datetime.date(2014, 1, 1)
    assert validated["rate"] == Decimal("20.00")
    assert validated["exoneration"] is True
    assert validated["vat_regime"] == "FRA"


def test_vat_rat_sage_schema_date_invalide():
    """Une date hors format ddmmyy lève une erreur"""
    with pytest.raises((ValidationError, ValueError)):
        VatRatSageSchema(vat="001", vat_start_date="2014-01-01", rate="20", auuid=AUUID)


def test_mode_reglement_schema():
    """Le mode de règlement porte l'uuid calculé en pré-traitement"""
    validated = ModeReglementSchema(
        code="CHQ", name="Chèque~~x", short_name="CHQ", legislation="FRA", uuid_identification=AUUID
    ).dict()

    assert validated["uuid_identification"] == uuid.UUID(AUUID)
    assert validated["name"] == "Chèque"


def test_payment_condition_schema():
    """Les décimaux et entiers sont convertis, les champs vides numériques ne sont pas tolérés"""
    validated = PaymentConditionSchema(
        code="30J", percent_at_term="100", offset_month="1", offset_days="0", end_month="2", auuid="PTE-1"
    ).dict()

    assert validated["percent_at_term"] == Decimal("100")
    assert validated["offset_month"] == 1
    assert validated["mont_echeance_min"] == Decimal("0")

    with pytest.raises(ValidationError) as excinfo:
        PaymentConditionSchema(code="30J", auuid="PTE-1", percent_at_term="", offset_month="")

    assert {error["loc"][0] for error in excinfo.value.errors()} == {"percent_at_term", "offset_month"}


def test_tab_div_sage_schema():
    """Décimaux vides → 0, booléen def_val Sage, nom tronqué"""
    validated = TabDivSageSchema(num_table="6100", code="B01", n_01="", n_02="1,5", def_val="2", name="x" * 40).dict()

    assert validated["num_table"] == 6100
    assert validated["n_01"] == Decimal("0")
    assert validated["n_02"] == Decimal("1.5")
    assert validated["def_val"] is True
    assert len(validated["name"]) == 30


def test_category_sage_schema():
    """Catégorie clients/fournisseurs"""
    validated = CategorySageSchema(initial="C", code="CLI", name="Clients~~x", cur="EUR").dict()

    assert validated["initial"] == "C"
    assert validated["name"] == "Clients"


def test_currency_sage_schema():
    """Dates ddmmyy, décimaux avec défaut 0 et uuid technique"""
    validated = CurrencySageSchema(
        currency_current="EUR",
        currency_change="USD",
        exchange_date="010124",
        exchange_type="1",
        exchange_rate="1,1",
        exchange_inverse="",
        divider="1",
        modification_date="020124",
    ).dict()

    assert validated["exchange_date"] == datetime.date(2024, 1, 1)
    assert validated["modification_date"] == datetime.date(2024, 1, 2)
    assert validated["exchange_rate"] == Decimal("1.1")
    assert validated["exchange_inverse"] == Decimal("0")
    assert isinstance(validated["uuid_identification"], uuid.UUID)


def test_currency_sage_schema_date_vide_refusee():
    """Une date vide devient None et est refusée car non nullable sur le modèle"""
    with pytest.raises(ValidationError) as excinfo:
        CurrencySageSchema(
            currency_current="EUR",
            currency_change="USD",
            exchange_date="",
            exchange_rate="1",
            exchange_inverse="1",
            modification_date="",
        )

    assert {error["loc"][0] for error in excinfo.value.errors()} == {"exchange_date", "modification_date"}
