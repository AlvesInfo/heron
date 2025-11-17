"""Commande Django pour vérifier l'état des tâches Celery"""
from django.core.management.base import BaseCommand
from apps.core.utils.celery_utils import (
    get_celery_tasks_status,
    get_active_tasks_list,
    is_celery_available,
    wait_for_celery_idle
)


class Command(BaseCommand):
    help = 'Vérifie les tâches Celery en cours'

    def add_arguments(self, parser):
        parser.add_argument(
            '--wait',
            action='store_true',
            help='Attendre que toutes les tâches soient terminées',
        )
        parser.add_argument(
            '--timeout',
            type=int,
            default=300,
            help='Timeout en secondes pour --wait (défaut: 300)',
        )
        parser.add_argument(
            '--details',
            action='store_true',
            help='Afficher les détails des tâches actives',
        )

    def handle(self, *args, **options):
        # Vérifier si Celery est disponible
        if not is_celery_available():
            self.stdout.write(
                self.style.ERROR('❌ Aucun worker Celery disponible')
            )
            return

        # Mode attente
        if options['wait']:
            self.stdout.write('⏳ Attente de la fin des tâches Celery...')
            success, remaining = wait_for_celery_idle(
                timeout=options['timeout'],
                check_interval=2
            )

            if success:
                self.stdout.write(
                    self.style.SUCCESS('✓ Toutes les tâches sont terminées')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠ Timeout atteint: {remaining} tâche(s) encore en cours'
                    )
                )
            return

        # Mode vérification simple
        status = get_celery_tasks_status()

        if not status['has_tasks']:
            self.stdout.write(
                self.style.SUCCESS('✓ Aucune tâche en cours')
            )
            self.stdout.write(
                f"Workers actifs: {len(status['workers'])}"
            )
            return

        # Il y a des tâches
        self.stdout.write(
            self.style.WARNING(
                f"⚠ {status['total']} tâche(s) en cours:"
            )
        )
        self.stdout.write(
            f"  - Actives: {status['active']}"
        )
        self.stdout.write(
            f"  - Planifiées: {status['scheduled']}"
        )
        self.stdout.write(
            f"  - Réservées: {status['reserved']}"
        )

        # Afficher les détails si demandé
        if options['details']:
            tasks = get_active_tasks_list()
            if tasks:
                self.stdout.write('\n📋 Détails des tâches actives:')
                for task in tasks:
                    self.stdout.write(
                        f"  • {task['task_name']}"
                    )
                    self.stdout.write(
                        f"    Worker: {task['worker']}"
                    )
                    self.stdout.write(
                        f"    ID: {task['task_id']}"
                    )
                    if task.get('time_start'):
                        self.stdout.write(
                            f"    Démarrée: {task['time_start']}"
                        )
                    self.stdout.write('')