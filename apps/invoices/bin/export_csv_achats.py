# pylint: disable=W0702,W1203,E0401
"""Module d'export des achats

Commentaire:

created at: 2024-06-27
created by: Paulo ALVES

modified at: 2024-06-27
modified by: Paulo ALVES
"""
import io
import os
import platform
import sys
from pathlib import Path

import django
from psycopg2 import sql

BASE_DIR = r"C:\SitesWeb\heron"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")

django.setup()

from django.db import connection

from heron.settings.base import APPS_DIR
from heron.loggers import LOGGER_EXPORT_EXCEL


def get_achats(file_io: io.BytesIO, file_name: str, dte_d: str, dte_f: str):
    """Rempli le stream StringIO de la requête postgresql
    :param file_io: stream de type StringIO
    :param file_name: name of file
    :param dte_d: date de début de période
    :param dte_f: date de fin de période
    :return: None
    """
    try:
        file_path = Path(f"{str(APPS_DIR)}/invoices/sql_files/sql_export_achats.sql")

        with file_path.open("r") as sql_file, connection.cursor() as cursor:
            query = sql.SQL(sql_file.read()).format(dte_d, dte_f)
            sql_copy = (
                "COPY ({query}) "
                "TO STDOUT "
                "WITH "
                "DELIMITER AS '{delimiter}' "
                "CSV "
                "QUOTE AS '{quote_character}'"
            )
            sql_expert = sql.SQL(sql_copy).format(query=query, delimiter=";", quote_character='"')
            cursor.copy_expert(sql=sql_expert, file=file_io)

    except:
        LOGGER_EXPORT_EXCEL.exception(f"{file_name!r}")
        return {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}

    return {"OK": f"GENERATION DU FICHIER {file_name} TERMINEE AVEC SUCCES"}
