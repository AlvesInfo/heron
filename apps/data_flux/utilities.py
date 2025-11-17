# pylint: disable=E0401
"""
Module des utilitaires

created at: 2021-10-30
created by: Paulo ALVES

modified at: 2021-10-30
modified by: Paulo ALVES
"""
import io
from pathlib import Path
import csv
import zipfile

import openpyxl
from chardet.universaldetector import UniversalDetector
import pandas as pd

from .exceptions import EncodingError, ExcelToCsvFileError, CsvFileToStringIoError


def encoding_detect(path_file):
    """Fonction qui renvoi l'encoding le plus probable du fichier passé en paramètre"""
    try:
        detector = UniversalDetector()

        with open(path_file, "rb") as file:
            for line in file:
                detector.feed(line)

                if detector.done:
                    break

            detector.close()

    except Exception as except_error:
        raise EncodingError(f"encoding_detect : {path_file.name !r}") from except_error

    if detector.result["confidence"] > 0.66:
        encoding = detector.result["encoding"]
    else:
        encoding = "utf8"

    return encoding


def excel_file_to_csv_string_io(excel_file: Path, string_io_file, header=True):
    """
    Fonction qui transforme un fichier excel en csv et rempli le string_io_file passer en paramètre
    :param excel_file:      String_io excel à passer en csv
    :param string_io_file:  String_io en csv
    :param header:          Entête
    """

    try:
        # noinspection PyArgumentList
        try:
            data = pd.read_excel(excel_file.resolve())
        except (openpyxl.utils.exceptions.InvalidFileException, zipfile.BadZipFile, OSError):
            data = pd.read_excel(excel_file.resolve(), engine="xlrd")

        data.to_csv(
            string_io_file,
            sep=";",
            header=header,
            index=False,
            encoding="utf8",
            quoting=csv.QUOTE_ALL,
            float_format=lambda x: f'{int(x)}' if x == int(x) else f'{x}'  # Supprime .0 inutiles
            # lineterminator="\n",
        )
        string_io_file.seek(0)

    except ValueError as except_error:
        raise ExcelToCsvFileError(
            f"Impossible de déterminer si le fichier {excel_file.name!r}, est un fichier excel"
        ) from except_error


def file_to_csv_string_io(file: Path, string_io_file: io.StringIO, encoding_file: str = None):
    """Fonction qui transforme un fichier en csv, reçu de type fichier et transformation en STringIO
    :param file:            Fichier csv, instance de Path (pathlib)
    :param string_io_file:  Fichier de type io.StringIO
    :param encoding_file:   Encoding du fichier si on le connait
    :return: String_io au format csv
    """
    try:
        encoding = encoding_file or encoding_detect(file)

        with file.open("r", encoding=encoding, errors="replace") as csv_file:
            string_io_file.write(csv_file.read())
            string_io_file.seek(0)

    except EncodingError as except_error:
        raise CsvFileToStringIoError(
            f"file_to_csv_string_io : {file.name!r}, errur sur la détermination de l'encoding"
        ) from except_error

    except Exception as except_error:
        raise CsvFileToStringIoError(f"file_to_csv_string_io : {file.name!r}") from except_error
