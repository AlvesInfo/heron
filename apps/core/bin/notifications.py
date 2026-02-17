"""
CRUD pour les notifications utilisateur

created at: 2025-02-14
created by: Paulo ALVES
"""

from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from apps.core.models.models_notifications import Notification


def create_notification(user, title, message, level="info", link=None, created_by=None):
    """Crée une notification pour un utilisateur"""
    return Notification.objects.create(
        user=user,
        title=title,
        message=message,
        level=level,
        link=link,
        created_by=created_by,
    )


def broadcast_notification(title, message, level="info", link=None, created_by=None):
    """Crée une notification pour tous les utilisateurs actifs"""
    User = get_user_model()
    users = User.objects.filter(is_active=True)
    notifications = [
        Notification(
            user=user,
            title=title,
            message=message,
            level=level,
            link=link,
            created_by=created_by,
        )
        for user in users
    ]
    return Notification.objects.bulk_create(notifications)


def get_unread_notifications(user):
    """Retourne le QuerySet des notifications non lues"""
    return Notification.objects.filter(user=user, is_read=False)


def get_unread_count(user):
    """Retourne le nombre de notifications non lues"""
    return Notification.objects.filter(user=user, is_read=False).count()


def get_all_notifications(user, limit=30):
    """Retourne les notifications de l'utilisateur, en excluant les notifications lues
    depuis plus d'une semaine"""
    one_week_ago = timezone.now() - timedelta(days=7)
    notifications = Notification.objects.filter(
        models.Q(user=user)
        & ~models.Q(is_read=True, read_at__lt=one_week_ago)
    )[:limit]

    return notifications


def mark_notification_as_read(notification_uuid, user):
    """Marque une notification comme lue"""
    try:
        notification = Notification.objects.get(
            uuid_identification=notification_uuid, user=user
        )
        notification.mark_as_read()
        return True
    except Notification.DoesNotExist:
        return False


def mark_all_as_read(user):
    """Marque toutes les notifications comme lues"""
    return Notification.objects.filter(user=user, is_read=False).update(
        is_read=True, read_at=timezone.now()
    )


def delete_notification(notification_uuid, user):
    """Supprime une notification"""
    try:
        notification = Notification.objects.get(
            uuid_identification=notification_uuid, user=user
        )
        notification.delete()
        return True
    except Notification.DoesNotExist:
        return False
