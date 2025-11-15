# pylint: disable=E0401
"""
Module générique pour envoyer des mises à jour de progression via SSE
RÉUTILISABLE pour toutes les jauges de l'application

Usage:
    from apps.invoices.bin.api_gmail.sse_progress_core import SSEProgressTracker

    sse = SSEProgressTracker("job-123")
    sse.send_start(total=500)

    for i in range(500):
        process_item(i)
        sse.send_progress(current=i+1, total=500, message="Processing...")

    sse.send_complete(total=500)

created at: 2025-01-10
created by: Paulo ALVES 
"""

from typing import Dict, Any

try:
    import django_eventstream
    SSE_AVAILABLE = True
except ImportError:
    SSE_AVAILABLE = False

from heron.loggers import LOGGER_INVOICES


class SSEProgressTracker:
    """
    Classe générique pour tracker la progression via Server-Sent Events
    Réutilisable pour n'importe quelle tâche avec progression
    """

    def __init__(self, channel_name: str, enabled: bool = True):
        """
        Initialise le tracker SSE
        :param channel_name: Nom unique du channel (ex: 'email-job-123')
        :param enabled: Si False, les événements ne sont pas envoyés (mode silent)
        """
        self.channel_name = f"progress-{channel_name}"
        self.enabled = enabled and SSE_AVAILABLE

        if not SSE_AVAILABLE and enabled:
            LOGGER_INVOICES.warning(
                "django-eventstream n'est pas installé. "
                "Les événements SSE ne seront pas envoyés. "
                "Pour installer: pip install django-eventstream"
            )

    def send_event(self, event_type: str, data: Dict[str, Any]):
        """
        Envoie un événement SSE générique
        :param event_type: Type d'événement (start, progress, complete, error, etc.)
        :param data: Données à envoyer au format dict
        """
        if not self.enabled:
            return

        try:
            django_eventstream.send_event(
                self.channel_name,
                event_type,
                data
            )
            LOGGER_INVOICES.debug(
                "SSE event sent: channel=%s, type=%s, data=%s",
                self.channel_name,
                event_type,
                data
            )
        except Exception as error:
            LOGGER_INVOICES.error(
                "Erreur lors de l'envoi SSE: %s", error
            )

    def send_start(self, total: int, **kwargs):
        """
        Notifie le début du processus
        :param total: Nombre total d'éléments à traiter
        :param kwargs: Données supplémentaires (title, message, etc.)
        """
        self.send_event('start', {
            'status': 'started',
            'total': total,
            'current': 0,
            'percentage': 0,
            **kwargs
        })

    def send_progress(
        self,
        current: int,
        total: int,
        message: str = None,
        **kwargs
    ):
        """
        Notifie la progression
        :param current: Nombre d'éléments traités
        :param total: Nombre total d'éléments
        :param message: Message optionnel à afficher
        :param kwargs: Données supplémentaires
        """
        percentage = int((current / total) * 100) if total > 0 else 0

        self.send_event('progress', {
            'status': 'in_progress',
            'current': current,
            'total': total,
            'percentage': percentage,
            'remaining': total - current,
            'message': message,
            **kwargs
        })

    def send_complete(self, total: int, message: str = None, **kwargs):
        """
        Notifie la fin avec succès
        :param total: Nombre total d'éléments traités
        :param message: Message de fin
        :param kwargs: Données supplémentaires
        """
        self.send_event('complete', {
            'status': 'completed',
            'total': total,
            'current': total,
            'percentage': 100,
            'message': message or 'Terminé avec succès',
            **kwargs
        })

    def send_error(self, error_message: str, **kwargs):
        """
        Notifie une erreur
        :param error_message: Message d'erreur
        :param kwargs: Données supplémentaires
        """
        self.send_event('error', {
            'status': 'error',
            'error': error_message,
            'message': f"Erreur: {error_message}",
            **kwargs
        })

    def send_warning(self, warning_message: str, **kwargs):
        """
        Notifie un avertissement (continue malgré l'erreur)
        :param warning_message: Message d'avertissement
        :param kwargs: Données supplémentaires
        """
        self.send_event('warning', {
            'status': 'warning',
            'warning': warning_message,
            'message': f"Attention: {warning_message}",
            **kwargs
        })

    def send_custom(self, event_type: str, data: Dict[str, Any]):
        """
        Envoie un événement personnalisé
        :param event_type: Type d'événement custom
        :param data: Données
        """
        self.send_event(event_type, data)


# Alias pour compatibilité
SSETracker = SSEProgressTracker