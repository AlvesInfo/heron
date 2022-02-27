"""
Module de backend du modèle User
"""
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from apps.users.models import User


class HeronBackend:
    @staticmethod
    def get_user(user_id):

        try:
            return User.objects.get(pk=user_id)
        except ObjectDoesNotExist:
            return None


def authenticate(email=None, password=None):
    user_username = email
    usermodel = get_user_model()

    try:
        # on teste, l'éxistence de l'utilisateur :
        user = usermodel._default_manager.get_by_natural_key(user_username)

        if user.check_password(password):
            return user

    except ObjectDoesNotExist:
        return None

    return None
