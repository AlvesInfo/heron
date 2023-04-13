"""
Module context_processors de django, pour alimenter l'ensemble des templates
    Date de création : 02/11/2019
    Créateur : Paulo ALVES
    Date de modification : 02/11/2019
    Correcteur : Paulo ALVES
"""

from datetime import date
from collections import OrderedDict
from pathlib import Path

from django.conf import settings
from django.contrib.sites.models import Site
from django.contrib.auth.models import Group
from apps.users.models import AuthGroupName


def debug(request):
    if request:
        ...
    return {"environnement_debug": settings.DEBUG}


def title(request):
    """Retourne le dictionnaire de context avec le titre de l'application
        :param request: object request
        :return: context dict
    """
    dic = {}

    if request:
        dic = {"title": "HERON"}

    return dic


def user_group(request):
    """Retourne le dictionnaire de context du groupe auquel appartient l'user
        :param request: object request
        :return: context dict
    """
    dic = {"user_group": tuple(request.user.groups.values_list("name", flat=True))}
    return dic


def groups_processor(request):
    """Retourne le dictionnaire de context du nom des groupes
        :param request: object request
        :return: context dict
    """
    dic = {"groups": []}

    if request:
        rows_groupes = Group.objects.all().values_list("name")
        groupes = [r[0] for r in rows_groupes]
        dic = {"groups": groupes}
    return dic


def groupes_processor(request):
    """Retourne le dictionnaire de context des groupes auquel appartient l'user
        :param request: object request
        :return: context dict
    """
    if request.user.is_superuser:
        rows_groupes = AuthGroupName.objects.exclude(
            group__name__iexact="Admin"
        ).values_list("group__name", "group_name")

    elif str(request.user) == "AnonymousUser":
        rows_groupes = {}

    else:
        rows_groupes = (
            AuthGroupName.objects.filter(group__user=request.user)
            .exclude(group__name__iexact="Admin")
            .values_list("group__name", "group_name")
        )

    groupes = {g: n for g, n in rows_groupes}
    groupes = OrderedDict(sorted(groupes.items(), key=lambda t: t[1]))
    dic = {"groupes": groupes}
    templates_path = Path(settings.PROJECT_DIR) / "templates/heron"

    for groupe in groupes.keys():
        file_groupe = templates_path / f"{groupe}.html"
        if not file_groupe.is_file():
            with file_groupe.open("w"):
                pass

    return dic


def date_du_jour(request):
    """Retourne le dictionnaire de context la date du jour
        :param request: object request
        :return: context dict
    """
    dic = {}

    if request:
        dic = {"date_du_jour": date.today()}

    return dic


def annee_du_jour(request):
    """Retourne le dictionnaire de context l'année de la date du jour
        :param request: object request
        :return: context dict
    """
    dic = {}

    if request:
        dic = {"annee_du_jour": date.today().year}

    return dic


def domain_site(request):
    """Retourne le domaine du site
        :return: context dict
    """
    return {"domain_site": f"http://{Site.objects.get_current().domain}"}


def domain_debug(request):
    """Retourne le domaine du site
        :return: context dict
    """
    return {"domain_debug": "http://127.0.0.1:8000"}


def user_paulo(request):
    """Retourne si l'user est paulo"""
    return request.user.email == "paulo@alves.ovh"
