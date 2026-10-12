"""Fixtures et aides communes aux tests des post-traitements de l'app edi (chantier B).


Importées explicitement par les modules de tests : `from apps.edi.tests.helpers_post import *`
"""

import datetime
from collections.abc import Callable
from decimal import Decimal
from typing import Any
from uuid import uuid4

import pytest
from django.db import connection

from conftest import next_code

# Fonction PostgreSQL maison utilisée par sql_interson (absente du schéma Django : définie à la main
# en production). Recréée dans la transaction de test.
IS_DATE_FUNCTION = """
create or replace function is_date(value text) returns boolean
language plpgsql immutable as $$
begin
    if value !~ '^\\d{2}/\\d{2}/\\d{4}$' then
        return false;
    end if;
    perform to_date(value, 'DD/MM/YYYY');
    return true;
exception when others then
    return false;
end;
$$
"""


@pytest.fixture
def pg_is_date(db) -> None:  # pylint: disable=W0613
    """Crée la fonction is_date(text) utilisée par les SQL Interson"""
    with connection.cursor() as cursor:
        cursor.execute(IS_DATE_FUNCTION)


@pytest.fixture
def icon_origins(make_icon_origin) -> None:
    """Origines 1 (import), 2 (sage), 3 (B.I), 4 (saisie) référencées par les SQL"""
    for origin, name in [(1, "Import"), (2, "Sage"), (3, "B.I"), (4, "Saisie")]:
        make_icon_origin(origin, name, "icon")


@pytest.fixture
def make_vat_rat(make_vat) -> Callable[..., Any]:
    """Fabrique de VatRatSage (taux à une date de début)"""
    from apps.accountancy.models import VatRatSage  # pylint: disable=C0415

    def _factory(
        vat: str = "001",
        rate: Decimal | str = Decimal(20),
        vat_start_date: datetime.date = datetime.date(2014, 1, 1),
        vat_regime: str = "FRA",
        **kwargs: Any,
    ):
        defaults = {"auuid": uuid4(), "exoneration": False}
        defaults.update(kwargs)
        return VatRatSage.objects.create(
            vat=make_vat(vat, vat_regime),
            vat_start_date=vat_start_date,
            rate=Decimal(str(rate)),
            vat_regime=vat_regime,
            **defaults,
        )

    return _factory


UNITS = {1: "U", 4: "H", 7: "PERS", 9: "FORM", 11: "P"}


@pytest.fixture
def units(make_unit) -> None:
    """Unités référencées par les SQL (1 pièce par défaut, 11 cosium/réceptions, 4 interson...)"""
    for num, unity in UNITS.items():
        make_unit(num, unity)


@pytest.fixture
def edi_batch(make_edi_import, units) -> Callable[..., Any]:  # pylint: disable=W0613
    """Crée des lignes edi_ediimport non validées (valid=False) partageant un même

    uuid_identification (un fichier importé) : `uuid, rows = edi_batch([{...}, {...}], flow_name=...)`
    """

    def _factory(lines: list[dict[str, Any]], **common: Any):
        uuid_identification = common.pop("uuid_identification", uuid4())
        common.setdefault("valid", False)
        rows = []

        for line in lines:
            values = {**common, **line}
            values.setdefault("uuid_identification", uuid_identification)
            rows.append(make_edi_import(**values))

        return uuid_identification, rows

    return _factory


def refresh(*rows):
    """Recharge des instances depuis la base et les renvoie"""
    for row in rows:
        row.refresh_from_db()

    return rows if len(rows) > 1 else rows[0]


def edi_values(uuid_identification, *fields: str) -> list[tuple]:
    """Valeurs (ordonnées par id) des lignes d'un import"""
    from apps.edi.models import EdiImport  # pylint: disable=C0415

    return list(
        EdiImport.objects.filter(uuid_identification=uuid_identification)
        .order_by("id")
        .values_list(*fields)
    )


def new_invoice() -> str:
    """Numéro de facture unique"""
    return next_code("FAC")
