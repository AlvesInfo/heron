# pylint: disable=E0401
"""
FR : Module pour renvoie des colonnes des fichiers de factures fournisseurs à traiter
EN : Module to return columns from supplier invoice files to be processed

Commentaire:

created at: 2021-11-07
created by: Paulo ALVES

modified at: 2021-11-07
modified by: Paulo ALVES
"""
from typing import AnyStr, Dict
from django.db import models
from apps.edi.loggers import EDI_LOGGER


def get_columns(model: models.Model, flow_name: AnyStr) -> Dict:
    """
    :param model:       model au sens django
    :param flow_name:  Nom de la table
    :return: Le Dictionnaire de correspondance entre le modèle et l'entête du fichier
    """
    return {
        dict_row.get("attr_name"): int(dict_row.get("file_column"))
        if dict_row.get("file_column").isnumeric()
        else dict_row.get("file_column")
        for dict_row in model.objects.filter(flow_name=flow_name)
        .order_by("ranking")
        .values("attr_name", "file_column")
    }


def get_first_line(model: models.Model, flow_name: AnyStr) -> int:
    """
    :param model:       model SupplierDefinition django
    :param flow_name:  Nom de la table
    :return: Retourne la première ligne du fichier
    """
    try:
        first_line_object = model.objects.get(flow_name=flow_name)
        return first_line_object.first_line
    except model.DoesNotExist:
        return 1


def get_loader_params_dict(model: models.Model, flow_name: AnyStr) -> int:
    """
    :param model:       model SupplierDefinition django
    :param flow_name:  Nom de la table
    :return: Retourne le dictionnaire des paramètres pour le loader
    """
    try:
        object_dict = model.objects.values(
            "encoding",
            "delimiter",
            "lineterminator",
            "quotechar",
            "escapechar",
        ).get(flow_name=flow_name)

        params_dict = {
            "encoding": object_dict.get("encoding") or None,
            "delimiter": object_dict.get("delimiter") or ";",
            "lineterminator": object_dict.get("lineterminator") or "\n",
            "quotechar": object_dict.get("quotechar") or '"',
            "escapechar": object_dict.get("escapechar") or '"',
        }
        return params_dict
    except model.DoesNotExist:
        return {}
