"""Tests des aides de rétrécissement de type (apps/core/bin/typing_helpers.py)."""

import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory

from apps.core.bin.typing_helpers import current_user, required


def test_required_renvoie_la_valeur():
    """Une valeur présente est renvoyée telle quelle"""
    assert required(0) == 0
    assert required("x", "libellé") == "x"


def test_required_refuse_none():
    """None lève une ValueError portant le libellé"""
    with pytest.raises(ValueError, match="période absente"):
        required(None, "période")


@pytest.mark.django_db
def test_current_user_authentifie(make_user):
    """L'utilisateur authentifié de la requête est renvoyé"""
    user = make_user()
    request = RequestFactory().get("/")
    request.user = user

    assert current_user(request) is user


def test_current_user_anonyme():
    """Un utilisateur anonyme est refusé"""
    request = RequestFactory().get("/")
    request.user = AnonymousUser()

    with pytest.raises(PermissionDenied):
        current_user(request)
