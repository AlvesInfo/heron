# pylint: disable=E0401
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
from heron.settings.base import TYPE_OF_BASE


def debug(request):
    """For debug"""
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
        rows_groupes = AuthGroupName.objects.exclude(group__name__iexact="Admin").values_list(
            "group__name", "group_name"
        )

    elif str(request.user) == "AnonymousUser":
        rows_groupes = {}

    else:
        rows_groupes = (
            AuthGroupName.objects.filter(group__user=request.user)
            .exclude(group__name__iexact="Admin")
            .values_list("group__name", "group_name")
        )

    groupes = dict(rows_groupes)
    groupes = OrderedDict(sorted(groupes.items(), key=lambda t: t[1]))
    dic = {"groupes": groupes}
    templates_path = Path(settings.PROJECT_DIR) / "templates/heron"

    for groupe in groupes.keys():
        file_groupe = templates_path / f"{groupe}.html"
        if not file_groupe.is_file():
            with file_groupe.open("w"):
                pass

    return dic


def in_acuitis(reqquest):
    """
    Retoune True si l'user appartient à la centrale fille Acuitis
    :param reqquest: request au sens django
    :return: bool
    """
    centers_list = []

    try:
        centers_list = reqquest.user.code_child_center.split("|")
    except AttributeError:
        # 'AnonymousUser' object has no attribute 'code_child_center'
        ...

    return {"in_acuitis": "ACF" in centers_list or "*" in centers_list}


def in_ari(reqquest):
    """
    Retoune True si l'user appartient à la centrale fille ARI
    :param reqquest: request au sens django
    :return: bool
    """
    centers_list = []

    try:
        centers_list = reqquest.user.code_child_center.split("|")
    except AttributeError:
        # 'AnonymousUser' object has no attribute 'code_child_center'
        ...

    return {"in_ari": "ARI" in centers_list or "*" in centers_list}


def in_do(reqquest):
    """
    Retoune True si l'user appartient à la centrale fille ARI
    :param reqquest: request au sens django
    :return: bool
    """
    centers_list = []

    try:
        centers_list = reqquest.user.code_child_center.split("|")
    except AttributeError:
        # 'AnonymousUser' object has no attribute 'code_child_center'
        ...

    return {"in_do": "DO" in centers_list or "*" in centers_list}


def in_ga(reqquest):
    """
    Retoune True si l'user appartient à la centrale fille Grand Audition
    :param reqquest: request au sens django
    :return: bool
    """
    centers_list = []

    try:
        centers_list = reqquest.user.code_child_center.split("|")
    except AttributeError:
        # 'AnonymousUser' object has no attribute 'code_child_center'
        ...

    return {"in_ga": "GAF" in centers_list or "*" in centers_list}


def in_maa(reqquest):
    """
    Retoune True si l'user appartient à la centrale fille MAA
    :param reqquest: request au sens django
    :return: bool
    """
    centers_list = []

    try:
        centers_list = reqquest.user.code_child_center.split("|")
    except AttributeError:
        # 'AnonymousUser' object has no attribute 'code_child_center'
        ...

    return {"in_maa": "MAA" in centers_list or "*" in centers_list}


def in_unisson(reqquest):
    """
    Retoune True si l'user appartient à la centrale fille Unisson
    :param reqquest: request au sens django
    :return: bool
    """
    centers_list = []

    try:
        centers_list = reqquest.user.code_child_center.split("|")
    except AttributeError:
        # 'AnonymousUser' object has no attribute 'code_child_center'
        ...

    return {"in_unisson": "UNI" in centers_list or "*" in centers_list}


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


def domain_site(_):
    """Retourne le domaine du site
    :return: context dict
    """
    return {"domain_site": f"http://{Site.objects.get_current().domain}"}


def domain_debug(_):
    """Retourne le domaine du site
    :return: context dict
    """
    return {"domain_debug": "http://127.0.0.1:8000"}


def user_paulo(request):
    """Retourne si l'user est paulo"""
    try:
        user_mail = request.user.email
    except AttributeError:
        user_mail = ""

    return {"user_paulo": user_mail == "paulo@alves.ovh"}


def type_of_base(_):
    """Retourne le texte si l'on est dans la base de test formation"""
    return {"type_of_base": TYPE_OF_BASE}
