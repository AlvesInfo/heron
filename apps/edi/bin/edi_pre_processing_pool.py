# pylint: disable=E0401
"""
FR : Module de pré-traitement avant import des fichiers de factures fournisseur
EN : Pre-processing module before importing supplier invoice files

Commentaire:

created at: 2022-04-10
created by: Paulo ALVES

modified at: 2023-01-01
modified by: Paulo ALVES
"""
import csv
from pathlib import Path
from operator import itemgetter
from decimal import Decimal

import pendulum

from apps.core.functions.functions_setups import settings
from apps.data_flux.postgres_save import get_random_name
from apps.data_flux.utilities import encoding_detect


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


def interson_translate_file(file: Path):
    """
    Transformation du fichier en entrée des factures Interson, pour remplacer le separateur \t par;
    :param file:
    :return: Path(file)
    """
    while True:
        new_file = Path(settings.INTERSON) / f"{get_random_name()}.csv"

        if not new_file.is_file():
            break

    encoding = encoding_detect(file)

    with file.open("r", encoding=encoding, errors="replace") as file_to_parse, new_file.open(
        "w", encoding="utf8", newline=""
    ) as file_to_write:

        csv_writer = csv.writer(
            file_to_write, delimiter=";", quotechar='"', quoting=csv.QUOTE_MINIMAL
        )

        for line in file_to_parse:
            if "\t" in line:
                write_line = line.replace(";", "").replace("\r", "").replace("\n", "").split("\t")
            else:
                write_line = line.replace("\r", "").replace("\n", "").split(";")

            csv_writer.writerow(write_line)

    file.unlink()

    with file.open("w", encoding="utf8") as old_file, new_file.open(
        "r", encoding="utf8"
    ) as file_to_read:
        old_file.write(file_to_read.read())

    new_file.unlink()

    return file


def transferts_cosium_file(file: Path):
    """
    Transformation du fichier en entrée des transferts, switcher en deux lignes.
    Une pour l'envoyeur, l'autre pour le receptionnaire.
    :param file: fichier
    :return: Path(file)
    """
    while True:
        new_file = Path(settings.PRE_PROCESSING) / f"{get_random_name()}.csv"

        if not new_file.is_file():
            break

    encoding = encoding_detect(file)

    with file.open("r", encoding=encoding, errors="replace") as file_to_parse, new_file.open(
        "w", encoding="utf8", newline=""
    ) as file_to_write:
        csv_reader = csv.reader(
            file_to_parse,
            delimiter=";",
            quotechar='"',
            lineterminator="\n",
            quoting=csv.QUOTE_MINIMAL,
        )
        csv_writer = csv.writer(
            file_to_write, delimiter=";", quotechar='"', quoting=csv.QUOTE_MINIMAL
        )
        slicing_parts = itemgetter(
            slice(0, 10, None),
            slice(10, 11, None),
            slice(11, 12, None),
            slice(12, 13, None),
            slice(13, 17, None),
        )

        for i, line in enumerate(csv_reader, 1):
            if not line:
                break

            if i > 2:
                rows = slicing_parts(line)
                if i == 3:
                    entetes_list = (
                        [
                            "third_party_num",
                            "invoice_number",
                            "invoice_date",
                            "invoice_type",
                            "devise",
                            "vat_rate",
                        ]
                        + rows[0]
                        + ["code_fournisseur", "code_maison"]
                        + rows[3]
                        + rows[4]
                    )
                    csv_writer.writerow(entetes_list)
                else:
                    date_cosium = pendulum.from_format(rows[0][0], "DD/MM/YYYY")
                    invoice_date = date_cosium.end_of("month").date()
                    invoice_number = f"TS-{invoice_date.isoformat()}"
                    qty = Decimal(rows[3][0])
                    rows[4][1] = str(rows[4][1]).replace("\r", "").replace("\n", " ")
                    csv_writer.writerow(
                        [
                            "COSI001",
                            invoice_number,
                            invoice_date.format("DD/MM/YYYY"),
                            "380",
                            "EUR",
                            ".2",
                        ]
                        + rows[0]
                        + rows[1]
                        + rows[1]
                        + [-qty]
                        + rows[4]
                    )
                    csv_writer.writerow(
                        [
                            "COSI001",
                            invoice_number,
                            invoice_date.format("DD/MM/YYYY"),
                            "380",
                            "EUR",
                            ".2",
                        ]
                        + rows[0]
                        + rows[2]
                        + rows[2]
                        + [qty]
                        + rows[4]
                    )

    file.unlink()

    with file.open("w", encoding="utf8") as old_file, new_file.open(
        "r", encoding="utf8"
    ) as file_to_read:
        old_file.write(file_to_read.read())

    new_file.unlink()

    return file


if __name__ == "__main__":
    transferts_cosium_file(
        Path(r"C:\SitesWeb\heron\files\backup\suppliers_invoices_files\TRANSFERTS\liste (2).csv")
    )
