"""Tests de l'import des ventes Cosium depuis la table B.I (SQL réelles)"""

import datetime
from decimal import Decimal

import pytest
from django.db import connection

from apps.compta.imports import import_ventes_cosium
from apps.compta.imports.import_ventes_cosium import (
    HISTORIC_VENTES_ID,
    force_update_sales,
    insert_ventes_cosium,
    mise_a_jour_ventes_cosium,
    set_cct_ventes,
    update_cct_from_bi,
    update_exchange_rates,
)
from apps.compta.models import VentesCosium

pytestmark = pytest.mark.django_db
PERIOD = ("2026-01-01", "2026-01-31")


@pytest.fixture
def maison_chf(make_maison, make_country, make_exchange_rate):
    """Maison suisse (devise CHF, code_maison AF0001) avec un taux de change pour janvier 2026"""
    pays = make_country("CH", "Suisse", currency_iso="CHF")
    make_exchange_rate("CHF", datetime.date(2026, 1, 1), Decimal(2))
    return make_maison("AF0001", pays=pays, code_maison="AF0001")


def test_insert_ventes_cosium_premier_import(bi_ventes_table, maison_chf):
    """Sans historique, les lignes B.I au-delà de l'id historique sont insérées et rattachées"""
    bi_ventes_table(code_maison="AF0001")
    bi_ventes_table(code_maison="", code_cosium="COS2")

    insert_ventes_cosium()

    ventes = {vente.code_cosium: vente for vente in VentesCosium.objects.all()}
    assert set(ventes) == {"COS1", "COS2"}
    vente = ventes["COS1"]
    assert vente.id_bi == HISTORIC_VENTES_ID + 1
    assert vente.sale_month == datetime.date(2026, 1, 1)
    assert vente.cct_uuid_identification == maison_chf
    # taux de change : 1/2 = 0.5 ; CA après remise 100 -> 50 €
    assert vente.taux_change_moyen == Decimal("0.5")
    assert vente.ca_ht_ap_remise_eur == Decimal(50)
    assert vente.px_vente_ttc_eur == Decimal(60)
    assert ventes["COS2"].cct_uuid_identification is None


def test_insert_ventes_cosium_reprend_apres_le_max(bi_ventes_table, make_vente):
    """Avec un historique, seules les lignes dont l'id dépasse le max importé sont reprises"""
    first = bi_ventes_table()
    second = bi_ventes_table(code_cosium="COS2")
    make_vente(id_bi=first, code_cosium="COS1")

    insert_ventes_cosium()

    assert sorted(VentesCosium.objects.values_list("id_bi", flat=True)) == [first, second]


def test_update_cct_from_bi(bi_ventes_table, make_vente):
    """Le code maison vide dans les ventes est repris depuis la B.I"""
    bi_id = bi_ventes_table(code_maison="AF0007")
    make_vente(id_bi=bi_id, code_maison="")

    with connection.cursor() as cursor:
        update_cct_from_bi(cursor)

    assert VentesCosium.objects.get(id_bi=bi_id).code_maison == "AF0007"


def test_set_cct_ventes(make_vente, make_maison):
    maison = make_maison("AF0003", code_maison="AF0003")
    vente = make_vente(code_maison="AF0003")
    autre = make_vente(code_maison="INCONNU")

    with connection.cursor() as cursor:
        set_cct_ventes(cursor)

    vente.refresh_from_db()
    autre.refresh_from_db()
    assert vente.cct_uuid_identification == maison
    assert autre.cct_uuid_identification is None


def test_mise_a_jour_ventes_cosium(bi_ventes_table, make_vente, maison_chf, caplog):
    """Les lignes B.I absentes des ventes sont ajoutées, les présentes sont ignorées"""
    present = bi_ventes_table()
    missing = bi_ventes_table(code_cosium="COS2")
    make_vente(id_bi=present, code_cosium="COS1", ca_ht_ap_remise=Decimal(7))

    with caplog.at_level("INFO", logger="import"):
        mise_a_jour_ventes_cosium()

    assert sorted(VentesCosium.objects.values_list("id_bi", flat=True)) == [present, missing]
    assert VentesCosium.objects.get(id_bi=present).ca_ht_ap_remise == Decimal(7)
    assert VentesCosium.objects.get(id_bi=missing).cct_uuid_identification == maison_chf


def test_update_exchange_rates(make_vente, maison_chf):
    vente = make_vente(
        cct_uuid_identification=maison_chf, ca_ht_ap_remise=Decimal(100), ca_ht_ap_remise_eur=None
    )
    hors_periode = make_vente(
        cct_uuid_identification=maison_chf,
        date_vente=datetime.date(2026, 2, 10),
        sale_month=datetime.date(2026, 2, 1),
        ca_ht_ap_remise_eur=None,
    )

    update_exchange_rates(*PERIOD)

    vente.refresh_from_db()
    hors_periode.refresh_from_db()
    assert vente.ca_ht_ap_remise_eur == Decimal(50)
    assert vente.pv_net_unitaire_eur == Decimal(50)
    assert hors_periode.ca_ht_ap_remise_eur is None


def test_force_update_sales(bi_ventes_table, make_vente, maison_chf):
    """Les ventes de la période sont remplacées par celles de la B.I, cct et taux recalculés"""
    bi_ventes_table(code_maison="AF0001", ca_ht_ap_remise=Decimal(300))
    make_vente(id_bi=5, code_cosium="ANCIENNE", ca_ht_ap_remise=Decimal(1))
    hors_periode = make_vente(date_vente=datetime.date(2025, 12, 5), code_cosium="DEC")

    force_update_sales(*PERIOD)

    codes = set(VentesCosium.objects.values_list("code_cosium", flat=True))
    assert codes == {"COS1", "DEC"}
    vente = VentesCosium.objects.get(code_cosium="COS1")
    assert vente.cct_uuid_identification == maison_chf
    assert vente.ca_ht_ap_remise_eur == Decimal(150)
    assert VentesCosium.objects.get(pk=hors_periode.pk).code_cosium == "DEC"


def test_module_main_guard():
    """Le bloc __main__ n'est pas exécuté à l'import"""
    assert import_ventes_cosium.__name__ == "apps.compta.imports.import_ventes_cosium"
