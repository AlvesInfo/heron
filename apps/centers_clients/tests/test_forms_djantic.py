# pylint: disable=E0401,W0621
"""FR : Tests du schéma djantic des abonnements par maison


EN : Tests for subscriptions djantic schema

created at: 2026-10-10
created by: Paulo ALVES
"""

import datetime
import uuid
from decimal import Decimal

import pytest
from pydantic import ValidationError

from apps.centers_clients.forms.forms_djantic.forms_maison_subscription import (
    MaisonSubcriptionSchema,
)
from apps.centers_clients.models import MaisonSubcription

ARTICLE_UUID = "6fa459ea-ee8a-3ca4-894e-db77e160355e"


def test_config():
    """Le schéma cible MaisonSubcription et les colonnes du fichier d'import"""
    assert MaisonSubcriptionSchema.model_config["model"] is MaisonSubcription
    assert MaisonSubcriptionSchema.model_config["include"] == [
        *list(MaisonSubcription.get_columns_import()),
        "created_at",
        "modified_at",
    ]


def test_validation_complete():
    """Conversion des types : maison str, article uuid, unité int, décimaux"""
    validated = MaisonSubcriptionSchema(
        maison="AF0001",
        article=ARTICLE_UUID,
        qty="2",
        unit_weight="1",
        net_unit_price="99.90",
        function="ABONNEMENT",
        for_signboard="ACF",
        vat="001",
    ).dict()

    assert validated["maison"] == "AF0001"
    assert validated["article"] == uuid.UUID(ARTICLE_UUID)
    assert validated["unit_weight"] == 1
    assert validated["qty"] == Decimal(2)
    assert validated["net_unit_price"] == Decimal("99.90")
    assert validated["vat"] == "001"
    assert isinstance(validated["created_at"], datetime.datetime)


def test_vat_optionnelle():
    """La tva est facultative et reste du texte (FK vers VatSage.vat, pas la clé entière)"""
    assert (
        MaisonSubcriptionSchema(
            maison="AF0001", article=ARTICLE_UUID, unit_weight=1, function="F", for_signboard="ACF"
        ).vat
        is None
    )


def test_erreurs():
    """Article non uuid, unité non entière et champs manquants"""
    with pytest.raises(ValidationError) as excinfo:
        MaisonSubcriptionSchema(maison="AF0001", article="pas-un-uuid", unit_weight="x")

    assert {error["loc"][0] for error in excinfo.value.errors()} == {
        "article",
        "unit_weight",
        "function",
        "for_signboard",
    }
