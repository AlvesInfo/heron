import logging

from django.shortcuts import render
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from axes.utils import reset

from apps.users.models import User
from apps.core.functions.functions_utilitaires import get_client_ip

logger = logging.getLogger("connexion")


def reactivate(request, uidb64, token):
    """Fonction de réactivation du compte suites à des tentatives de connexions sur ce compte
    :param request: request
    :param uidb64: uidb64 - pk de l'user
    :param token: token pour vérifier la connexion
    :return: url
    """
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and PasswordResetTokenGenerator().check_token(user, token):
        # Reset des tentatives de connexions
        reset(username=user.email)

        logger.info(f"Réactivation : mail : {user.email} - " f"ip : {get_client_ip(request)}")

        return render(request, "heron/account_reactivate_done.html", {"user": user})

    return render(request, "heron/account_reactivate_invalid.html")


def logout_email(request):
    """Page affichée après la déconnexion demandée depuis un email"""
    return render(request, "heron/logout_email.html")
