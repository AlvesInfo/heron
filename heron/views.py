import logging
import time

from django.shortcuts import render, redirect, reverse
from django.conf import settings
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.translation import gettext_lazy as _
from axes.utils import reset

from apps.users.models import User
from apps.core.functions.functions_utilitaires import get_client_ip
from heron.forms import ModalForms

logger = logging.getLogger("connexion")

start_thread = 0


def home(request):
    global start_thread
    context = {
        "environnement": settings.ENVIRONNEMENT,
    }
    return render(request, "heron/home.html", context=context)


def import_edi(request):
    from apps.edi.loops.imports_loop_pool import main

    global start_thread
    start = time.time()
    main()
    start_thread = time.time() - start
    return redirect("home")


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
    return render(request, "heron/logout_email.html")


from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def modals_views(request):
    form = ModalForms(request.POST or None)

    if request.method == "POST" and form.is_valid():
        return render(request, "heron/base_modals.html", form.cleaned_data)

    return redirect(reverse("projets:details_projet", args=[3]))
