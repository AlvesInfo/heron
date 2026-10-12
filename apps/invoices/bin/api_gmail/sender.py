"""
FR : Module d'envoi d'emails via l'API Gmail
EN : Email sending module via Gmail API

Commentaire:
Ce module gère l'envoi d'emails via l'API Gmail avec gestion intelligente
des quotas et retry automatique en cas d'erreur.

Pour 1000 emails: environ 2-3 minutes avec les paramètres optimisés

created at: 2025-01-10
created by: Paulo ALVES 
"""

import base64
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from googleapiclient.errors import HttpError
from bs4 import BeautifulSoup
from django.utils.functional import SimpleLazyObject

from heron.loggers import LOGGER_EMAIL
from .auth import authenticator
from .config import config
from apps.core.models import SSEProgress


@dataclass
class EmailResult:
    """Résultat de l'envoi d'un email"""

    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None
    recipient: Optional[str] = None


class RateLimiter:
    """Gère le rate limiting pour respecter les quotas Gmail"""

    def __init__(self, max_per_second: int = 10):
        """
        Initialise le rate limiter
        :param max_per_second: Nombre maximum d'emails par seconde
        """
        self.max_per_second = max_per_second
        self.min_interval = 1.0 / max_per_second  # Intervalle minimum entre envois
        self.last_send_time = 0.0

    def wait_if_needed(self):
        """Attend si nécessaire pour respecter le rate limit"""
        current_time = time.time()
        time_since_last_send = current_time - self.last_send_time

        if time_since_last_send < self.min_interval:
            sleep_time = self.min_interval - time_since_last_send
            time.sleep(sleep_time)

        self.last_send_time = time.time()


