"""FR : Module pour renvoie des colonnes des fichiers de factures fournisseurs à traiter.

EN : Module to return columns from supplier invoice files to be processed.

Commentaire:

created at: 2021-11-07
created by: Paulo ALVES

modified at: 2021-11-07
modified by: Paulo ALVES
"""

from django.core.exceptions import ObjectDoesNotExist
from django.db import models


def get_columns(model: type[models.Model], flow_name: str) -> dict:
    """:param model:      Model au sens django

    :param flow_name:  Nom de la table
    :return: Le Dictionnaire de correspondance entre le modèle et l'entête du fichier
    """
    return {
        dict_row["attr_name"]: int(dict_row["file_column"])
        if dict_row["file_column"].isnumeric()
        else dict_row["file_column"]
        for dict_row in model._default_manager.filter(flow_name=flow_name)
        .order_by("ranking")
        .values("attr_name", "file_column")
    }


def get_first_line(model: type[models.Model], flow_name: str) -> int:
    """:param model:      Model SupplierDefinition django

    :param flow_name:  Nom de la table
    :return: Retourne la première ligne du fichier
    """
    try:
        first_line_object = model._default_manager.get(flow_name=flow_name)
    except ObjectDoesNotExist:
        return 1
    else:
        return first_line_object.first_line  # type: ignore[attr-defined]  # modèle de définition des flux (first_line)


def get_loader_params_dict(model: type[models.Model], flow_name: str) -> dict:
    """:param model:      Model SupplierDefinition django

    :param flow_name:  Nom de la table
    :return: Retourne le dictionnaire des paramètres pour le loader
    """
    try:
        object_dict = model._default_manager.values(
            "encoding",
            "delimiter",
            "lineterminator",
            "quotechar",
            "escapechar",
        ).get(flow_name=flow_name)

        return {
            "encoding": object_dict.get("encoding") or None,
            "delimiter": object_dict.get("delimiter") or ";",
            "lineterminator": object_dict.get("lineterminator") or "\n",
            "quotechar": object_dict.get("quotechar") or '"',
            "escapechar": object_dict.get("escapechar") or '"',
        }
    except ObjectDoesNotExist:
        return {}
