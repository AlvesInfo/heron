# pylint: disable=E0401,W0621
"""FR : Tests des formulaires Django de validation des imports Sage (forms/forms_django)


EN : Tests for Django validation forms of Sage imports

Commentaire:

SageNullBooleanField (apps.core) reçoit la valeur brute du fichier Sage : 2 = vrai, 1 = faux,
toute autre valeur = null.

created at: 2026-10-10
created by: Paulo ALVES
"""

import datetime

import pytest

from apps.accountancy import forms as accountancy_forms
from apps.accountancy.forms import (
    AccountSageForm,
    AxeSageForm,
    CategorySageForm,
    CurrencySageForm,
    PaymentConditionForm,
    SectionSageForm,
    TabDivSageForm,
    VatRatSageForm,
    VatRegimeSageForm,
    VatSageForm,
)
from apps.accountancy.forms.forms_django import axes_articles_facturation_forms
from apps.accountancy.models import (
    AccountSage,
    AxeSage,
    CategorySage,
    CurrencySage,
    PaymentCondition,
    SectionSage,
    TabDivSage,
    VatRatSage,
    VatRegimeSage,
    VatSage,
)
from apps.core.validations.forms_base import SageNullBooleanField, TildeTextField

pytestmark = pytest.mark.django_db

AUUID = "6fa459ea-ee8a-3ca4-894e-db77e160355e"


def _tab_div_data(**overrides):
    data = {"num_table": "6100", "code": "B01", "name": "Budget~~1", "short_name": "B1"}
    data.update({f"a_{i:02d}": f"a{i}" for i in range(1, 16)})
    data.update({f"n_{i:02d}": str(i) for i in range(1, 16)})
    data.update({"def_val": "2", "active": "2"})
    data.update(overrides)
    return data


# CHAMPS DE BASE ===================================================================================


@pytest.mark.parametrize(
    ("value", "expected"),
    [("2", True), (2, True), (" 2.0 ", True), ("1", False), (1, False), ("1.0", False)],
)
def test_sage_null_boolean_field_vrai_faux(value, expected):
    """2 (vrai Sage) → True, 1 (faux Sage) → False"""
    assert SageNullBooleanField().clean(value) is expected


@pytest.mark.parametrize("value", ["", None, "x", "0", "true"])
def test_sage_null_boolean_field_inconnu_vaut_null(value):
    """Toute autre valeur vaut None, sans erreur de validation (champ nullable)"""
    assert SageNullBooleanField().clean(value) is None


@pytest.mark.parametrize(
    ("value", "expected"), [("Clients~~Clients divers", "Clients"), ("Sans tilde", "Sans tilde")]
)
def test_tilde_text_field(value, expected):
    """Le champ garde la partie avant les ~~ des exports Sage"""
    assert TildeTextField().clean(value) == expected


def test_tilde_text_field_valeur_non_texte():
    """Une valeur non str n'est pas splittée et passe au clean de CharField"""
    assert TildeTextField(required=False).clean(None) == ""
    assert TildeTextField(required=False).clean(12) == "12"


# FORMULAIRES SANS BOOLÉEN SAGE : VALIDES ==========================================================


def test_axe_sage_form_valide():
    """AxeSageForm nettoie les tildes et sauvegarde"""
    form = AxeSageForm(data={"axe": "BU", "name": "Business~~Unit", "short_name": "BU~~x"})

    assert form.is_valid(), form.errors
    assert form.cleaned_data == {"axe": "BU", "name": "Business", "short_name": "BU"}
    assert form.save().pk is not None
    assert AxeSage.objects.get(axe="BU").name == "Business"


def test_axe_sage_form_nom_obligatoire():
    """TildeTextField est required : un nom vide invalide le formulaire"""
    form = AxeSageForm(data={"axe": "BU", "name": "", "short_name": "BU"})

    assert not form.is_valid()
    assert set(form.errors) == {"name"}


def test_vat_sage_form_valide():
    """VatSageForm accepte un auuid et crée la taxe"""
    form = VatSageForm(
        data={
            "vat": "001",
            "name": "TVA 20~~%",
            "short_name": "20",
            "vat_regime": "FRA",
            "auuid": AUUID,
        }
    )

    assert form.is_valid(), form.errors
    assert form.save().name == "TVA 20"
    assert VatSage.objects.filter(vat="001").exists()


