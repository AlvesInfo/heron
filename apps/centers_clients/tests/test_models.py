# pylint: disable=E0401,W0621,W0212
"""FR : Tests des modèles de l'app centers_clients


EN : Tests for centers_clients models

created at: 2026-10-10
created by: Paulo ALVES
"""

import datetime
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.urls import reverse

from apps.centers_clients import models as cc_models
from apps.centers_clients.models import (
    CHOICES_LANGUE,
    ClientFamilly,
    Contact,
    ContactExchange,
    Maison,
    MaisonBi,
    MaisonSubcription,
    MaisonSupllierExclusion,
    MaisonSupplierIdentifier,
    SupllierCountryExclusion,
    TypeVente,
)

pytestmark = pytest.mark.django_db


# CLIENT FAMILLY / TYPE VENTE ======================================================================


def test_client_familly_capitalise_et_str(make_client_familly):
    """Le nom est capitalisé à la sauvegarde, __str__ le renvoie, tri par nom"""
    familly = make_client_familly("SUCCURSALE")
    make_client_familly("franchise")

    assert familly.name == "Succursale"
    assert str(familly) == "Succursale"
    assert list(ClientFamilly.objects.values_list("name", flat=True)) == ["Franchise", "Succursale"]


def test_client_familly_unique(make_client_familly):
    """Deux noms identiques après capitalisation sont refusés"""
    make_client_familly("franchise")

    with transaction.atomic(), pytest.raises(IntegrityError):
        ClientFamilly.objects.create(name="FRANCHISE")


def test_type_vente(make_type_vente):
    """Types de vente triés par numéro, __str__ = nom"""
    make_type_vente(2)
    make_type_vente(0)

    assert [str(t) for t in TypeVente.objects.all()] == ["BLOCAGE", "OD ANA"]

    with transaction.atomic(), pytest.raises(IntegrityError):
        TypeVente.objects.create(num=0, name="doublon")


def test_choices_langue():
    """Constante des langues disponibles"""
    assert dict(CHOICES_LANGUE)["FRA"] == "Français"
    assert len(CHOICES_LANGUE) == 5


# MAISON ===========================================================================================


def test_maison_creation_et_str(make_maison):
    """Création complète, code_maison par défaut = cct, __str__, défauts RFA et flags"""
    maison = make_maison("AF0001", intitule="Acuitis Paris")

    assert str(maison) == "AF0001 - Acuitis Paris"
    assert maison.code_maison == "AF0001"
    assert maison.rfa_frequence == Maison.Frequence.MENSUEL
    assert maison.rfa_remise == Maison.Remise.TOTAL
    assert maison.generic_coefficient == Decimal(1)
    assert maison.integrable is True
    assert maison.chargeable is True
    assert maison.od_ana is False
    assert maison.type_x3.num == 0
    assert maison.currency.code == "EUR"
    assert maison.language.code == "FRA"


def test_maison_code_maison_fourni_conserve(make_maison):
    """Un code maison explicite n'est pas écrasé par le cct"""
    assert make_maison("AF0002", code_maison="M-002").code_maison == "M-002"


def test_maison_choices():
    """Libellés des énumérations Frequence et Remise"""
    assert Maison.Frequence.choices[0] == (0, "---------")
    assert dict(Maison.Frequence.choices)[4] == "Annuel"
    assert dict(Maison.Remise.choices)[3] == "Article"


@pytest.mark.parametrize(
    ("fields", "expected"),
    [
        (
            {
                "intitule": "Acuitis",
                "immeuble": "Bât. A",
                "adresse": "1 rue X",
                "code_postal": "75001",
                "ville": "Paris",
            },
            "Acuitis, Bât. A, 1 rue X - 75001 Paris",
        ),
        (
            {
                "intitule": "Acuitis",
                "immeuble": None,
                "adresse": "1 rue X",
                "code_postal": "75001",
                "ville": "Paris",
            },
            "Acuitis, 1 rue X - 75001 Paris",
        ),
        (
            {"intitule": "Acuitis", "immeuble": "", "adresse": "", "code_postal": "", "ville": ""},
            "Acuitis",
        ),
        (
            {"intitule": "", "immeuble": "", "adresse": "", "code_postal": "75001", "ville": ""},
            " - 75001",
        ),
    ],
)
def test_maison_get_address(fields, expected):
    """Intitulé, immeuble et adresse séparés par des virgules, puis ' - code postal ville'"""
    assert Maison(**fields).get_address == expected


def test_maison_get_absolute_url():
    """Retour sur la liste des maisons"""
    assert Maison.get_absolute_url() == reverse("centers_clients:maisons_list")


@pytest.mark.usefixtures("make_cct")
def test_maison_cct_one_to_one(make_maison):
    """Un cct ne peut porter qu'une maison et un cct utilisé est protégé"""
    maison = make_maison("AF0001")
    cct = type(maison.cct).objects.filter(pk=maison.cct.pk)

    with transaction.atomic(), pytest.raises(IntegrityError):
        make_maison("AF0001")

    with pytest.raises(ProtectedError):
        cct.delete()


