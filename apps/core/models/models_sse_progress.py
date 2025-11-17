"""
Modèle Django pour suivre la progression SSE
À ajouter dans apps/core/models.py

created at: 2025-01-10
created by: Paulo ALVES
"""

import json

from django.db import models, transaction, connection
from django.utils import timezone
from django.conf import settings


class SSEProgress(models.Model):
    """
    Modèle générique pour suivre la progression de tâches avec SSE
    Réutilisable pour n'importe quelle tâche (envoi emails, import, export, etc.)
    """

    job_id = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        verbose_name="ID du job",
        help_text="Identifiant unique du job (UUID)",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sse_progress_jobs",
        verbose_name="Utilisateur",
    )

    STATUS_CHOICES = [
        ("pending", "En attente"),
        ("in_progress", "En cours"),
        ("completed", "Terminé"),
        ("failed", "Échoué"),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        verbose_name="Statut",
        db_index=True,
    )

    task_type = models.CharField(
        max_length=50,
        verbose_name="Type de tâche",
        help_text="email_sending, data_import, report_generation, etc.",
        db_index=True,
    )

    total_items = models.IntegerField(
        default=0,
        verbose_name="Nombre total d'éléments",
    )
    processed_items = models.IntegerField(
        default=0,
        verbose_name="Éléments traités",
    )
    failed_items = models.IntegerField(
        default=0,
        verbose_name="Éléments en erreur",
    )

    current_message = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="Message en cours",
    )

    error_message = models.TextField(
        blank=True,
        null=True,
        verbose_name="Message d'erreur",
    )

    custom_title = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Titre personnalisé",
        help_text="Titre personnalisé affiché dans la jauge de progression",
    )

    completion_message = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="Message de fin personnalisé",
        help_text="Message personnalisé affiché à la fin du traitement",
    )

    metadata = models.JSONField(
        blank=True,
        null=True,
        verbose_name="Métadonnées",
        help_text="Données supplémentaires spécifiques au type de tâche",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création",
    )
    started_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Date de démarrage",
    )
    completed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Date de fin",
    )

    class Meta:
        verbose_name = "Progression SSE"
        verbose_name_plural = "Progressions SSE"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["job_id"]),
            models.Index(fields=["status"]),
            models.Index(fields=["task_type"]),
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.task_type} - {self.job_id} - {self.status} ({self.processed_items}/{self.total_items})"

    @property
    def progress_percentage(self):
        """Calcule le pourcentage de progression"""
        if self.total_items == 0:
            return 0
        return int((self.processed_items / self.total_items) * 100)

    @property
    def success_count(self):
        """Nombre d'éléments traités avec succès"""
        return self.processed_items - self.failed_items

    @property
    def success_rate(self):
        """Calcule le taux de succès"""
        if self.processed_items == 0:
            return 0
        return int((self.success_count / self.processed_items) * 100)

    @property
    def duration(self):
        """Calcule la durée du job en secondes"""
        if not self.started_at:
            return 0

        end_time = self.completed_at or timezone.now()
        duration = end_time - self.started_at
        return duration.total_seconds()

    @property
    def estimated_remaining_time(self):
        """Estime le temps restant en secondes"""
        if self.processed_items == 0 or self.duration == 0:
            return None

        remaining_items = self.total_items - self.processed_items
        if remaining_items <= 0:
            return 0

        avg_time_per_item = self.duration / self.processed_items
        return int(remaining_items * avg_time_per_item)

    @property
    def items_per_second(self):
        """Calcule le nombre d'éléments traités par seconde"""
        if self.duration == 0 or self.processed_items == 0:
            return 0
        return round(self.processed_items / self.duration, 2)

    def mark_as_started(self):
        """Marque le job comme démarré"""
        self.status = "in_progress"
        self.started_at = timezone.now()
        self.save()

    def mark_as_completed(self):
        """Marque le job comme terminé"""
        self.status = "completed"
        self.completed_at = timezone.now()
        self.save()

    def mark_as_failed(self, error_message=None):
        """Marque le job comme échoué"""
        self.status = "failed"
        self.completed_at = timezone.now()
        if error_message:
            self.error_message = error_message
        self.save()

    def update_progress(self, processed=0, failed=0, message=None, item_name=None):
        """Met à jour la progression

        :param processed: Nombre d'items traités à ajouter
        :param failed: Nombre d'items en erreur à ajouter
        :param message: Message de progression
        :param item_name: Nom de l'item (fichier) pour l'ajouter aux listes

        Note: Dans Django 3.2, il n'est pas possible de faire des commits intermédiaires
        dans une transaction atomique. Les mises à jour ne seront visibles qu'après
        le commit de la transaction parente.
        """
        # Mettre à jour les valeurs locales
        self.processed_items += processed
        self.failed_items += failed

        if message:
            self.current_message = message

        # Ajouter l'item aux listes de succès ou d'erreur
        if item_name:
            metadata = self.metadata or {"success": [], "failed": []}

            if failed > 0:
                if "failed" not in metadata:
                    metadata["failed"] = []
                metadata["failed"].append(
                    {"name": item_name, "error": message or "Erreur inconnue"}
                )
            else:
                if "success" not in metadata:
                    metadata["success"] = []
                metadata["success"].append(item_name)

            self.metadata = metadata

        # Sauvegarder normalement
        # Note: Si on est dans une transaction atomique, les changements ne seront
        # visibles qu'après le commit de la transaction
        self.save()

    def to_dict(self):
        """Convertit en dictionnaire pour l'API"""
        return {
            "job_id": self.job_id,
            "task_type": self.task_type,
            "status": self.status,
            "status_display": self.get_status_display(),
            "total_items": self.total_items,
            "processed_items": self.processed_items,
            "failed_items": self.failed_items,
            "success_count": self.success_count,
            "progress_percentage": self.progress_percentage,
            "success_rate": self.success_rate,
            "current_message": self.current_message,
            "error_message": self.error_message,
            "custom_title": self.custom_title,
            "completion_message": self.completion_message,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "duration": self.duration,
            "estimated_remaining_time": self.estimated_remaining_time,
            "items_per_second": self.items_per_second,
        }
