# pylint: disable=E0401,W0621
"""FR : Tests des formulaires de la centrale d'achat (forms_django, forms_djantic)


EN : Tests for purchasing center forms

created at: 2026-10-11
created by: Paulo ALVES
"""

import datetime
import uuid

import pytest
from pydantic import ValidationError

from apps.centers_purchasing.forms import (
    AccountsAxeProCategoryDeleteForm,
    AccountsAxeProCategoryForm,
    ApplicableProVatDeleteForm,
    ApplicableProVatForm,
    AxeProGroupingGoodsDeleteForm,
    AxeProGroupingGoodsForm,
    FillesForm,
    GroupingGoodsDeleteForm,
    GroupingGoodsForm,
    MeresForm,
    SignboardForm,
    SignboardModelForm,
    SignboardModelTranslateForm,
    TranslationForm,
    TranslationParamatersForm,
    TypeFactureDeleteForm,
    TypeFactureForm,
)
from apps.centers_purchasing.forms.forms_djantic.forms_data import AxeProAccountSchema
from apps.centers_purchasing.models import (
    AccountsAxeProCategory,
    ApplicableProVat,
    AxeProGroupingGoods,
    GroupingGoods,
    SignboardModel,
    SignboardModelTranslate,
    Translation,
    TranslationParamaters,
    TypeFacture,
)

pytestmark = pytest.mark.django_db


# CENTRALES ET ENSEIGNES ===========================================================================


def test_meres_form():
    form = MeresForm({"code": "HA", "name": "Héron Achats", "generic_coefficient": "1"})

    assert MeresForm.use_required_attribute is False
    assert form.is_valid(), form.errors
    assert form.save().code == "HA"
    assert MeresForm({"code": "", "name": "x"}).is_valid() is False


def test_filles_form_champs_facultatifs_et_libelle_des_tiers(make_principal_center, make_society):
    """Mentions légales, bas de page, banque et tiers facultatifs ; tiers triés et libellés"""
    make_principal_center("HA")
    make_society("TIERS02", name="Second")
    make_society("TIERS01", name=None)
    form = FillesForm()

    assert FillesForm.use_required_attribute is False
    assert all(
        form.fields[name].required is False
        for name in ("comment", "legal_notice", "footer", "iban", "society", "bank")
    )
    assert form.fields["legal_notice"].widget.attrs["is"] == "textarea-autogrow"
    assert [
        form.fields["society"].label_from_instance(s) for s in form.fields["society"].queryset
    ] == ["TIERS01 - ", "TIERS02 - Second"]


def test_filles_form_valide(make_principal_center):
    make_principal_center("HA")
    form = FillesForm(
        {
            "code": "ACF",
            "base_center": "HA",
            "name": "Acuitis",
            "generic_coefficient": "1",
            "societe_cpy_x3": "ACU",
            "site_fcy_x3": "ACF",
            "code_plan_sage": "FRA",
            "iban": "FR76 3000 6000",
        }
    )

    assert form.is_valid(), form.errors
    assert form.save().iban == "FR76 3000 6000"
    assert FillesForm({"code": "ACF", "base_center": "HA"}).is_valid() is False


def test_signboard_form(make_child_center):
    make_child_center("ACF")
    form = SignboardForm(
        {"child_center": "ACF", "code": "ACF", "name": "Acuitis", "generic_coefficient": "1"}
    )

    assert SignboardForm.use_required_attribute is False
    assert form.fields["comment"].required is False
    assert form.fields["message"].required is False
    assert form.fields["message"].widget.attrs["is"] == "textarea-autogrow"
    assert form.is_valid(), form.errors
    assert form.save().child_center.code == "ACF"


@pytest.mark.parametrize(
    ("form_class", "model", "fields"),
    [
        (
            SignboardModelForm,
            SignboardModel,
            ["sign_board", "name", "short_name", "action", "comment"],
        ),
        (
            TranslationForm,
            Translation,
            [
                "name",
                "short_name",
                "french_text",
                "italian_text",
                "spanih_text",
                "portuguese_text",
                "english_text",
            ],
        ),
        (SignboardModelTranslateForm, SignboardModelTranslate, ["sign_board_model", "translation"]),
        (
            TranslationParamatersForm,
            TranslationParamaters,
            ["code", "translation", "prefix_suffix", "field"],
        ),
    ],
)
def test_formulaires_des_modeles_d_enseignes(form_class, model, fields):
    """Formulaires sans écran pour l'instant : ciblage du modèle et champs déclarés"""
    assert form_class.Meta.model is model
    assert form_class.Meta.fields == fields
    assert list(form_class().fields) == fields


# DICTIONNAIRES ====================================================================================


def test_type_facture_form(make_child_center):
    make_child_center("ACF")
    form = TypeFactureForm(
        {
            "child_center": "ACF",
            "invoice_type": "381",
            "purchase_type_facture": "AVO",
            "sale_type_facture": "AVV",
        }
    )

    assert form.is_valid(), form.errors
    assert form.save().get_invoice_type_display() == "Avoir"
    assert TypeFactureForm({"child_center": "ACF", "invoice_type": "999"}).is_valid() is False


def test_grouping_goods_form():
    form = GroupingGoodsForm({"ranking": "3", "base": "Marchandises", "grouping_goods": "Verres"})

    assert form.is_valid(), form.errors
    assert form.save().ranking == 3


