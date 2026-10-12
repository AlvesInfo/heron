"""Management command pour initialiser tous les répertoires nécessaires au projet.

Usage:
    python manage.py init_directories

Ce command crée tous les répertoires définis dans les settings, ce qui peut être
utile lors du déploiement initial ou pour s'assurer que tous les répertoires existent.

created at: 2025-11-16
created by: Claude Code
"""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from heron.utils.directories import ensure_directory


class Command(BaseCommand):
    """Commande de création des répertoires définis dans les settings."""

    help = "Initialise tous les répertoires nécessaires pour le projet"

    def handle(self, *_args, **_options):
        """Crée tous les répertoires définis dans les settings."""
        self.stdout.write(self.style.MIGRATE_HEADING("Initialisation des répertoires..."))
        created_count = 0
        skipped_count = 0

        for dir_name, dir_path in self._directories_to_create():
            created = self._create(dir_name, dir_path)

            if created:
                created_count += 1
            elif created is False:
                skipped_count += 1

        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("Résumé:"))
        self.stdout.write(self.style.SUCCESS(f"  {created_count} répertoires créés"))
        self.stdout.write(self.style.WARNING(f"  {skipped_count} répertoires existaient déjà"))
        self.stdout.write(
            self.style.MIGRATE_HEADING(f"  Total: {created_count + skipped_count} répertoires")
        )
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Initialisation terminée avec succès!"))

    @staticmethod
    def _module_paths(module, excluded=()):
        """Constantes Path (nom en majuscules) d'un module de settings."""
        for attr_name in dir(module):
            attr_value = getattr(module, attr_name)

            if attr_name.isupper() and attr_name not in excluded and isinstance(attr_value, Path):
                yield attr_name, attr_value

    def _directories_to_create(self):
        """Liste (nom, chemin) de tous les répertoires déclarés par les settings."""
        # Import différé volontaire : les modules de settings sont lus à l'exécution de la commande
        from heron.settings import directories, suppliers  # noqa: PLC0415

        paths = [
            *self._module_paths(directories, excluded=("FILES_BASE_DIR",)),
            *self._module_paths(suppliers),
        ]

        if hasattr(settings, "LOG_DIR"):
            paths.append(("LOG_DIR", settings.LOG_DIR))

        # STATICFILES_DIRS est toujours défini par Django (vide par défaut)
        paths.extend(
            (f"STATICFILES_DIR_{i}", static_dir)
            for i, static_dir in enumerate(settings.STATICFILES_DIRS)
            if isinstance(static_dir, Path)
        )
        return paths

    def _create(self, dir_name, dir_path):
        """Crée le répertoire s'il manque ; True s'il a été créé, False s'il existait, None en erreur."""
        try:
            if dir_path.exists():
                return False

            ensure_directory(dir_path)
            self.stdout.write(self.style.SUCCESS(f"✓ Créé: {dir_name} -> {dir_path}"))

        except OSError as error:
            self.stdout.write(self.style.ERROR(f"✗ Erreur pour {dir_name}: {error}"))
            return None

        else:
            return True