class GmailSender:
    """Classe pour envoyer des emails via l'API Gmail"""

    def __init__(self):
        """Initialise le sender"""
        self.config = config
        self.service = None
        self.rate_limiter = RateLimiter(max_per_second=self.config.max_per_second)
        self._ensure_service()

    def _ensure_service(self):
        """S'assure que le service Gmail est initialisé"""
        if self.service is None:
            self.service = authenticator.get_gmail_service()

    def _reset_service(self):
        """Réinitialise le service Gmail (connexion SSL cassée, etc.)"""
        LOGGER_EMAIL.warning("Réinitialisation du service Gmail API...")
        authenticator.service = None
        self.service = None
        self._ensure_service()

    def create_message(
        self,
        to: List[str],
        subject: str,
        body_text: str,
        body_html: str,
        context: Dict,
        attachments: Optional[List[Path]] = None,
    ) -> dict:
        """
        Crée un message email au format attendu par l'API Gmail
        :param to: Liste des destinataires
        :param subject: Sujet de l'email
        :param body_text: Corps en texte brut
        :param body_html: Corps en HTML
        :param context: Contexte pour formater le message
        :param attachments: Liste des fichiers à attacher
        :return: Message au format dict pour l'API Gmail
        """
        # Formate le sujet et le corps avec le contexte
        formatted_subject = subject.format(**context)
        formatted_html = body_html.format(**context)
        formatted_text = BeautifulSoup(formatted_html, "lxml").get_text()

        # Crée le message MIME
        message = MIMEMultipart()
        message["From"] = self.config.sender_email
        message["To"] = ", ".join(to)
        message["Subject"] = formatted_subject

        # Corps du message
        body = MIMEMultipart("alternative")
        body.attach(MIMEText(formatted_text, "plain"))
        body.attach(MIMEText(formatted_html, "html"))
        message.attach(body)

        # Ajoute les pièces jointes
        if attachments:
            for file_path in attachments:
                if not file_path.exists():
                    LOGGER_EMAIL.warning(
                        "Fichier non trouvé, ignoré: %s", file_path
                    )
                    continue

                try:
                    with open(file_path, "rb") as file:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(file.read())

                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename={file_path.name}",
                    )
                    message.attach(part)
                except Exception as error:
                    LOGGER_EMAIL.error(
                        "Erreur lors de l'ajout de la pièce jointe %s: %s",
                        file_path,
                        error,
                    )
                    raise

        # Encode le message en base64
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

        return {"raw": raw_message}

    def _retry_delay(self, attempt: int) -> float:
        """Délai avant la tentative suivante : exponentiel, plafonné à max_retry_delay"""
        retry_delay = self.config.retry_delay * (
            self.config.retry_backoff ** attempt
        )
        return min(retry_delay, self.config.max_retry_delay)

    def _send_once(self, message: dict, to: List[str]) -> EmailResult:
        """Une tentative d'envoi (après attente éventuelle du rate limiting)"""
        # Attend si nécessaire pour le rate limiting
        self.rate_limiter.wait_if_needed()

        # Envoie le message
        result = (
            self.service.users()
            .messages()
            .send(userId="me", body=message)
            .execute()
        )

        message_id = result.get("id")
        LOGGER_EMAIL.info(
            "Email envoyé avec succès (ID: %s) à %s",
            message_id,
            ", ".join(to),
        )

        return EmailResult(
            success=True,
            message_id=message_id,
            recipient=", ".join(to),
        )

    def _http_error_result(self, error: HttpError, attempt: int, to: List[str]) -> Optional[EmailResult]:
        """
        Erreur HTTP de l'API : attend et renvoie None si elle est récupérable (rate limit, erreur
        temporaire), sinon renvoie le résultat d'échec définitif
        """
        error_code = error.resp.status

        # Erreurs récupérables (rate limit, erreurs temporaires)
        if error_code in [429, 500, 502, 503, 504]:
            retry_delay = self._retry_delay(attempt)

            LOGGER_EMAIL.warning(
                "Erreur HTTP %s (tentative %d/%d), "
                "nouvelle tentative dans %s secondes: %s",
                error_code,
                attempt + 1,
                self.config.max_retries,
                retry_delay,
                error,
            )

            time.sleep(retry_delay)
            return None

        # Erreurs non récupérables
        error_msg = (
            f"Erreur HTTP non récupérable {error_code}: {error}"
        )
        LOGGER_EMAIL.error(error_msg)
        return EmailResult(
            success=False,
            error=error_msg,
            recipient=", ".join(to),
        )

    def _after_send_error(self, error: Exception, attempt: int) -> None:
        """Erreur inattendue à l'envoi : journal, réinitialisation SSL, attente avant de retenter"""
        LOGGER_EMAIL.error(
            "Erreur lors de l'envoi (tentative %d/%d): %s",
            attempt + 1,
            self.config.max_retries,
            error,
        )

        # Réinitialise le service en cas d'erreur de connexion SSL
        if "EOF occurred" in str(error) or "ssl" in str(error).lower():
            self._reset_service()

        if attempt < self.config.max_retries - 1:
            time.sleep(self._retry_delay(attempt))

    def send_message(
        self,
        to: List[str],
        subject: str,
        body_text: str,
        body_html: str,
        context: Dict,
        attachments: Optional[List[Path]] = None,
    ) -> EmailResult:
        """
        Envoie un email via l'API Gmail avec retry automatique
        :param to: Liste des destinataires
        :param subject: Sujet de l'email
        :param body_text: Corps en texte brut
        :param body_html: Corps en HTML
        :param context: Contexte pour formater le message
        :param attachments: Liste des fichiers à attacher
        :return: EmailResult avec le statut de l'envoi
        """
        self._ensure_service()

        # Crée le message
        try:
            message = self.create_message(
                to, subject, body_text, body_html, context, attachments
            )
        except Exception as error:
            error_msg = f"Erreur lors de la création du message: {error}"
            LOGGER_EMAIL.error(error_msg)
            return EmailResult(
                success=False,
                error=error_msg,
                recipient=", ".join(to),
            )

        # Tente d'envoyer avec retry
        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                return self._send_once(message, to)

            except HttpError as error:
                last_error = error
                failure = self._http_error_result(error, attempt, to)

                if failure is not None:
                    return failure

            except Exception as error:
                last_error = error
                self._after_send_error(error, attempt)

        # Toutes les tentatives ont échoué
        error_msg = f"Échec après {self.config.max_retries} tentatives: {last_error}"
        LOGGER_EMAIL.error(error_msg)
        return EmailResult(
            success=False,
            error=error_msg,
            recipient=", ".join(to),
        )

    @staticmethod
    def _report_mass_result(i: int, total: int, result: EmailResult, attachments_name: str, progress) -> None:
        """Journalise le résultat d'un envoi en masse et met à jour la jauge éventuelle"""
        if result.success:
            msg = f"[{i}/{total}] {attachments_name} envoyée avec succès"
            LOGGER_EMAIL.info(msg)
            update_kwargs = {"processed": 1}
        else:
            msg = f"[{i}/{total}] Erreur sur envoi {attachments_name}"
            LOGGER_EMAIL.error(msg)
            update_kwargs = {"processed": 1, "failed": 1}

        if progress is not None:
            progress.update_progress(**update_kwargs, message=msg, item_name=attachments_name)

    @staticmethod
    def _log_mass_progress(i: int, total: int, start_time: float) -> None:
        """Log de progression tous les 50 emails"""
        if i % 50 == 0:
            elapsed = time.time() - start_time
            rate = i / elapsed
            estimated_remaining = (total - i) / rate
            msg = (
                f"Progression: {i}/{total} emails envoyés "
                f"({rate:.1f} emails/s, temps restant estimé: {estimated_remaining:.0f}s)"
            )
            LOGGER_EMAIL.info(msg)

    def _send_mass_item(self, i: int, email_data: Tuple) -> Tuple[EmailResult, Optional[str]]:
        """
        Envoie un email de la liste et renvoie un seul résultat pour lui
        :param i: rang de l'email
        :param email_data: tuple (to, subject, text, html, context, attachments)
        :return: (résultat, nom des pièces jointes) ; le nom est None si l'envoi n'a pas été tenté
        """
        try:
            to, subject, body_text, body_html, context, attachments = email_data
            # Calculé avant l'envoi : rien ne peut échouer entre l'envoi et son résultat
            attachments_name = ", ".join(file.name for file in attachments or ())

            # Filtre les emails vides
            to = [email for email in to if email]

            if not to:
                LOGGER_EMAIL.warning("Aucun destinataire valide pour l'email %d", i)
                return EmailResult(success=False, error="Aucun destinataire valide"), None

            return (
                self.send_message(to, subject, body_text, body_html, context, attachments),
                attachments_name,
            )

        except Exception as error:
            LOGGER_EMAIL.exception("Erreur lors de l'envoi de l'email %d: %s", i, error)
            return EmailResult(success=False, error=str(error)), None

    def send_mass_mail(
        self, email_list: List[Tuple], job_id: str = None
    ) -> Tuple[int, int, List[EmailResult]]:
        """
        Envoie plusieurs emails en masse avec gestion intelligente des quotas
        :param email_list: Liste de tuples (to, subject, text, html, context, attachments)
        :param job_id: identifiant du job
        :return: Tuple (nb_success, nb_errors, results)
        """
        if not email_list:
            LOGGER_EMAIL.warning("Aucun email à envoyer")
            return 0, 0, []

        LOGGER_EMAIL.info(
            "Début de l'envoi de %d emails via l'API Gmail", len(email_list)
        )

        start_time = time.time()
        results = []
        nb_success = 0
        nb_errors = 0

        # Jauge de progression optionnelle (envoi hors écran de suivi)
        progress = SSEProgress.objects.filter(job_id=job_id).first() if job_id else None

        for i, email_data in enumerate(email_list, 1):
            result, attachments_name = self._send_mass_item(i, email_data)
            results.append(result)
            sent = bool(result.success)
            nb_success += sent
            nb_errors += not sent

            if attachments_name is None:
                continue

            # Le suivi (jauge, logs) ne doit pas changer le résultat d'un email déjà traité
            try:
                self._report_mass_result(i, len(email_list), result, attachments_name, progress)
                self._log_mass_progress(i, len(email_list), start_time)
            except Exception:
                LOGGER_EMAIL.exception("Suivi de l'envoi de l'email %d non enregistré", i)

        elapsed_time = time.time() - start_time
        average_rate = len(email_list) / elapsed_time if elapsed_time > 0 else 0

        LOGGER_EMAIL.info(
            "Envoi terminé: %d succès, %d erreurs sur %d emails "
            "(temps total: %.1fs, moyenne: %.1f emails/s)",
            nb_success,
            nb_errors,
            len(email_list),
            elapsed_time,
            average_rate,
        )

        return nb_success, nb_errors, results


# Instance globale du sender, construite (et authentifiée) au premier accès
sender = SimpleLazyObject(GmailSender)
