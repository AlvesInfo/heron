"""Tests de la génération du chiffre d'affaires par maison et axe pro"""

from decimal import Decimal

import pytest

from apps.compta.bin.generate_ca import delete_ca, set_ca
from apps.compta.models import CaClients

pytestmark = pytest.mark.django_db
PERIOD = ("2026-01-01", "2026-01-31")


def test_set_ca_agrege_par_maison_et_axe(make_vente, make_maison, cosium_familly_axes, make_user):
    user = make_user()
    maison = make_maison("AF0001")
    cosium_familly_axes("LUNETTES", "OPT")
    cosium_familly_axes("VERRES", "OPT")
    cosium_familly_axes("AUDIO", "AUD")
    make_vente(
        cct_uuid_identification=maison,
        famille_cosium="LUNETTES",
        ca_ht_ap_remise_eur=Decimal(100),
        ca_ht_ap_remise=Decimal(100),
    )
    make_vente(
        cct_uuid_identification=maison,
        famille_cosium="VERRES",
        ca_ht_ap_remise_eur=Decimal(50),
        ca_ht_ap_remise=Decimal(55),
    )
    make_vente(
        cct_uuid_identification=maison,
        famille_cosium="AUDIO",
        ca_ht_ap_remise_eur=Decimal(10),
        ca_ht_ap_remise=Decimal(10),
    )
    make_vente(
        cct_uuid_identification=maison,
        famille_cosium="LUNETTES",
        code_ean="BON KDO",
        ca_ht_ap_remise_eur=Decimal(999),
    )
    make_vente(
        cct_uuid_identification=maison,
        famille_cosium="INCONNUE",
        ca_ht_ap_remise_eur=Decimal(999),
    )

    set_ca(*PERIOD, user.uuid_identification)

    rows = {row.axe_pro.section: row for row in CaClients.objects.all()}
    assert set(rows) == {"OPT", "AUD"}
    assert rows["OPT"].ca_ht_eur == Decimal(150)
    assert rows["OPT"].ca_ht_devise == Decimal(155)
    assert rows["OPT"].famille_cosium == "LUNETTES|VERRES"
    assert rows["OPT"].date_ca.isoformat() == "2026-01-31"
    assert rows["OPT"].created_by == user
    assert rows["AUD"].ca_ht_eur == Decimal(10)

    # Relance : "on conflict do nothing", rien n'est doublé
    set_ca(*PERIOD, user.uuid_identification)
    assert CaClients.objects.count() == 2


def test_delete_ca(make_ca_client):
    make_ca_client(date_ca="2026-01-31")
    make_ca_client(date_ca="2026-02-28", code_cosium="COS2")

    delete_ca(*PERIOD)

    assert list(CaClients.objects.values_list("date_ca", flat=True).order_by("date_ca")) == [
        __import__("datetime").date(2026, 2, 28)
    ]
