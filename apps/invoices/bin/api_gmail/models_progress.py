# pylint: disable=E0401
"""
FR : Modèle pour suivre la progression de l'envoi des emails
EN : Model to track email sending progress

Commentaire:
Ce modèle permet de stocker la progression de l'envoi des emails
pour pouvoir afficher une jauge en temps réel dans l'interface.

created at: 2025-01-10
created by: Paulo ALVES 
"""

from django.db import models
from django.utils import timezone
from apps.users.models import User


class EmailSendProgress(models.Model):
    """Modèle pour suivre la progression de l'envoi des emails"""

    # Identifiant unique du job
    job_id = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        verbose_name="ID du job",
        help_text="Identifiant unique du job Celery",
    )

    # Utilisateur qui a lancé l'envoi
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="email_send_jobs",
        verbose_name="Utilisateur",
    )

    # Statut du job
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
    )

    # Progression
    total_emails = models.IntegerField(
        default=0,
        verbose_name="Nombre total d'emails",
    )
    sent_emails = models.IntegerField(
        default=0,
        verbose_name="Emails envoyés",
    )
    failed_emails = models.IntegerField(
        default=0,
        verbose_name="Emails en erreur",
    )

    # Métadonnées
    current_operation = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Opération en cours",
        help_text="Description de l'opération en cours",
    )

    error_message = models.TextField(
        blank=True,
        null=True,
        verbose_name="Message d'erreur",
    )

    # Dates
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

    # Informations supplémentaires
    cct = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="CCT",
    )
    period = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Période",
    )

    class Meta:
        verbose_name = "Progression d'envoi d'email"
        verbose_name_plural = "Progressions d'envoi d'emails"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["job_id"]),
            models.Index(fields=["status"]),
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self):
        return f"Job {self.job_id} - {self.status} ({self.sent_emails}/{self.total_emails})"

    @property
    def progress_percentage(self):
        """Calcule le pourcentage de progression"""
        if self.total_emails == 0:
            return 0
        return int((self.sent_emails / self.total_emails) * 100)

    @property
    def success_rate(self):
        """Calcule le taux de succès"""
        if self.sent_emails == 0:
            return 0
        successful = self.sent_emails - self.failed_emails
        return int((successful / self.sent_emails) * 100)

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
        if self.sent_emails == 0 or self.duration == 0:
            return None

        remaining_emails = self.total_emails - self.sent_emails
        if remaining_emails <= 0:
            return 0

        avg_time_per_email = self.duration / self.sent_emails
        return int(remaining_emails * avg_time_per_email)

    @property
    def emails_per_second(self):
        """Calcule le nombre d'emails envoyés par seconde"""
        if self.duration == 0 or self.sent_emails == 0:
            return 0
        return round(self.sent_emails / self.duration, 2)

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

    def update_progress(self, sent=0, failed=0, current_operation=None):
        """Met à jour la progression"""
        self.sent_emails += sent
        self.failed_emails += failed

        if current_operation:
            self.current_operation = current_operation

        self.save()

    def to_dict(self):
        """Convertit en dictionnaire pour l'API"""
        return {
            "job_id": self.job_id,
            "status": self.status,
            "status_display": self.get_status_display(),
            "total_emails": self.total_emails,
            "sent_emails": self.sent_emails,
            "failed_emails": self.failed_emails,
            "successful_emails": self.sent_emails - self.failed_emails,
            "progress_percentage": self.progress_percentage,
            "success_rate": self.success_rate,
            "current_operation": self.current_operation,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration": self.duration,
            "estimated_remaining_time": self.estimated_remaining_time,
            "emails_per_second": self.emails_per_second,
            "cct": self.cct,
            "period": self.period,
        }