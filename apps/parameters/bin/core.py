# pylint: disable=E0401,E1101
"""
FR : Module core des parametrages
EN : Core module parameters

Commentaire:

created at: 2022-12-27
created by: Paulo ALVES

modified at: 2022-12-27
modified by: Paulo ALVES
"""
from typing import Any, AnyStr, Dict

import pendulum
from django_celery_results.models import TaskResult

from apps.core.exceptions import LaunchDoesNotExistsError
from apps.core.functions.functions_utilitaires import get_module_object
from apps.book.models import Society
from apps.centers_clients.models import Maison
from apps.parameters.models import ActionInProgress, InvoiceFunctions, Counter, CounterNums


def get_pre_suf(name: AnyStr, attr_instance: Any = None) -> str:
    """Retourne le texte de la attr_instance souhaitée dans le préfix ou le suffix
    :param name: nom du préfix ou du suffix
    :param attr_instance: attr_instance à retrouver, soit une date, soit un tiers, soit un cct
    :return: le texte du préfix ou du suffix
    """
    if name == "AAAAMM":
        return (
            attr_instance.format("YYYYMM", locale="fr")
            if attr_instance
            else pendulum.now().format("YYYYMM", locale="fr")
        )

    if name == "AAAA-MM":
        return (
            attr_instance.format("YYYY-MM", locale="fr")
            if attr_instance
            else pendulum.now().format("YYYY-MM", locale="fr")
        )

    if name == "AAAA_MM":
        return (
            attr_instance.format("YYYY_MM", locale="fr")
            if attr_instance
            else pendulum.now().format("YYYY_MM", locale="fr")
        )

    if name == "AAAAMMDD":
        return (
            attr_instance.format("YYYYMMDD", locale="fr")
            if attr_instance
            else pendulum.now().format("YYYYMMDD", locale="fr")
        )

    if name == "AAAA-MM-DD":
        return (
            attr_instance.format("YYYY-MM-DD", locale="fr")
            if attr_instance
            else pendulum.now().format("YYYY-MM-DD", locale="fr")
        )

    if name == "AAAA_MM_DD":
        return (
            attr_instance.format("YYYY_MM_DD", locale="fr")
            if attr_instance
            else pendulum.now().format("YYYY_MM_DD", locale="fr")
        )

    if name == "TIERS":
        try:
            if not attr_instance:
                return ""
            else:
                return str(
                    Society.objects.get(third_party_num=attr_instance).third_party_num
                ).replace(" ", "")
        except Society.DoesNotExist:
            return ""

    if name.startswith("TIERS_"):
        try:
            if not attr_instance:
                return "_".join(name.split("_")[1:])
            else:
                return (
                    str(Society.objects.get(third_party_num=attr_instance).third_party_num).replace(
                        " ", ""
                    )
                    + "_"
                    + "_".join(name.split("_")[1:])
                )
        except Society.DoesNotExist:
            return name.split("_")[0]

    if "_TIERS" in name:
        try:
            if not attr_instance:
                return "_".join(name.split("_")[:-1])
            else:
                return (
                    "_".join(name.split("_")[:-1])
                    + "_"
                    + str(
                        Society.objects.get(third_party_num=attr_instance).third_party_num
                    ).replace(" ", "")
                )
        except Society.DoesNotExist:
            return name.split("_")[0]

    if name == "CCT":
        try:
            if not attr_instance:
                return ""
            else:
                return str(Maison.objects.get(third_party_num=attr_instance).cct.cct).replace(
                    " ", ""
                )
        except Maison.DoesNotExist:
            return ""

    if name.startswith("CCT_"):
        try:
            if not attr_instance:
                return "_".join(name.split("_")[1:])
            else:
                return (
                    str(Maison.objects.get(third_party_num=attr_instance).cct.cct).replace(" ", "")
                    + "_"
                    + "_".join(name.split("_")[1:])
                )
        except Maison.DoesNotExist:
            return name.split("_")[0]

    if "_CCT" in name:
        try:
            if not attr_instance:
                return "_".join(name.split("_")[:-1])
            else:
                return (
                    "_".join(name.split("_")[:-1])
                    + "_"
                    + str(Maison.objects.get(third_party_num=attr_instance).cct.cct).replace(
                        " ", ""
                    )
                )
        except Maison.DoesNotExist:
            return name.split("_")[0]

    return name or ""


