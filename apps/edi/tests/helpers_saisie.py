"""Aides partagées des tests de saisie manuelle (set_hand_invoices, vue create_hand_invoices)"""

import datetime
import uuid
from decimal import Decimal
from typing import Any

from apps.accountancy.models import VatRatSage


def make_vat_rate(
    make_vat, vat: str = "001", rate: str = "20", vat_regime: str = "FRA"
) -> VatRatSage:
    """Taux de TVA Sage applicable depuis 2014 (le tiers vat est créé s'il n'existe pas)"""
    return VatRatSage.objects.create(
        vat=make_vat(vat, vat_regime),
        vat_start_date=datetime.date(2014, 1, 1),
        rate=Decimal(rate),
        vat_regime=vat_regime,
        auuid=uuid.uuid4(),
        exoneration=False,
    )


def entete(**kwargs: Any) -> dict:
    """Entête de facture saisie (marchandises par défaut)"""
    data = {
        "third_party_num": "FOUR001",
        "invoice_number": "FA-001",
        "invoice_date": datetime.date(2026, 1, 15),
        "invoice_type": "380",
        "devise": "EUR",
        "sens": "2",
    }
    data.update(kwargs)
    return data


def ligne(maison, article, **kwargs: Any) -> dict:
    """Ligne de facture saisie, telle que nettoyée par data_dict_invoices_clean"""
    data = {
        "num": 1,
        "cct_uuid_identification": str(maison.uuid_identification),
        "reference_article": str(article.pk),
        "qty": "2",
        "net_unit_price": "10",
        "vat": "001",
        "libelle": "Monture",
        "client_name": "",
        "serial_number": "",
        "ean_code": "",
        "famille": "",
        "unit_weight": "1",
        "vat_amount": "",
        "amount_with_vat": "",
        "delivery_number": "",
        "delivery_date": "",
    }
    data.update(kwargs)
    return data