def test_maison_suppression_tiers_en_cascade(make_maison):
    """La suppression du tiers X3 supprime la maison (CASCADE)"""
    maison = make_maison("AF0001")

    type(maison.third_party_num).objects.filter(pk=maison.third_party_num.pk).delete()

    assert not Maison.objects.filter(pk=maison.pk).exists()


def test_maison_ordering_et_related(make_maison):
    """Tri par cct, related_name sur le cct et le tiers"""
    make_maison("AF0002")
    maison = make_maison("AF0001")

    assert list(Maison.objects.values_list("cct", flat=True)) == ["AF0001", "AF0002"]
    assert maison.cct.maison_cct == maison
    assert maison in maison.third_party_num.tiers_maison.all()


# MAISON.clean() ===================================================================================


def test_clean_od_ana_exige_un_axe_bu(make_maison):
    """Type de vente OD ANA (2) sans axe BU : erreur sur axe_bu"""
    maison = make_maison("AF0001", type_x3=2)

    with pytest.raises(ValidationError) as excinfo:
        maison.clean()

    assert set(excinfo.value.message_dict) == {"axe_bu"}


def test_clean_od_ana_conserve_l_axe_bu(make_maison, make_section):
    """Type OD ANA avec axe BU : valide et l'axe est conservé"""
    axe_bu = make_section("BU", "BU01")
    maison = make_maison("AF0001", type_x3=2, axe_bu=axe_bu)

    maison.clean()

    assert maison.axe_bu == axe_bu


@pytest.mark.parametrize("type_num", [0, 1])
def test_clean_hors_od_ana_efface_l_axe_bu(make_maison, make_section, type_num):
    """Pour les autres types de vente, l'axe BU est remis à None"""
    maison = make_maison("AF0001", type_x3=type_num, axe_bu=make_section("BU", "BU01"))

    maison.clean()

    assert maison.axe_bu is None


def test_clean_reference_cosium_unique_entre_maisons(make_maison):
    """La référence Cosium ne peut pas être portée par deux maisons"""
    make_maison("AF0001", reference_cosium="COS-1")
    doublon = make_maison("AF0002")
    doublon.reference_cosium = "COS-1"

    with pytest.raises(ValidationError) as excinfo:
        doublon.clean()

    assert "AF0001" in str(excinfo.value.message_dict["reference_cosium"][0])


def test_clean_reference_cosium_meme_maison(make_maison):
    """La maison qui porte déjà la référence peut la revalider"""
    maison = make_maison("AF0001", reference_cosium="COS-1")

    maison.clean()

    assert maison.reference_cosium == "COS-1"


@pytest.mark.parametrize("field", ["credit_account", "debit_account"])
def test_clean_comptes_collectifs(make_maison, make_account, field):
    """Les comptes au crédit et au débit doivent être collectifs"""
    maison = make_maison("AF0001", **{field: make_account("FRA", "411000", collective=False)})

    with pytest.raises(ValidationError) as excinfo:
        maison.clean()

    assert set(excinfo.value.message_dict) == {field}

    setattr(maison, field, make_account("FRA", "411100", collective=True))
    maison.clean()


def test_clean_tiers_doit_etre_client(make_maison, make_society):
    """Le tiers X3 doit être flagué client dans Sage"""
    maison = make_maison("AF0001", third_party_num=make_society("FOUR001", is_client=False))

    with pytest.raises(ValidationError) as excinfo:
        maison.clean()

    assert set(excinfo.value.message_dict) == {"third_party_num"}


def test_clean_sans_fk_renseignees():
    """clean() sur une instance vide ne lève pas d'exception d'accès aux FK"""
    Maison().clean()
    Maison(reference_cosium="COS-1").clean()


def test_full_clean_maison_valide(make_maison, make_account):
    """Une maison complète passe full_clean (validation modèle + champs).

    `acquitted` (FlagsTable, null=True sans blank=True) est exclu comme le fait tout ModelForm.
    """
    maison = make_maison(
        "AF0001",
        credit_account=make_account("FRA", "411000", collective=True),
        debit_account=make_account("FRA", "401000", collective=True),
        signature_franchise_date=datetime.date(2020, 1, 1),
    )

    maison.full_clean(exclude=["acquitted"])


# AUTRES MODÈLES ===================================================================================


def test_documents_subscription_et_contact_exchange(make_contact, make_document_subscription):
    """__str__ des abonnements documents et des échanges contact/document"""
    contact = make_contact(first_name="Jean", last_name="Dupont")
    document = make_document_subscription("Factures")
    exchange = ContactExchange.objects.create(contact=contact, document=document)

    assert str(document) == "Factures"
    assert str(exchange) == "Jean - Dupont - Factures"
    assert list(document.document_contact.all()) == [exchange]


