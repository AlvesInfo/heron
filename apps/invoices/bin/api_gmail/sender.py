# pylint: disable=E0401,W0718,R0913,R0914,R0915
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

from heron.loggers import LOGGER_EMAIL
from apps.core.exceptions import EmailException
from .auth import authenticator
from .config import config


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

            except HttpError as error:
                last_error = error
                error_code = error.resp.status

                # Erreurs récupérables (rate limit, erreurs temporaires)
                if error_code in [429, 500, 502, 503, 504]:
                    retry_delay = self.config.retry_delay * (
                        self.config.retry_backoff ** attempt
                    )
                    retry_delay = min(retry_delay, self.config.max_retry_delay)

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
                    continue

                # Erreurs non récupérables
                else:
                    error_msg = (
                        f"Erreur HTTP non récupérable {error_code}: {error}"
                    )
                    LOGGER_EMAIL.error(error_msg)
                    return EmailResult(
                        success=False,
                        error=error_msg,
                        recipient=", ".join(to),
                    )

            except Exception as error:
                last_error = error
                LOGGER_EMAIL.error(
                    "Erreur lors de l'envoi (tentative %d/%d): %s",
                    attempt + 1,
                    self.config.max_retries,
                    error,
                )

                if attempt < self.config.max_retries - 1:
                    retry_delay = self.config.retry_delay * (
                        self.config.retry_backoff ** attempt
                    )
                    retry_delay = min(retry_delay, self.config.max_retry_delay)
                    time.sleep(retry_delay)

        # Toutes les tentatives ont échoué
        error_msg = f"Échec après {self.config.max_retries} tentatives: {last_error}"
        LOGGER_EMAIL.error(error_msg)
        return EmailResult(
            success=False,
            error=error_msg,
            recipient=", ".join(to),
        )

    def send_mass_mail(
        self, email_list: List[Tuple]
    ) -> Tuple[int, int, List[EmailResult]]:
        """
        Envoie plusieurs emails en masse avec gestion intelligente des quotas
        :param email_list: Liste de tuples (to, subject, text, html, context, attachments)
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

        for i, email_data in enumerate(email_list, 1):
            try:
                to, subject, body_text, body_html, context, attachments = email_data

                # Filtre les emails vides
                to = [email for email in to if email]

                if not to:
                    LOGGER_EMAIL.warning("Aucun destinataire valide pour l'email %d", i)
                    results.append(
                        EmailResult(
                            success=False,
                            error="Aucun destinataire valide",
                        )
                    )
                    nb_errors += 1
                    continue

                # Envoie l'email
                result = self.send_message(
                    to, subject, body_text, body_html, context, attachments
                )
                results.append(result)

                if result.success:
                    nb_success += 1
                else:
                    nb_errors += 1

                # Log de progression tous les 50 emails
                if i % 50 == 0:
                    elapsed = time.time() - start_time
                    rate = i / elapsed
                    estimated_remaining = (len(email_list) - i) / rate
                    LOGGER_EMAIL.info(
                        "Progression: %d/%d emails envoyés "
                        "(%.1f emails/s, temps restant estimé: %.0fs)",
                        i,
                        len(email_list),
                        rate,
                        estimated_remaining,
                    )

            except Exception as error:
                LOGGER_EMAIL.exception("Erreur lors de l'envoi de l'email %d: %s", i, error)
                results.append(
                    EmailResult(
                        success=False,
                        error=str(error),
                    )
                )
                nb_errors += 1

        elapsed_time = time.time() - start_time
        average_rate = len(email_list) / elapsed_time

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


# Instance globale du sender
sender = GmailSender()