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
from typing import AnyStr, Dict

from django_celery_results.models import TaskResult

from apps.core.exceptions import LaunchDoesNotExistsError
from apps.core.functions.functions_utilitaires import get_module_object
from apps.parameters.models import ActionInProgress, InvoiceFunctions, Counter, CounterNums
from apps.parameters.parameters.counters_parameters import get_pre_suf


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


def initial_counter_nums(model_instance: Counter):
    """Initialise un compteur si il n'existe pas
    :param model_instance: instance du model Counter
    :return: None
    """
    obj = None
    try:
        obj = CounterNums.objects.get(counter=model_instance)
    except CounterNums.DoesNotExist:
        obj = CounterNums(counter=model_instance)
        obj.save()

    finally:
        return obj


def get_counter_num(model_instance: Counter, attr_object_dict: Dict = None) -> str:
    """Retourne la numérotation
    :param model_instance: instance du compteur à appliquer
    :param attr_object_dict: dictonaire des valeurs des attr_object à appliquer
    :return: la numérotation demandée
    """
    if attr_object_dict is None:
        attr_object_dict = {}

    counter_num_obj = initial_counter_nums(model_instance)
    str_num = ""
    name = model_instance.name
    prefix = model_instance.prefix or ""
    attr_prefix = attr_object_dict.get("prefix")
    suffix = model_instance.prefix or ""
    attr_suffix = attr_object_dict.get("suffix")
    ldap_num = model_instance.lpad_num
    separateur = model_instance.separateur or ""

    if prefix:
        str_num += get_pre_suf(name=name, attr_object=attr_prefix) + separateur

    str_num += str(counter_num_obj.num).zfill(ldap_num) + separateur

    if suffix:
        str_num += get_pre_suf(name=name, attr_object=attr_suffix) + separateur

    counter_num_obj.num += 1
    counter_num_obj.save()

    return str_num