def get_action(action: AnyStr = "import_edi_invoices"):
    """Récupération de l'état d'action"""
    # action_dict = {"action": "comment", ...}
    action_dict = {
        "import_edi_invoices": "Executable pour l'import des fichiers edi des factures founisseurs",
        "generate_invoices": "génération de la facturation",
    }

    # Si l'action n'existe pas on la créée
    try:
        action = ActionInProgress.objects.get(action=action)
        print("GET ACTION")
    except ActionInProgress.DoesNotExist:
        action = ActionInProgress(
            action=action,
            comment=action_dict.get(action),
        )
        action.save()
        print("EXCEPT")

    return action


def get_in_progress():
    """Renvoi si un process d'intégration edi est en cours"""
    try:
        in_action_object = ActionInProgress.objects.get(action="import_edi_invoices")
        in_action = in_action_object.in_progress

        # On contrôle si une tâche est réellement en cours pour éviter les faux positifs
        if in_action:
            celery_tasks = TaskResult.objects.filter(
                task_name="apps.edi.tasks.start_edi_import"
            ).exclude(status__in=["SUCCESS", "FAILURE"])
            in_action = celery_tasks.exists()

    except ActionInProgress.DoesNotExist:
        in_action = False

    return in_action


def get_object(task_to_launch: AnyStr):
    """Retourne la fonction à lancer
    :param task_to_launch: Tâche à lancer
    :return:
    """
    try:
        function_object = InvoiceFunctions.objects.get(function_name=task_to_launch)
        func = get_module_object(function_object.function)

    except (AttributeError, InvoiceFunctions.DoesNotExist) as error:
        raise LaunchDoesNotExistsError(
            f"The function_name to launch, '{task_to_launch!r}' does not exists!"
        ) from error

    return func


def initial_counter_nums(counter_instance: Counter):
    """Initialise un compteur si il n'existe pas
    :param counter_instance: instance du model Counter
    :return: None
    """
    obj = None
    try:
        obj = CounterNums.objects.get(counter=counter_instance)
    except CounterNums.DoesNotExist:
        obj = CounterNums(counter=counter_instance)
        obj.save()

    finally:
        return obj


def get_counter_num(counter_instance: Counter, attr_instance_dict: Dict = None) -> str:
    """Retourne la numérotation
    :param counter_instance: instance du compteur à appliquer
    :param attr_instance_dict: dictonaire des valeurs des attr_instance à appliquer
    :return: la numérotation demandée
    """
    if attr_instance_dict is None:
        attr_instance_dict = {}

    counter_num_obj = initial_counter_nums(counter_instance)

    str_num = ""
    prefix = counter_instance.prefix or attr_instance_dict.get("prefix", "")
    attr_instance_prefix = attr_instance_dict.get("prefix", "")

    suffix = counter_instance.suffix or attr_instance_dict.get("suffix", "")
    attr_instance_suffix = attr_instance_dict.get("suffix", "")

    ldap_num = counter_instance.lpad_num or attr_instance_dict.get("ldap_num", "0")
    separateur = counter_instance.separateur or attr_instance_dict.get("separateur", "")

    if prefix:
        str_num += get_pre_suf(name=prefix, attr_instance=attr_instance_prefix) + separateur

    if suffix:
        str_num += get_pre_suf(name=suffix, attr_instance=attr_instance_suffix) + separateur

    str_num += str(counter_num_obj.num).zfill(ldap_num)

    counter_num_obj.num += 1
    counter_num_obj.save()

    return str_num
