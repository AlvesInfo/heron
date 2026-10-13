"""Tests des modules d'essai de validation (form django, djantic, serializers DRF)"""

import datetime
from decimal import Decimal

import pytest

from apps.edi.models import EdiImport
from apps.edi.validations import (
    validation_by_django_form,
    validation_by_pydantic,
)

DECIMAL_FIELDS = [
    "qte_emballage",
    "px_unitaire_brut",
    "px_unitaire_net",
    "emballage",
    "port",
    "montant_brut",
    "montant_remise_1",
    "montant_remise_2",
    "montant_remise_3",
    "montant_tva",
    "montant_ttc",
    "invoice_amount_without_tax",
    "invoice_amount_tax",
    "invoice_amount_with_tax",
]


@pytest.mark.usefixtures("db")
def test_edi_form_fields_and_cleaning():
    form = validation_by_django_form.EdiForm(
        {
            **dict.fromkeys(DECIMAL_FIELDS, "0"),
            "invoice_date": "2026-01-15",
            "date_commande_acuitis": "2026-01-02",
            "date_bl": "2026-01-03",
            "date_facture": "2026-01-04",
            "supplier": "Fournisseur~~Code",
            "qte": "1,5",
            "montant_net": "1.234,56",
            "taux_tva": "0",
        }
    )

    assert form.is_valid() is False  # champs texte obligatoires du modèle non renseignés
    assert form.cleaned_data["date_facture"] == datetime.date(2026, 1, 4)
    assert form.cleaned_data["qte"] == Decimal("1.5")
    assert form.cleaned_data["montant_net"] == Decimal("1234.56")
    assert form.cleaned_data["taux_tva"] == 0
    assert form.cleaned_data["supplier"] == "Fournisseur~~Code"  # pas de max_length : non tronqué
    assert "pk" not in form.fields
    assert form.Meta.model is EdiImport


def test_edi_import_schema_covers_model_fields():
    schema = validation_by_pydantic.EdiImportSchema

    assert schema.model_config["model"] is EdiImport
    assert "invoice_number" in schema.__fields__
    assert "uuid_identification" in schema.__fields__
