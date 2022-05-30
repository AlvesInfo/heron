# pylint: disable=E0401
"""
FR : Module de pré-traitement avant import des fichiers de factures fournisseur
EN : Pre-processing module before importing supplier invoice files

Commentaire:

created at: 2022-05-10
created by: Paulo ALVES

modified at: 2022-05-10
modified by: Paulo ALVES
"""
import csv
from pathlib import Path

from apps.core.functions.functions_setups import CNX_STRING
from apps.core.functions.functions_postgresql import cnx_postgresql
from apps.data_flux.postgres_save import get_random_name
from apps.book.models import Society


def bp_book_pre_processing(path_dir: Path, file: Path):
    """
    Transformation du fichier en entrée des fournisseurs - BPS et client - BPC,
    pour y ajouter les colonnes nécessaires du type de tiers (fournisseur, client, employé, ...)
    :param path_dir: Répertoire du fichier à traité
    :param file: Fichier à traiter
    """
    while True:
        new_file = path_dir / f"{get_random_name()}.csv"
        if not new_file.is_file():
            break

    with file.open("r", encoding="utf8") as file_to_parse, new_file.open(
        "w", encoding="utf8", newline=""
    ) as file_to_write:
        csv_reader = csv.reader(
            file_to_parse,
            delimiter=";",
            quotechar='"',
            lineterminator="",
            quoting=csv.QUOTE_MINIMAL,
        )
        csv_writer = csv.writer(file_to_write, delimiter=";", quotechar='"', quoting=csv.QUOTE_ALL)

        # On cré le dictionnaire des types de tiers pour les ajoutés au fichier issu de sage
        societies_dict_exist = {
            row_dict.get("third_party_num"): [
                "2" if value else "1" for key, value in row_dict.items() if key != "third_party_num"
            ]
            for row_dict in Society.objects.all().values(
                "third_party_num",
                "is_client",
                "is_agent",
                "is_prospect",
                "is_supplier",
                "is_various",
                "is_service_provider",
                "is_transporter",
                "is_contractor",
                "is_physical_person",
            )
        }

        # On cré le dictionnaire des moyens de paiement pour les ajoutés au fichier issu de sage
        with cnx_postgresql(CNX_STRING).cursor() as cursor:
            cursor.execute(
                """
            select
                "code",
                max("auuid") as "auuid"
            from "accountancy_paymentcondition" "ap"
            group by "code"
            """
            )
            code_dict_exists = dict(cursor.fetchall())

        for row in csv_reader:
            (third_party_num, payment_condition_client, vat_sheme_client, account_client_code) = row
            csv_writer.writerow(
                [
                    third_party_num,
                    code_dict_exists.get(payment_condition_client),
                    vat_sheme_client,
                    account_client_code,
                ]
                + societies_dict_exist.get(row[0])
            )

    file.unlink()
    new_file.rename(file.resolve())


def society_book_pre_processing(path_dir: Path, file: Path):
    """
    Transformation du fichier en entrée des adresses sociétés sage, en vérifiant quelles existent
    :param path_dir: Répertoire du fichier à traité
    :param file: Fichier à traiter
    """
    while True:
        new_file = path_dir / f"{get_random_name()}.csv"
        if not new_file.is_file():
            break

    with file.open("r", encoding="utf8") as file_to_parse, new_file.open(
        "w", encoding="utf8", newline=""
    ) as file_to_write:
        csv_reader = csv.reader(
            file_to_parse,
            delimiter=";",
            quotechar='"',
            lineterminator="",
            quoting=csv.QUOTE_MINIMAL,
        )
        csv_writer = csv.writer(file_to_write, delimiter=";", quotechar='"', quoting=csv.QUOTE_ALL)
        societies_exist = {
            row_dict.get("third_party_num")
            for row_dict in Society.objects.all().values("third_party_num")
        }
        for row in csv_reader:
            if row and row[0] in societies_exist:
                csv_writer.writerow(row)

    file.unlink()
    new_file.rename(file.resolve())


def bank_book_pre_processing(path_dir: Path, file: Path):
    """
    Transformation du fichier en entrée des adresses sociétés sage, en vérifiant quelles existent
    :param path_dir: Répertoire du fichier à traité
    :param file: Fichier à traiter
    """
    while True:
        new_file = path_dir / f"{get_random_name()}.csv"
        if not new_file.is_file():
            break

    with file.open("r", encoding="utf8") as file_to_parse, new_file.open(
        "w", encoding="utf8", newline=""
    ) as file_to_write:
        csv_reader = csv.reader(
            file_to_parse,
            delimiter=";",
            quotechar='"',
            lineterminator="",
            quoting=csv.QUOTE_MINIMAL,
        )
        csv_writer = csv.writer(file_to_write, delimiter=";", quotechar='"', quoting=csv.QUOTE_ALL)
        society_bank_exist = set()
        societies_exist = {
            row_dict.get("third_party_num")
            for row_dict in Society.objects.all().values("third_party_num")
        }

        for row in csv_reader:
            if row and tuple(row[:2]) not in society_bank_exist and row[0] in societies_exist:
                society_bank_exist.add(tuple(row[:2]))
                csv_writer.writerow(row)

    file.unlink()
    new_file.rename(file.resolve())
