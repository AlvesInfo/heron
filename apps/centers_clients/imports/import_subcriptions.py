# pylint: disable=E0401,C0412,W1203,R0914
"""
FR : Module d'import des fichiers des abonnements par maison
EN : Module for importing subscription files per house

Commentaire:

created at: 2022-04-09
created by: Paulo ALVES

modified at: 2022-04-09
modified by: Paulo ALVES
"""
from pathlib import Path
from typing import AnyStr, Tuple, Union
import csv
import shutil
from operator import itemgetter
from decimal import Decimal

from xlrd.biffh import XLRDError
from django.db import connection
from django.utils import timezone

from apps.core.functions.functions_setups import settings
from apps.core.functions.functions_excel import ExcelToCsv
from heron.loggers import LOGGER_IMPORT
from apps.data_flux.make_inserts import make_insert
from apps.data_flux.trace import get_trace
from apps.centers_clients.models import MaisonSubcription
from apps.centers_clients.forms.forms_djantic.forms_maison_subscription import (
    MaisonSubcriptionSchema,
)
from apps.data_flux.models import Trace


def insert_maison_subscription(
    file_path: Path, trace: Union[Trace, None] = None
) -> (Trace, AnyStr):
    """
    Import du fichier des abonnements par maison
    :param file_path: Path du fichier à traiter
    :param trace: trace si on veut utiliser une trace existante
    """
    model = MaisonSubcription
    validator = MaisonSubcriptionSchema
    file_name = file_path.name
    trace_name = "Mise à jour abonnements par maisons"
    application_name = "import_abonnements_par_maisons"
    flow_name = "Abonnements_par_maisons"
    comment = f"import {file_name} des abonnements par maisons"
    trace = trace or get_trace(trace_name, file_name, application_name, flow_name, comment)
    params_dict_loader = {
        "trace": trace,
        "add_fields_dict": {
            "created_at": timezone.now(),
            "modified_at": timezone.now(),
        },
    }
    to_print = make_insert(model, flow_name, file_path, trace, validator, params_dict_loader)

    return trace, to_print


def get_fields_values() -> Tuple:
    """Retourne les lignes des dictionnaires pour vérification"""
    file_path = Path(f"{str(settings.APPS_DIR)}/centers_clients/sql/sql_import_subscription.sql")
    articles_dict = {}
    maisons_dict = {}
    for_signboards_dict = {}
    fonctions_dict = {}
    unit_weights_dict = {}

    with file_path.open("r", encoding="utf8") as sql_file, connection.cursor() as cursor:
        query = sql_file.read()
        # print(cursor.mogrify(query).decode())
        cursor.execute(query)
        set_dicts = {
            "article": articles_dict,
            "maison": maisons_dict,
            "signboard": for_signboards_dict,
            "function": fonctions_dict,
            "unit_weight": unit_weights_dict,
        }
        for model, reference, identification in cursor.fetchall():
            set_dicts.get(model, {})[reference] = identification

        return articles_dict, maisons_dict, for_signboards_dict, fonctions_dict, unit_weights_dict


def file_for_insert_excel_to_csv(file_excel_path: Path) -> [bool, AnyStr]:
    """Transforme le fichier excel en fichier csv
    ci-après la position des champs dans le fichier issu
    de la table centers_clients_maisonsubcription
            "maison": line[0],
            "article": line[2],
            "qty": line[3],
            "unit_weight": line[4],
            "net_unit_price": line[5],
            "function": line[6],
            "for_signboard": line[7],
    """
    errors = []
    csv_file = Path("csv_file")
    new_file = Path("new_file")
    rows_getter = itemgetter(0, 2, 3, 4, 5, 6, 7)
    (
        articles_dict,
        maisons_dict,
        for_signboards_dict,
        fonctions_dict,
        unit_weights_dict,
    ) = get_fields_values()

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

        with csv_file.open("r", encoding="utf-8", errors="replace") as file_to_parse, new_file.open(
            "w", encoding="utf-8", newline=""
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
            rows_diff_set = set()

            for i, line in enumerate(csv_reader, 1):
                if line and i > 3:
                    (
                        maison,
                        article,
                        qty,
                        unit_weight,
                        net_unit_price,
                        fonction,
                        for_signboard,
                    ) = rows_getter(line)

                    article = articles_dict.get(article)
                    maison = maisons_dict.get(maison)
                    for_signboard = for_signboards_dict.get(for_signboard)
                    fonction = fonctions_dict.get(fonction)
                    unit_weight = unit_weights_dict.get(unit_weight)

                    line_to_add = (
                        maison,
                        article,
                        qty,
                        unit_weight,
                        str(round(Decimal(net_unit_price), 2)),
                        fonction,
                        for_signboard,
                    )

                    if (article, maison, for_signboard, fonction) not in rows_diff_set:
                        rows_diff_set.add((article, maison, for_signboard, fonction))

                    else:
                        errors.append(
                            f"la ligne {i+1}, du fichier {csv_file.name}, est en doublon : "
                            f"{' - '.join(rows_getter(line))}"
                        )

                    if not all(line_to_add):
                        errors.append(
                            f"la ligne {i+1}, du fichier {csv_file.name}, contient des erreurs : "
                            f"{' - '.join(line_to_add)}"
                        )

                    csv_writer.writerow(line_to_add)

    except XLRDError:
        LOGGER_IMPORT.exception("Erreur de conversion d'un fichier excel en csv")
        errors.append(
            "Erreur de conversion en csv, la version du fichier excel n'est pas supportée"
        )

    csv_file.unlink(missing_ok=True)

    if errors:
        new_file.unlink(missing_ok=True)
        return True, ", ".join(errors)

    return False, str(new_file)


def import_abonnements_par_maisons():
    """
    Fonction d'import des abonnements par maisons, par le fichier excel
    sorti dans l'écran des abonnements
    """
    messages_errors = ""
    messages_ok = ""

    for excel_file in Path(settings.PROCESSING_CLIENS_SUBSCRIPTION).glob("*.xlsx"):
        file_name = excel_file.name
        trace_name = "Mise à jour abonnements par maisons"
        application_name = "import_abonnements_par_maisons"
        flow_name = "Abonnements_par_maisons"
        comment = f"import {file_name} des abonnements par maisons"
        trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
        error, errors_text = file_for_insert_excel_to_csv(excel_file)

        if error:
            trace.comment = errors_text
            trace.errors = True
            trace.time_to_process = (timezone.now() - trace.created_at).total_seconds()
            trace.final_at = timezone.now()
            trace.save()
            messages_errors += (
                f"\nIl y a eu une erreur d'import pour le fichier {str(excel_file.name)}: "
                f"{errors_text}"
            )

        else:
            trace, _ = insert_maison_subscription(Path(errors_text), trace)

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
            and not (Path(settings.BACKUP_CLIENS_SUBSCRIPTION_DIR) / excel_file.name).is_file()
        ):
            shutil.move(
                excel_file.resolve(),
                (Path(settings.BACKUP_CLIENS_SUBSCRIPTION_DIR) / excel_file.name).resolve(),
            )

        excel_file.unlink(missing_ok=True)

    return messages_errors, messages_ok


if __name__ == "__main__":
    import_abonnements_par_maisons()
