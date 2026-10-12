# pylint: disable=E0401,W0621
"""FR : Tests des vues racine de heron (accueil, réactivation de compte, déconnexion par email),


     du middleware de connexion, des écrans de réinitialisation de mot de passe et de l'URLconf
EN : Tests for heron root views, login middleware, password reset screens and URLconf

created at: 2026-10-12
created by: Paulo ALVES
"""

import importlib

import pytest
from django.conf import settings as django_settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core import mail
from django.test import Client
from django.urls import clear_url_caches, reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from heron import urls as heron_urls
from heron.views import users_views

pytestmark = pytest.mark.django_db


def _uid_token(user):
    return urlsafe_base64_encode(force_bytes(user.pk)), PasswordResetTokenGenerator().make_token(
        user
    )


# VUES =============================================================================================


def test_accueil(logged_client):
    response = logged_client.get(reverse("home"))

    assert response.status_code == 200
    assert response.context["environnement"] == django_settings.ENVIRONNEMENT
    assert "heron/home.html" in [template.name for template in response.templates]


def test_deconnexion_par_email_accessible_sans_connexion(client):
    response = client.get(reverse("logout_email"))

    assert response.status_code == 200
    assert "heron/logout_email.html" in [template.name for template in response.templates]


def test_reactivation_du_compte(client, make_user, monkeypatch):
    """Lien valide : les tentatives de connexion (axes) sont remises à zéro et le compte réactivé"""
    resets, logs = [], []
    monkeypatch.setattr(users_views, "reset", lambda username: resets.append(username))
    # le logger "connexion" ne propage pas vers la racine : on capture ses appels directement
    monkeypatch.setattr(
        users_views.logger, "info", lambda message, *args: logs.append(message % args)
    )
    user = make_user()
    uidb64, token = _uid_token(user)

    response = client.get(reverse("reactivate", kwargs={"uidb64": uidb64, "token": token}))

    assert response.status_code == 200
    assert "heron/account_reactivate_done.html" in [
        template.name for template in response.templates
    ]
    assert response.context["user"] == user
    assert resets == [user.email]
    assert logs == [f"Réactivation : mail : {user.email} - ip : 127.0.0.1"]


@pytest.mark.parametrize("case", ["mauvais_jeton", "uid_illisible", "utilisateur_inconnu"])
def test_reactivation_invalide(client, make_user, monkeypatch, case):
    monkeypatch.setattr(
        users_views, "reset", lambda _username: pytest.fail("reset ne doit pas être appelé")
    )
    user = make_user()
    uidb64, token = _uid_token(user)

    if case == "mauvais_jeton":
        token = "abc-def"
    elif case == "uid_illisible":
        uidb64 = "zz"
    else:
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk + 1000))

    response = client.get(reverse("reactivate", kwargs={"uidb64": uidb64, "token": token}))

    assert response.status_code == 200
    assert "heron/account_reactivate_invalid.html" in [
        template.name for template in response.templates
    ]


# MIDDLEWARE DE CONNEXION ==========================================================================


def test_middleware_redirige_les_anonymes_vers_la_connexion(client):
    for url in (reverse("home"), reverse("parameters:categories_list")):
        response = client.get(url)

        assert response.status_code == 302
        assert response.url == reverse("accounts:login")


@pytest.mark.parametrize(
    "route",
    [
        "accounts:login",
        "logout_email",
        "password_reset",
        "password_reset_done",
        "password_reset_complete",
    ],
)
def test_middleware_laisse_passer_les_pages_publiques(client, route):
    assert client.get(reverse(route)).status_code == 200


def test_middleware_laisse_passer_les_liens_de_reinitialisation(client, make_user):
    """Les liens reçus par email (reactivate, password-reset-confirm) sont accessibles déconnecté"""
    uidb64, token = _uid_token(make_user())

    reactivate = client.get(reverse("reactivate", kwargs={"uidb64": uidb64, "token": token}))
    confirm = client.get(
        reverse("password_reset_confirm", kwargs={"uidb64": uidb64, "token": "jeton-faux"})
    )

    assert reactivate.status_code == 200
    assert confirm.status_code == 200
    assert confirm.context["validlink"] is False


# RÉINITIALISATION DU MOT DE PASSE ================================================================


def test_parcours_de_reinitialisation_du_mot_de_passe(client, make_user):
    """Demande par email, lien de confirmation, nouveau mot de passe, écran de fin"""
    user = make_user(password="AncienMotDePasse!1")

    asked = client.post(reverse("password_reset"), {"email": user.email})
    assert asked.status_code == 302
    assert asked.url == reverse("password_reset_done")
    assert len(mail.outbox) == 1
    assert user.email in mail.outbox[0].to
    assert "reactivate" not in mail.outbox[0].body
    assert "password-reset-confirm" in mail.outbox[0].body

    uidb64, token = _uid_token(user)
    confirm = client.get(
        reverse("password_reset_confirm", kwargs={"uidb64": uidb64, "token": token})
    )
    assert confirm.status_code == 302
    set_password_url = confirm.url
    assert set_password_url.endswith("/set-password/")

    form_page = client.get(set_password_url)
    assert form_page.status_code == 200
    assert form_page.context["validlink"] is True

    changed = client.post(
        set_password_url,
        {"new_password1": "NouveauMotDePasse!1", "new_password2": "NouveauMotDePasse!1"},
    )
    assert changed.status_code == 302
    assert changed.url == reverse("password_reset_complete")

    user.refresh_from_db()
    assert user.check_password("NouveauMotDePasse!1")
    assert Client().get(reverse("password_reset_complete")).status_code == 200


# URLCONF ==========================================================================================


def test_espaces_de_noms_des_applications():
    expected = {
        "articles",
        "book",
        "centers_clients",
        "compta",
        "centers_purchasing",
        "core",
        "countries",
        "edi",
        "groups",
        "import_files",
        "parameters",
        "periods",
        "permissions",
        "invoices",
        "traces",
        "users",
        "accounts",
        "validation_purchases",
        "validation_sales",
        "data_flux",
        "rfa",
    }
    namespaces = {
        pattern.namespace
        for pattern in heron_urls.urlpatterns
        if getattr(pattern, "namespace", None)
    }

    assert expected <= namespaces
    assert reverse("home") == "/"
    assert reverse("admin:index") == "/back-heron-plateforme/"


def test_urlconf_en_mode_debug_ajoute_la_barre_de_debug(settings):
    """Avec DEBUG, les routes de django-debug-toolbar sont ajoutées ; l'URLconf est rechargée"""
    settings.DEBUG = True

    try:
        reloaded = importlib.reload(heron_urls)
        debug_routes = [
            pattern for pattern in reloaded.urlpatterns if "__debug__" in str(pattern.pattern)
        ]
        assert len(debug_routes) == 1
    finally:
        settings.DEBUG = False
        importlib.reload(heron_urls)
        clear_url_caches()

    assert not [
        pattern for pattern in heron_urls.urlpatterns if "__debug__" in str(pattern.pattern)
    ]
