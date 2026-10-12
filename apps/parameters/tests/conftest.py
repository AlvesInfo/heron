# pylint: disable=W0621,E0401,R0913
"""FR : conftest de l'app parameters - fabriques du référentiel de paramétrage


EN : parameters app conftest - settings referential factories

Commentaire:

Les fabriques génériques (make_big_category, make_sub_category, make_nature, make_unit,
make_invoice_function, make_default_axes, make_sale_price_category, make_section, make_maison,
make_country, make_country_currency, make_user, logged_client, ajax_client, ...) viennent du
conftest racine. Ici : compteurs, contrôles de refacturation, emails types, taux de change,
ventes Cosium minimales.

created at: 2026-10-11
created by: Paulo ALVES
"""

import datetime
from collections.abc import Callable
from decimal import Decimal
from typing import Any

import pytest

from apps.parameters.models import ControlRebilling, Counter, CounterNums, Email, ExchangeRate


@pytest.fixture
def make_counter(db) -> Callable[..., Counter]:  # pylint: disable=W0613
    """Fabrique de compteurs (avec leur numéro courant initialisé)"""

    def _factory(name: str = "generic", num: int = 1, **kwargs: Any) -> Counter:
        defaults = {"lpad_num": 5, "separateur": ""}
        defaults.update(kwargs)
        counter, _ = Counter.objects.get_or_create(name=name, defaults=defaults)
        CounterNums.objects.get_or_create(counter=counter, defaults={"num": num})
        return counter

    return _factory


@pytest.fixture
def make_control(db) -> Callable[..., ControlRebilling]:  # pylint: disable=W0613
    """Fabrique de contrôles de refacturation"""

    def _factory(name: str = "Fournisseur à contrôler", **kwargs: Any) -> ControlRebilling:
        return ControlRebilling.objects.get_or_create(name=name, defaults=kwargs)[0]

    return _factory


@pytest.fixture
def make_email(db) -> Callable[..., Email]:  # pylint: disable=W0613
    """Fabrique d'emails types (factures par défaut)"""

    def _factory(name: int = 0, **kwargs: Any) -> Email:
        defaults = {
            "description": "Envoi des factures",
            "subject": "Vos factures",
            "email_body": "<p>Bonjour</p>",
        }
        defaults.update(kwargs)
        return Email.objects.get_or_create(name=name, defaults=defaults)[0]

    return _factory


@pytest.fixture
def make_exchange_rate(make_country_currency) -> Callable[..., ExchangeRate]:
    """Fabrique de taux de change mensuels (base EUR)"""

    def _factory(
        currency: str = "CHF",
        rate_month: datetime.date = datetime.date(2026, 1, 1),
        rate: str = "1",
        **kwargs: Any,
    ) -> ExchangeRate:
        return ExchangeRate.objects.create(
            currency_change=make_country_currency(currency, currency),
            rate_month=rate_month,
            rate=Decimal(rate),
            **kwargs,
        )

    return _factory


@pytest.fixture
def make_vente(make_maison) -> Callable[..., Any]:
    """Fabrique de ventes Cosium minimales rattachées à une maison"""
    from apps.compta.models import VentesCosium  # pylint: disable=C0415

    counter = {"id": 0}

    def _factory(maison=None, sale_month: datetime.date = datetime.date(2026, 1, 1), **kwargs: Any):
        counter["id"] += 1
        defaults = {
            "id_bi": counter["id"],
            "code_ean": "3660000000001",
            "date_vente": sale_month.replace(day=15),
            "sale_month": sale_month,
            "ca_ht_ap_remise": Decimal(100),
            "ca_ht_avt_remise": Decimal(110),
            "pv_brut_unitaire": Decimal(110),
            "pv_net_unitaire": Decimal(100),
            "px_vente_ttc_devise": Decimal(120),
            "px_vente_ttc_devise_apres_remise": Decimal(120),
        }
        defaults.update(kwargs)
        return VentesCosium.objects.create(
            cct_uuid_identification=maison or make_maison(), **defaults
        )

    return _factory
