import logging
import time

from django.shortcuts import render
from django.conf import settings

logger = logging.getLogger("connexion")

start_thread = 0


def home(request):
    global start_thread
    context = {
        "environnement": settings.ENVIRONNEMENT,
    }
    return render(request, "heron/home.html", context=context)
