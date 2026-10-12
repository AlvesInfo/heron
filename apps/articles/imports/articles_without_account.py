"""FR : Module d'import des fichiers articles sans comptes.

EN : Module for importing item files without accounts.

Commentaire:

created at: 2022-04-09
created by: Paulo ALVES

modified at: 2022-04-09
modified by: Paulo ALVES
"""

import csv
import shutil
from pathlib import Path

from django.db import connection
from django.utils import timezone
from xlrd.biffh import XLRDError

from apps.articles.forms.forms_djantic.forms_articles_account import ArticleAccountSageSchema
from apps.articles.models import ArticleAccount
from apps.core.functions.functions_excel import ExcelToCsv
from apps.core.functions.functions_setups import settings
from apps.data_flux.make_inserts import make_insert
from apps.data_flux.models import Trace
from apps.data_flux.trace import get_trace
from heron.loggers import LOGGER_IMPORT


def insert_articles_without_account(file_path: Path) -> tuple[Trace, str]:
    """Import du fichier des comptes comptable Sage X3.

    :param file_path: Path du fichier à traiter.
    """
    model = ArticleAccount
    validator = ArticleAccountSageSchema
    file_name = file_path.name
    trace_name = "Mise à jour Comptes manquant pour les articles"
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
    # Les comptes existants ne sont modifiables que par l'écran de modification des comptes
    to_print = make_insert(
        model,
        flow_name,
        file_path,
        trace,
        validator,
        params_dict_loader,
        insert_mode="do_nothing",
    )

    return trace, to_print


def accounts_validation(accounts_set: set) -> bool:
    """Validation que tous les comptes venus dand le fichier, soient présents dans la table de compte.

    comptable de sage
    :param accounts_set: liste des comptes comptable
    :return: None.
    """
    file_sql_path = Path(f"{settings.APPS_DIR!s}/articles/sql/accounts_validation.sql")
    params_dict = {"accounts": tuple(accounts_set), "accounts_nb": len(accounts_set)}

    with file_sql_path.open("r", encoding="utf8") as sql_file, connection.cursor() as cursor:
        query = sql_file.read()
        cursor.execute(query, params_dict)

        return cursor.fetchone()


# Position des champs dans le fichier issu de l'écran articles sans comptes :
# article, child_center, vat, purchase_account, sale_account
ACCOUNT_COLUMNS = (0, 1, 9, 11, 12)
MIRROR_CENTER = "GAF"
FIRST_DATA_LINE = 4


def _source_to_csv(file_excel_path: Path) -> Path:
    """Renvoie le csv de travail : copie du csv déposé, ou conversion du fichier excel.

    :param file_excel_path: Path du fichier à traiter.
    """
    if file_excel_path.suffix == ".csv":
        csv_file = Path(file_excel_path.parent) / f"copy_{file_excel_path.stem}.csv"
        shutil.copy(str(file_excel_path), str(csv_file))
        return csv_file

    file = ExcelToCsv(
        rep=str(file_excel_path.parents[0]),
        header=False,
        deletion=False,
        file_name=str(file_excel_path.name),
    ).make_csv()[0]

    return Path(file)


def _account_lines(csv_reader, *, update_mode: bool) -> tuple[bool, list, set]:
    """Lignes de comptes à insérer, chacune doublée pour la centrale GAF.

    :param csv_reader: lecteur csv du fichier de travail
    :param update_mode: ignore les lignes GAF du fichier et dédoublonne par article / centrale / tva
    :return: (fichier complet, lignes à écrire, comptes comptables rencontrés).
    """
    lines: list = []
    unique_lines: dict = {}
    accounts: set = set()

    for i, line in enumerate(csv_reader, 1):
        if not line or i < FIRST_DATA_LINE:
            continue

        line_to_add = [line[index] for index in ACCOUNT_COLUMNS]

        if not all(line_to_add):
            return False, lines, accounts

        if update_mode and line_to_add[1] == MIRROR_CENTER:
            continue

        accounts.update(line_to_add[3:])

        # on ajoute la même ligne pour GA en changeant le child_center
        line_gaf = [line_to_add[0], MIRROR_CENTER, *line_to_add[2:]]

        if update_mode:
            # une même clé ne peut être mise à jour deux fois dans un upsert
            unique_lines[tuple(line_to_add[:3])] = line_to_add
            unique_lines[tuple(line_gaf[:3])] = line_gaf
        else:
            lines.extend([line_to_add, line_gaf])

    return True, lines + list(unique_lines.values()), accounts


