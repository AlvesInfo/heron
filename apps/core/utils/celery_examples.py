"""
Exemples d'utilisation des utilitaires Celery dans votre code Django

Ces exemples montrent comment utiliser les fonctions de monitoring
dans différents contextes de votre application.
"""
from django.db import transaction
from apps.core.utils.celery_utils import (
    has_active_celery_tasks,
    get_celery_tasks_status,
    wait_for_celery_idle,
    get_active_tasks_list
)


# ============================================================================
# EXEMPLE 1: Vérifier avant de lancer un traitement lourd
# ============================================================================
def exemple_avant_traitement():
    """
    Vérifier qu'il n'y a pas de tâches en cours avant de lancer
    un nouveau traitement
    """
    if has_active_celery_tasks():
        print("⚠ Des tâches sont en cours, attente recommandée")
        return False

    print("✓ Aucune tâche en cours, on peut démarrer")
    # Lancer votre traitement ici
    return True


# ============================================================================
# EXEMPLE 2: Dans une vue avec vérification
# ============================================================================
def exemple_vue_avec_verification(request):
    """
    Vue qui vérifie l'état de Celery avant de déclencher une action
    """
    from django.http import JsonResponse

    # Vérifier si des tâches sont en cours
    status = get_celery_tasks_status()

    if status['has_tasks']:
        return JsonResponse({
            'success': False,
            'message': f"Impossible de démarrer: {status['total']} tâche(s) en cours",
            'tasks': status['total']
        }, status=409)  # Conflict

    # Déclencher votre traitement
    # your_celery_task.delay(...)

    return JsonResponse({
        'success': True,
        'message': 'Traitement démarré'
    })


# ============================================================================
# EXEMPLE 3: Attendre la fin des tâches avant une action critique
# ============================================================================
def exemple_attente_avant_action_critique():
    """
    Attendre que toutes les tâches soient terminées avant
    une opération critique (ex: maintenance, déploiement)
    """
    print("Vérification des tâches Celery en cours...")

    if not has_active_celery_tasks():
        print("✓ Aucune tâche en cours")
        return True

    print("⏳ Attente de la fin des tâches...")
    success, remaining = wait_for_celery_idle(timeout=300)

    if success:
        print("✓ Toutes les tâches sont terminées")
        # Faire l'opération critique ici
        return True
    else:
        print(f"⚠ Timeout: {remaining} tâche(s) encore en cours")
        return False


# ============================================================================
# EXEMPLE 4: Dans un signal Django
# ============================================================================
from django.db.models.signals import pre_save
from django.dispatch import receiver


@receiver(pre_save, sender='votre_app.VotreModele')
def exemple_signal_verification(sender, instance, **kwargs):
    """
    Vérifier l'état de Celery dans un signal Django
    avant de sauvegarder un modèle important
    """
    if instance.status == 'PROCESSING':
        # Vérifier qu'il n'y a pas de conflit avec d'autres tâches
        if has_active_celery_tasks():
            tasks = get_active_tasks_list()
            # Logique pour gérer les conflits potentiels
            print(f"Attention: {len(tasks)} tâche(s) en cours")


# ============================================================================
# EXEMPLE 5: Dans une commande Django management
# ============================================================================
from django.core.management.base import BaseCommand


class ExempleCommand(BaseCommand):
    help = 'Exemple de commande qui vérifie Celery'

    def handle(self, *args, **options):
        """Exemple d'utilisation dans une commande management"""

        # Vérifier l'état de Celery
        status = get_celery_tasks_status()

        if status['has_tasks']:
            self.stdout.write(
                self.style.WARNING(
                    f"⚠ {status['total']} tâche(s) en cours"
                )
            )

            # Afficher les détails
            tasks = get_active_tasks_list()
            for task in tasks:
                self.stdout.write(f"  - {task['task_name']}")

            # Demander confirmation
            confirm = input("Continuer quand même? (o/n): ")
            if confirm.lower() != 'o':
                self.stdout.write("Annulé")
                return
        else:
            self.stdout.write(
                self.style.SUCCESS("✓ Aucune tâche en cours")
            )

        # Continuer avec votre logique
        self.stdout.write("Démarrage du traitement...")


