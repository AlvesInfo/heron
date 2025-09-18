# pylint: disable=
# E0401,W0703,W1203
"""
FR : fixtures pour les statistiques et axes pro des articles

Commentaire:

created at: 2022-05-10
created by: Paulo ALVES

modified at: 2022-05-10
modified by: Paulo ALVES
"""
import os
import platform
import sys
import csv
from uuid import UUID
from pathlib import Path

import django

BASE_DIR = r"C:\SitesWeb\heron"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")

django.setup()

# from apps.core.functions.functions_setups import *

# from apps.book.models import SupplierArticleAxePro, FamilleAxePro
# from apps.accountancy.models import SectionSage
#
#
# def insert_supplier_axes_name():
#     """"""
#     file = Path("supplier_stat_edi.csv")
#
#     with file.open("r", encoding="utf8") as csv_file:
#         csv_reader = csv.reader(csv_file, delimiter=";", quotechar='"')
#
#         for i, line in enumerate(csv_reader):
#             if i == 0:
#                 print(*line)
#             else:
#                 print(len(line), *line, sep="|")
#                 name, uuid_identification, axe_pro_default, invoice_column, regex = line
#                 print(
#                     len(line),
#                     name,
#                     uuid_identification,
#                     axe_pro_default,
#                     invoice_column,
#                     regex,
#                     sep="|",
#                 )
#                 SupplierArticleAxePro.objects.get_or_create(
#                     name=name,
#                     uuid_identification=UUID(uuid_identification),
#                     axe_pro_default=SectionSage.objects.get(uuid_identification=axe_pro_default)
#                     if axe_pro_default
#                     else None,
#                     invoice_column=invoice_column or None,
#                     regex=regex or None,
#                 )
#
#
# def insert_fammilles_axes_edi():
#     name = SupplierArticleAxePro.objects.get(name="EDI")
#     base_pro_dic = {
#         "active": True,
#         "delete": False,
#         "export": False,
#         "valid": True,
#         "flag_to_active": False,
#         "flag_to_delete": False,
#         "flag_to_export": False,
#         "flag_to_valid": False,
#     }
#     file = Path("stats_edi_access.csv")
#
#     with file.open("r", encoding="utf8") as csv_file:
#         csv_reader = csv.reader(csv_file, delimiter=";", quotechar='"')
#
#         for i, line in enumerate(csv_reader):
#             if i == 0:
#                 print(*line)
#             else:
#                 print(len(line), *line, sep="|")
#                 _, _, supplier_article_axe_pro, axe_pro, supplier_familly = line
#                 pro_dict = {
#                     "supplier_article_axe_pro": SupplierArticleAxePro.objects.get(
#                         uuid_identification=supplier_article_axe_pro
#                     ),
#                     "supplier_familly": supplier_familly,
#                     "axe_pro": SectionSage.objects.get(uuid_identification=axe_pro),
#                 }
#                 FamilleAxePro.objects.get_or_create(**base_pro_dic, **pro_dict)
#
#
# if __name__ == "__main__":
#     insert_supplier_axes_name()
#     insert_fammilles_axes_edi()
