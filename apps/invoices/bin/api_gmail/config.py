# pylint: disable=E0401
"""
FR : Configuration pour l'API Gmail
EN : Configuration for Gmail API

Commentaire:
Ce module lit la configuration depuis le fichier YAML situé dans heron/env/

created at: 2025-01-10
created by: Paulo ALVES
"""

import os
import sys
import platform
from pathlib import Path
from typing import Dict, Any
import yaml

from apps.core.functions.functions_setups import settings

# Répertoire contenant le fichier de configuration YAML
ENV_DIR = Path(settings.PROJECT_DIR) / "env"
CONFIG_FILE = ENV_DIR / "gmail_api_config.yaml"


class GmailConfig:
    """Classe pour gérer la configuration de l'API Gmail"""

    def __init__(self, config_file: Path = CONFIG_FILE):
        """
        Initialise la configuration
        :param config_file: Chemin vers le fichier de configuration YAML
        """
        self.config_file = config_file
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self):
        """Charge la configuration depuis le fichier YAML"""
        if not self.config_file.exists():
            raise FileNotFoundError(
                f"Le fichier de configuration {self.config_file} n'existe pas. "
                f"Veuillez créer ce fichier avec les paramètres nécessaires."
            )

        try:
            with open(self.config_file, "r", encoding="utf-8") as file:
                self._config = yaml.safe_load(file)
        except yaml.YAMLError as error:
            raise ValueError(
                f"Erreur lors de la lecture du fichier de configuration YAML: {error}"
            ) from error

    def get(self, key: str, default: Any = None) -> Any:
        """
        Récupère une valeur de configuration
        :param key: Clé de configuration (peut être un chemin avec des points, ex: "oauth2.client_id")
        :param default: Valeur par défaut si la clé n'existe pas
        :return: Valeur de configuration
        """
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value

    # ===== PROPRIÉTÉS OAUTH2 =====
    @property
    def oauth2_client_id(self) -> str:
        """Client ID OAuth2"""
        return self.get("oauth2.client_id", "")

    @property
    def oauth2_client_secret(self) -> str:
        """Client Secret OAuth2"""
        return self.get("oauth2.client_secret", "")

    @property
    def oauth2_redirect_uris(self) -> list:
        """URIs de redirection OAuth2"""
        return self.get("oauth2.redirect_uris", ["http://localhost"])

    @property
    def oauth2_auth_uri(self) -> str:
        """URL d'autorisation OAuth2"""
        return self.get("oauth2.auth_uri", "https://accounts.google.com/o/oauth2/auth")

    @property
    def oauth2_token_uri(self) -> str:
        """URL de token OAuth2"""
        return self.get("oauth2.token_uri", "https://oauth2.googleapis.com/token")

    # ===== PROPRIÉTÉS SCOPES =====
    @property
    def scopes(self) -> list:
        """Scopes Gmail API"""
        return self.get("scopes", ["https://www.googleapis.com/auth/gmail.send"])

    # ===== PROPRIÉTÉS EXPÉDITEUR =====
    @property
    def sender_email(self) -> str:
        """Email de l'expéditeur"""
        return self.get("sender.email", "")

    @property
    def sender_name(self) -> str:
        """Nom de l'expéditeur"""
        return self.get("sender.name", "")

    # ===== PROPRIÉTÉS RATE LIMITING =====
    @property
    def max_per_second(self) -> int:
        """Nombre maximum d'emails par seconde"""
        return self.get("rate_limiting.max_per_second", 5)

    @property
    def max_per_minute(self) -> int:
        """Nombre maximum d'emails par minute"""
        return self.get("rate_limiting.max_per_minute", 100)

    @property
    def batch_size(self) -> int:
        """Taille des batches"""
        return self.get("rate_limiting.batch_size", 50)

    @property
    def delay_between_batches(self) -> float:
        """Délai entre les batches (en secondes)"""
        return self.get("rate_limiting.delay_between_batches", 2)

    # ===== PROPRIÉTÉS RETRY =====
    @property
    def max_retries(self) -> int:
        """Nombre maximum de tentatives"""
        return self.get("retry.max_retries", 3)

    @property
    def retry_delay(self) -> int:
        """Délai entre les tentatives (en secondes)"""
        return self.get("retry.retry_delay", 5)

    @property
    def retry_backoff(self) -> int:
        """Multiplicateur du délai (backoff exponentiel)"""
        return self.get("retry.retry_backoff", 2)

    @property
    def max_retry_delay(self) -> int:
        """Délai maximum entre les tentatives (en secondes)"""
        return self.get("retry.max_retry_delay", 60)

    # ===== PROPRIÉTÉS TIMEOUTS =====
    @property
    def http_timeout(self) -> int:
        """Timeout pour les requêtes HTTP (en secondes)"""
        return self.get("timeouts.http_timeout", 30)

    @property
    def auth_timeout(self) -> int:
        """Timeout pour l'authentification (en secondes)"""
        return self.get("timeouts.auth_timeout", 60)

    # ===== PROPRIÉTÉS CHEMINS =====
    @property
    def credentials_file_name(self) -> str:
        """Nom du fichier de credentials"""
        return self.get("paths.credentials_file", "gmail_credentials.json")

    @property
    def token_file_name(self) -> str:
        """Nom du fichier de token"""
        return self.get("paths.token_file", "gmail_token.json")

    @property
    def credentials_file_path(self) -> Path:
        """Chemin complet vers le fichier de credentials"""
        return ENV_DIR / self.credentials_file_name

    @property
    def token_file_path(self) -> Path:
        """Chemin complet vers le fichier de token"""
        return ENV_DIR / self.token_file_name

    # ===== PROPRIÉTÉS LOGGING =====
    @property
    def log_level(self) -> str:
        """Niveau de log"""
        return self.get("logging.level", "INFO")

    @property
    def debug(self) -> bool:
        """Mode debug"""
        return self.get("logging.debug", False)

    # ===== PROPRIÉTÉS AVANCÉES =====
    @property
    def use_batch_mode(self) -> bool:
        """Utiliser le mode batch"""
        return self.get("advanced.use_batch_mode", True)

    @property
    def check_quotas(self) -> bool:
        """Vérifier les quotas"""
        return self.get("advanced.check_quotas", True)

    @property
    def save_draft_on_failure(self) -> bool:
        """Sauvegarder en brouillon en cas d'échec"""
        return self.get("advanced.save_draft_on_failure", False)

    def get_oauth2_credentials_dict(self) -> Dict[str, Any]:
        """
        Retourne un dictionnaire au format attendu par google-auth
        :return: Dictionnaire de credentials
        """
        return {
            "installed": {
                "client_id": self.oauth2_client_id,
                "client_secret": self.oauth2_client_secret,
                "redirect_uris": self.oauth2_redirect_uris,
                "auth_uri": self.oauth2_auth_uri,
                "token_uri": self.oauth2_token_uri,
                "auth_provider_x509_cert_url": self.get(
                    "oauth2.auth_provider_x509_cert_url",
                    "https://www.googleapis.com/oauth2/v1/certs",
                ),
            }
        }


# Instance globale de la configuration
config = GmailConfig()