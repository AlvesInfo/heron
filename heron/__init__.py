# TODO : Vérification à faire que le prix de la facture
#       ne depasse pas le prix des prix de ventes déterminés
#       dans la table apps.articles.models import SellingPrice
from .celery import app as celery_app

__all__ = ('celery_app',)
