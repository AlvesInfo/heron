"""FR : Module d'import de données issues d'un fichier.

EN : Module for importing data from a file.

Commentaire:

created at: 2023-05-14
created by: Paulo ALVES

modified at: 2023-05-14
modified by: Paulo ALVES
"""

import shutil
from pathlib import Path

from django.utils import timezone

from apps.data_flux.exceptions import DuplicatesError, ModelFieldError
from apps.data_flux.make_inserts import make_insert
from apps.data_flux.trace import get_trace
from heron.loggers import LOGGER_IMPORT

# Messages utilisateur des erreurs de structure du fichier
FILE_ERRORS = {
    DuplicatesError: "Vous avez des doublons dans le fichier",
    ModelFieldError: "Vous avez des champs qui n'existent pas en base",
}


def _call_hook(params_dict: dict, name: str):
    """Appelle la fonction optionnelle (pre_processing / post_processing) du paramétrage."""
    hook = params_dict.get(name)

    if hook:
        hook()


def _translated_file(file_path: Path, params_dict: dict) -> Path:
    """Fichier à intégrer : le fichier traduit par translate_file s'il est paramétré."""
    translate = params_dict.get("translate_file")
    return translate(file_path) if translate else file_path


def _cleanup_translated(new_file_path, file_path: Path):
    """Supprime le fichier traduit temporaire s'il existe encore."""
    if new_file_path and new_file_path != file_path and new_file_path.is_file():
        new_file_path.unlink()


def _archive_source(file_path: Path, save_dir):
    """Déplace le fichier source vers le répertoire de sauvegarde, ou le supprime."""
    if save_dir:
        destination = Path(save_dir) / file_path.name
        shutil.move(file_path.resolve(), destination.resolve())
    else:
        file_path.unlink()


def _finish_trace(trace, *, error: bool):
    """Marque la trace en erreur le cas échéant et l'enregistre."""
    if trace is None:
        return

    if error:
        trace.errors = True
        trace.comment = trace.comment + "\n. Une erreur c'est produite veuillez consulter les logs"

    trace.save()


def import_file_process(file_path: Path, params_dict: dict, save_dir: Path | None = None):
    """Intégration de fichiers dans les modèles ou tables.

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
    :param save_dir: Répertoire de sauvegarde du fichier, s'il n'est pas donné,
                           le fichier est effaçé
    :return: Liste des fichiers.
    """
    new_file_path: Path | str = ""
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
        new_file_path = _translated_file(file_path, params_dict)
        _call_hook(params_dict, "pre_processing")

        to_print = make_insert(
            params_dict.get("model"),
            params_dict.get("flow_name"),
            new_file_path,
            trace,
            params_dict.get("validator"),
            params_dict_loader,
        )

        _cleanup_translated(new_file_path, file_path)
        _call_hook(params_dict, "post_processing")

        trace.time_to_process = (timezone.now() - trace.created_at).total_seconds()
        trace.final_at = timezone.now()
        trace.save()
        _archive_source(file_path, save_dir)

    except (DuplicatesError, ModelFieldError) as except_error:
        error = True
        to_print = FILE_ERRORS[type(except_error)]
        LOGGER_IMPORT.exception("TypeError")

    except TypeError:
        error = True
        LOGGER_IMPORT.exception("TypeError")

    except Exception:
        error = True
        LOGGER_IMPORT.exception("Exception Générale: %s", file_path.name)

    finally:
        _finish_trace(trace, error=error)
        _cleanup_translated(new_file_path, file_path)
        LOGGER_IMPORT.info("%s %s", "to_print : ", to_print)

    return error, to_print
