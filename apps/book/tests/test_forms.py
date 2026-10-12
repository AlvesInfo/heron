# pylint: disable=E0401,W0621
"""
FR : Tests des formulaires de l'app book (forms_django, forms_serializers)
EN : Tests for book forms

created at: 2026-10-11
created by: Paulo ALVES
"""
import pytest

from apps.book.forms import (
    BookAdressesSageForm,
    BookBanksSageForm,
    BookContactsSageForm,
    BpcBookSageForm,
    BprBookSageForm,
    BpsBookSageForm,
    CodeContactsSageForm,
    DeleteSupplierFamilyAxesForm,
    SageEmailForm,
    SocietyForm,
    StatFamillyAxesForm,
    SupplierCctForm,
    SupplierCctUnitForm,
    SupplierFamilyAxesForm,
)
from apps.book.models import Address, Contact, Society, SocietyBank, SupplierCct
from apps.core.validations.forms_base import SageNullBooleanField

pytestmark = pytest.mark.django_db


# FORMULAIRE DU TIERS ==============================================================================


def _society_data(society, **overrides):
    data = {"third_party_num": society.third_party_num, "name": society.name}
    data.update(overrides)
    return data


def test_society_form_champs_optionnels_et_cases_a_cocher(make_society):
    """Les cases à cocher et les champs d'adresse ne sont pas obligatoires"""
    form = SocietyForm(instance=make_society("TIERS01"))

    assert form.use_required_attribute is False
    assert all(
        form.fields[name].required is False
        for name in ("in_use", "is_multi_billing", "integrable", "chargeable", "od_ana", "default_axe_pro", "stat_name", "email_01", "invoice_entete")
    )
    assert form.fields["third_party_num"].required is True


def test_society_form_normalise_les_identifiants(make_society):
    """Identifiants nettoyés, dédoublonnés et triés"""
    society = make_society("TIERS01")
    form = SocietyForm(_society_data(society, centers_suppliers_indentifier=" b | a |a||"), instance=society)

    assert form.is_valid(), form.errors
    assert form.cleaned_data["centers_suppliers_indentifier"] == "a|b"
    assert form.save().centers_suppliers_indentifier == "a|b"


def test_society_form_identifiant_deja_utilise_par_un_autre_tiers(make_society):
    """Un identifiant déjà porté par un autre tiers est refusé, le même tiers peut le garder"""
    make_society("AUTRE01", centers_suppliers_indentifier="X|Y")
    society = make_society("TIERS01", centers_suppliers_indentifier="Z")

    form = SocietyForm(_society_data(society, centers_suppliers_indentifier="Y|Z"), instance=society)

    assert form.is_valid() is False
    assert "Doublons décelés dans Identifiant Centrale :" in form.errors["__all__"][0]
    assert "'Y', existe dèjà pour le Tiers : AUTRE01" in form.errors["__all__"][0]

    form = SocietyForm(_society_data(society, centers_suppliers_indentifier="Z"), instance=society)
    assert form.is_valid(), form.errors


def test_society_form_sans_identifiant(make_society):
    society = make_society("TIERS01")
    form = SocietyForm(_society_data(society, centers_suppliers_indentifier=""), instance=society)

    assert form.is_valid(), form.errors
    assert form.cleaned_data["centers_suppliers_indentifier"] is None


# FORMULAIRES DES IDENTIFIANTS ET STATISTIQUES =====================================================


@pytest.mark.parametrize("form_class", [SupplierCctForm, SupplierCctUnitForm])
def test_supplier_cct_forms(form_class, make_supplier_cct):
    """Seul l'identifiant est saisissable (l'id auto n'est pas un champ de formulaire)"""
    supplier_cct = make_supplier_cct(cct_identifier="A|")
    form = form_class({"cct_identifier": "B|"}, instance=supplier_cct)

    assert form_class.Meta.model is SupplierCct
    assert list(form.fields) == ["cct_identifier"]
    assert form.is_valid()
    assert form.changed_data == ["cct_identifier"]
    assert form_class({"cct_identifier": "x" * 151}).is_valid() is False


