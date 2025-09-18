# pylint: disable=E0401
"""
FR : Module de pré-traitement avant import des fichiers sage
EN : Pre-processing module before importing sage files

Commentaire:

created at: 2023-02-11
created by: Paulo ALVES

modified at: 2023-02-11
modified by: Paulo ALVES
"""
from uuid import uuid4
import csv
from pathlib import Path

from apps.core.functions.functions_setups import settings
from apps.data_flux.postgres_save import get_random_name
from apps.accountancy.models import ModeReglement


def mode_reglement_file(file: Path):
    """
    Transformation du fichier des modes de règlement pour recherche des uuid déjà existantes
    :param file: Fichier à transformer
    :return: Path(file)
    """
    while True:
        new_file = Path(settings.PRE_PROCESSING) / f"{get_random_name()}.csv"

        if not new_file.is_file():
            break

    with file.open("r", encoding="utf8", errors="replace") as file_to_parse, new_file.open(
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

        for i, line in enumerate(csv_reader, 1):
            if not line:
                break
            code, name, short_name, legislation = line
            name = str("" if name is None else str(name).split("~~", maxsplit=1)[0]).strip()
            short_name = str(
                "" if short_name is None else str(short_name).split("~~", maxsplit=1)[0]
            ).strip()
            mode = ModeReglement.objects.filter(
                code=code, name=name, short_name=short_name, legislation=legislation
            ).first()

            if mode:
                uuid_identification = mode.uuid_identification
            else:
                uuid_identification = uuid4()

            csv_writer.writerow([code, name, short_name, legislation, uuid_identification])

    file.unlink()

    with file.open("w", encoding="utf8") as old_file, new_file.open(
        "r", encoding="utf8"
    ) as file_to_read:
        old_file.write(file_to_read.read())

    new_file.unlink()

    return file
