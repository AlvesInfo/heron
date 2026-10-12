"""
FR : Vue d'accueil de l'application
EN : Application home view
"""
from django.shortcuts import render
from django.conf import settings


def home(request):
    """Page d'accueil : l'environnement (LOCAL / PRODUCTION) est affiché dans le gabarit"""
    context = {"environnement": settings.ENVIRONNEMENT}
    return render(request, "heron/home.html", context=context)