def test_vat_sage_form_auuid_invalide():
    """Un auuid non uuid est rejeté"""
    form = VatSageForm(
        data={
            "vat": "001",
            "name": "n",
            "short_name": "s",
            "vat_regime": "FRA",
            "auuid": "pas-un-uuid",
        }
    )

    assert not form.is_valid()
    assert set(form.errors) == {"auuid"}


def test_payment_condition_form_valide():
    """PaymentConditionForm accepte une échéance complète"""
    form = PaymentConditionForm(
        data={
            "code": "30J",
            "name": "30 jours~~fin de mois",
            "short_name": "30J",
            "mode": "VRT",
            "percent_at_term": "100",
            "paiement_type": "VIREMENT",
            "offset_month": "1",
            "offset_days": "0",
            "end_month": "2",
            "mont_echeance_min": "0",
            "auuid": "PTE-30J",
        }
    )

    assert form.is_valid(), form.errors
    condition = form.save()
    assert condition.name == "30 jours"
    assert PaymentCondition.objects.get(auuid="PTE-30J").offset_month == 1


def test_category_sage_form_valide():
    """CategorySageForm crée une catégorie"""
    form = CategorySageForm(
        data={
            "initial": "C",
            "code": "CLI",
            "name": "Clients~~x",
            "short_name": "CLI",
            "cur": "EUR",
        }
    )

    assert form.is_valid(), form.errors
    assert form.save().name == "Clients"
    assert CategorySage.objects.filter(initial="C", code="CLI").exists()


