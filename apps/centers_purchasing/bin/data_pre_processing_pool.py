# pylint: disable=E0401,C0413,R0914
"""
FR : Module de traduction des fichiers (lettre en uuid)
EN : File translation module (letter to uuid)

Commentaire:

created at: 2023-05-13
created by: Paulo ALVES

modified at: 2023-05-13
modified by: Paulo ALVES
"""
import os
import sys
import platform
import io
import csv
from pathlib import Path
from uuid import uuid4
from functools import lru_cache
from typing import AnyStr

import django

BASE_DIR = r"C:\SitesWeb\heron"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")

django.setup()

from apps.data_flux.utilities import excel_file_to_csv_string_io
from apps.parameters.models import Category, SubCategory
from apps.accountancy.models import SectionSage, AccountSage


@lru_cache(maxsize=256)
def get_big_category(big_category: AnyStr) -> AnyStr:
    """
    Retourne le str de l'identifiant pour la grande catégorie
    :param big_category: big_category à rechercher
    :return: le str de l'identifiant
    """
    try:
        category = Category.objects.get(name=big_category).uuid_identification
    except Category.DoesNotExist:
        category = ""

    return category


@lru_cache(maxsize=256)
def get_sub_category(sub_category: AnyStr) -> AnyStr:
    """
    Retourne le str de l'identifiant pour la rubrique presta
    :param sub_category: sub_category à rechercher
    :return: le str de l'identifiant
    """
    try:
        rubrique = SubCategory.objects.get(name=sub_category).uuid_identification
    except SubCategory.DoesNotExist:
        rubrique = ""

    return rubrique


@lru_cache(maxsize=256)
def get_axe_pro(axe_pro: AnyStr) -> AnyStr:
    """
    Retourne le str de l'identifiant pour l'axe pro
    :param axe_pro: axe_pro à rechercher
    :return: le str de l'identifiant
    """
    try:
        pro = SectionSage.objects.get(section=axe_pro, axe="PRO").uuid_identification
    except SectionSage.DoesNotExist:
        pro = ""

    return pro


@lru_cache(maxsize=256)
def get_account(code_plan: AnyStr, account: AnyStr) -> AnyStr:
    """
    Retourne le str de l'identifiant pour l'axe pro
    :param code_plan: code plan sage à rechercher
    :param account: compte à rechercher
    :return: le str de l'identifiant
    """
    try:
        compte = AccountSage.objects.get(
            code_plan_sage=code_plan, account=account
        ).uuid_identification
    except AccountSage.DoesNotExist:
        compte = ""

    return compte


def translate_accounts_axe_pro_category(file: Path):
    """Traduction des comptes par centrales axe pro categories
    :param file: fichier
    :return: Path(file)
    """
    new_csv_file = file.parents[0] / f"{file.stem}.csv"
    csv_io = io.StringIO()
    excel_file_to_csv_string_io(file, csv_io)
    first_line = 4
    get_big_category.cache_clear()
    get_sub_category.cache_clear()
    get_axe_pro.cache_clear()
    get_account.cache_clear()

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
            if i == first_line:
                csv_writer.writerow(line)

            if i > first_line and line[0]:
                (
                    child_center,
                    big_category,
                    sub_category,
                    axe_pro,
                    vat,
                    purchase_account,
                    sale_account,
                ) = line

                child_center = child_center.split("-")[0].strip()

                try:
                    big_category = get_big_category(big_category.split("-")[1].strip())
                except IndexError:
                    big_category = get_big_category(big_category)

                try:
                    sub_category = get_sub_category(sub_category.split("-")[2].strip())
                except IndexError:
                    sub_category = get_sub_category(sub_category)

                axe_pro = get_axe_pro(axe_pro.split("-")[0].strip())

                vat = vat.split("-")[0].strip()

                if "-" in purchase_account:
                    code_plan, account, *_ = purchase_account.split("-")
                    purchase_account = get_account(code_plan, account)
                else:
                    purchase_account = get_account("FRA", purchase_account)

                if "-" in sale_account:
                    code_plan, account, *_ = sale_account.split("-")
                    sale_account = get_account(code_plan, account)
                else:
                    sale_account = get_account("FRA", sale_account)

                csv_writer.writerow(
                    [
                        child_center,
                        big_category,
                        sub_category,
                        axe_pro,
                        vat,
                        purchase_account,
                        sale_account
                    ]
                )

    csv_io.close()
    # file.unlink()

    return new_csv_file


if __name__ == "__main__":
    file_path = Path(
        r"C:\SitesWeb\heron\files\processing\suppliers_invoices_files\IMPORT_ACCOUNTS"
        r"\LISTING_DES_AXE_PRO_VS_REGROUPEMENTS_DE_FACTURATION_2023_5_13_1683972386.xlsx"
    )
    translate_accounts_axe_pro_category(file_path)
