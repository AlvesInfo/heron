"""
Management command pour initialiser tous les répertoires nécessaires au projet.

Usage:
    python manage.py init_directories

Ce command crée tous les répertoires définis dans les settings, ce qui peut être
utile lors du déploiement initial ou pour s'assurer que tous les répertoires existent.

created at: 2025-11-16
created by: Claude Code  
"""
from django.core.management.base import BaseCommand
from pathlib import Path
from django.conf import settings
from heron.utils.directories import ensure_directory


class Command(BaseCommand):
    help = 'Initialise tous les répertoires nécessaires pour le projet'

    def handle(self, *args, **options):
        """Crée tous les répertoires définis dans les settings"""
        
        directories_to_create = []
        
        # Importation des modules settings
        from heron.settings import directories, suppliers
        
        # Collecte de tous les paths depuis directories.py
        for attr_name in dir(directories):
            if attr_name.isupper() and not attr_name.startswith('_'):
                attr_value = getattr(directories, attr_name)
                if isinstance(attr_value, Path) and attr_name not in ['FILES_BASE_DIR']:
                    directories_to_create.append((attr_name, attr_value))
        
        # Collecte de tous les paths depuis suppliers.py
        for attr_name in dir(suppliers):
            if attr_name.isupper() and not attr_name.startswith('_'):
                attr_value = getattr(suppliers, attr_name)
                if isinstance(attr_value, Path):
                    directories_to_create.append((attr_name, attr_value))
        
        # Ajout du LOG_DIR
        if hasattr(settings, 'LOG_DIR'):
            directories_to_create.append(('LOG_DIR', settings.LOG_DIR))
        
        # Ajout des STATICFILES_DIRS
        if hasattr(settings, 'STATICFILES_DIRS'):
            for i, static_dir in enumerate(settings.STATICFILES_DIRS):
                if isinstance(static_dir, Path):
                    directories_to_create.append((f'STATICFILES_DIR_{i}', static_dir))
        
        # Création des répertoires
        created_count = 0
        skipped_count = 0
        
        self.stdout.write(self.style.MIGRATE_HEADING('Initialisation des répertoires...'))
        
        for dir_name, dir_path in directories_to_create:
            try:
                if not dir_path.exists():
                    ensure_directory(dir_path)
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Créé: {dir_name} -> {dir_path}')
                    )
                    created_count += 1
                else:
                    self.stdout.write(
                        self.style.WARNING(f'- Existe: {dir_name} -> {dir_path}')
                    )
                    skipped_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Erreur pour {dir_name}: {e}')
                )
        
        # Résumé
        self.stdout.write('')
        self.stdout.write(self.style.MIGRATE_HEADING('Résumé:'))
        self.stdout.write(self.style.SUCCESS(f'  {created_count} répertoires créés'))
        self.stdout.write(self.style.WARNING(f'  {skipped_count} répertoires existaient déjà'))
        self.stdout.write(self.style.MIGRATE_HEADING(f'  Total: {created_count + skipped_count} répertoires'))
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Initialisation terminée avec succès!'))
