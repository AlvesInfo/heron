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
from apps.data_flux.postgres_save import get_random_name
from apps.book.models import Society


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
        csv_writer = csv.writer(
            file_to_write, delimiter=";", quotechar='"', quoting=csv.QUOTE_ALL
        )
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
        csv_writer = csv.writer(
            file_to_write, delimiter=";", quotechar='"', quoting=csv.QUOTE_ALL
        )
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
