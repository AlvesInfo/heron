# pylint: disable=W0703,W1203,E0401,R0912,R0915
"""
FR : Module d'import de données issues d'un fichier
EN : Module for importing data from a file

Commentaire:

created at: 2023-05-14
created by: Paulo ALVES

modified at: 2023-05-14
modified by: Paulo ALVES
"""
from typing import Dict
import shutil
from pathlib import Path

from django.utils import timezone

from heron.loggers import LOGGER_IMPORT
from apps.data_flux.exceptions import DuplicatesError, ModelFieldError
from apps.data_flux.trace import get_trace
from apps.data_flux.make_inserts import make_insert


def import_file_process(file_path: Path, params_dict: Dict, save_dir: Path = None):
    """
    Intégration de fichiers dans les modèles ou tables
    :param file_path: Fichier à importer
    :param params_dict: Dictionnaire des paramètres :
                        params_dict = {
                            "model": ModelDjango,
                            "validator": PydanticSchema,
                            "trace_name": "trace_name",
                            "application_name": "application_name",
                            "flow_name": "flow_name",
                            "comment": "comment",
                            "add_fields_dict": {
                                "uuid_identification": trace.uuid_identification,
                                "created_at": timezone.now(),
                                "modified_at": timezone.now(),
                            },
                            "translate_file": function or None,
                            "pre_processing": function or None,
                            "post_processing": function or None
                        }
    :param save_dir: Répertoire de sauvegarde du fichier, si il n'est pas donné,
                           le fichier est effaçé
    :return: Liste des fichiers
    """
    new_file_path = ""
    error = False
    trace = None
    to_print = ""

    try:
        trace = get_trace(
            params_dict.get("trace_name"),
            file_path.name,
            params_dict.get("application_name"),
            params_dict.get("flow_name"),
            params_dict.get("comment"),
        )
        params_dict_loader = {
            "trace": trace,
            "add_fields_dict": params_dict.get("add_fields_dict"),
        }

        new_file_path = (
            params_dict.get("translate_file")(file_path)
            if params_dict.get("translate_file")
            else file_path
        )

        if params_dict.get("pre_processing"):
            params_dict.get("pre_processing")()

        to_print = make_insert(
            params_dict.get("model"),
            params_dict.get("flow_name"),
            new_file_path,
            trace,
            params_dict.get("validator"),
            params_dict_loader,
            # insert_mode="upsert",
        )

        if new_file_path != file_path:
            new_file_path.unlink()

        if params_dict.get("post_processing"):
            params_dict.get("post_processing")()

        trace.time_to_process = (timezone.now() - trace.created_at).total_seconds()
        trace.final_at = timezone.now()
        trace.save()

        if save_dir:
            destination = Path(save_dir) / file_path.name
            shutil.move(file_path.resolve(), destination.resolve())
        else:
            file_path.unlink()

    except DuplicatesError as except_error:
        error = True
        to_print = "Vous avez des doublons dans le fichier"
        LOGGER_IMPORT.exception(f"TypeError : {except_error!r}")

    except ModelFieldError as except_error:
        error = True
        to_print = "Vous avez des champs qui n'existent pas en base"
        LOGGER_IMPORT.exception(f"TypeError : {except_error!r}")

    except TypeError as except_error:
        error = True
        LOGGER_IMPORT.exception(f"TypeError : {except_error!r}")

    except Exception as except_error:
        error = True
        LOGGER_IMPORT.exception(f"Exception Générale: {file_path.name}\n{except_error!r}")

    finally:
        if error and trace:
            trace.errors = True
            trace.comment = (
                trace.comment + "\n. Une erreur c'est produite veuillez consulter les logs"
            )

        if trace is not None:
            trace.save()

        if new_file_path and new_file_path != file_path and new_file_path.is_file():
            new_file_path.unlink()

        print("to_print : ", to_print)

    return error, to_print
