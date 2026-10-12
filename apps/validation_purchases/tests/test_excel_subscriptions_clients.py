# pylint: disable=E0401,W0621,W0611
"""Tests des exports Excel 3.5 abonnements et 3.3 nouveaux clients"""

import datetime
import logging
from decimal import Decimal

import pytest

from apps.validation_purchases.excel_outputs import (
    excel_clients_news as clients_module,
    excel_subscriptions as subscriptions_module,
)
from apps.validation_purchases.tests.helpers_excel import KO, cells, month_ago, run_export

pytestmark = pytest.mark.django_db


# 3.5 ABONNEMENTS ==================================================================================
def test_subscriptions(make_edi_row, make_maison, make_subscription, make_sale_rows, excel_io):
    """Deux abonnements, une maison fermée facturée (cellules rouges), un historique facturé"""
    paris = make_maison("AF0001", code_maison="AF0001")
    fermee = make_maison("AF0002", code_maison="AF0002", closing_date=datetime.date(2025, 12, 31))
    make_subscription(paris, "ROYALTIES")
    make_subscription(paris, "PUBLICITE")
    make_edi_row(
        "ZROYAL",
        maison=paris,
        flow_name="ROYALTIES",
        reference_article="ROY",
        sale_invoice=True,
        purchase_invoice=False,
        net_amount=Decimal(100),
    )
    make_edi_row(
        "ZROYAL",
        maison=fermee,
        flow_name="ROYALTIES",
        reference_article="ROY",
        sale_invoice=True,
        purchase_invoice=False,
        net_amount=Decimal(20),
    )
    make_edi_row(
        "ZPUB",
        maison=paris,
        flow_name="PUBLICITE",
        reference_article="PUB",
        sale_invoice=True,
        purchase_invoice=False,
        net_amount=Decimal(50),
    )
    make_edi_row(
        "ZPUB",
        maison=paris,
        flow_name="PUBLICITE",
        reference_article="PUB",
        sale_invoice=True,
        purchase_invoice=False,
        net_amount=Decimal(0),
    )
    make_sale_rows(
        cct="AF0001", third_party_num="ZROYAL", invoice_month=month_ago(2), net_amount=Decimal(30)
    )
    make_sale_rows(
        cct="AF0001", third_party_num="ZROYAL", invoice_month=month_ago(7), net_amount=Decimal(7)
    )

    result, file_io = run_export(subscriptions_module.excel_subscriptions, "ABONNEMENTS.xlsx")

    assert "OK" in result
    rows = excel_io(file_io)
    assert rows[0][0] == "3.5 - Contrôle des Abonnements"
    assert cells(rows, "ZROYAL - ROYALTIES - ROY")
    assert cells(rows, "ZPUB - PUBLICITE - PUB")
    royal_paris = next(
        row
        for row in rows
        if row[0] == "ZROYAL - ROYALTIES - ROY" and row[1] == "AF0001 - Maison AF0001"
    )
    assert royal_paris[15] == 100  # M en cours (edi)
    assert royal_paris[14] == 30  # M-1 facturé
    assert royal_paris[9] == 7  # M-6 facturé, hors des 6 derniers mois
    assert royal_paris[16] == 130  # 6 derniers mois
    fermee_row = next(
        row
        for row in rows
        if row[0] == "ZROYAL - ROYALTIES - ROY" and row[1] == "AF0002 - Maison AF0002"
    )
    assert fermee_row[15] == 20
    assert isinstance(fermee_row[3], datetime.datetime)
    pub_fermee = next(
        row
        for row in rows
        if row[0] == "ZPUB - PUBLICITE - PUB" and row[1] == "AF0002 - Maison AF0002"
    )
    assert pub_fermee[15] in (None, "")  # maison sans publicité : ligne vide du produit cartésien


def test_subscriptions_sans_abonnement(excel_io):
    result, file_io = run_export(subscriptions_module.excel_subscriptions, "ABONNEMENTS.xlsx")

    assert "OK" in result
    assert len(excel_io(file_io)) <= 3


def test_subscriptions_erreur(ko_writer, caplog):
    ko_writer(subscriptions_module)

    with caplog.at_level(logging.ERROR):
        result, _ = run_export(subscriptions_module.excel_subscriptions, "ABONNEMENTS.xlsx")

    assert result == KO


# 3.3 NOUVEAUX CLIENTS =============================================================================
def test_clients_news(make_edi_row, make_maison, make_purchase_invoice, excel_io):
    recent = make_maison("AF0001", opening_date=month_ago(2))
    autre = make_maison("AF0002", opening_date=month_ago(4))
    make_maison("AF0003", opening_date=datetime.date(2015, 1, 1))  # ancienne : exclue
    make_edi_row(maison=recent, net_amount=Decimal(100))
    make_edi_row(
        third_party_num="FOUR002", maison=recent, net_amount=Decimal(3)
    )  # 2e tiers, même maison
    make_edi_row(third_party_num="FOUR002", maison=autre, net_amount=Decimal(10))
    make_purchase_invoice(integration_month=month_ago(2), net_amount=Decimal(40), cct="AF0001")
    make_purchase_invoice(integration_month=month_ago(5), net_amount=Decimal(5), cct="AF0001")

    result, file_io = run_export(clients_module.excel_clients_news, "CLIENTS.xlsx")

    assert "OK" in result
    rows = excel_io(file_io)
    assert rows[0][0] == "3.3 - Contrôle des nouveaux clients"
    assert cells(rows, "AF0001 - Maison AF0001")
    assert cells(rows, "AF0002 - Maison AF0002")
    assert not cells(rows, "AF0003 - Maison AF0003")
    assert any(str(cell).startswith("Ouverture le : ") for row in rows for cell in row if cell)
    four = next(
        row for row in rows if row[0] == "AF0001 - Maison AF0001" and row[1] == "FOUR001 - FOUR001"
    )
    assert four[7] == 100
    assert four[6] == 40
    assert four[3] == 5
    assert four[8] == 145


def test_clients_news_erreur(ko_writer, caplog):
    ko_writer(clients_module)

    with caplog.at_level(logging.ERROR):
        result, _ = run_export(clients_module.excel_clients_news, "CLIENTS.xlsx")

    assert result == KO