def test_currency_sage_form_dates_format_sage():
    """Les dates arrivent au format ddmmyy de Sage"""
    form = CurrencySageForm(
        data={
            "currency_current": "EUR",
            "currency_change": "USD",
            "exchange_date": "010123",
            "exchange_type": "1",
            "exchange_rate": "1.1",
            "exchange_inverse": "0.9",
            "divider": "1",
            "modification_date": "150224",
        }
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["exchange_date"] == datetime.date(2023, 1, 1)
    assert form.cleaned_data["modification_date"] == datetime.date(2024, 2, 15)
    assert CurrencySage.objects.filter(pk=form.save().pk).exists()


def test_currency_sage_form_date_iso_refusee():
    """Un autre format de date que ddmmyy est refusé"""
    form = CurrencySageForm(
        data={
            "currency_current": "EUR",
            "currency_change": "USD",
            "exchange_date": "2023-01-01",
            "exchange_type": "1",
            "exchange_rate": "1.1",
            "exchange_inverse": "0.9",
            "divider": "1",
            "modification_date": "15/02/2024",
        }
    )

    assert not form.is_valid()
    assert set(form.errors) == {"exchange_date", "modification_date"}


# FORMULAIRES AVEC BOOLÉEN SAGE ====================================================================


@pytest.mark.parametrize(
    ("form_class", "data", "boolean_fields"),
    [
        (
            AccountSageForm,
            {
                "code_plan_sage": "FRA",
                "account": "411000",
                "name": "Clients~~x",
                "short_name": "Cli",
                "collective": "2",
                "analytic": "2",
                "nb_axes": "0",
            },
            {"collective", "analytic"},
        ),
        (
            SectionSageForm,
            {"axe": "BU", "section": "S1", "name": "n", "short_name": "s", "chargeable": "2"},
            {"chargeable"},
        ),
        (
            VatRegimeSageForm,
            {
                "vat_regime": "FRA",
                "active": "2",
                "name": "n",
                "short_name": "s",
                "vat_code": "001",
                "sale_class": "x",
                "regime_type": "t",
                "legislation": "FRA",
            },
            {"active"},
        ),
        (
            VatRatSageForm,
            {
                "vat": "001",
                "vat_start_date": "010123",
                "rate": "20",
                "exoneration": "2",
                "auuid": AUUID,
            },
            {"exoneration"},
        ),
        (TabDivSageForm, _tab_div_data(), {"def_val", "active"}),
    ],
)
def test_formulaires_avec_booleens_sage_vrai(make_axe, make_vat, form_class, data, boolean_fields):
    """Avec "2" (vrai Sage), les formulaires sont valides et les booléens valent True"""
    make_axe("BU")
    make_vat("001")

    form = form_class(data=data)

    assert form.is_valid(), form.errors
    assert all(form.cleaned_data[field] is True for field in boolean_fields)
    assert form.save().pk is not None


@pytest.mark.parametrize(("sage_value", "expected"), [("1", False), ("", None), ("zzz", None)])
def test_formulaires_avec_booleens_sage_faux_ou_null(sage_value, expected):
    """1 (faux Sage) → False ; vide ou inconnu → None, sans bloquer le formulaire"""
    form = VatRegimeSageForm(
        data={
            "vat_regime": "FRA",
            "active": sage_value,
            "name": "n",
            "short_name": "s",
            "vat_code": "001",
            "sale_class": "x",
            "regime_type": "t",
            "legislation": "FRA",
        }
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["active"] is expected
    assert form.save().active is expected


def test_formulaires_avec_booleens_sage_sans_la_cle():
    """Sans la clé booléenne dans les données, la valeur est None"""
    form = VatRegimeSageForm(
        data={
            "vat_regime": "FRA",
            "name": "n",
            "short_name": "s",
            "vat_code": "001",
            "sale_class": "x",
            "regime_type": "t",
            "legislation": "FRA",
        }
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["active"] is None


def test_section_sage_form_axe_inconnu(make_axe):
    """Le champ axe est une ModelChoiceField sur le code axe (to_field)"""
    make_axe("BU")
    form = SectionSageForm(
        data={"axe": "ZZZ", "section": "S1", "name": "n", "short_name": "s", "chargeable": "2"}
    )

    assert not form.is_valid()
    assert "axe" in form.errors
    assert form.fields["axe"].to_field_name == "axe"


def test_vat_rat_sage_form_vat_inconnue():
    """Le champ vat impose une VatSage existante"""
    form = VatRatSageForm(
        data={
            "vat": "999",
            "vat_start_date": "010123",
            "rate": "20",
            "exoneration": "2",
            "auuid": AUUID,
        }
    )

    assert not form.is_valid()
    assert set(form.errors) == {"vat"}


def test_tab_div_sage_form_tous_les_champs_sont_obligatoires():
    """Sur TabDivSageForm, tous les a_xx / n_xx et noms sont requis ; les booléens Sage ne le sont pas"""
    form = TabDivSageForm(data={"num_table": "6100", "code": "B01"})

    assert not form.is_valid()
    assert len(form.errors) == 32
    assert not {"def_val", "active"} & set(form.errors)


# COHÉRENCE META ===================================================================================


@pytest.mark.parametrize(
    ("form_class", "model", "expected_fields"),
    [
        (AccountSageForm, AccountSage, list(AccountSage.get_columns_import())),
        (AxeSageForm, AxeSage, list(AxeSage.get_columns_import())),
        (SectionSageForm, SectionSage, list(SectionSage.get_columns_import())[:7]),
        (VatRegimeSageForm, VatRegimeSage, list(VatRegimeSage.get_columns_import())),
        (VatSageForm, VatSage, list(VatSage.get_columns_import())),
        (
            VatRatSageForm,
            VatRatSage,
            [c for c in VatRatSage.get_columns_import() if c != "vat_regime"],
        ),
        (PaymentConditionForm, PaymentCondition, list(PaymentCondition.get_columns_import())),
        (TabDivSageForm, TabDivSage, [*TabDivSage.get_columns_import(), "active"]),
        (CategorySageForm, CategorySage, list(CategorySage.get_columns_import())),
        (CurrencySageForm, CurrencySage, list(CurrencySage.get_columns_import())),
    ],
)
def test_meta_des_formulaires(form_class, model, expected_fields):
    """Chaque ModelForm cible le bon modèle et les colonnes du fichier Sage"""
    assert form_class.Meta.model is model
    assert form_class.Meta.fields == expected_fields
    assert set(form_class.base_fields) == set(expected_fields)


def test_exports_du_package_forms():
    """Le package forms ré-exporte les formulaires Django (les schémas djantic restent dans forms_djantic.sage)"""
    assert accountancy_forms.AccountSageForm is AccountSageForm
    assert not hasattr(accountancy_forms, "AccountSageSchema")
    assert axes_articles_facturation_forms.__doc__
