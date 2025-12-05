# pylint: disable=E0401
"""
FR : Module d'authentification OAuth2 pour l'API Gmail
EN : OAuth2 authentication module for Gmail API

Commentaire:
Ce module gère l'authentification OAuth2 pour l'API Gmail.
Il crée et rafraîchit automatiquement les tokens d'accès.

created at: 2025-01-10
created by: Paulo ALVES 
"""

import json
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from heron.loggers import LOGGER_EMAIL
from .config import config


class GmailAuthenticator:
    """Classe pour gérer l'authentification Gmail OAuth2"""

    def __init__(self):
        """Initialise l'authenticator"""
        self.config = config
        self.creds: Optional[Credentials] = None
        self.service = None

    def get_credentials(self) -> Credentials:
        """
        Récupère ou crée les credentials OAuth2
        :return: Credentials OAuth2
        """
        token_file = self.config.token_file_path
        credentials_file = self.config.credentials_file_path

        # Tente de charger le token existant
        if token_file.exists():
            try:
                self.creds = Credentials.from_authorized_user_file(
                    str(token_file), self.config.scopes
                )
                LOGGER_EMAIL.info("Token OAuth2 chargé depuis %s", token_file)
            except Exception as error:
                LOGGER_EMAIL.warning(
                    "Erreur lors du chargement du token: %s", error
                )
                self.creds = None

        # Si pas de credentials valides, on en crée de nouveaux
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                # Rafraîchit le token expiré
                try:
                    LOGGER_EMAIL.info("Rafraîchissement du token OAuth2...")
                    self.creds.refresh(Request())
                    LOGGER_EMAIL.info("Token OAuth2 rafraîchi avec succès")
                except Exception as error:
                    LOGGER_EMAIL.error(
                        "Erreur lors du rafraîchissement du token: %s", error
                    )
                    self.creds = None

            # Si toujours pas de credentials, lance le flow OAuth2
            if not self.creds:
                # Crée le fichier credentials.json depuis la configuration YAML si nécessaire
                self._create_credentials_file_if_needed(credentials_file)

                if not credentials_file.exists():
                    raise FileNotFoundError(
                        f"Le fichier de credentials {credentials_file} n'existe pas. "
                        f"Veuillez créer ce fichier avec vos credentials OAuth2 Google. "
                        f"Vous pouvez aussi créer le fichier via la configuration YAML "
                        f"en remplissant les informations oauth2.client_id et oauth2.client_secret"
                    )

                LOGGER_EMAIL.info(
                    "Lancement du flow d'authentification OAuth2..."
                )

                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(credentials_file), self.config.scopes
                    )
                    self.creds = flow.run_local_server(port=0)
                    LOGGER_EMAIL.info("Authentification OAuth2 réussie")
                except Exception as error:
                    LOGGER_EMAIL.exception(
                        "Erreur lors de l'authentification OAuth2: %s", error
                    )
                    raise

            # Sauvegarde le token pour la prochaine fois
            try:
                with open(token_file, "w", encoding="utf-8") as token:
                    token.write(self.creds.to_json())
                LOGGER_EMAIL.info("Token OAuth2 sauvegardé dans %s", token_file)
            except Exception as error:
                LOGGER_EMAIL.warning(
                    "Erreur lors de la sauvegarde du token: %s", error
                )

        return self.creds

    def _create_credentials_file_if_needed(self, credentials_file: Path):
        """
        Crée le fichier credentials.json depuis la configuration YAML si nécessaire
        :param credentials_file: Chemin vers le fichier credentials.json
        """
        if not credentials_file.exists():
            LOGGER_EMAIL.info(
                "Création du fichier credentials.json depuis la configuration YAML..."
            )
            credentials_dict = self.config.get_oauth2_credentials_dict()

            try:
                with open(credentials_file, "w", encoding="utf-8") as file:
                    json.dump(credentials_dict, file, indent=2)
                LOGGER_EMAIL.info(
                    "Fichier credentials.json créé avec succès: %s",
                    credentials_file,
                )
            except Exception as error:
                LOGGER_EMAIL.error(
                    "Erreur lors de la création du fichier credentials.json: %s",
                    error,
                )
                raise

    def get_gmail_service(self):
        """
        Récupère le service Gmail API
        :return: Service Gmail API
        """
        if self.service is None:
            try:
                creds = self.get_credentials()
                self.service = build(
                    "gmail",
                    "v1",
                    credentials=creds,
                    cache_discovery=False,
                )
                LOGGER_EMAIL.info("Service Gmail API créé avec succès")
            except Exception as error:
                LOGGER_EMAIL.exception(
                    "Erreur lors de la création du service Gmail API: %s", error
                )
                raise

        return self.service

    def revoke_credentials(self):
        """Révoque les credentials OAuth2"""
        token_file = self.config.token_file_path

        if token_file.exists():
            try:
                token_file.unlink()
                LOGGER_EMAIL.info("Token OAuth2 révoqué et supprimé")
                self.creds = None
                self.service = None
            except Exception as error:
                LOGGER_EMAIL.error(
                    "Erreur lors de la révocation du token: %s", error
                )
                raise


# Instance globale de l'authenticator
authenticator = GmailAuthenticator()