def test_axe_pro_grouping_form(make_section, make_grouping_goods):
    section = make_section("PRO", "OPT")
    grouping = make_grouping_goods()
    form = AxeProGroupingGoodsForm(
        {
            "axe_pro": str(section.uuid_identification),
            "grouping_goods": str(grouping.uuid_identification),
        }
    )

    assert form.fields["axe_pro"].widget.attrs["class"]
    assert form.is_valid(), form.errors
    assert form.save().axe_pro == section


def test_applicable_pro_vat_form(make_child_center, make_vat):
    make_child_center("ACF")
    make_vat("001")
    form = ApplicableProVatForm({"child_center": "ACF", "axe_pro": "", "vat": "001"})

    assert form.is_valid(), form.errors
    assert form.save().axe_pro is None


def _account_data(account, **overrides):
    data = {
        "child_center": account.child_center.code,
        "big_category": str(account.big_category.uuid_identification),
        "sub_category": str(account.sub_category.uuid_identification)
        if account.sub_category
        else "",
        "axe_pro": str(account.axe_pro.uuid_identification),
        "vat": account.vat.vat,
        "purchase_account": str(account.purchase_account.uuid_identification),
        "sale_account": str(account.sale_account.uuid_identification),
    }
    data.update(overrides)
    return data


def test_accounts_form_refuse_un_doublon_meme_sans_rubrique(
    make_accounts_axe_pro_category, make_sub_category
):
    """La rubrique nulle est comparée comme une chaîne vide : le doublon est détecté"""
    account = make_accounts_axe_pro_category(child_center="ACF", vat="001")
    form = AccountsAxeProCategoryForm(_account_data(account))

    assert form.fields["sub_category"].required is False
    assert form.is_valid() is False
    assert form.errors["__all__"] == ["Un élément identique existe déjà!"]

    with_sub = AccountsAxeProCategoryForm(
        _account_data(account, sub_category=str(make_sub_category("Montures").uuid_identification))
    )
    assert with_sub.is_valid(), with_sub.errors


def test_accounts_form_modification_de_la_ligne_elle_meme(
    make_accounts_axe_pro_category, make_account
):
    """En modification, la ligne éditée n'est pas son propre doublon : le compte peut changer"""
    account = make_accounts_axe_pro_category(child_center="ACF", vat="001")
    other = make_account("FRA", "607100")
    form = AccountsAxeProCategoryForm(
        _account_data(account, purchase_account=str(other.uuid_identification)), instance=account
    )

    assert form.is_valid(), form.errors
    assert form.save().purchase_account == other


def test_accounts_form_tva_autre(make_accounts_axe_pro_category, make_vat):
    account = make_accounts_axe_pro_category(child_center="ACF", vat="001")
    make_vat("002")

    assert AccountsAxeProCategoryForm(_account_data(account, vat="002")).is_valid()


@pytest.mark.parametrize(
    ("form_class", "model", "fixture_name"),
    [
        (TypeFactureDeleteForm, TypeFacture, "make_type_facture"),
        (GroupingGoodsDeleteForm, GroupingGoods, "make_grouping_goods"),
        (AxeProGroupingGoodsDeleteForm, AxeProGroupingGoods, "make_axe_pro_grouping"),
        (ApplicableProVatDeleteForm, ApplicableProVat, "make_applicable_pro_vat"),
        (
            AccountsAxeProCategoryDeleteForm,
            AccountsAxeProCategory,
            "make_accounts_axe_pro_category",
        ),
    ],
)
def test_formulaires_de_suppression_verifient_l_existence(request, form_class, model, fixture_name):
    instance = request.getfixturevalue(fixture_name)()

    assert form_class.Meta.model is model
    assert form_class({"id": instance.pk}).is_valid()
    assert form_class({"id": instance.pk + 1000}).is_valid() is False
    assert form_class({"id": ""}).is_valid() is False


# SCHÉMA DJANTIC ===================================================================================


def test_axe_pro_account_schema():
    """Les identifiants sont des uuid, la rubrique vide devient None"""
    now = datetime.datetime.now()
    identifiers = {
        name: uuid.uuid4()
        for name in (
            "big_category",
            "axe_pro",
            "purchase_account",
            "sale_account",
            "uuid_identification",
        )
    }
    identifiers.update({"created_at": now, "modified_at": now})
    validated = AxeProAccountSchema(
        child_center="ACF", sub_category="", vat="001", **identifiers
    ).dict()
    with_sub = AxeProAccountSchema(
        child_center="ACF", sub_category=str(identifiers["axe_pro"]), vat="001", **identifiers
    )

    assert AxeProAccountSchema.Config.model is AccountsAxeProCategory
    assert AxeProAccountSchema.Config.include == [
        "child_center",
        "big_category",
        "sub_category",
        "axe_pro",
        "vat",
        "purchase_account",
        "sale_account",
        "uuid_identification",
        "created_at",
        "modified_at",
    ]
    assert validated["sub_category"] is None
    assert validated["big_category"] == identifiers["big_category"]
    assert with_sub.sub_category == identifiers["axe_pro"]

    kwargs = {k: v for k, v in identifiers.items() if k != "big_category"}

    with pytest.raises(ValidationError):
        AxeProAccountSchema(child_center="ACF", vat="001", big_category="pas-un-uuid", **kwargs)
