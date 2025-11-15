# pylint: disable=E0401
"""
FR : Vues pour l'API de progression des emails
EN : Views for email progress API

Commentaire:
Ces vues permettent de récupérer la progression de l'envoi des emails
via une API JSON pour l'affichage en temps réel.

created at: 2025-01-10
created by: Paulo ALVES 
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

from heron.loggers import LOGGER_EMAIL

# Import conditionnel du modèle
try:
    from .models_progress import EmailSendProgress
except ImportError:
    # Si le modèle n'est pas encore migré
    EmailSendProgress = None


@require_http_methods(["GET"])
@login_required
def get_progress(request, job_id):
    """
    Récupère la progression d'un job d'envoi d'emails
    :param request: Request Django
    :param job_id: ID du job
    :return: JsonResponse avec les données de progression
    """
    if EmailSendProgress is None:
        return JsonResponse(
            {
                "error": "Le modèle EmailSendProgress n'est pas disponible. "
                "Veuillez exécuter les migrations."
            },
            status=500,
        )

    try:
        progress = EmailSendProgress.objects.get(job_id=job_id)

        # Vérifier que l'utilisateur a le droit de voir cette progression
        if progress.user != request.user and not request.user.is_staff:
            return JsonResponse(
                {"error": "Vous n'avez pas accès à cette progression"}, status=403
            )

        return JsonResponse({"success": True, "data": progress.to_dict()})

    except EmailSendProgress.DoesNotExist:
        return JsonResponse(
            {"error": "Job non trouvé", "job_id": job_id}, status=404
        )

    except Exception as error:
        LOGGER_EMAIL.exception("Erreur lors de la récupération de la progression")
        return JsonResponse({"error": str(error)}, status=500)


@require_http_methods(["GET"])
@login_required
def get_all_progress(request):
    """
    Récupère toutes les progressions pour l'utilisateur connecté
    :param request: Request Django
    :return: JsonResponse avec la liste des progressions
    """
    if EmailSendProgress is None:
        return JsonResponse(
            {
                "error": "Le modèle EmailSendProgress n'est pas disponible. "
                "Veuillez exécuter les migrations."
            },
            status=500,
        )

    try:
        # Récupère les 10 dernières progressions de l'utilisateur
        if request.user.is_staff:
            # Admin : voir toutes les progressions
            progressions = EmailSendProgress.objects.all()[:10]
        else:
            # Utilisateur : voir uniquement ses progressions
            progressions = EmailSendProgress.objects.filter(user=request.user)[:10]

        data = [progress.to_dict() for progress in progressions]

        return JsonResponse({"success": True, "data": data})

    except Exception as error:
        LOGGER_EMAIL.exception("Erreur lors de la récupération des progressions")
        return JsonResponse({"error": str(error)}, status=500)


@require_http_methods(["GET"])
@login_required
def get_active_progress(request):
    """
    Récupère les progressions actives (en cours ou en attente)
    :param request: Request Django
    :return: JsonResponse avec les progressions actives
    """
    if EmailSendProgress is None:
        return JsonResponse(
            {
                "error": "Le modèle EmailSendProgress n'est pas disponible. "
                "Veuillez exécuter les migrations."
            },
            status=500,
        )

    try:
        # Récupère les progressions actives
        if request.user.is_staff:
            progressions = EmailSendProgress.objects.filter(
                status__in=["pending", "in_progress"]
            )
        else:
            progressions = EmailSendProgress.objects.filter(
                user=request.user, status__in=["pending", "in_progress"]
            )

        data = [progress.to_dict() for progress in progressions]

        return JsonResponse({"success": True, "data": data, "count": len(data)})

    except Exception as error:
        LOGGER_EMAIL.exception("Erreur lors de la récupération des progressions actives")
        return JsonResponse({"error": str(error)}, status=500)


@require_http_methods(["DELETE"])
@csrf_exempt  # Pour les requêtes DELETE (ou utilisez CSRF token)
@login_required
def delete_progress(request, job_id):
    """
    Supprime une progression (uniquement si terminée ou échouée)
    :param request: Request Django
    :param job_id: ID du job
    :return: JsonResponse
    """
    if EmailSendProgress is None:
        return JsonResponse(
            {
                "error": "Le modèle EmailSendProgress n'est pas disponible. "
                "Veuillez exécuter les migrations."
            },
            status=500,
        )

    try:
        progress = EmailSendProgress.objects.get(job_id=job_id)

        # Vérifier les droits
        if progress.user != request.user and not request.user.is_staff:
            return JsonResponse(
                {"error": "Vous n'avez pas accès à cette progression"}, status=403
            )

        # Ne pas supprimer si en cours
        if progress.status in ["pending", "in_progress"]:
            return JsonResponse(
                {"error": "Impossible de supprimer un job en cours"}, status=400
            )

        progress.delete()
        return JsonResponse({"success": True, "message": "Progression supprimée"})

    except EmailSendProgress.DoesNotExist:
        return JsonResponse({"error": "Job non trouvé"}, status=404)

    except Exception as error:
        LOGGER_EMAIL.exception("Erreur lors de la suppression de la progression")
        return JsonResponse({"error": str(error)}, status=500)