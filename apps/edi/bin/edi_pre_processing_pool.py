"""FR : Module de pré-traitement avant import des fichiers de factures fournisseur.

EN : Pre-processing module before importing supplier invoice files.

Commentaire:

created at: 2022-04-10
created by: Paulo ALVES

modified at: 2023-01-01
modified by: Paulo ALVES
"""

import csv
import io
from decimal import Decimal
from operator import itemgetter
from pathlib import Path

import pendulum

from apps.core.bin.get_sage_elements import (
    get_uuid_bu,
    get_uuid_prj,
    get_uuid_pro,
    get_uuid_pys,
    get_uuid_rfa,
    # get_vat_regime,
)
from apps.core.functions.functions_dates import validate_date
from apps.core.functions.functions_setups import settings
from apps.data_flux.postgres_save import get_random_name
from apps.data_flux.utilities import encoding_detect, excel_file_to_csv_string_io
from apps.edi.models import SupplierDefinition
from heron.loggers import LOGGER_EDI


def bulk_translate_file(file: Path):
    """Transformation du fichier en entrée des factures BBGR Bulk, arrivant au format entêtes/lignes.

    pour le transformer en fichier à plat
    :param file: Fichier
    :return: Path(file).
    """
    while True:
        new_file = Path(settings.PRE_PROCESSING) / f"{get_random_name()}.csv"

        if not new_file.is_file():
            break

    with (
        file.open("r", encoding="utf8") as file_to_parse,
        new_file.open("w", encoding="utf8") as file_to_write,
    ):
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
        e_row: list[str] = []

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
    """Remplace le séparateur tabulation du fichier des factures Interson par un point-virgule.

    :param file: Fichier
    :return: Path(file).
    """
    while True:
        new_file = Path(settings.INTERSON) / f"{get_random_name()}.csv"

        if not new_file.is_file():
            break

    encoding = encoding_detect(file)

    with (
        file.open("r", encoding=encoding, errors="replace") as file_to_parse,
        new_file.open("w", encoding="utf8", newline="") as file_to_write,
    ):
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

    with (
        file.open("w", encoding="utf8") as old_file,
        new_file.open("r", encoding="utf8") as file_to_read,
    ):
        old_file.write(file_to_read.read())

    new_file.unlink()

    return file


TRANSFERT_HEADERS = [
    "third_party_num",
    "invoice_number",
    "invoice_date",
    "invoice_type",
    "devise",
    "vat_rate",
]


def _transfert_rows(rows) -> list:
    """Lignes d'un transfert : une sortie chez l'envoyeur (quantité négative) et une entrée chez.

    le réceptionnaire ; aucune ligne si la quantité est nulle
    :param rows: parties de la ligne du fichier (début, envoyeur, réceptionnaire, quantité, fin).
    """
    date_cosium = pendulum.from_format(validate_date(rows[0][0]).date().isoformat(), "YYYY-MM-DD")
    invoice_date = date_cosium.end_of("month")
    invoice_number = f"TS-{invoice_date.date().isoformat()}"
    qty = Decimal(rows[3][0])

    if not qty:
        return []

    rows[4][1] = str(rows[4][1]).replace("\r", "").replace("\n", " ")
    start_row = [
        "ZTRANSFERT",
        invoice_number,
        invoice_date.format("DD/MM/YYYY"),
        "380",
        "EUR",
        ".2",
    ] + rows[0]

    return [
        start_row + rows[1] + rows[1] + [-qty] + rows[4],
        start_row + rows[2] + rows[2] + [qty] + rows[4],
    ]


def transferts_cosium_file(file: Path):
    """Transformation du fichier en entrée des transferts, switcher en deux lignes.

    Une pour l'envoyeur, l'autre pour le receptionnaire.
    :param file: Fichier
    :return: Path(file).
    """
    while True:
        new_file = Path(settings.PRE_PROCESSING) / f"{get_random_name()}.csv"

        if not new_file.is_file():
            break

    encoding = encoding_detect(file)

    with (
        file.open("r", encoding=encoding, errors="replace") as file_to_parse,
        new_file.open("w", encoding="utf8", newline="") as file_to_write,
    ):
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

            if i < 3:
                continue

            rows = slicing_parts(line)

            if i == 3:
                csv_writer.writerow(
                    TRANSFERT_HEADERS
                    + rows[0]
                    + ["code_fournisseur", "code_maison"]
                    + rows[3]
                    + rows[4]
                )
            else:
                csv_writer.writerows(_transfert_rows(rows))

    file.unlink()

    with (
        file.open("w", encoding="utf8") as old_file,
        new_file.open("r", encoding="utf8") as file_to_read,
    ):
        old_file.write(file_to_read.read())

    new_file.unlink()

    return file


