# pylint: disable=E0401,C0412,W1203
"""
FR : Module d'import des fichiers articles sans comptes
EN : Module for importing item files without accounts

Commentaire:

created at: 2022-04-09
created by: Paulo ALVES

modified at: 2022-04-09
modified by: Paulo ALVES
"""
from pathlib import Path
from typing import AnyStr, Set
import csv
import shutil

from xlrd.biffh import XLRDError
from django.utils import timezone
from django.db import connection

from apps.core.functions.functions_setups import settings
from apps.core.functions.functions_excel import ExcelToCsv
from heron.loggers import LOGGER_IMPORT
from apps.data_flux.make_inserts import make_insert
from apps.data_flux.trace import get_trace
from apps.articles.models import ArticleAccount
from apps.articles.forms.forms_djantic.forms_articles_account import ArticleAccountSageSchema


def insert_articles_without_account(file_path: Path) -> (AnyStr, AnyStr):
    """
    Import du fichier des comptes comptable Sage X3
    :param file_path: Path du fichier à traiter
    """
    model = ArticleAccount
    validator = ArticleAccountSageSchema
    file_name = file_path.name
    trace_name = "Mise à jour Comptes Sage"
    application_name = "import_articles_without_account"
    flow_name = "Articles_without_account"
    comment = f"import {file_name} des articles sans comptes"
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
        },
    }
    to_print = make_insert(model, flow_name, file_path, trace, validator, params_dict_loader)

    return trace, to_print


def accounts_validation(accounts_set: Set) -> bool:
    """
    Validation que tous les comptes venus dand le fichier, soient présents dans la table de compte
    comptable de sage
    :param accounts_set: liste des comptes comptable
    :return: None
    """

    file_sql_path = Path(f"{str(settings.APPS_DIR)}/articles/sql/accounts_validation.sql")
    params_dict = {"accounts": tuple(accounts_set), "accounts_nb": len(accounts_set)}

    with file_sql_path.open("r", encoding="utf8") as sql_file, connection.cursor() as cursor:
        query = sql_file.read()
        # print(cursor.mogrify(query, params_dict).decode())
        cursor.execute(query, params_dict)

        return cursor.fetchone()


def file_for_insert_excel_to_csv(file_excel_path: Path) -> [bool, AnyStr]:
    """Transforme le fichier excel en fichier csv
    ci-après la position des champs dans le fichier issu de l'écran articles sans comptes
         article = line[0]
         child_center = line[1]
         vat = line[9]
         purchase_account = line[11]
         sale_account = line[12]
    """
    errors = []
    csv_file = Path("csv_file")
    new_file = Path("new_file")

    try:
        # On transforme le fichier excel en csv
        file = ExcelToCsv(
            rep=str(file_excel_path.parents[0]),
            header=False,
            deletion=False,
            file_name=str(file_excel_path.name),
        ).make_csv()[0]

        csv_file = Path(file)
        new_file = Path(file_excel_path.parent) / f"{file_excel_path.stem}.csv"
        informations = True

        with csv_file.open("r", encoding="utf8", errors="replace") as file_to_parse, new_file.open(
            "w", encoding="utf8", newline=""
        ) as file_to_write:
            csv_reader = csv.reader(
                file_to_parse,
                delimiter=";",
                quotechar='"',
                lineterminator="\n",
                quoting=csv.QUOTE_ALL,
            )
            csv_writer = csv.writer(
                file_to_write, delimiter=";", quotechar='"', quoting=csv.QUOTE_MINIMAL
            )
            accounts_validation_set = set()

            for i, line in enumerate(csv_reader, 1):
                if line and i > 3:
                    line_to_add = [line[0], line[1], line[9], line[11], line[12]]

                    if not all(line_to_add):
                        informations = False
                        break

                    accounts_validation_set.add(line[11])
                    accounts_validation_set.add(line[12])

                    csv_writer.writerow(line_to_add)

                    # on ajoute la même ligne pour GA en changeant le child_center
                    line_to_add[1] = 'GAF'
                    csv_writer.writerow(line_to_add)

        if not informations:
            errors.append("Il manque des informations obligatoires dans le fichier")
            LOGGER_IMPORT.exception(str(errors[-1]))

        if informations and not accounts_validation(accounts_validation_set):
            errors.append(
                "Il y a des comptes présents dans le fichier, "
                "qui n'existent pas dans SAGE, veuillez vérifier"
            )
            LOGGER_IMPORT.exception(str(errors[-1]))

    except XLRDError:
        LOGGER_IMPORT.exception("Erreur de conversion d'un fichier excel en csv")
        erreur = "Erreur de conversion en csv, la version du fichier excel n'est pas supportée"
        errors.append(erreur)

    csv_file.unlink(missing_ok=True)

    if not errors:
        return False, str(new_file)

    new_file.unlink(missing_ok=True)

    return True, ", ".join(errors)


def import_articles_without_account():
    """
    Fonction d'import des articles sans comptes, par le fichier excel
    sorti dans l'écran des articles sans comptes
    """

    messages_errors = ""
    messages_ok = ""

    for excel_file in Path(settings.PROCESSING_WITHOUT_ACCOUNT_DIR).glob("*.xlsx"):
        error, errors_text = file_for_insert_excel_to_csv(excel_file)

        if error:
            messages_errors += (
                f"\nIl y a eu une erreur d'import pour le fichier {str(excel_file.name)}: "
                f"{errors_text}"
            )

        else:
            trace, _ = insert_articles_without_account(Path(errors_text))

            if trace.errors:
                messages_errors += (
                    f"\nIl y a eu une erreur d'import pour le fichier {str(excel_file.name)}: "
                    f"Consulté la Trace N° {str(trace.uuid_identification)}"
                )
            else:
                messages_ok += f"\nLe fichier {str(excel_file.name)} a bien été intégré "

            Path(errors_text).unlink(missing_ok=True)

        if (
            excel_file.is_file()
            and not (Path(settings.BACKUP_WITHOUT_ACCOUNT_DIR) / excel_file.name).is_file()
        ):
            shutil.move(
                excel_file.resolve(),
                (Path(settings.BACKUP_WITHOUT_ACCOUNT_DIR) / excel_file.name).resolve(),
            )

        excel_file.unlink(missing_ok=True)

    return messages_errors, messages_ok


if __name__ == "__main__":
    import_articles_without_account()
