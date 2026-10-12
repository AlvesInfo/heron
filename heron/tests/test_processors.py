# pylint: disable=E0401,W0621
"""FR : Tests des processeurs de contexte de heron (titre, groupes, centrales filles, dates, site)


EN : Tests for heron context processors

created at: 2026-10-12
created by: Paulo ALVES
"""

import datetime

import pytest
from django.contrib.auth.models import AnonymousUser, Group
from django.contrib.sites.models import Site
from django.test import RequestFactory

from apps.users.models import AuthGroupName
from heron import processors

pytestmark = pytest.mark.django_db


@pytest.fixture
def request_for():
    """Requête GET portée par un utilisateur (ou anonyme si None)"""

    def _factory(user=None):
        request = RequestFactory().get("/")
        request.user = user or AnonymousUser()
        return request

    return _factory


@pytest.fixture
def groupes():
    """Groupes Django nommés (Admin exclu des menus) ; les tests appelants sont marqués django_db"""
    names = {}

    for name, label in (
        ("Admin", "Administration"),
        ("Achats", "Achats"),
        ("Compta", "Comptabilité"),
    ):
        group = Group.objects.create(name=name)
        AuthGroupName.objects.create(group=group, group_name=label)
        names[name] = group

    return names


def test_processeurs_simples(request_for, settings):
    request = request_for()

    assert processors.debug(request) == {"environnement_debug": False}
    assert processors.title(request) == {"title": "HERON"}
    assert processors.title(None) == {}
    assert processors.date_du_jour(request) == {"date_du_jour": datetime.date.today()}
    assert processors.date_du_jour(None) == {}
    assert processors.annee_du_jour(request) == {"annee_du_jour": datetime.date.today().year}
    assert processors.annee_du_jour(None) == {}
    assert processors.domain_debug(None) == {"domain_debug": settings.DOMAIN_DEBUG}
    settings.TYPE_OF_BASE = "FORMATION"
    assert processors.type_of_base(None) == {"type_of_base": "FORMATION"}


def test_domaine_du_site(settings, request_for):
    """Le schéma est celui de la requête (http en test, https derrière un proxy TLS)."""
    Site.objects.update_or_create(
        pk=settings.SITE_ID, defaults={"domain": "heron.local", "name": "Héron"}
    )

    assert processors.domain_site(request_for()) == {"domain_site": "http://heron.local"}


def test_groupes_de_l_utilisateur(request_for, make_user, groupes):
    user = make_user()
    user.groups.add(groupes["Achats"], groupes["Admin"])

    assert set(processors.user_group(request_for(user))["user_group"]) == {"Achats", "Admin"}
    assert processors.user_group(request_for()) == {"user_group": ()}
    assert sorted(processors.groups_processor(request_for())["groups"]) == [
        "Achats",
        "Admin",
        "Compta",
    ]
    assert processors.groups_processor(None) == {"groups": []}


def test_menus_par_groupes(request_for, make_user, groupes):
    """Superuser : tous les groupes sauf Admin ; utilisateur : ses groupes sauf Admin ; anonyme : rien"""
    superuser = make_user(email="root@heron.local", username="root", is_superuser=True)
    user = make_user()
    user.groups.add(groupes["Compta"], groupes["Admin"])

    assert processors.groupes_processor(request_for(superuser)) == {
        "groupes": {"Achats": "Achats", "Compta": "Comptabilité"}
    }
    assert processors.groupes_processor(request_for(user)) == {
        "groupes": {"Compta": "Comptabilité"}
    }
    assert processors.groupes_processor(request_for()) == {"groupes": {}}


@pytest.mark.parametrize(
    ("centers", "expected"),
    [
        (
            "ACF|DO",
            {
                "in_acuitis": True,
                "in_ari": False,
                "in_do": True,
                "in_ga": False,
                "in_maa": False,
                "in_unisson": False,
            },
        ),
        (
            "*",
            {
                "in_acuitis": True,
                "in_ari": True,
                "in_do": True,
                "in_ga": True,
                "in_maa": True,
                "in_unisson": True,
            },
        ),
        (
            "ARI|GAF|MAA|UNI",
            {
                "in_acuitis": False,
                "in_ari": True,
                "in_do": False,
                "in_ga": True,
                "in_maa": True,
                "in_unisson": True,
            },
        ),
    ],
)
def test_centrales_filles(request_for, make_user, centers, expected):
    request = request_for(make_user(code_child_center=centers))

    result = {}
    for name in expected:
        result.update(getattr(processors, name)(request))

    assert result == expected


def test_centrales_filles_anonyme(request_for):
    request = request_for()

    assert processors.in_acuitis(request) == {"in_acuitis": False}
    assert processors.in_ari(request) == {"in_ari": False}
    assert processors.in_do(request) == {"in_do": False}
    assert processors.in_ga(request) == {"in_ga": False}
    assert processors.in_maa(request) == {"in_maa": False}
    assert processors.in_unisson(request) == {"in_unisson": False}


def test_utilisateur_paulo(request_for, make_user):
    assert processors.user_paulo(
        request_for(make_user(email="paulo@alves.ovh", username="paulo"))
    ) == {"user_paulo": True}
    assert processors.user_paulo(request_for(make_user())) == {"user_paulo": False}
    assert processors.user_paulo(request_for()) == {"user_paulo": False}


def test_notifications_non_lues(request_for, make_user, monkeypatch):
    user = make_user()

    assert processors.unread_notifications_count(request_for()) == {"unread_notifications_count": 0}
    assert processors.unread_notifications_count(request_for(user)) == {
        "unread_notifications_count": 0
    }

    monkeypatch.setattr(processors, "get_unread_count", lambda who: 3 if who == user else 0)
    assert processors.unread_notifications_count(request_for(user)) == {
        "unread_notifications_count": 3
    }
