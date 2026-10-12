# pylint: disable=E0401,W0621
"""
FR : Tests des formulaires Django de l'app centers_clients
EN : Tests for centers_clients Django forms

created at: 2026-10-10
created by: Paulo ALVES
"""
from decimal import Decimal

import pytest

from apps.centers_clients import forms as cc_forms
from apps.centers_clients.forms import (
    ClientFamillyDeleteForm,
    ClientFamillyForm,
    DeleteMaisonSubcriptionForm,
    ImportMaisonBiForm,
    MaisonForm,
    MaisonImportForm,
    MaisonSubcriptionForm,
    MaisonSupllierExclusionDeleteForm,
    MaisonSupllierExclusionForm,
    SupllierCountryExclusionDeleteForm,
    SupllierCountryExclusionForm,
)
from apps.centers_clients.models import ClientFamilly, Maison, MaisonSubcription

pytestmark = pytest.mark.django_db


# MAISON FORM ======================================================================================


def test_maison_form_choix_tiers_clients_seulement(make_society):
    """Le select des tiers ne propose que les clients, avec un choix vide en tête"""
    make_society("CLI001", name="Client un", is_client=True)
    make_society("FOUR001", name="Fournisseur", is_client=False)

    form = MaisonForm()

    assert form.fields["third_party_num"].choices == [("", ""), ("CLI001", "CLI001 - Client un")]
    assert form.fields["credit_account"].required
    assert form.fields["debit_account"].required
    assert not form.fields["code_maison"].required
    assert not form.fields["reference_cosium"].required


def test_maison_form_valide_et_sauvegarde(maison_post_data, make_child_center):
    """Formulaire complet : sauvegarde avec code_maison = cct (la centrale est posée par la vue)"""
    form = MaisonForm(data=maison_post_data)

    assert form.is_valid(), form.errors
    assert "center_purchase" not in form.fields
    form.instance.center_purchase = make_child_center("ACF")
    maison = form.save()
    assert maison.code_maison == "AF0001"
    assert maison.credit_account.account == "411000"
    assert Maison.objects.count() == 1


def test_maison_form_od_ana_sans_axe_bu(maison_post_data):
    """La règle du modèle remonte dans le formulaire : OD ANA exige un axe BU"""
    form = MaisonForm(data={**maison_post_data, "type_x3": "2"})

    assert not form.is_valid()
    assert set(form.errors) == {"axe_bu"}


def test_maison_form_compte_non_collectif(maison_post_data, make_account):
    """Un compte au crédit non collectif est refusé"""
    account = make_account("FRA", "607000", collective=False)
    form = MaisonForm(data={**maison_post_data, "credit_account": str(account.uuid_identification)})

    assert not form.is_valid()
    assert "credit_account" in form.errors


def test_maison_form_champs_obligatoires():
    """Sans données, les champs obligatoires sont en erreur"""
    form = MaisonForm(data={})

    assert not form.is_valid()
    assert {"cct", "intitule", "adresse", "third_party_num", "credit_account", "debit_account"} <= set(form.errors)


def test_maison_form_incomplet_avec_reference_cosium():
    """Référence Cosium sans cct : le clean du modèle ne plante pas (FK non renseignée)"""
    form = MaisonForm(data={"reference_cosium": "COS-1", "type_x3": "0"})

    assert not form.is_valid()
    assert "reference_cosium" not in form.errors


def test_maison_import_form_fields():
    """Le formulaire d'import expose les colonnes du fichier d'import B.I"""
    assert MaisonImportForm.Meta.model is Maison
    assert MaisonImportForm.Meta.fields[:3] == ["code_maison", "cct", "third_party_num"]
    assert "sage_plan_code" in MaisonImportForm.Meta.fields


# IMPORT MAISON BI FORM ============================================================================


def test_import_maison_bi_form_choices(make_maison_bi, make_cct, make_society):
    """Maisons B.I (hors code 0) et ccts triés, tiers clients uniquement"""
    make_maison_bi("M002", intitule="Deux")
    make_maison_bi("M001", intitule="Un")
    make_maison_bi("0", intitule="Fictive")
    make_cct("AF0002", name="Lyon")
    make_cct("AF0001", name="Paris")
    make_society("CLI001", name="Client")
    make_society("FOUR001", name="Fournisseur", is_client=False)

    form = ImportMaisonBiForm()

    assert form.fields["maison_bi"].choices == [("", ""), ("M001", "M001-Un"), ("M002", "M002-Deux")]
    assert form.fields["cct"].choices == [("", ""), ("AF0001", "AF0001-Paris"), ("AF0002", "AF0002-Lyon")]
    assert form.fields["tiers"].choices == [("", ""), ("CLI001", "CLI001-Client")]
    assert all(form.fields[name].required for name in ("maison_bi", "cct", "tiers"))


def test_import_maison_bi_form_validation(make_maison_bi, make_cct, make_society):
    """Valide avec des codes existants, invalide sinon"""
    make_maison_bi("M001")
    make_cct("AF0001")
    make_society("CLI001")

    assert ImportMaisonBiForm({"maison_bi": "M001", "cct": "AF0001", "tiers": "CLI001"}).is_valid()

    form = ImportMaisonBiForm({"maison_bi": "ZZZ", "cct": "AF0001", "tiers": "CLI001"})
    assert not form.is_valid()
    assert set(form.errors) == {"maison_bi"}


# EXCLUSIONS =======================================================================================


