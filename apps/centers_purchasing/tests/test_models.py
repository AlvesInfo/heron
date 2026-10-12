# pylint: disable=E0401,W0621,W0212
"""
FR : Tests des modèles de la centrale d'achat (apps/centers_purchasing/models.py)
EN : Tests for purchasing center models

created at: 2026-10-11
created by: Paulo ALVES
"""
import pytest
from django.db import IntegrityError, transaction
from django.urls import reverse

from apps.centers_purchasing.models import (
    AccountsAxeProCategory,
    Action,
    ApplicableProVat,
    AxeProGroupingGoods,
    ChildCenterPurchase,
    GroupingGoods,
    PrincipalCenterPurchase,
    Signboard,
    SignboardModel,
    SignboardModelTranslate,
    Translation,
    TranslationParamaters,
    TypeFacture,
)

pytestmark = pytest.mark.django_db


def test_centrale_mere(make_principal_center):
    mere = make_principal_center("HA", name="Héron Achats")

    assert str(mere) == "HA - Héron Achats"
    assert PrincipalCenterPurchase.get_absolute_url() == reverse("centers_purchasing:meres_list")
    assert mere.generic_coefficient == 1

    with pytest.raises(IntegrityError), transaction.atomic():
        PrincipalCenterPurchase.objects.create(code="HA", name="Doublon")


@pytest.mark.parametrize(
    ("iban", "expected"),
    [("FR76 3000-6000 0112 3456 7890 189", "FR76 3000 6000 0112 3456 7890 189"), ("fr761234567", "fr76 1234 567"), (None, ""), ("", "")],
)
def test_centrale_fille_iban_formate_par_groupes_de_quatre(make_child_center, iban, expected):
    """L'IBAN est nettoyé (espaces, tirets) et regroupé par 4, sans espace final"""
    fille = make_child_center("ACF", iban=iban)

    assert fille.iban == expected


def test_centrale_fille_str_url_et_tri(make_child_center):
    fille = make_child_center("GAF", name="GrandAudition")
    make_child_center("ACF", name="Acuitis")

    assert str(fille) == "GAF - GrandAudition"
    assert ChildCenterPurchase.get_absolute_url() == reverse("centers_purchasing:filles_list")
    assert [center.code for center in ChildCenterPurchase.objects.all()] == ["ACF", "GAF"]


def test_enseigne(make_signboard, make_child_center, make_sale_price_category):
    enseigne = make_signboard("ACF", name="Acuitis", child_center=make_child_center("ACF"), sale_price_category=make_sale_price_category())

    assert str(enseigne) == "ACF - Acuitis"
    assert Signboard.get_absolute_url() == reverse("centers_purchasing:enseignes_list")
    assert enseigne.child_center.code == "ACF"


def test_modeles_et_traductions_des_enseignes(make_signboard):
    """Modèles, traductions, liaisons et paramètres d'interpolation : affichages et unicités"""
    enseigne = make_signboard("ACF", name="Acuitis")
    model = SignboardModel.objects.create(sign_board=enseigne, name="Relance")
    translation = Translation.objects.create(name="Relance FR", french_text="Bonjour")
    link = SignboardModelTranslate.objects.create(sign_board_model=model, translation=translation)
    parameter = TranslationParamaters.objects.create(code="NOM", translation=link, field="name")

    assert str(model) == "ACF - Acuitis - Relance"
    assert str(translation) == "Relance FR"
    assert str(link) == "ACF - Acuitis - Relance - Relance FR"
    assert str(parameter) == "NOM - ACF - Acuitis - Relance - Relance FR"
    assert parameter.prefix_suffix == "$"
    assert not hasattr(model, "get_absolute_url")

    with pytest.raises(IntegrityError), transaction.atomic():
        SignboardModelTranslate.objects.create(sign_board_model=model, translation=translation)


def test_regroupements_de_facturation(make_grouping_goods):
    second = make_grouping_goods("Verres", ranking=2)
    first = make_grouping_goods("Montures", ranking=1)

    assert str(first) == "1 - Marchandises - Montures"
    assert list(GroupingGoods.objects.all()) == [first, second]

    with pytest.raises(IntegrityError), transaction.atomic():
        GroupingGoods.objects.create(ranking=3, base="Marchandises", grouping_goods="Montures")


def test_axe_pro_regroupement_un_axe_une_seule_fois(make_axe_pro_grouping, make_section, make_grouping_goods):
    link = make_axe_pro_grouping("OPT")

    assert link.grouping_goods.grouping_goods == "Montures"
    assert list(AxeProGroupingGoods.objects.all()) == [link]

    axe_pro = make_section("PRO", "OPT")
    grouping_goods = make_grouping_goods("Verres", 2)

    with pytest.raises(IntegrityError), transaction.atomic():
        AxeProGroupingGoods.objects.create(axe_pro=axe_pro, grouping_goods=grouping_goods)


def test_comptes_par_axe_pro(make_accounts_axe_pro_category, make_sub_category):
    """Clé d'import, colonnes du fichier et unicité du quintuplet (rubrique renseignée)"""
    make_accounts_axe_pro_category(child_center="ACF", vat="001")
    account = make_accounts_axe_pro_category(child_center="ACF", vat="001", sub_category=make_sub_category("Montures"))

    assert AccountsAxeProCategory.get_uniques() == {"child_center", "big_category", "sub_category", "axe_pro", "vat"}
    assert list(AccountsAxeProCategory.get_columns_import()) == ["child_center", "big_category", "sub_category", "axe_pro", "vat", "purchase_account", "sale_account"]
    assert AccountsAxeProCategory.objects.count() == 2
    assert account.purchase_account.account == "607000"

    with pytest.raises(IntegrityError), transaction.atomic():
        AccountsAxeProCategory.objects.create(
            child_center=account.child_center, big_category=account.big_category, sub_category=account.sub_category,
            axe_pro=account.axe_pro, vat=account.vat, purchase_account=account.purchase_account, sale_account=account.sale_account,
        )


def test_tva_applicable_par_axe_pro(make_applicable_pro_vat, make_child_center, make_vat):
    with_axe = make_applicable_pro_vat("ACF", "OPT", "001")
    without_axe = make_applicable_pro_vat("ACF", None, "002")

    assert with_axe.axe_pro.section == "OPT"
    assert without_axe.axe_pro is None
    assert ApplicableProVat.objects.count() == 2

    child_center = make_child_center("ACF")
    vat = make_vat("001")

    with pytest.raises(IntegrityError), transaction.atomic():
        ApplicableProVat.objects.create(child_center=child_center, axe_pro=with_axe.axe_pro, vat=vat)


def test_type_facture(make_type_facture, make_child_center):
    facture = make_type_facture("ACF", "380")
    avoir = make_type_facture("ACF", "381", purchase_type_facture="AVO", sale_type_facture="AVV")

    assert TypeFacture.get_absolute_url() == reverse("centers_purchasing:type_facture_list")
    assert TypeFacture.InvType.AV.label == "Avoir"
    assert facture.get_invoice_type_display() == "Facture"
    assert list(TypeFacture.objects.all()) == [facture, avoir]

    child_center = make_child_center("ACF")

    with pytest.raises(IntegrityError), transaction.atomic():
        TypeFacture.objects.create(child_center=child_center, invoice_type="380", purchase_type_facture="X", sale_type_facture="Y")


def test_action_sans_champ_metier():
    """Le modèle Action n'a que les drapeaux communs"""
    assert {field.name for field in Action._meta.fields} >= {"id", "active", "delete", "created_by"}
    assert Action.objects.count() == 0