def test_stat_familly_axes_form():
    form = StatFamillyAxesForm({"name": "ACUITIS", "description": "", "regex_bool": "on"})

    assert form.use_required_attribute is False
    assert form.is_valid(), form.errors
    assert form.cleaned_data["regex_bool"] is True
    assert StatFamillyAxesForm({"name": ""}).is_valid() is False


def test_supplier_family_axes_form(make_stat_familly, make_section, make_big_category, make_unit):
    """La rubrique est facultative, l'unité obligatoire, sélections fluides sur axes et catégories"""
    stat = make_stat_familly("ACUITIS")
    pro = make_section("PRO", "OPT")
    category = make_big_category("Marchandises")
    make_unit(1, "U")
    form = SupplierFamilyAxesForm(
        {
            "stat_name": stat.name,
            "invoice_column": "famille",
            "regex_match": "LUN",
            "expected_result": "LUNETTES",
            "axe_pro": str(pro.uuid_identification),
            "big_category": str(category.uuid_identification),
            "item_weight": "1.5",
            "unit_weight": "1",
        }
    )

    assert form.use_required_attribute is False
    assert form.fields["sub_category"].required is False
    assert form.fields["unit_weight"].required is True
    assert form.fields["axe_pro"].widget.attrs["class"]
    assert form.is_valid(), form.errors
    assert form.save().axe_pro == pro


def test_delete_supplier_family_axes_form(make_supplier_family_axes):
    """L'id doit désigner une définition existante"""
    definition = make_supplier_family_axes("LUNETTES")

    assert DeleteSupplierFamilyAxesForm({"id": definition.pk}).is_valid()
    assert DeleteSupplierFamilyAxesForm({"id": definition.pk + 1000}).is_valid() is False
    assert DeleteSupplierFamilyAxesForm({"id": ""}).is_valid() is False


# FORMULAIRES DE VALIDATION DES FICHIERS SAGE ======================================================


@pytest.mark.parametrize(
    ("form_class", "model", "sage_booleans"),
    [
        (BprBookSageForm, Society, {"is_client", "is_agent", "is_prospect", "is_supplier", "is_various", "is_service_provider", "is_transporter", "is_contractor"}),
        (BpsBookSageForm, Society, set()),
        (BpcBookSageForm, Society, set()),
        (BookAdressesSageForm, Address, {"default_adress"}),
        (CodeContactsSageForm, Contact, set()),
        (BookContactsSageForm, Contact, set()),
        (BookBanksSageForm, SocietyBank, {"is_default"}),
    ],
)
def test_formulaires_sage_booleens(form_class, model, sage_booleans):
    """Les drapeaux Sage sont des SageNullBooleanField (2 = vrai, 1 = faux), le modèle est ciblé"""
    form = form_class()

    assert form_class.Meta.model is model
    assert {name for name, field in form.fields.items() if isinstance(field, SageNullBooleanField)} == sage_booleans
    assert set(form_class.Meta.fields) <= {field.name for field in model._meta.fields}  # pylint: disable=W0212


def test_bpr_book_sage_form_valide_un_tiers(make_country):
    make_country("FR")
    form = BprBookSageForm(
        {"third_party_num": "FOUR001", "name": "Fournisseur", "country": "FR", "is_client": "1", "is_supplier": "2", "is_agent": ""}
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["is_supplier"] is True
    assert form.cleaned_data["is_client"] is False
    assert form.cleaned_data["is_agent"] is None


def test_book_banks_sage_form_valide_une_banque(make_society, make_country):
    """Le tiers est désigné par son numéro X3, le pays par son code"""
    make_society("FOUR001")
    make_country("FR")
    form = BookBanksSageForm({"society": "FOUR001", "account_number": "FR76", "country": "FR", "is_default": "2"})

    assert form.is_valid(), form.errors
    assert form.save().is_default is True


# SÉRIALISEUR EMAIL ================================================================================


@pytest.mark.parametrize(
    ("email", "expected"),
    [("contact@acuitis.com", True), ("prenom.nom@domaine.fr", True), ("sans-arobase", False), ("", False), ("a@b", False)],
)
def test_sage_email_form(email, expected):
    assert SageEmailForm(data={"email": email, "third_party_num": "X"}).is_valid() is expected
