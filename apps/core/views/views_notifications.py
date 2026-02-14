"""
Vues API pour les notifications utilisateur
Endpoints JSON pour le dropdown cloche

created at: 2025-02-14
created by: Paulo ALVES
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required

from apps.core.bin.notifications import (
    get_all_notifications,
    get_unread_count,
    mark_notification_as_read,
    mark_all_as_read,
    delete_notification,
)


@login_required
@require_http_methods(["GET"])
def notifications_list(request):
    """
    Liste des notifications + compteur non lues

    URL: /core/notifications/
    Méthode: GET
    """
    limit = int(request.GET.get("limit", 50))
    notifications = get_all_notifications(request.user, limit=limit)
    unread_count = get_unread_count(request.user)

    return JsonResponse({
        "unread_count": unread_count,
        "notifications": [n.to_dict() for n in notifications],
    })


@login_required
@require_http_methods(["POST"])
def notification_mark_read(request, notification_uuid):
    """
    Marquer une notification comme lue

    URL: /core/notifications/mark-read/<uuid>/
    Méthode: POST
    """
    success = mark_notification_as_read(notification_uuid, request.user)

    if success:
        unread_count = get_unread_count(request.user)
        return JsonResponse({"success": True, "unread_count": unread_count})

    return JsonResponse({"error": "Notification non trouvée"}, status=404)


@login_required
@require_http_methods(["POST"])
def notification_mark_all_read(request):
    """
    Marquer toutes les notifications comme lues

    URL: /core/notifications/mark-all-read/
    Méthode: POST
    """
    mark_all_as_read(request.user)
    return JsonResponse({"success": True, "unread_count": 0})


@login_required
@require_http_methods(["POST"])
def notification_delete(request, notification_uuid):
    """
    Supprimer une notification

    URL: /core/notifications/delete/<uuid>/
    Méthode: POST
    """
    success = delete_notification(notification_uuid, request.user)

    if success:
        unread_count = get_unread_count(request.user)
        return JsonResponse({"success": True, "unread_count": unread_count})

    return JsonResponse({"error": "Notification non trouvée"}, status=404)
