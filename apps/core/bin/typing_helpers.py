"""Aides de rétrécissement de type pour mypy (plugin Django).

Elles remplacent les `assert` et rendent explicites les cas « impossibles » : une valeur absente
lève une erreur claire au lieu d'un AttributeError sur None.
"""

from django.core.exceptions import PermissionDenied
from django.http import HttpRequest

from apps.users.models import User


def required[T](value: T | None, label: str = "valeur") -> T:
    """Renvoie `value` en garantissant qu'elle n'est pas None (ValueError sinon)."""
    if value is None:
        raise ValueError(f"{label} absente")

    return value


def current_user(request: HttpRequest) -> User:
    """Utilisateur authentifié de la requête (PermissionDenied pour un anonyme)."""
    user = request.user

    if not isinstance(user, User):
        raise PermissionDenied("utilisateur non authentifié")

    return user
