"""Utilitaires pour la gestion paresseuse des répertoires.

Ce module permet de définir des chemins de répertoires sans les créer immédiatement,
ce qui améliore significativement les performances au démarrage de Django.

Les répertoires sont créés uniquement quand ils sont réellement utilisés.

Created at: 2025-11-16
"""

from functools import cache
from pathlib import Path

# Cache en mémoire des répertoires déjà vérifiés/créés
_initialized_dirs: set[str] = set()


def ensure_directory(path: Path) -> Path:
    """Crée un répertoire seulement s'il n'a pas déjà été vérifié dans cette session.

    Utilise un cache en mémoire pour éviter les vérifications répétées.

    Args:
        path: Le chemin du répertoire à créer

    Returns:
        Le Path du répertoire créé

    Example:
        >>> from heron.utils.directories import ensure_directory
        >>> from django.conf import settings
        >>> ensure_directory(settings.MEDIA_DIR)
        >>> with open(settings.MEDIA_DIR / "file.txt", "w") as f:
        >>>     f.write("content")

    """
    path_str = str(path.resolve())

    if path_str not in _initialized_dirs:
        path.mkdir(parents=True, exist_ok=True)
        _initialized_dirs.add(path_str)

    return path


@cache
def get_files_base_dir() -> Path:
    """Retourne le répertoire de base des fichiers (mis en cache).

    Returns:
        Path vers le répertoire racine du projet

    """
    return Path(__file__).resolve().parent.parent.parent


def lazy_mkdir(relative_path: str) -> Path:
    """Retourne le Path résolu sans créer le répertoire.

    Le répertoire sera créé lors de la première utilisation via ensure_directory().

    Args:
        relative_path: Chemin relatif depuis la racine du projet

    Returns:
        Path résolu (mais le répertoire n'est pas créé)

    Example:
        >>> MEDIA_DIR = lazy_mkdir("files/media")
        >>> # Le répertoire n'existe pas encore
        >>> ensure_directory(MEDIA_DIR)
        >>> # Maintenant, il existe

    """
    return (get_files_base_dir() / relative_path).resolve()