@pytest.mark.parametrize(
    ("first_name", "last_name", "expected"),
    [("Jean", "Dupont", "Jean - Dupont"), (None, "Dupont", "Dupont"), ("", "Dupont", "Dupont")],
)
def test_contact_str(make_contact, first_name, last_name, expected):
    """Le prénom n'est préfixé que s'il est renseigné"""
    assert str(make_contact(first_name=first_name, last_name=last_name)) == expected


def test_contact_cascade_et_nature(make_contact, make_nature):
    """La nature est optionnelle, la suppression de la maison supprime le contact"""
    contact = make_contact(nature=make_nature("Gérant"))

    assert contact.nature.name == "Gérant"
    assert contact.language.code == "FRA"

    Maison.objects.filter(pk=contact.maison.pk).delete()

    assert not Contact.objects.filter(pk=contact.pk).exists()


def test_maison_bi_defauts(make_maison_bi):
    """Une maison B.I est nouvelle et non modifiée à la création, pk = code maison"""
    maison_bi = make_maison_bi("M001")

    assert maison_bi.pk == "M001"
    assert maison_bi.is_new is True
    assert maison_bi.is_modify is False
    assert MaisonBi.objects.get(pk="M001").pays.country == "FR"


def test_maison_supllier_exclusion(make_exclusion):
    """__str__, url de succès, unicité du couple et cascade sur la maison"""
    exclusion = make_exclusion()

    assert (
        str(exclusion)
        == f"{exclusion.third_party_num} - {exclusion.cct_uuid_identification.cct.cct}"
    )
    assert MaisonSupllierExclusion.get_success_url() == reverse("home")

    with transaction.atomic(), pytest.raises(IntegrityError):
        MaisonSupllierExclusion.objects.create(
            third_party_num=exclusion.third_party_num,
            cct_uuid_identification=exclusion.cct_uuid_identification,
        )

    Maison.objects.filter(pk=exclusion.cct_uuid_identification.pk).delete()
    assert not MaisonSupllierExclusion.objects.exists()


def test_supllier_country_exclusion(make_country_exclusion, make_country):
    """__str__, url de succès, unicité du couple tiers/pays"""
    exclusion = make_country_exclusion(country=make_country("BE", "Belgique"))

    assert str(exclusion) == f"{exclusion.third_party_num} - {exclusion.pays}"
    assert SupllierCountryExclusion.get_success_url() == reverse("home")

    with transaction.atomic(), pytest.raises(IntegrityError):
        SupllierCountryExclusion.objects.create(
            third_party_num=exclusion.third_party_num, pays=exclusion.pays
        )


def test_maison_supplier_identifier(make_supplier_identifier):
    """__str__ et unicité du couple tiers/maison"""
    identifier = make_supplier_identifier(identifiant="X-1")

    assert str(identifier) == f"{identifier.third_party_num} - {identifier.maison}"
    assert identifier.identifiant == "X-1"

    with transaction.atomic(), pytest.raises(IntegrityError):
        MaisonSupplierIdentifier.objects.create(
            third_party_num=identifier.third_party_num, maison=identifier.maison, identifiant="X-2"
        )


def test_maison_subcription_metadonnees():
    """Colonnes d'import, clés d'unicité et urls de retour"""
    assert list(MaisonSubcription.get_columns_import()) == [
        "maison",
        "article",
        "qty",
        "unit_weight",
        "net_unit_price",
        "function",
        "for_signboard",
        "vat",
    ]
    assert list(MaisonSubcription.get_columns_import().values()) == list(range(8))
    assert MaisonSubcription.get_uniques() == {"maison", "article", "function", "for_signboard"}
    assert MaisonSubcription.get_absolute_url() == reverse("centers_clients:subscriptions_list")
    assert MaisonSubcription.get_success_url() == reverse("centers_clients:subscriptions_list")


def test_maison_subcription_defauts_et_unicite(make_subscription, make_vat):
    """Défauts (qty 1, enseigne ACF, tva nulle) et unicité maison/fonction/article/enseigne"""
    subscription = make_subscription(vat=make_vat("001"))

    assert subscription.qty == Decimal(1)
    assert subscription.for_signboard.code == "ACF"
    assert subscription.vat.vat == "001"

    with transaction.atomic(), pytest.raises(IntegrityError):
        make_subscription(
            maison=subscription.maison,
            article=subscription.article,
            function=subscription.function,
            for_signboard=subscription.for_signboard,
        )


def test_maison_subcription_cascade_et_protect(make_subscription):
    """Suppression de la maison en cascade, article protégé"""
    subscription = make_subscription()
    article = type(subscription.article).objects.filter(pk=subscription.article.pk)

    with pytest.raises(ProtectedError):
        article.delete()

    Maison.objects.filter(pk=subscription.maison.pk).delete()
    assert not MaisonSubcription.objects.exists()


def test_module_expose_les_modeles():
    """Le module models expose bien tous les modèles de l'app"""
    assert {m.__name__ for m in (cc_models.Maison, cc_models.Contact, cc_models.MaisonBi)} <= set(
        dir(cc_models)
    )