# ============================================================================
# EXEMPLE 6: Dans une tâche Celery elle-même
# ============================================================================
from celery import shared_task
import time
from apps.core.bin.clean_celery import clean_memory


@shared_task
@clean_memory
def exemple_task_qui_verifie():
    """
    Une tâche Celery qui vérifie si d'autres tâches sont en cours
    avant de s'exécuter (utile pour les tâches exclusives)
    """
    # Attendre un peu que les autres tâches se terminent
    max_attempts = 10
    attempt = 0

    while attempt < max_attempts:
        status = get_celery_tasks_status()
        # Ne compter que les autres tâches (pas celle-ci)
        if status['total'] <= 1:  # Seulement cette tâche
            break

        print(f"Attente... {status['total']-1} autre(s) tâche(s) en cours")
        time.sleep(5)
        attempt += 1

    if attempt >= max_attempts:
        print("⚠ Timeout: trop de tâches en cours")
        return False

    # Exécuter la logique de la tâche
    print("✓ Exécution de la tâche")
    return True


# ============================================================================
# EXEMPLE 7: API REST avec Django REST Framework
# ============================================================================
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status as http_status


class CeleryStatusAPIView(APIView):
    """
    API endpoint pour vérifier le statut de Celery
    GET /api/celery/status/
    """

    def get(self, request):
        """Retourne le statut des tâches Celery"""
        status = get_celery_tasks_status()
        return Response(status)


class CeleryIdleCheckAPIView(APIView):
    """
    API endpoint pour vérifier si Celery est idle
    GET /api/celery/is-idle/
    """

    def get(self, request):
        """Vérifie si Celery est idle"""
        is_idle = not has_active_celery_tasks()

        return Response({
            'is_idle': is_idle,
            'has_tasks': not is_idle
        })


# ============================================================================
# EXEMPLE 8: Middleware Django
# ============================================================================
class CeleryMonitoringMiddleware:
    """
    Middleware qui ajoute l'état de Celery dans les headers de réponse
    Utile pour le monitoring côté frontend
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Ajouter des headers avec l'état de Celery
        if request.user.is_staff:  # Seulement pour le staff
            status = get_celery_tasks_status()
            response['X-Celery-Tasks'] = status['total']
            response['X-Celery-Idle'] = 'true' if not status['has_tasks'] else 'false'

        return response


# ============================================================================
# EXEMPLE 9: Décorateur pour vues qui nécessitent Celery idle
# ============================================================================
from functools import wraps
from django.http import HttpResponseConflict


def require_celery_idle(view_func):
    """
    Décorateur qui bloque l'accès à une vue si des tâches Celery
    sont en cours
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if has_active_celery_tasks():
            return HttpResponseConflict(
                "Des tâches sont en cours. Veuillez réessayer plus tard."
            )
        return view_func(request, *args, **kwargs)
    return wrapper


# Usage du décorateur
@require_celery_idle
def exemple_vue_exclusive(request):
    """Vue qui nécessite que Celery soit idle"""
    # Votre logique ici
    pass


# ============================================================================
# EXEMPLE 10: Context manager pour exécution exclusive
# ============================================================================
class ExclusiveCeleryExecution:
    """
    Context manager qui attend que Celery soit idle avant d'exécuter
    """

    def __init__(self, timeout=300, raise_on_timeout=False):
        self.timeout = timeout
        self.raise_on_timeout = raise_on_timeout

    def __enter__(self):
        if has_active_celery_tasks():
            print("⏳ Attente de la fin des tâches Celery...")
            success, remaining = wait_for_celery_idle(timeout=self.timeout)

            if not success and self.raise_on_timeout:
                raise TimeoutError(
                    f"Timeout: {remaining} tâche(s) encore en cours"
                )

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


# Usage du context manager
def exemple_avec_context_manager():
    """Exemple d'utilisation du context manager"""
    with ExclusiveCeleryExecution(timeout=60, raise_on_timeout=True):
        # Votre code qui nécessite que Celery soit idle
        print("Exécution en cours...")
        # ...
