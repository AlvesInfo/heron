# pylint: disable=E0401,R0913
"""
FR : Client HTTP du serveur Factur-X (projet facturx_server, API de facturx-fr).
     heron ne peut pas importer facturx-fr (Python 3.12 / Pydantic v2) : la génération
     est déléguée au micro-service via son API, avec la seule dépendance ``requests``.
EN : HTTP client for the Factur-X server (facturx_server project, facturx-fr API).

Commentaire:

created at: 2026-10-10
created by: Paulo ALVES

modified at: 2026-10-10
modified by: Paulo ALVES
"""
import json
from typing import Any, AnyStr, Dict, List, Optional

import requests
from django.conf import settings

from heron.loggers import LOGGER_INVOICES


class FacturXClientError(Exception):
    """Erreur renvoyée par le serveur Factur-X ou erreur de communication"""

    def __init__(self, message: str, status: Optional[int] = None, details: Any = None):
        super().__init__(message)
        self.message = message
        self.status = status
        self.details = details

    def __str__(self) -> str:
        text = self.message
        if self.status is not None:
            text = f"[{self.status}] {text}"
        if self.details:
            text = f"{text} - {self._format_details(self.details)}"
        return text

    @staticmethod
    def _format_details(details: Any) -> str:
        """Formate les détails (erreurs Pydantic ou schématron) en texte lisible"""
        if isinstance(details, list):
            lines: List[str] = []
            for detail in details[:20]:
                if isinstance(detail, dict):
                    loc = ".".join(str(part) for part in detail.get("loc", []))
                    lines.append(f"{loc} : {detail.get('msg', detail)}")
                else:
                    lines.append(str(detail))
            if len(details) > 20:
                lines.append(f"... ({len(details) - 20} erreurs supplémentaires)")
            return " | ".join(lines)
        return str(details)


class FacturXClient:
    """Client de l'API HTTP de génération Factur-X"""

    def __init__(
        self,
        base_url: Optional[AnyStr] = None,
        api_key: Optional[AnyStr] = None,
        profile: Optional[AnyStr] = None,
        timeout: Optional[int] = None,
        validate: Optional[bool] = None,
    ):
        self.base_url = str(base_url or settings.FACTURX_SERVER_URL).rstrip("/")
        self.api_key = str(api_key if api_key is not None else settings.FACTURX_API_KEY)
        self.profile = str(profile or settings.FACTURX_PROFILE)
        self.timeout = int(timeout or settings.FACTURX_TIMEOUT)
        self.validate = settings.FACTURX_VALIDATE if validate is None else bool(validate)
        self.session = requests.Session()

    @property
    def headers(self) -> Dict[str, str]:
        """En-têtes d'authentification"""
        return {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

    def _url(self, path: str) -> str:
        return f"{self.base_url}/facturx/{path.lstrip('/')}"

    @staticmethod
    def _raise_for_error(response: requests.Response) -> None:
        """Convertit une réponse en erreur si le statut n'est pas 2xx"""
        if response.ok:
            return

        try:
            payload = response.json()
        except ValueError:
            payload = {}

        raise FacturXClientError(
            payload.get("error") or f"Erreur HTTP {response.status_code}",
            status=response.status_code,
            details=payload.get("details"),
        )

    def health(self) -> Dict[str, Any]:
        """Vérifie que le serveur répond et renvoie ses informations"""
        try:
            response = self.session.get(
                self._url("health/"), headers=self.headers, timeout=self.timeout
            )
        except requests.RequestException as error:
            raise FacturXClientError(
                f"Serveur Factur-X injoignable ({self.base_url}) : {error}"
            ) from error

        self._raise_for_error(response)
        return response.json()

    def is_available(self) -> bool:
        """Renvoie True si le serveur est joignable et la clé acceptée"""
        try:
            return self.health().get("status") == "ok"
        except FacturXClientError as error:
            LOGGER_INVOICES.warning(f"Serveur Factur-X indisponible : {error}")
            return False

    def generate(
        self,
        invoice: Dict[str, Any],
        pdf_bytes: bytes,
        profile: Optional[AnyStr] = None,
        validate: Optional[bool] = None,
        file_name: AnyStr = "facture.pdf",
    ) -> bytes:
        """
        Génère le PDF Factur-X d'une facture
        :param invoice: facture au format JSON-compatible (schéma facturx_fr.models.Invoice)
        :param pdf_bytes: contenu du PDF source
        :param profile: profil Factur-X (défaut settings.FACTURX_PROFILE)
        :param validate: valider le XML avant embarquement
        :param file_name: nom du fichier PDF transmis
        :return: contenu du PDF Factur-X
        """
        should_validate = self.validate if validate is None else validate
        data = {
            "invoice": json.dumps(invoice, default=str, ensure_ascii=False),
            "profile": str(profile or self.profile),
            "validate": "true" if should_validate else "false",
            "output": "pdf",
        }
        files = {"pdf": (str(file_name), pdf_bytes, "application/pdf")}

        try:
            response = self.session.post(
                self._url("generate/"),
                headers=self.headers,
                data=data,
                files=files,
                timeout=self.timeout,
            )
        except requests.RequestException as error:
            raise FacturXClientError(
                f"Serveur Factur-X injoignable ({self.base_url}) : {error}"
            ) from error

        self._raise_for_error(response)

        content = response.content
        if not content.startswith(b"%PDF"):
            raise FacturXClientError(
                "Réponse inattendue du serveur Factur-X (pas un PDF)",
                status=response.status_code,
            )

        return content
