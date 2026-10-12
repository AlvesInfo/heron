"""Tests des changements de cct et de grande catégorie par double-clic"""

import logging
import uuid

import pytest
from django.urls import reverse

from apps.edi.models import EdiImport
from apps.validation_purchases.tests.helpers_views import messages_of

pytestmark = pytest.mark.django_db


def test_cct_change(ajax_client, integration_data, make_maison):
    lyon = make_maison("AF0002")
    row = integration_data.rows[0]
    data = {
        "cct": "AF0002",
        "uuid_identification": str(row.uuid_identification),
        "third_party_num": "FOUR001",
        "invoice_number": "F001",
        "invoice_year": 2026,
    }

    response = ajax_client.post(reverse("validation_purchases:cct_change"), {**data, "id": 0})

    assert response.json() == {"success": "success"}
    row.refresh_from_db()
    assert row.cct_uuid_identification == lyon
    assert row.is_multi_store is False
    assert any("nouveau CCT" in message for message in messages_of(response))
    assert ajax_client.session["level"] == 20

    # même cct : rien à changer
    response = ajax_client.post(reverse("validation_purchases:cct_change"), data)
    assert response.json() == {"success": "success"}
    assert "Vous n'avez rien modifié !" in messages_of(response)


def test_cct_change_avec_id(ajax_client, integration_data, make_maison):
    make_maison("AF0003")
    row = integration_data.rows[1]

    response = ajax_client.post(
        reverse("validation_purchases:cct_change"),
        {
            "cct": "AF0003",
            "uuid_identification": str(row.uuid_identification),
            "third_party_num": "FOUR001",
            "invoice_number": "F002",
            "invoice_year": 2026,
            "id": row.pk,
        },
    )

    assert response.json() == {"success": "success"}
    row.refresh_from_db()
    assert row.cct_uuid_identification.cct.cct == "AF0003"


def test_cct_change_formulaire_invalide(ajax_client, caplog):
    with caplog.at_level(logging.ERROR, logger="error_views"):
        response = ajax_client.post(reverse("validation_purchases:cct_change"), {"cct": "AF0001"})

    assert response.json() == {"success": "ko"}
    assert messages_of(response)[0].startswith("Une erreur c'est produite")
    assert "cct_change, form invalid" in caplog.text


def test_big_category_change(ajax_client, integration_data, make_big_category):
    category = make_big_category("Formation")
    data = {
        "big_category": str(category.uuid_identification),
        "big_category_default": str(category.uuid_identification),
        "uuid_origin": str(uuid.uuid4()),
        "third_party_num": "FOUR001",
        "invoice_month": "2026-01-01",
    }

    response = ajax_client.post(reverse("validation_purchases:big_category_change"), data)

    assert response.json() == {"success": "success"}
    assert set(EdiImport.objects.values_list("big_category", flat=True)) == {
        category.uuid_identification
    }
    assert any("nouvelle catégorie : Formation" in message for message in messages_of(response))

    response = ajax_client.post(
        reverse("validation_purchases:big_category_change"),
        {**data, "id": integration_data.rows[0].pk},
    )
    assert "Vous n'avez rien modifié !" in messages_of(response)


def test_big_category_change_formulaire_invalide(ajax_client, caplog):
    with caplog.at_level(logging.ERROR, logger="error_views"):
        response = ajax_client.post(
            reverse("validation_purchases:big_category_change"), {"third_party_num": "FOUR001"}
        )

    assert response.json() == {"success": "ko"}
    assert "big_category_change, form invalid" in caplog.text
