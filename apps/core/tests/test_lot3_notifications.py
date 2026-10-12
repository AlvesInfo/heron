# pylint: disable=E0401,W0621
"""FR : Tests des notifications utilisateur : modèle, CRUD (bin/notifications.py) et vues JSON


EN : Tests for user notifications: model, CRUD and JSON views

created at: 2026-10-11
created by: Paulo ALVES
"""

import datetime
import uuid

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.core.bin.notifications import (
    broadcast_notification,
    create_notification,
    delete_notification,
    get_all_notifications,
    get_unread_count,
    get_unread_notifications,
    mark_all_as_read,
    mark_notification_as_read,
)
from apps.core.models import Notification

pytestmark = pytest.mark.django_db


@pytest.fixture
def user(make_user):
    return make_user()


@pytest.fixture
def other_user(make_user):
    return make_user(email="autre@heron.local", username="autre")


# MODÈLE ===========================================================================================


def test_notification_str_et_lecture(user):
    notification = create_notification(user, "Titre", "Message", level="warning", link="/book/")

    assert str(notification) == f"Titre - {user} (non lu)"
    assert notification.read_at is None

    notification.mark_as_read()
    read_at = notification.read_at

    notification.mark_as_read()

    notification.refresh_from_db()
    assert str(notification) == f"Titre - {user} (lu)"
    assert notification.is_read is True
    assert notification.read_at == read_at


@pytest.mark.parametrize(
    ("age", "expected"),
    [
        (datetime.timedelta(seconds=30), "à l'instant"),
        (datetime.timedelta(minutes=5), "il y a 5 min"),
        (datetime.timedelta(hours=3), "il y a 3 h"),
        (datetime.timedelta(days=2, hours=1), "il y a 2 j"),
    ],
)
def test_notification_temps_ecoule(user, age, expected):
    notification = create_notification(user, "Titre", "Message")
    Notification.objects.filter(pk=notification.pk).update(created_at=timezone.now() - age)
    notification.refresh_from_db()

    assert notification.time_since == expected


@pytest.mark.parametrize(
    ("level", "icon", "color"),
    [
        ("info", "info circle", "blue"),
        ("warning", "exclamation triangle", "yellow"),
        ("error", "times circle", "red"),
        ("success", "check circle", "green"),
        ("inconnu", "info circle", "blue"),
    ],
)
def test_notification_icone_et_couleur(user, level, icon, color):
    notification = create_notification(user, "Titre", "Message", level=level)

    assert notification.level_icon == icon
    assert notification.level_color == color


def test_notification_to_dict(user, other_user):
    notification = create_notification(
        user, "Titre", "Message", level="error", link="/x/", created_by=other_user
    )

    payload = notification.to_dict()

    assert payload["uuid"] == str(notification.uuid_identification)
    assert (payload["title"], payload["message"], payload["level"]) == ("Titre", "Message", "error")
    assert (payload["level_icon"], payload["level_color"]) == ("times circle", "red")
    assert (payload["is_read"], payload["link"], payload["time_since"]) == (
        False,
        "/x/",
        "à l'instant",
    )
    assert payload["created_at"] == notification.created_at.isoformat()
    assert notification.created_by == other_user


# CRUD =============================================================================================


def test_broadcast_et_compteurs(user, other_user, make_user):
    """Une notification par utilisateur actif, les inactifs sont ignorés"""
    inactive = make_user(email="inactif@heron.local", username="inactif")
    inactive.is_active = False
    inactive.save()

    created = broadcast_notification("Erreurs", "Des erreurs", level="error", link="/book/")

    assert {notification.user for notification in created} == {user, other_user}
    assert get_unread_count(user) == 1
    assert list(get_unread_notifications(user)) == [Notification.objects.get(user=user)]
    assert get_unread_count(inactive) == 0


def test_get_all_notifications_exclut_les_lues_depuis_plus_d_une_semaine(user, other_user):
    recent = create_notification(user, "Récente", "x")
    read_recent = create_notification(user, "Lue récemment", "x")
    read_recent.mark_as_read()
    old_read = create_notification(user, "Lue ancienne", "x")
    Notification.objects.filter(pk=old_read.pk).update(
        is_read=True, read_at=timezone.now() - datetime.timedelta(days=8)
    )
    old_unread = create_notification(user, "Non lue ancienne", "x")
    Notification.objects.filter(pk=old_unread.pk).update(
        created_at=timezone.now() - datetime.timedelta(days=30)
    )
    create_notification(other_user, "Autre", "x")

    notifications = list(get_all_notifications(user))

    assert set(notifications) == {recent, read_recent, old_unread}
    assert len(get_all_notifications(user, limit=2)) == 2


