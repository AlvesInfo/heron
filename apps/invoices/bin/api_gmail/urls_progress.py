# pylint: disable=E0401
"""
FR : URLs pour l'API de progression des emails
EN : URLs for email progress API

Commentaire:
Ces URLs doivent être incluses dans votre fichier urls.py principal

Dans votre apps/invoices/urls.py, ajoutez :

from apps.invoices.bin.api_gmail.urls_progress import urlpatterns as gmail_progress_urls

urlpatterns = [
    # ... vos URLs existantes ...
] + gmail_progress_urls

Ou utilisez include() :

path('api/gmail/', include('apps.invoices.bin.api_gmail.urls_progress')),

created at: 2025-01-10
created by: Paulo ALVES 
"""

from django.urls import path
from . import views_progress

# Namespace pour les URLs
app_name = "gmail_progress"

urlpatterns = [
    # Récupérer la progression d'un job spécifique
    path(
        "api/gmail/progress/<str:job_id>/",
        views_progress.get_progress,
        name="get_progress",
    ),
    # Récupérer toutes les progressions de l'utilisateur
    path(
        "api/gmail/progress/",
        views_progress.get_all_progress,
        name="get_all_progress",
    ),
    # Récupérer les progressions actives
    path(
        "api/gmail/progress/active/all/",
        views_progress.get_active_progress,
        name="get_active_progress",
    ),
    # Supprimer une progression
    path(
        "api/gmail/progress/<str:job_id>/delete/",
        views_progress.delete_progress,
        name="delete_progress",
    ),
]