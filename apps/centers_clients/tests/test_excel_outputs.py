# pylint: disable=E0401,W0621
"""FR : Tests des exports Excel de l'app centers_clients


EN : Tests for centers_clients Excel exports

created at: 2026-10-10
created by: Paulo ALVES
"""

import io
import logging
from decimal import Decimal

import pytest

from apps.centers_clients.excel_outputs import (
    centers_clients_excel_maisons_list,
    excel_client_familly_list,
    excel_exclusions_tiers_clients_list,
    excel_exclusions_tiers_pays_clients_list,
    excel_maisons_excel_subscriptions,
)
from apps.centers_clients.excel_outputs.centers_clients_columns import columns_list_maisons
from apps.core.excel_outputs import generic_list_export
from conftest import patched_attrs

pytestmark = pytest.mark.django_db

EXCEL_FUNCTIONS = [
    (excel_client_familly_list, "excel_client_familly"),
    (excel_exclusions_tiers_clients_list, "excel_liste_exclusion"),
    (excel_exclusions_tiers_pays_clients_list, "excel_liste_exclusion_pays"),
    (excel_maisons_excel_subscriptions, "excel_liste_subscriptions"),
    (centers_clients_excel_maisons_list, "excel_liste_maisons"),
]


# LIGNES ===========================================================================================


def test_lignes_familles(make_client_familly):
    """Nom et commentaire (vide si None)"""
    make_client_familly("franchise", comment="Franchisés")
    make_client_familly("succursale")

    assert excel_client_familly_list.get_clean_rows() == [
        ("Franchise", "Franchisés"),
        ("Succursale", ""),
    ]


def test_lignes_exclusions(make_exclusion):
    """Tiers et maison (cct - intitulé)"""
    exclusion = make_exclusion()

    assert excel_exclusions_tiers_clients_list.get_clean_rows() == [
        (str(exclusion.third_party_num), str(exclusion.cct_uuid_identification))
    ]


def test_lignes_exclusions_pays(make_country_exclusion):
    """Tiers et pays"""
    exclusion = make_country_exclusion()

    assert excel_exclusions_tiers_pays_clients_list.get_clean_rows() == [
        (str(exclusion.third_party_num), str(exclusion.pays))
    ]


def test_lignes_abonnements(make_subscription):
    """Les 8 colonnes de l'export des abonnements"""
    subscription = make_subscription(qty=Decimal(3), net_unit_price=Decimal("12.5"))

    assert excel_maisons_excel_subscriptions.get_clean_rows() == [
        (
            subscription.maison.cct.cct,
            subscription.maison.intitule,
            subscription.article.reference,
            Decimal("3.00000"),
            "U",
            Decimal("12.50000"),
            "ABONNEMENT",
            "ACF",
        )
    ]


def test_lignes_maisons(make_maison, make_address, make_account, make_section):
    """L'export des maisons aligne ses colonnes sur la définition, avec les emails Sage"""
    maison = make_maison(
        "AF0001",
        intitule="Paris",
        siret_number="12345678901234",
        credit_account=make_account("FRA", "411000", collective=True),
        axe_bu=make_section("BU", "BU01"),
    )
    make_address(
        maison.third_party_num, "1", email_01="un@heron.local", email_05="cinq@heron.local"
    )
    make_address(maison.third_party_num, "2", email_01="autre@heron.local")

    rows = centers_clients_excel_maisons_list.get_clean_rows()

    assert len(rows) == 1
    row = rows[0]
    assert len(row) == len(columns_list_maisons)
    assert row[0] == "AF0001"
    assert row[1] == "NON"
    assert row[4] == "Paris"
    assert row[20] == "411000"
    assert row[27] == "Mensuel"
    assert row[28] == "Fournisseur Total"
    assert row[42] == "un@heron.local"
    assert row[46] == "cinq@heron.local"
    assert row[56] == "BU01"
    assert row[57].replace(" ", "") == "12345678901234"


def test_lignes_maisons_siren_sans_siret(make_maison):
    """Sans siret, le siren est utilisé pour la colonne formatée"""
    make_maison("AF0001", siren_number="123456789", siret_number="")

    row = centers_clients_excel_maisons_list.get_clean_rows()[0]

    assert row[57].replace(" ", "") == "123456789"
    assert row[42] is None


def test_definition_des_colonnes():
    """Chaque colonne de chaque export a un entête, des formats et une largeur"""
    for module, _ in EXCEL_FUNCTIONS[:-1]:
        for column in module.columns:
            assert {"entete", "f_entete", "f_ligne", "width"} <= set(column)

    assert all(
        {"entete", "f_entete", "f_ligne", "width"} <= set(column) for column in columns_list_maisons
    )


# FICHIERS =========================================================================================


@pytest.mark.parametrize(("module", "function_name"), EXCEL_FUNCTIONS)
def test_generation_excel(
    module,
    function_name,
    make_client_familly,
    make_exclusion,
    make_country_exclusion,
    make_subscription,
):
    """Chaque export génère un xlsx en mémoire et renvoie OK"""
    make_client_familly("franchise")
    make_exclusion()
    make_country_exclusion()
    make_subscription()
    file_io = io.BytesIO()

    result = getattr(module, function_name)(file_io, "export.xlsx")

    assert result == {"OK": "GENERATION DU FICHIER export.xlsx TERMINEE AVEC SUCCES"}
    assert file_io.getvalue()[:2] == b"PK"


@pytest.mark.parametrize(("module", "function_name"), EXCEL_FUNCTIONS)
def test_generation_excel_en_erreur(module, function_name, monkeypatch, caplog):
    """Une erreur d'écriture est journalisée, le classeur fermé et KO renvoyé"""

    def _boom(*_args, **_kwargs):
        raise RuntimeError("écriture impossible")

    with (
        patched_attrs(monkeypatch, generic_list_export, titre_page_writer=_boom),
        patched_attrs(monkeypatch, module, titre_page_writer=_boom),
        caplog.at_level(logging.ERROR, logger="export_excel"),
    ):
        result = getattr(module, function_name)(io.BytesIO(), "export.xlsx")

    assert result == {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}
    assert "export.xlsx" in caplog.text
