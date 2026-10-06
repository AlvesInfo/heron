# pylint: disable=E0401,C0412,W1203
"""
FR : Module d'update des comptes des articles, par le fichier excel sorti dans l'écran
     12. Articles/Comptes
EN : Module for updating item accounts

Commentaire:
    Même traitement que l'import des articles sans comptes, mais en upsert : les comptes
    existants sont mis à jour, les comptes absents sont créés. Chaque ligne est aussi
    appliquée à la centrale GAF

created at: 2026-09-28
created by: Paulo ALVES

modified at: 2026-09-28
modified by: Paulo ALVES
"""
from pathlib import Path
from typing import AnyStr
import shutil

from django.utils import timezone

from heron.utils.directories import ensure_directory
from apps.core.functions.functions_setups import settings
from apps.data_flux.make_inserts import make_insert
from apps.data_flux.trace import get_trace
from apps.articles.models import ArticleAccount
from apps.articles.forms.forms_djantic.forms_articles_account import ArticleAccountSageSchema
from apps.articles.imports.articles_without_account import (
    delete_mac_files,
    file_for_insert_excel_to_csv,
)


def upsert_articles_accounts(file_path: Path) -> (AnyStr, AnyStr):
    """
    Update des comptes comptables Sage X3 des articles
    :param file_path: Path du fichier à traiter
    """
    model = ArticleAccount
    validator = ArticleAccountSageSchema
    file_name = file_path.name
    trace_name = "Mise à jour des Comptes des articles"
    application_name = "update_articles_accounts"
    flow_name = "Update_articles_accounts"
    comment = f"update {file_name} des comptes des articles"
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
        },
    }
    to_print = make_insert(
        model,
        flow_name,
        file_path,
        trace,
        validator,
        params_dict_loader,
        insert_mode="upsert",
    )

    return trace, to_print


def update_articles_accounts():
    """
    Fonction d'update des comptes des articles, par le fichier excel
    sorti dans l'écran 12. Articles/Comptes
    """

    messages_errors = ""
    messages_ok = ""
    processing_dir = ensure_directory(Path(settings.PROCESSING_UPDATE_ARTICLES_ACCOUNTS_DIR))
    backup_dir = ensure_directory(Path(settings.BACKUP_UPDATE_ARTICLES_ACCOUNTS_DIR))
    delete_mac_files(processing_dir)

    for excel_file in processing_dir.glob("*.*"):

        if not excel_file.is_file():
            continue

        if excel_file.suffix not in {".csv", ".xlsx", ".xls"}:
            excel_file.unlink(missing_ok=True)
            continue

        error, errors_text = file_for_insert_excel_to_csv(excel_file, update_mode=True)

        if error:
            messages_errors += (
                f"\nIl y a eu une erreur d'update pour le fichier {str(excel_file.name)}: "
                f"{errors_text}"
            )

        else:
            trace, _ = upsert_articles_accounts(Path(errors_text))

            if trace.errors:
                messages_errors += (
                    f"\nIl y a eu une erreur d'update pour le fichier {str(excel_file.name)}: "
                    f"Consulté la Trace N° {str(trace.uuid_identification)}"
                )
            else:
                messages_ok += f"\nLe fichier {str(excel_file.name)} a bien été intégré "

            Path(errors_text).unlink(missing_ok=True)

        if excel_file.is_file() and not (backup_dir / excel_file.name).is_file():
            shutil.move(excel_file.resolve(), (backup_dir / excel_file.name).resolve())

        excel_file.unlink(missing_ok=True)

    return messages_errors, messages_ok


if __name__ == "__main__":
    update_articles_accounts()
