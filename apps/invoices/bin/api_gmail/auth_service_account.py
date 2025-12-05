# pylint: disable=E0401
"""
FR : Module d'authentification via Service Account pour l'API Gmail
EN : Service Account authentication module for Gmail API

Commentaire:
Ce module gère l'authentification via Service Account avec délégation de domaine.
Cela permet d'envoyer des emails sans authentification interactive (pas de 2FA).

PRÉREQUIS:
1. Créer un Service Account dans Google Cloud Console
2. Activer la délégation de domaine (Domain-Wide Delegation)
3. L'administrateur Google Workspace doit autoriser le Service Account

created at: 2025-01-10
created by: Paulo ALVES
"""

import json
from pathlib import Path
from typing import Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build

from heron.loggers import LOGGER_EMAIL
from apps.core.functions.functions_setups import settings

# Répertoire contenant les fichiers de configuration
ENV_DIR = Path(settings.PROJECT_DIR) / "env"

# Scopes nécessaires pour envoyer des emails
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


class GmailServiceAccountAuthenticator:
    """
    Classe pour gérer l'authentification Gmail via Service Account

    Avantages par rapport à OAuth2 classique:
    - Pas d'authentification interactive (pas de navigateur)
    - Pas de problème avec la 2FA
    - Token qui ne expire pas (pas besoin de refresh)
    - Idéal pour les serveurs et tâches automatisées

    Prérequis:
    - Un Service Account créé dans Google Cloud Console
    - La délégation de domaine activée
    - L'autorisation de l'admin Google Workspace
    """

    def __init__(
        self,
        service_account_file: str = "gmail_service_account.json",
        delegated_email: str = "comptabilite@acuitis.com"
    ):
        """
        Initialise l'authenticator Service Account

        :param service_account_file: Nom du fichier JSON du Service Account
        :param delegated_email: Email de l'utilisateur à impersonnifier
        """
        self.service_account_file = ENV_DIR / service_account_file
        self.delegated_email = delegated_email
        self.credentials = None
        self.service = None

    def get_credentials(self):
        """
        Récupère les credentials du Service Account avec délégation

        :return: Credentials du Service Account
        :raises FileNotFoundError: Si le fichier Service Account n'existe pas
        """
        if not self.service_account_file.exists():
            raise FileNotFoundError(
                f"Le fichier Service Account {self.service_account_file} n'existe pas.\n\n"
                f"Pour créer ce fichier:\n"
                f"1. Allez sur https://console.cloud.google.com/\n"
                f"2. Sélectionnez votre projet\n"
                f"3. Allez dans 'IAM & Admin' > 'Service Accounts'\n"
                f"4. Créez un Service Account ou sélectionnez-en un existant\n"
                f"5. Cliquez sur 'Keys' > 'Add Key' > 'Create new key' > 'JSON'\n"
                f"6. Téléchargez le fichier et placez-le dans: {ENV_DIR}\n"
                f"7. Renommez-le en: gmail_service_account.json"
            )

        try:
            # Charge les credentials du Service Account
            self.credentials = service_account.Credentials.from_service_account_file(
                str(self.service_account_file),
                scopes=SCOPES
            )

            # Délègue les credentials à l'utilisateur cible
            # Cela permet au Service Account d'agir au nom de cet utilisateur
            self.credentials = self.credentials.with_subject(self.delegated_email)

            LOGGER_EMAIL.info(
                "Credentials Service Account chargés pour %s",
                self.delegated_email
            )

            return self.credentials

        except Exception as error:
            LOGGER_EMAIL.exception(
                "Erreur lors du chargement des credentials Service Account: %s",
                error
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
                LOGGER_EMAIL.info(
                    "Service Gmail API (Service Account) créé avec succès pour %s",
                    self.delegated_email
                )
            except Exception as error:
                LOGGER_EMAIL.exception(
                    "Erreur lors de la création du service Gmail API: %s",
                    error
                )
                raise

        return self.service

    def test_connection(self) -> bool:
        """
        Teste la connexion au service Gmail

        :return: True si la connexion fonctionne, False sinon
        """
        try:
            service = self.get_gmail_service()
            # Tente de récupérer le profil de l'utilisateur
            profile = service.users().getProfile(userId="me").execute()
            LOGGER_EMAIL.info(
                "Connexion Service Account réussie. Email: %s",
                profile.get("emailAddress")
            )
            return True
        except Exception as error:
            LOGGER_EMAIL.error(
                "Échec du test de connexion Service Account: %s",
                error
            )
            return False


# Instance globale de l'authenticator Service Account
service_account_authenticator = GmailServiceAccountAuthenticator()


# =============================================================================
# INSTRUCTIONS D'UTILISATION
# =============================================================================
"""
ÉTAPE 1 : Créer un Service Account dans Google Cloud Console
============================================================
1. Allez sur https://console.cloud.google.com/
2. Sélectionnez votre projet (ou créez-en un)
3. Dans le menu, allez dans "IAM & Admin" > "Service Accounts"
4. Cliquez sur "Create Service Account"
5. Donnez un nom (ex: "gmail-sender") et une description
6. Cliquez sur "Create and Continue"
7. Pas besoin de rôle spécifique, cliquez sur "Continue"
8. Cliquez sur "Done"

ÉTAPE 2 : Créer une clé JSON pour le Service Account
====================================================
1. Cliquez sur le Service Account que vous venez de créer
2. Allez dans l'onglet "Keys"
3. Cliquez sur "Add Key" > "Create new key"
4. Sélectionnez "JSON" et cliquez sur "Create"
5. Le fichier JSON sera téléchargé automatiquement
6. Placez ce fichier dans: /Users/paulo/SitesWeb/heron/heron/env/
7. Renommez-le en: gmail_service_account.json

ÉTAPE 3 : Activer la délégation de domaine (Domain-Wide Delegation)
===================================================================
1. Retournez sur la page du Service Account
2. Cliquez sur le Service Account
3. Développez "Show domain-wide delegation"
4. Cochez "Enable Google Workspace Domain-wide Delegation"
5. Cliquez sur "Save"
6. Notez le "Client ID" (un nombre comme 123456789012345678901)

ÉTAPE 4 : Autoriser le Service Account dans Google Workspace Admin
==================================================================
⚠️ CETTE ÉTAPE DOIT ÊTRE FAITE PAR L'ADMINISTRATEUR GOOGLE WORKSPACE ⚠️

1. L'admin doit aller sur https://admin.google.com/
2. Aller dans "Security" > "API Controls" > "Domain-wide Delegation"
   (ou "Sécurité" > "Contrôles des API" > "Délégation au niveau du domaine")
3. Cliquer sur "Add new" (ou "Ajouter")
4. Entrer le Client ID du Service Account (noté à l'étape 3)
5. Dans "OAuth Scopes", entrer: https://www.googleapis.com/auth/gmail.send
6. Cliquer sur "Authorize" (ou "Autoriser")

ÉTAPE 5 : Tester la connexion
=============================
cd /Users/paulo/SitesWeb/heron
source .venv/bin/activate
python -c "from apps.invoices.bin.api_gmail.auth_service_account import service_account_authenticator; print(service_account_authenticator.test_connection())"

Si le test retourne True, la configuration est correcte !

UTILISATION DANS LE CODE
========================
# Remplacez l'import de l'authenticator classique par celui du Service Account:

# Avant (OAuth2 classique):
# from apps.invoices.bin.api_gmail.auth import authenticator
# service = authenticator.get_gmail_service()

# Après (Service Account):
from apps.invoices.bin.api_gmail.auth_service_account import service_account_authenticator
service = service_account_authenticator.get_gmail_service()

# Le reste du code reste identique !
"""