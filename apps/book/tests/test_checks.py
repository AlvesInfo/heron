# pylint: disable=E0401,W0621
"""FR : Tests des vérifications de book (bin/checks.py) : identifiants cct et emails des tiers


EN : Tests for book checks: cct identifiers and third parties emails

created at: 2026-10-11
created by: Paulo ALVES
"""

import pytest

from apps.book.bin.checks import (
    check_cct_identifier,
    check_emails,
    check_emails_notifications,
    check_emails_to_send,
    split_identifiers,
)
from apps.core.models.models_notifications import Notification

pytestmark = pytest.mark.django_db


# IDENTIFIANTS CCT =================================================================================


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, [""]),
        ("", [""]),
        ("A", ["A"]),
        ("A|", ["A"]),
        ("A|B|", ["A", "B"]),
        ("A||", ["A", ""]),
    ],
)
def test_split_identifiers(value, expected):
    assert split_identifiers(value) == expected


@pytest.fixture
def supplier_ccts(make_society, make_cct, make_supplier_cct):
    """Un fournisseur avec deux cct identifiés, un autre fournisseur avec le même identifiant"""
    society = make_society("FOUR001", is_client=False)
    paris = make_supplier_cct(society, make_cct("AF0001", name="Paris"), "PAR|P2|")
    lyon = make_supplier_cct(society, make_cct("AF0002", name="Lyon"), "LYO")
    make_supplier_cct(make_society("FOUR002", is_client=False), make_cct("AF0001"), "NEW|")
    return {"paris": paris, "lyon": lyon}


@pytest.mark.parametrize("after", ["PAR|P2|", "PAR|P2", "P2|PAR|"])
def test_check_cct_identifier_rien_modifie(supplier_ccts, after):
    """Même liste (ordre ou "|" final différents) : rien à modifier, ou identifiant déjà présent"""
    changed, message = check_cct_identifier({"id": supplier_ccts["paris"], "cct_identifier": after})

    assert changed is False
    assert message in {
        "Vous n'avez rien modifié !",
        "Vous avez ajouté un dentifiant déjà présent pour le cct : AF0001",
    }


def test_check_cct_identifier_meme_ensemble_dans_un_autre_ordre(supplier_ccts):
    changed, message = check_cct_identifier(
        {"id": supplier_ccts["paris"], "cct_identifier": "P2|PAR|"}
    )

    assert changed is False
    assert message == "Vous avez ajouté un dentifiant déjà présent pour le cct : AF0001"


def test_check_cct_identifier_vide_vers_vide(make_supplier_cct):
    """Identifiant absent avant et après : rien modifié (None et chaîne vide sont équivalents)"""
    supplier_cct = make_supplier_cct(cct_identifier=None)

    assert check_cct_identifier({"id": supplier_cct, "cct_identifier": ""}) == (
        False,
        "Vous n'avez rien modifié !",
    )
    assert check_cct_identifier({"id": supplier_cct, "cct_identifier": None}) == (
        False,
        "Vous n'avez rien modifié !",
    )


def test_check_cct_identifier_nouvel_identifiant_libre(supplier_ccts):
    """Un identifiant inconnu du tiers peut être ajouté ; celui d'un autre tiers n'interfère pas"""
    assert check_cct_identifier({"id": supplier_ccts["paris"], "cct_identifier": "PAR|P2|P3|"}) == (
        True,
        "",
    )
    assert check_cct_identifier({"id": supplier_ccts["lyon"], "cct_identifier": "NEW|"}) == (
        True,
        "",
    )
    assert check_cct_identifier({"id": supplier_ccts["lyon"], "cct_identifier": None}) == (True, "")


def test_check_cct_identifier_deja_utilise_par_un_autre_cct(supplier_ccts):
    """Un identifiant déjà porté par un autre cct du même tiers est refusé, tous sont listés"""
    changed, message = check_cct_identifier(
        {"id": supplier_ccts["lyon"], "cct_identifier": "LYO|PAR|P2|"}
    )

    assert changed is None
    assert message == (
        "L'identifiant PAR est déjà utilisé dans le cct AF0001   -   "
        "L'identifiant P2 est déjà utilisé dans le cct AF0001"
    )


# EMAILS ===========================================================================================


@pytest.fixture
def societies_emails(make_society):
    """Deux tiers : un avec des emails valides et deux faux, un sans email"""
    make_society(
        "TIERS01",
        email_01="bon@acuitis.com",
        email_02="faux-email",
        email_03="",
        email_04="autre@acuitis.com",
        email_05="pas bon non plus",
    )
    make_society("TIERS02")


def test_check_emails_renvoie_les_faux_emails(societies_emails):
    assert list(check_emails()) == [
        {"email": "faux-email", "third_party_num": "TIERS01"},
        {"email": "pas bon non plus", "third_party_num": "TIERS01"},
    ]
    assert Notification.objects.count() == 0


def test_check_emails_en_boucle_notifie_une_seule_fois(societies_emails, make_user):
    """En boucle supervisor, une notification est créée pour chaque utilisateur actif, une fois"""
    user = make_user()
    inactive = make_user(email="inactif@heron.local", username="inactif")
    inactive.is_active = False
    inactive.save()

    errors = list(check_emails(is_loop=True))

    assert len(errors) == 2
    notification = Notification.objects.get()
    assert notification.user == user
    assert notification.title == "Erreurs Emails"
    assert notification.level == "error"
    assert notification.link == "/book/emails_errors_list/"


def test_check_emails_sans_erreur_ne_notifie_pas(make_society, make_user):
    make_user()
    make_society("TIERS01", email_01="bon@acuitis.com")

    assert list(check_emails(is_loop=True)) == []
    assert Notification.objects.count() == 0


def test_check_emails_notifications(societies_emails, make_user):
    """Consomme check_emails en mode boucle"""
    make_user()

    check_emails_notifications()

    assert Notification.objects.count() == 1


def test_check_emails_to_send_sans_facture_en_cours(societies_emails):
    """Sans facture de vente non finalisée, aucun tiers n'est contrôlé"""
    assert list(check_emails_to_send()) == []


def test_check_emails_to_send_filtre_les_faux_emails_des_tiers_a_facturer(
    societies_emails, make_society, make_sale_invoice
):
    """Seuls les faux emails des tiers ayant une facture de vente non finalisée sont renvoyés"""
    make_society("TIERS03", email_01="faux aussi")
    make_sale_invoice(third_party_num="TIERS01", final=False)
    make_sale_invoice(third_party_num="TIERS02", final=False)
    make_sale_invoice(third_party_num="TIERS03", final=True)

    assert list(check_emails_to_send()) == [
        {"email": "faux-email", "third_party_num": "TIERS01"},
        {"email": "pas bon non plus", "third_party_num": "TIERS01"},
    ]