def test_mark_as_read_et_delete_par_utilisateur(user, other_user):
    """Un utilisateur ne peut marquer ou supprimer que ses propres notifications"""
    mine = create_notification(user, "Mienne", "x")
    theirs = create_notification(other_user, "Autre", "x")

    assert mark_notification_as_read(mine.uuid_identification, user) is True
    assert mark_notification_as_read(theirs.uuid_identification, user) is False
    assert mark_notification_as_read(uuid.uuid4(), user) is False
    assert Notification.objects.get(pk=mine.pk).is_read is True
    assert Notification.objects.get(pk=theirs.pk).is_read is False

    assert delete_notification(theirs.uuid_identification, user) is False
    assert delete_notification(mine.uuid_identification, user) is True
    assert not Notification.objects.filter(pk=mine.pk).exists()
    assert Notification.objects.filter(pk=theirs.pk).exists()


def test_mark_all_as_read(user, other_user):
    create_notification(user, "Une", "x")
    create_notification(user, "Deux", "x")
    create_notification(other_user, "Autre", "x")

    assert mark_all_as_read(user) == 2
    assert get_unread_count(user) == 0
    assert get_unread_count(other_user) == 1
    assert mark_all_as_read(user) == 0


# VUES =============================================================================================


def test_vues_exigent_une_authentification(client):
    response = client.get(reverse("core:notifications_list"))

    assert response.status_code == 302
    assert "login" in response.url


def test_liste_des_notifications(logged_client, other_user):
    first = create_notification(logged_client.user, "Première", "x")
    second = create_notification(logged_client.user, "Seconde", "x")
    create_notification(other_user, "Autre", "x")

    response = logged_client.get(reverse("core:notifications_list"))
    limited = logged_client.get(reverse("core:notifications_list"), {"limit": 1})

    payload = response.json()
    assert response.status_code == 200
    assert payload["unread_count"] == 2
    assert [item["uuid"] for item in payload["notifications"]] == [
        str(second.uuid_identification),
        str(first.uuid_identification),
    ]
    assert len(limited.json()["notifications"]) == 1
    assert logged_client.post(reverse("core:notifications_list")).status_code == 405


def test_marquer_lue(logged_client, other_user):
    mine = create_notification(logged_client.user, "Mienne", "x")
    create_notification(logged_client.user, "Autre mienne", "x")
    theirs = create_notification(other_user, "Autre", "x")

    response = logged_client.post(
        reverse("core:notification_mark_read", args=[mine.uuid_identification])
    )
    forbidden = logged_client.post(
        reverse("core:notification_mark_read", args=[theirs.uuid_identification])
    )

    assert response.json() == {"success": True, "unread_count": 1}
    assert forbidden.status_code == 404
    assert forbidden.json() == {"error": "Notification non trouvée"}
    assert (
        logged_client.get(
            reverse("core:notification_mark_read", args=[mine.uuid_identification])
        ).status_code
        == 405
    )


def test_tout_marquer_lu(logged_client):
    create_notification(logged_client.user, "Une", "x")

    response = logged_client.post(reverse("core:notification_mark_all_read"))

    assert response.json() == {"success": True, "unread_count": 0}
    assert get_unread_count(logged_client.user) == 0


def test_supprimer(logged_client, other_user):
    mine = create_notification(logged_client.user, "Mienne", "x")
    create_notification(logged_client.user, "Autre mienne", "x")
    theirs = create_notification(other_user, "Autre", "x")

    response = logged_client.post(
        reverse("core:notification_delete", args=[mine.uuid_identification])
    )
    forbidden = logged_client.post(
        reverse("core:notification_delete", args=[theirs.uuid_identification])
    )

    assert response.json() == {"success": True, "unread_count": 1}
    assert not Notification.objects.filter(pk=mine.pk).exists()
    assert forbidden.status_code == 404