def johnson_file(file: Path):
    """Transformation du fichier jonhson pour supprimer les sous totaux (en deuxième position *).

    Une pour l'envoyeur, l'autre pour le receptionnaire.
    :param file: Fichier
    :return: Path(file).
    """
    new_csv_file = file.parents[0] / f"{file.stem}.csv"
    csv_io = io.StringIO()
    excel_file_to_csv_string_io(file, csv_io)

    first_line = SupplierDefinition.objects.get(flow_name="Johnson").first_line

    with new_csv_file.open("w", encoding="utf8", newline="") as file_to_write:
        csv_reader = csv.reader(
            csv_io,
            delimiter=";",
            quotechar='"',
            lineterminator="\n",
            quoting=csv.QUOTE_MINIMAL,
        )
        csv_writer = csv.writer(
            file_to_write, delimiter=";", quotechar='"', quoting=csv.QUOTE_MINIMAL
        )

        for i, line in enumerate(csv_reader, 1):
            if line[1] == "*" or (i >= first_line and not line[2]):
                continue

            csv_writer.writerow(line)

    csv_io.close()
    file.unlink()

    return new_csv_file


def wsau_file(file: Path):
    """Contrôle du fichier wsau, qu'il ne manque pas le supplier_ident.

    :param file: Fichier
    :return: Path(file).
    """
    error_lines = []

    with file.open("r", encoding="utf8", newline="") as file_to_read:
        csv_reader = csv.reader(
            file_to_read.readlines(),
            delimiter=";",
            quotechar='"',
            lineterminator="\n",
            quoting=csv.QUOTE_MINIMAL,
        )

        for i, line in enumerate(csv_reader, 1):
            if not line[1]:
                error_lines.append(str(i))

    if error_lines:
        error = (
            "Erreur dans le fichier WSAU, il manque l'identifiant (WIDE/REXT/SIGN/AUDI) "
            f"aux lignes : {', '.join(sorted(error_lines))}"
        )
        LOGGER_EDI.error("Exception Générale : %r", error)
        raise AttributeError(error)

    name = str(file.stem)

    new_csv_file = file.parents[0] / f"{name}_change.csv"

    with (
        file.open("r", encoding="utf8", newline="") as csv_io,
        new_csv_file.open("w", encoding="utf8", newline="") as file_to_write,
    ):
        csv_reader = csv.reader(
            csv_io.readlines(),
            delimiter=";",
            quotechar='"',
            lineterminator="\n",
            quoting=csv.QUOTE_MINIMAL,
        )
        csv_writer = csv.writer(
            file_to_write, delimiter=";", quotechar='"', quoting=csv.QUOTE_MINIMAL
        )

        for line in csv_reader:
            if not line[17]:
                line[17] = "1900-01-01"

            csv_writer.writerow(line)

    file.unlink()
    new_csv_file.rename(new_csv_file.with_stem(name))


def z_bu_refac_file(file: Path) -> Path:
    """Transformation du fichier jonhson pour supprimer les sous totaux (en deuxième position *).

    Une pour l'envoyeur, l'autre pour le receptionnaire.
    :param file: Fichier
    :return: Path(file).
    """
    while True:
        new_file = Path(settings.PRE_PROCESSING) / f"{get_random_name()}.csv"

        if not new_file.is_file():
            break

    with (
        file.open("r", encoding="utf-8-sig") as file_to_parse,
        new_file.open("w", encoding="utf8", newline="") as file_to_write,
    ):
        csv_reader = csv.reader(
            file_to_parse,
            delimiter=";",
            quotechar='"',
            lineterminator="\n",
            quoting=csv.QUOTE_MINIMAL,
        )
        csv_writer = csv.writer(file_to_write, delimiter=";", quotechar='"', quoting=csv.QUOTE_ALL)

        for i, line in enumerate(csv_reader, 1):
            if i == 1:
                csv_writer.writerow([*list(line)[:16], "vat_regime"])
            else:
                (
                    tiers,
                    bl,
                    n_piece,
                    date_compta,
                    compte,
                    pys,
                    col,
                    cct,
                    prj,
                    bu,
                    rfa,
                    sens,
                    montant,
                    tva,
                    libelle,
                    *unit_weight,
                ) = line

                vat_sage = ("000" + str(tva))[-3:]

                if vat_sage not in {"001", "002"}:
                    vat_sage = "001"

                list_to_write = [
                    tiers,
                    bl,
                    n_piece,
                    date_compta,
                    compte,
                    get_uuid_pys(pys),
                    get_uuid_pro(col),
                    cct,
                    get_uuid_prj(prj),
                    get_uuid_bu(bu),
                    get_uuid_rfa(rfa),
                    str(sens).strip(),
                    montant,
                    vat_sage,
                    libelle,
                    " ".join([str(value) for value in unit_weight]).strip(),
                    "FRA",  # vat_regime,
                ]
                csv_writer.writerow(list_to_write)

    file.unlink()

    return new_file
