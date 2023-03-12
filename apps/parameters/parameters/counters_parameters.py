# pylint: disable=E0401
"""
Fonctions paramètres et constantes pour les Compteurs
FR : Module des fonctions, paramètres et constantes pour les Compteurs
EN : Module of functions, parameters and constants for Counters

Commentaire:

created at: 2023-03-11
created by: Paulo ALVES

modified at: 2023-03-11
modified by: Paulo ALVES
"""
from typing import AnyStr, Any

import pendulum
from apps.book.models import Society
from apps.centers_clients.models import Maison


def get_pre_suf(name: AnyStr, attr_object: Any = None) -> str:
    """Retourne le texte de la attr_object souhaitée dans le préfix ou le suffix
    :param name: nom du préfix ou du suffix
    :param attr_object: attr_object à retrouver, soit une date, soit un tiers, soit un cct
    :return: le texte du préfix ou du suffix
    """
    if name == "AAAAMM":
        return (
            attr_object.format("YYYYMM", locale="fr")
            if attr_object
            else pendulum.now().format("YYYYMM", locale="fr")
        )

    if name == "AAAA-MM":
        return (
            attr_object.format("YYYY-MM", locale="fr")
            if attr_object
            else pendulum.now().format("YYYY-MM", locale="fr")
        )

    if name == "AAAA_MM":
        return (
            attr_object.format("YYYY_MM", locale="fr")
            if attr_object
            else pendulum.now().format("YYYY_MM", locale="fr")
        )

    if name == "AAAAMMDD":
        return (
            attr_object.format("YYYYMMDD", locale="fr")
            if attr_object
            else pendulum.now().format("YYYYMMDD", locale="fr")
        )

    if name == "AAAA-MM-DD":
        return (
            attr_object.format("YYYY-MM-DD", locale="fr")
            if attr_object
            else pendulum.now().format("YYYY-MM-DD", locale="fr")
        )

    if name == "AAAA_MM_DD":
        return (
            attr_object.format("YYYY_MM_DD", locale="fr")
            if attr_object
            else pendulum.now().format("YYYY_MM_DD", locale="fr")
        )

    if name == "TIERS":
        try:
            if not attr_object:
                return ""
            else:
                return str(
                    Society.objects.get(third_party_num=attr_object).third_party_num
                ).replace(" ", "")
        except Society.DoesNotExist:
            return ""

    if name.startswith("TIERS_"):
        try:
            if not attr_object:
                return "_".join(name.split("_")[1:])
            else:
                return (
                    str(Society.objects.get(third_party_num=attr_object).third_party_num).replace(
                        " ", ""
                    )
                    + "_"
                    + "_".join(name.split("_")[1:])
                )
        except Society.DoesNotExist:
            return name.split("_")[0]

    if "_TIERS" in name:
        try:
            if not attr_object:
                return "_".join(name.split("_")[:-1])
            else:
                return (
                    "_".join(name.split("_")[:-1])
                    + "_"
                    + str(Society.objects.get(third_party_num=attr_object).third_party_num).replace(
                        " ", ""
                    )
                )
        except Society.DoesNotExist:
            return name.split("_")[0]

    if name == "CCT":
        try:
            if not attr_object:
                return ""
            else:
                return str(Maison.objects.get(third_party_num=attr_object).cct.cct).replace(" ", "")
        except Maison.DoesNotExist:
            return ""

    if name.startswith("CCT_"):
        try:
            if not attr_object:
                return "_".join(name.split("_")[1:])
            else:
                return (
                    str(Maison.objects.get(third_party_num=attr_object).cct.cct).replace(" ", "")
                    + "_"
                    + "_".join(name.split("_")[1:])
                )
        except Maison.DoesNotExist:
            return name.split("_")[0]

    if "_CCT" in name:
        try:
            if not attr_object:
                return "_".join(name.split("_")[:-1])
            else:
                return (
                    "_".join(name.split("_")[:-1])
                    + "_"
                    + str(Maison.objects.get(third_party_num=attr_object).cct.cct).replace(" ", "")
                )
        except Maison.DoesNotExist:
            return name.split("_")[0]

    return name or ""
