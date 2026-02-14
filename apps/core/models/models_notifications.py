"""
Modèle Django pour les notifications utilisateur

created at: 2025-02-14
created by: Paulo ALVES
"""

import uuid

from django.db import models
from django.conf import settings
from django.utils import timezone


class Notification(models.Model):
    """Notification destinée à un utilisateur"""

    LEVEL_CHOICES = [
        ("info", "Information"),
        ("warning", "Avertissement"),
        ("error", "Erreur"),
        ("success", "Succès"),
    ]

    uuid_identification = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="Destinataire",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications_created",
        verbose_name="Créé par",
    )
    title = models.CharField(max_length=255, verbose_name="Titre")
    message = models.TextField(verbose_name="Message")
    level = models.CharField(
        max_length=10,
        choices=LEVEL_CHOICES,
        default="info",
        verbose_name="Niveau",
    )
    is_read = models.BooleanField(default=False, verbose_name="Lu")
    read_at = models.DateTimeField(null=True, blank=True, verbose_name="Lu le")
    link = models.CharField(
        max_length=500, blank=True, null=True, verbose_name="Lien"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    modified_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read"]),
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.user} ({'lu' if self.is_read else 'non lu'})"

    def mark_as_read(self):
        """Marque la notification comme lue"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at", "modified_at"])

    @property
    def time_since(self):
        """Retourne le temps écoulé depuis la création"""
        delta = timezone.now() - self.created_at
        seconds = int(delta.total_seconds())

        if seconds < 60:
            return "à l'instant"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"il y a {minutes} min"
        elif seconds < 86400:
            hours = seconds // 3600
            return f"il y a {hours} h"
        else:
            days = seconds // 86400
            return f"il y a {days} j"

    @property
    def level_icon(self):
        """Retourne l'icône Semantic UI correspondant au niveau"""
        icons = {
            "info": "info circle",
            "warning": "exclamation triangle",
            "error": "times circle",
            "success": "check circle",
        }
        return icons.get(self.level, "info circle")

    @property
    def level_color(self):
        """Retourne la couleur Semantic UI correspondant au niveau"""
        colors = {
            "info": "blue",
            "warning": "yellow",
            "error": "red",
            "success": "green",
        }
        return colors.get(self.level, "blue")

    def to_dict(self):
        """Convertit en dictionnaire pour l'API JSON"""
        return {
            "uuid": str(self.uuid_identification),
            "title": self.title,
            "message": self.message,
            "level": self.level,
            "level_icon": self.level_icon,
            "level_color": self.level_color,
            "is_read": self.is_read,
            "link": self.link,
            "time_since": self.time_since,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
