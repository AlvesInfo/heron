# pylint: disable=E0401
"""
FR : Module de pré-traitement avant import des fichiers de factures fournisseur
EN : Pre-processing module before importing supplier invoice files

Commentaire:

created at: 2022-04-10
created by: Paulo ALVES

modified at: 2022-04-10
modified by: Paulo ALVES
"""
import csv
from pathlib import Path

from apps.core.functions.functions_setups import settings
from apps.data_flux.postgres_save import get_random_name


def bulk_translate_file(file: Path):
    """
    Transformation du fichier en entrée des factures BBGR Bulk, arrivant au format entêtes/lignes
    pour le transformer en fichier à plat
    :param file:
    :return: Path(file)
    """
    while True:
        new_file = Path(settings.PRE_PROCESSING) / f"{get_random_name()}.csv"
        if not new_file.is_file():
            break

    with file.open("r", encoding="utf8") as file_to_parse, new_file.open(
        "w", encoding="utf8"
    ) as file_to_write:
        csv_reader = csv.reader(
            file_to_parse,
            delimiter=";",
            quotechar='"',
            lineterminator="",
            quoting=csv.QUOTE_MINIMAL,
        )
        csv_writer = csv.writer(
            file_to_write, delimiter=";", quotechar='"', quoting=csv.QUOTE_MINIMAL
        )
        e_row = None

        for row in csv_reader:
            if row:
                write_row = list(map(str.strip, row))
                part = row[0]

                if part == "E20":
                    e_row = write_row
                elif part == "G21":
                    csv_writer.writerow(e_row + write_row)

    return new_file
