# pylint: disable=
"""Module pour validation de fichiers à intégrer en base de donnée

Commentaire:

created at: 2021-10-30
created by: Paulo ALVES

modified at: 2021-10-30
modified by: Paulo ALVES
"""
import os
import sys
import platform
import csv
from pathlib import Path

import django
from django.db import connection, connections
from django.db.utils import IntegrityError

BASE_DIR = r"C:\SitesWeb\heron"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.insert(0, BASE_DIR)
sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")
django.setup()


def set_uuid_control():

    file_path = Path(r"C:\Users\33680\Documents\ACUITIS_HERON\uuid_control.csv")

    sql_file = """
    update edi_ediimport 
    set uuid_control = %(uuid_control)s 
    
    where third_party_num = %(third_party_num)s
    and supplier = %(supplier)s
    and supplier_name = %(supplier_name)s
    and supplier_ident = %(supplier_ident)s
    """

    with file_path.open("r", encoding="cp1252") as file, connections["heron"].cursor() as cursor:
        csv_reader = csv.reader(file, delimiter=";", quotechar='"')

        for i, row in enumerate(csv_reader, 1):
            if i > 1:
                third_party_num, supplier, supplier_name, supplier_ident, uuid_control = row
                context = {
                    "third_party_num": third_party_num,
                    "supplier": supplier,
                    "supplier_name": supplier_name,
                    "supplier_ident": supplier_ident,
                    "uuid_control": uuid_control,
                }

                cursor.execute(sql_file, context)


if __name__ == '__main__':
    set_uuid_control()