def test_exclusion_forms_tiers_en_usage(make_society, make_maison, make_country):
    """Les formulaires d'exclusion ne proposent que les tiers en usage"""
    used = make_society("FOUR001", is_client=False, in_use=True)
    make_society("FOUR002", is_client=False, in_use=False)
    maison = make_maison("AF0001")

    form = MaisonSupllierExclusionForm()
    country_form = SupllierCountryExclusionForm()

    assert used in form.fields["third_party_num"].queryset
    assert used in country_form.fields["third_party_num"].queryset
    assert not form.fields["third_party_num"].queryset.filter(third_party_num="FOUR002").exists()
    assert not country_form.fields["third_party_num"].queryset.filter(third_party_num="FOUR002").exists()

    form = MaisonSupllierExclusionForm(data={"third_party_num": "FOUR001", "cct_uuid_identification": str(maison.uuid_identification)})
    assert form.is_valid(), form.errors
    assert form.save().cct_uuid_identification == maison

    country_form = SupllierCountryExclusionForm(data={"third_party_num": "FOUR001", "pays": make_country("FR").pk})
    assert country_form.is_valid(), country_form.errors
    assert country_form.save().pays.country == "FR"


def test_exclusion_form_tiers_hors_usage_refuse(make_society, make_maison):
    """Un tiers non en usage est refusé par le formulaire"""
    make_society("FOUR002", is_client=False, in_use=False)
    maison = make_maison("AF0001")

    form = MaisonSupllierExclusionForm(data={"third_party_num": "FOUR002", "cct_uuid_identification": str(maison.uuid_identification)})

    assert not form.is_valid()
    assert set(form.errors) == {"third_party_num"}


# ABONNEMENTS ======================================================================================


def test_maison_subcription_form_querysets(make_maison, make_article, make_big_category):
    """Les articles proposés sont limités aux grandes catégories d'abonnement"""
    make_maison("AF0001")
    abonnement = make_article("ABO-1", big_category=make_big_category("Abonnements"))
    make_article("MARCH-1", big_category=make_big_category("Marchandises"))
    prestation = make_article("PRESTA-1", big_category=make_big_category("Prestation"))

    form = MaisonSubcriptionForm()

    assert set(form.fields["article"].queryset) == {abonnement, prestation}
    assert "cct" in form.fields["maison"].queryset.query.select_related
    assert form.fields["qty"].widget.attrs["step"] == "1"


def test_maison_subcription_form_valide(make_maison, make_article, make_unit, make_invoice_function, make_signboard, make_vat):
    """Création d'un abonnement par le formulaire"""
    maison = make_maison("AF0001")
    article = make_article("ABO-1")
    make_unit(1, "U")
    make_invoice_function("ABONNEMENT")
    make_signboard("ACF")
    make_vat("001")

    form = MaisonSubcriptionForm(
        data={
            "maison": "AF0001",
            "article": str(article.uuid_identification),
            "qty": "2",
            "unit_weight": "1",
            "net_unit_price": "99.90",
            "function": "ABONNEMENT",
            "for_signboard": "ACF",
            "vat": "001",
        }
    )

    assert form.is_valid(), form.errors
    subscription = form.save()
    assert subscription.maison == maison
    assert subscription.net_unit_price == Decimal("99.90")
    assert MaisonSubcription.objects.count() == 1


def test_maison_subcription_form_invalide(make_maison):
    """Sans article ni fonction, le formulaire est invalide"""
    make_maison("AF0001")
    form = MaisonSubcriptionForm(data={"maison": "AF0001", "qty": "1"})

    assert not form.is_valid()
    assert {"article", "unit_weight", "function"} <= set(form.errors)


# FAMILLES CLIENTS =================================================================================


def test_client_familly_form(make_client_familly):
    """Création, capitalisation à la sauvegarde et unicité"""
    form = ClientFamillyForm(data={"name": "succursale", "comment": "Magasins intégrés"})

    assert form.is_valid(), form.errors
    assert form.save().name == "Succursale"

    make_client_familly("franchise")

    for name in ("Franchise", "franchise", "FRANCHISE"):
        form = ClientFamillyForm(data={"name": name})
        assert not form.is_valid()
        assert set(form.errors) == {"name"}


# FORMULAIRES DE SUPPRESSION =======================================================================


@pytest.mark.parametrize(
    ("form_class", "factory_name"),
    [
        (ClientFamillyDeleteForm, "make_client_familly"),
        (MaisonSupllierExclusionDeleteForm, "make_exclusion"),
        (SupllierCountryExclusionDeleteForm, "make_country_exclusion"),
        (DeleteMaisonSubcriptionForm, "make_subscription"),
    ],
)
def test_formulaires_de_suppression(request, form_class, factory_name):
    """Valides avec un id existant, invalides avec un id inconnu ou vide"""
    instance = request.getfixturevalue(factory_name)()

    form = form_class({"id": instance.pk})

    assert form.is_valid()
    assert form.cleaned_data["id"] == instance
    assert not form_class({"id": instance.pk + 1000}).is_valid()
    assert not form_class({"id": None}).is_valid()
    assert form_class.Meta.fields in (["id"], ("id",))


def test_package_forms_reexporte(make_client_familly):
    """Le package forms expose les formulaires Django"""
    assert cc_forms.MaisonForm is MaisonForm
    assert isinstance(ClientFamilly.objects.first() or make_client_familly(), ClientFamilly)
