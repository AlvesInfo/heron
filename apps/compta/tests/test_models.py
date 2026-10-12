"""Tests des modèles compta"""

import pytest
from django.db import IntegrityError

pytestmark = pytest.mark.django_db


def test_ventes_cosium_str(make_vente):
    vente = make_vente(code_maison="AF0002", code_ean="EAN1")

    assert str(vente) == "AF0002 - EAN1"


def test_ventes_cosium_unique_code_cosium_id_bi(make_vente):
    make_vente(id_bi=10, code_cosium="COS1")

    with pytest.raises(IntegrityError):
        make_vente(id_bi=10, code_cosium="COS1")


def test_ca_clients_str(make_ca_client, make_maison, make_section):
    ca = make_ca_client(maison=make_maison("AF0009"), axe_pro=make_section("PRO", "AUD"))

    assert str(ca) == "2026-01-31 - AF0009 - AUD"


def test_ca_clients_unique(make_ca_client, make_maison, make_section):
    maison, axe = make_maison("AF0010"), make_section("PRO", "OPT")
    make_ca_client(maison=maison, axe_pro=axe)

    with pytest.raises(IntegrityError):
        make_ca_client(maison=maison, axe_pro=axe)
