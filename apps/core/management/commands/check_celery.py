"""Commande Django pour vérifier l'état des tâches Celery."""

from django.core.management.base import BaseCommand

from apps.core.utils.celery_utils import (
    get_active_tasks_list,
    get_celery_tasks_status,
    is_celery_available,
    wait_for_celery_idle,
)


class Command(BaseCommand):
    """Commande de contrôle des tâches Celery en cours."""

    help = "Vérifie les tâches Celery en cours"

    def add_arguments(self, parser):
        """Déclare l'option d'attente de la fin des tâches."""
        parser.add_argument(
            "--wait",
            action="store_true",
            help="Attendre que toutes les tâches soient terminées",
        )
        parser.add_argument(
            "--timeout",
            type=int,
            default=300,
            help="Timeout en secondes pour --wait (défaut: 300)",
        )
        parser.add_argument(
            "--details",
            action="store_true",
            help="Afficher les détails des tâches actives",
        )

    def handle(self, *_args, **options):
        """Point d'entrée : disponibilité, attente ou simple état des tâches."""
        if not is_celery_available():
            self.stdout.write(self.style.ERROR("❌ Aucun worker Celery disponible"))
            return

        if options["wait"]:
            self._wait_until_idle(options["timeout"])
            return

        status = get_celery_tasks_status()

        if not status["has_tasks"]:
            self.stdout.write(self.style.SUCCESS("✓ Aucune tâche en cours"))
            self.stdout.write(f"Workers actifs: {len(status['workers'])}")
            return

        self._write_status(status)

        if options["details"]:
            self._write_details()

    def _wait_until_idle(self, timeout):
        """Mode attente : bloque jusqu'à la fin des tâches ou le timeout."""
        self.stdout.write("⏳ Attente de la fin des tâches Celery...")
        success, remaining = wait_for_celery_idle(timeout=timeout, check_interval=2)

        if success:
            self.stdout.write(self.style.SUCCESS("✓ Toutes les tâches sont terminées"))
        else:
            self.stdout.write(
                self.style.WARNING(f"⚠ Timeout atteint: {remaining} tâche(s) encore en cours")
            )

    def _write_status(self, status):
        """Résumé des tâches en cours par état."""
        self.stdout.write(self.style.WARNING(f"⚠ {status['total']} tâche(s) en cours:"))
        self.stdout.write(f"  - Actives: {status['active']}")
        self.stdout.write(f"  - Planifiées: {status['scheduled']}")
        self.stdout.write(f"  - Réservées: {status['reserved']}")

    def _write_details(self):
        """Détail des tâches actives (option --details)."""
        tasks = get_active_tasks_list()

        if not tasks:
            return

        self.stdout.write("\n📋 Détails des tâches actives:")

        for task in tasks:
            self.stdout.write(f"  • {task['task_name']}")
            self.stdout.write(f"    Worker: {task['worker']}")
            self.stdout.write(f"    ID: {task['task_id']}")

            if task.get("time_start"):
                self.stdout.write(f"    Démarrée: {task['time_start']}")

            self.stdout.write("")
