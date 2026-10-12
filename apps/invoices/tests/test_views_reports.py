"""Tests des vues d'export des achats (reports_eric, reports_views) et des essais d'envoi"""
import datetime
import logging

import pytest
from django.test import RequestFactory
from django.urls import NoReverseMatch, reverse

from apps.invoices.views import essais_views, reports_eric, reports_views
from conftest import patched_attrs

pytestmark = pytest.mark.django_db


def fake_get_achats(file_io, file_name, dte_d, dte_f):
    file_io.write(f"{file_name};{dte_d.date()};{dte_f.date()}".encode())


def test_valid_export_achats(logged_client):
    assert logged_client.get(reverse("invoices:valid_export_achats")).status_code == 200
    assert logged_client.post(reverse("invoices:valid_export_achats")).url == reverse("invoices:export_achats")


def test_export_achats(logged_client, make_edi_validation, monkeypatch):
    make_edi_validation(billing_period=datetime.date(2026, 1, 1), final=True)
    with patched_attrs(monkeypatch, reports_eric, get_achats=fake_get_achats):
        response = logged_client.get(reverse("invoices:export_achats"))

    assert "ACHATS_HERON_PERIOD_2026_1_1_TO_2026_1_31" in response["Content-Disposition"]
    assert b"2026-01-01;2026-01-31" in response.content


def test_export_achats_sans_periode_finalisee(logged_client, caplog):
    """Sans période finalisée, retour à l'écran de lancement (plus de boucle de redirection)"""
    with caplog.at_level(logging.ERROR):
        response = logged_client.get(reverse("invoices:export_achats"))

    assert response.url == reverse("invoices:valid_export_achats")
    assert "export_achats" in caplog.text


def test_finalize_purchases_export(make_user, make_edi_validation, monkeypatch, caplog):
    user = make_user()
    factory = RequestFactory()

    request = factory.get("/")
    request.user = user
    assert reports_views.finalize_purchases_export(request).status_code == 200

    make_edi_validation(billing_period=datetime.date(2026, 3, 1), final=True)
    request = factory.post("/")
    request.user = user
    with patched_attrs(monkeypatch, reports_views, get_achats=fake_get_achats):
        response = reports_views.finalize_purchases_export(request)

    assert "2026_3_1_TO_2026_3_31" in response["Content-Disposition"]

    def boom(*args, **kwargs):
        raise RuntimeError("boom")

    with patched_attrs(monkeypatch, reports_views, response_file=boom), caplog.at_level(logging.ERROR):
        response = reports_views.finalize_purchases_export(request)

    assert response.status_code == 200
    assert "finalize_purchases_export" in caplog.text


def test_send_email_essais_non_routee():
    """La vue d'essai n'est plus exposée par l'URLconf"""
    with pytest.raises(NoReverseMatch):
        reverse("invoices:send_email_essais")


def test_send_email_essais(make_user, monkeypatch):
    """Vue d'essai conservée mais non routée : appel direct"""
    calls = []
    request = RequestFactory().get("/essais/")
    request.user = make_user()

    with patched_attrs(monkeypatch, essais_views, launch_celery_send_emails_essais=lambda user_pk: calls.append(user_pk)):
        response = essais_views.send_email_essais(request)

    assert response.url == reverse("invoices:send_email_pdf_invoice")
    assert calls == [str(request.user.pk)]