def _content_errors(*, complete: bool, accounts: set) -> list:
    """Erreurs de contenu : informations manquantes, ou comptes absents de Sage.

    :param complete: False si une ligne n'avait pas toutes ses informations
    :param accounts: comptes comptables du fichier.
    """
    if not complete:
        error = "Il manque des informations obligatoires dans le fichier"
    elif not accounts_validation(accounts):
        error = (
            "Il y a des comptes présents dans le fichier, "
            "qui n'existent pas dans SAGE, veuillez vérifier"
        )
    else:
        return []

    LOGGER_IMPORT.error(error)

    return [error]


def file_for_insert_excel_to_csv(
    file_excel_path: Path, *, update_mode: bool = False
) -> tuple[bool, str]:
    """Transforme le fichier excel en fichier csv (colonnes ACCOUNT_COLUMNS).

    :param file_excel_path: Path du fichier à traiter
    :param update_mode: si True (update des articles / comptes), les lignes GAF du fichier sont
                        ignorées, car GAF est aligné sur la centrale de la ligne, et les lignes
                        sont dédoublonnées par article / centrale / tva pour l'upsert.
    """
    errors = []
    csv_file = Path("csv_file")
    new_file = Path("new_file")

    try:
        csv_file = _source_to_csv(file_excel_path)
        new_file = Path(file_excel_path.parent) / f"new_{file_excel_path.stem}.csv"

        with (
            csv_file.open("r", encoding="utf8", errors="replace") as file_to_parse,
            new_file.open("w", encoding="utf8", newline="") as file_to_write,
        ):
            csv_reader = csv.reader(
                file_to_parse,
                delimiter=";",
                quotechar='"',
                lineterminator="\n",
                quoting=csv.QUOTE_ALL,
            )
            complete, lines, accounts = _account_lines(csv_reader, update_mode=update_mode)
            csv.writer(
                file_to_write, delimiter=";", quotechar='"', quoting=csv.QUOTE_MINIMAL
            ).writerows(lines)

        errors.extend(_content_errors(complete=complete, accounts=accounts))

    except XLRDError:
        LOGGER_IMPORT.exception("Erreur de conversion d'un fichier excel en csv")
        erreur = "Erreur de conversion en csv, la version du fichier excel n'est pas supportée"
        errors.append(erreur)

    csv_file.unlink(missing_ok=True)

    if not errors:
        return False, str(new_file)

    new_file.unlink(missing_ok=True)

    return True, ", ".join(errors)


def delete_mac_files(directory: Path) -> None:
    """Supprime les fichiers "._*" que macOS pose à côté des fichiers déposés sur le serveur.

    :param directory: répertoire à nettoyer.
    """
    for mac_file in Path(directory).glob("._*"):
        if mac_file.is_file():
            mac_file.unlink(missing_ok=True)


def import_articles_without_account():
    """Fonction d'import des articles sans comptes, par le fichier excel.

    sorti dans l'écran des articles sans comptes.
    """
    messages_errors = ""
    messages_ok = ""
    processing_dir = Path(settings.PROCESSING_WITHOUT_ACCOUNT_DIR)
    delete_mac_files(processing_dir)

    for excel_file in processing_dir.glob("*.*"):
        if not excel_file.is_file():
            continue

        if excel_file.suffix not in {".csv", ".xlsx", ".xls"}:
            excel_file.unlink(missing_ok=True)
            continue

        error, errors_text = file_for_insert_excel_to_csv(excel_file)

        if error:
            messages_errors += (
                f"\nIl y a eu une erreur d'import pour le fichier {excel_file.name!s}: "
                f"{errors_text}"
            )

        else:
            trace, _ = insert_articles_without_account(Path(errors_text))

            if trace.errors:
                messages_errors += (
                    f"\nIl y a eu une erreur d'import pour le fichier {excel_file.name!s}: "
                    f"Consulté la Trace N° {trace.uuid_identification!s}"
                )
            else:
                messages_ok += f"\nLe fichier {excel_file.name!s} a bien été intégré "

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
