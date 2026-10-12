# pylint: disable=W0621,E0401,R0913,R0914
"""
FR : conftest de l'app rfa - fabriques du paramétrage RFA et jeu de données de génération
EN : rfa app conftest

Commentaire:

Les fabriques génériques (make_society, make_maison, make_signboard, make_section, make_vat,
make_edi_import, make_edi_import_control, make_edi_validation, make_user, logged_client,
ajax_client, ...) viennent du conftest racine.

created at: 2026-10-12
created by: Paulo ALVES
"""
import datetime
from uuid import uuid4
from decimal import Decimal
from typing import Any
from collections.abc import Callable

import pytest

from apps.rfa.models import (
    ClientExclusion,
    ClientSupplierExclusion,
    SectionProExclusion,
    SectionRfa,
    SignboardExclusion,
    SupplierRate,
)

RFA_PERIOD = "2026RFA_01"
BILLING_PERIOD = datetime.date(2026, 1, 1)


@pytest.fixture
def make_signboard_exclusion(make_signboard) -> Callable[..., SignboardExclusion]:
    """Fabrique d'exclusions RFA par enseigne"""

    def _factory(code: str = "ACF") -> SignboardExclusion:
        return SignboardExclusion.objects.get_or_create(signboard=make_signboard(code))[0]

    return _factory


@pytest.fixture
def make_client_exclusion(make_maison) -> Callable[..., ClientExclusion]:
    """Fabrique d'exclusions RFA par maison (cct)"""

    def _factory(maison=None) -> ClientExclusion:
        return ClientExclusion.objects.get_or_create(cct=maison or make_maison(type_x3=1))[0]

    return _factory


@pytest.fixture
def make_client_supplier_exclusion(make_maison, make_society) -> Callable[..., ClientSupplierExclusion]:
    """Fabrique d'exclusions RFA par couple maison / fournisseur"""

    def _factory(maison=None, third_party_num: str = "FOUR001") -> ClientSupplierExclusion:
        return ClientSupplierExclusion.objects.get_or_create(
            maison=maison or make_maison(type_x3=1), supplier=make_society(third_party_num, is_client=False)
        )[0]

    return _factory


@pytest.fixture
def make_supplier_rate(make_society) -> Callable[..., SupplierRate]:
    """Fabrique de taux de RFA par fournisseur"""

    def _factory(third_party_num: str = "FOUR001", rate: str = "0.05", **kwargs: Any) -> SupplierRate:
        return SupplierRate.objects.get_or_create(
            supplier=make_society(third_party_num, is_client=False, **kwargs), defaults={"rfa_rate": Decimal(rate)}
        )[0]

    return _factory


@pytest.fixture
def make_section_rfa(make_section) -> Callable[..., SectionRfa]:
    """Fabrique de sections de l'axe RFA retenues pour le calcul"""

    def _factory(section: str = RFA_PERIOD) -> SectionRfa:
        return SectionRfa.objects.get_or_create(axe_rfa=make_section("RFA", section))[0]

    return _factory


@pytest.fixture
def make_section_pro_exclusion(make_section) -> Callable[..., SectionProExclusion]:
    """Fabrique d'exclusions RFA par section de l'axe PRO"""

    def _factory(section: str = "AUD") -> SectionProExclusion:
        return SectionProExclusion.objects.get_or_create(axe_pro=make_section("PRO", section))[0]

    return _factory


@pytest.fixture
def rfa_data(
    make_maison, make_section, make_section_rfa, make_supplier_rate, make_edi_import, make_edi_import_control,
    make_edi_validation, make_vat, make_unit,
):
    """Jeu de données complet pour une génération de RFA :
    fournisseur FOUR001 à 5 %, maison AF0001 (enseigne ACF), deux factures validées de janvier 2026
    sur l'axe RFA retenu, TVA 002 à 5,5 %, période de facturation ouverte.
    """
    from apps.accountancy.models import VatRatSage  # pylint: disable=C0415

    maison = make_maison("AF0001", type_x3=1)
    axe_pro = make_section("PRO", "OPT")
    section_rfa = make_section_rfa(RFA_PERIOD)
    rate = make_supplier_rate(
        "FOUR001", "0.05", name="FOURN UN", short_name="FOURN UN", centers_suppliers_indentifier="F1|F2"
    )
    # Unité de poids 11 posée en dur par l'insertion des RFA (comme par les flux Cosium / BBGR)
    make_unit(11, "Forfait")
    control = make_edi_import_control(valid=True)
    common = {
        "cct_uuid_identification": maison,
        "code_signboard": "ACF",
        "axe_pro": axe_pro,
        "axe_rfa": section_rfa.axe_rfa,
        "uuid_control": control,
        "flow_name": "Widex",
        "invoice_date": datetime.date(2026, 1, 15),
    }
    lines = [
        make_edi_import("FOUR001", "ART-1", invoice_number="FAC-1", net_amount=Decimal("100"), gross_amount=Decimal("110"), gross_unit_price=Decimal("110"), **common),
        make_edi_import("FOUR001", "ART-2", invoice_number="FAC-1", net_amount=Decimal("50"), gross_amount=Decimal("55"), gross_unit_price=Decimal("55"), **common),
    ]
    vat = make_vat("002")
    VatRatSage.objects.get_or_create(
        vat=vat, vat_start_date=datetime.date(2024, 1, 1), defaults={"rate": Decimal("5.5"), "auuid": uuid4()}
    )
    validation = make_edi_validation(BILLING_PERIOD)
    return {
        "maison": maison, "axe_pro": axe_pro, "section_rfa": section_rfa, "rate": rate,
        "control": control, "lines": lines, "validation": validation,
    }
