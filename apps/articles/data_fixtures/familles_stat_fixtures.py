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

import django

BASE_DIR = r"C:\SitesWeb\heron"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")
django.setup()

# from apps.core.functions.functions_setups import *

from apps.articles.models import SupplierArticleAxePro, FamilleAxePro
from apps.accountancy.models import SectionSage


def supplier_axes_name():
    """"""
    list_name = ["EDI", "ESSILOR"]

    for name in list_name:
        SupplierArticleAxePro.objects.get_or_create(name=name)


def fammilles_axes_edi():
    name = SupplierArticleAxePro.objects.get(name="EDI")
    base_pro_dic = {
        "active": True,
        "delete": False,
        "export": False,
        "valid": True,
        "flag_to_active": False,
        "flag_to_delete": False,
        "flag_to_export": False,
        "flag_to_valid": False,
        "name": name,
        "regex": r"([\d]).{2}([\d ]{2})",
    }
    list_pro = [
        {
            "supplier_familly": "10001",
            "supplier_axe": "verre de base",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les verres",
            "axe_pro": "db81e0d2-c3d3-49ca-9612-87c56dedce5b",
        },
        {
            "supplier_familly": "10002",
            "supplier_axe": "supplément",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les verres",
            "axe_pro": "db81e0d2-c3d3-49ca-9612-87c56dedce5b",
        },
        {
            "supplier_familly": "10003",
            "supplier_axe": "montage",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les verres",
            "axe_pro": "db81e0d2-c3d3-49ca-9612-87c56dedce5b",
        },
        {
            "supplier_familly": "10004",
            "supplier_axe": "frais de port",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les verres",
            "axe_pro": "9e43beae-edb6-491d-9a3e-007efb20b009",
        },
        {
            "supplier_familly": "10005",
            "supplier_axe": "verre + monture",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les verres",
            "axe_pro": "db81e0d2-c3d3-49ca-9612-87c56dedce5b",
        },
        {
            "supplier_familly": "10006",
            "supplier_axe": "publicité",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les verres",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "10007",
            "supplier_axe": "emballage",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les verres",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "10009",
            "supplier_axe": "autres",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les verres",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "100RF",
            "supplier_axe": "RRRO",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les verres",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "10040",
            "supplier_axe": "frais de port",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les verres",
            "axe_pro": "9e43beae-edb6-491d-9a3e-007efb20b009",
        },
        {
            "supplier_familly": "10099",
            "supplier_axe": "remises cumulées",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les verres",
            "axe_pro": "db81e0d2-c3d3-49ca-9612-87c56dedce5b",
        },
        {
            "supplier_familly": "20000",
            "supplier_axe": "monture optique",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les montures",
            "axe_pro": "1ef4cb07-ccaa-48bf-9534-257beea71b61",
        },
        {
            "supplier_familly": "20001",
            "supplier_axe": "monture optique demi-lune",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les montures",
            "axe_pro": "1ef4cb07-ccaa-48bf-9534-257beea71b61",
        },
        {
            "supplier_familly": "20010",
            "supplier_axe": "monture solaire",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les montures",
            "axe_pro": "413b1ce5-f4c1-41eb-8943-9a9d441c3d70",
        },
        {
            "supplier_familly": "20011",
            "supplier_axe": "monture solaire demi-lune",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les montures",
            "axe_pro": "413b1ce5-f4c1-41eb-8943-9a9d441c3d70",
        },
        {
            "supplier_familly": "20020",
            "supplier_axe": "clip solaire",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les montures",
            "axe_pro": "413b1ce5-f4c1-41eb-8943-9a9d441c3d70",
        },
        {
            "supplier_familly": "20099",
            "supplier_axe": "autre",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les montures",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "20090",
            "supplier_axe": "pièces détachées",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les montures",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "200RF",
            "supplier_axe": "RRRO",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les montures",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "20040",
            "supplier_axe": "frais de port",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les montures",
            "axe_pro": "9e43beae-edb6-491d-9a3e-007efb20b009",
        },
        {
            "supplier_familly": "20004",
            "supplier_axe": "frais de port",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les montures",
            "axe_pro": "9e43beae-edb6-491d-9a3e-007efb20b009",
        },
        {
            "supplier_familly": "30000",
            "supplier_axe": "lentilles souple",
            "familly_type": "famille statistique dans la norme OPTO 33 pour la contactologie",
            "axe_pro": "522fbe08-77cb-4128-bd48-99ed906fc1ef",
        },
        {
            "supplier_familly": "30001",
            "supplier_axe": "lentilles rigide",
            "familly_type": "famille statistique dans la norme OPTO 33 pour la contactologie",
            "axe_pro": "522fbe08-77cb-4128-bd48-99ed906fc1ef",
        },
        {
            "supplier_familly": "30002",
            "supplier_axe": "solutions",
            "familly_type": "famille statistique dans la norme OPTO 33 pour la contactologie",
            "axe_pro": "bdd95f55-7921-4e0b-bf3c-4215bbeeaa76",
        },
        {
            "supplier_familly": "30003",
            "supplier_axe": "suppléments",
            "familly_type": "famille statistique dans la norme OPTO 33 pour la contactologie",
            "axe_pro": "522fbe08-77cb-4128-bd48-99ed906fc1ef",
        },
        {
            "supplier_familly": "30004",
            "supplier_axe": "frais de port",
            "familly_type": "famille statistique dans la norme OPTO 33 pour la contactologie",
            "axe_pro": "9e43beae-edb6-491d-9a3e-007efb20b009",
        },
        {
            "supplier_familly": "30005",
            "supplier_axe": "divers",
            "familly_type": "famille statistique dans la norme OPTO 33 pour la contactologie",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "30006",
            "supplier_axe": "étuis",
            "familly_type": "famille statistique dans la norme OPTO 33 pour la contactologie",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "30007",
            "supplier_axe": "articles publicitaires",
            "familly_type": "famille statistique dans la norme OPTO 33 pour la contactologie",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "300RF",
            "supplier_axe": "RRRO",
            "familly_type": "famille statistique dans la norme OPTO 33 pour la contactologie",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "40001",
            "supplier_axe": "main d'œuvre",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les instruments",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "40002",
            "supplier_axe": "déplacement",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les instruments",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "40003",
            "supplier_axe": "pièces détachées",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les instruments",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "40004",
            "supplier_axe": "machine",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les instruments",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "40005",
            "supplier_axe": "publicité",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les instruments",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "40006",
            "supplier_axe": "frais de port",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les instruments",
            "axe_pro": "9e43beae-edb6-491d-9a3e-007efb20b009",
        },
        {
            "supplier_familly": "40007",
            "supplier_axe": "emballage",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les instruments",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "40008",
            "supplier_axe": "matériel d'atelier",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les instruments",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "40009",
            "supplier_axe": "matériel d'optimétrie",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les instruments",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "40010",
            "supplier_axe": "petit outillage",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les instruments",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "40011",
            "supplier_axe": "mobilier",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les instruments",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "40099",
            "supplier_axe": "autres",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les instruments",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "400RF",
            "supplier_axe": "RRRO",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les instruments",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "50001",
            "supplier_axe": "jumelles",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les grossissants",
            "axe_pro": "656200e4-0681-4c4f-b118-126c7263475a",
        },
        {
            "supplier_familly": "50002",
            "supplier_axe": "monoculaire / longue vue",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les grossissants",
            "axe_pro": "656200e4-0681-4c4f-b118-126c7263475a",
        },
        {
            "supplier_familly": "50003",
            "supplier_axe": "astronomie / téléscope / microscope",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les grossissants",
            "axe_pro": "656200e4-0681-4c4f-b118-126c7263475a",
        },
        {
            "supplier_familly": "50004",
            "supplier_axe": "opération particulière - lunettes éclispe",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les grossissants",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "50005",
            "supplier_axe": "basse vision",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les grossissants",
            "axe_pro": "656200e4-0681-4c4f-b118-126c7263475a",
        },
        {
            "supplier_familly": "50006",
            "supplier_axe": "lunettes pré-montées",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les grossissants",
            "axe_pro": "656200e4-0681-4c4f-b118-126c7263475a",
        },
        {
            "supplier_familly": "50007",
            "supplier_axe": "loupes",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les grossissants",
            "axe_pro": "656200e4-0681-4c4f-b118-126c7263475a",
        },
        {
            "supplier_familly": "50008",
            "supplier_axe": "frais de port",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les grossissants",
            "axe_pro": "9e43beae-edb6-491d-9a3e-007efb20b009",
        },
        {
            "supplier_familly": "50099",
            "supplier_axe": "autres",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les grossissants",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "500RF",
            "supplier_axe": "RRRO",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les grossissants",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "60001",
            "supplier_axe": "baromètre, thermomètre, podomètre, boussoles",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les divers",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "60002",
            "supplier_axe": "étuis",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les divers",
            "axe_pro": "86e44d1b-6cfc-4457-807d-20fc39d44ebe",
        },
        {
            "supplier_familly": "60003",
            "supplier_axe": "essuies verres",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les divers",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "60004",
            "supplier_axe": "produits d'entretien (lunettes)",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les divers",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "60005",
            "supplier_axe": "péniches",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les divers",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "60006",
            "supplier_axe": "papéterie",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les divers",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "60007",
            "supplier_axe": "produits de soins et de maquillage",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les divers",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "60008",
            "supplier_axe": "cordon, chaînette, croacky",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les divers",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "60009",
            "supplier_axe": "atelier de montage",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les divers",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "60010",
            "supplier_axe": "frais de port",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les divers",
            "axe_pro": "9e43beae-edb6-491d-9a3e-007efb20b009",
        },
        {
            "supplier_familly": "60011",
            "supplier_axe": "emballage",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les divers",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "60012",
            "supplier_axe": "présentoirs",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les divers",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "60099",
            "supplier_axe": "autres",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les divers",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "600RF",
            "supplier_axe": "RRRO",
            "familly_type": "famille statistique dans la norme OPTO 33 pour les divers",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
    ]
    for pro_dict in list_pro:
        axe_pro = SectionSage.objects.get(uuid_identification=pro_dict.get("axe_pro"))
        FamilleAxePro.objects.update_or_create(
            **{**base_pro_dic, **pro_dict, **{"axe_pro": axe_pro}}
        )


def fammilles_axes_essilor():
    name = SupplierArticleAxePro.objects.get(name="ESSILOR")
    base_pro_dic = {
        "active": True,
        "delete": False,
        "export": False,
        "valid": True,
        "flag_to_active": False,
        "flag_to_delete": False,
        "flag_to_export": False,
        "flag_to_valid": False,
        "name": name,
        "regex": r"([\d]).{2}([\d ]{2})",
    }
    list_pro = [
        {
            "supplier_familly": "10001",
            "supplier_axe": "verre de base",
            "familly_type": "famille statistique Essilor pour les verres",
            "axe_pro": "db81e0d2-c3d3-49ca-9612-87c56dedce5b",
        },
        {
            "supplier_familly": "10002",
            "supplier_axe": "supplément",
            "familly_type": "famille statistique Essilor pour les verres",
            "axe_pro": "db81e0d2-c3d3-49ca-9612-87c56dedce5b",
        },
        {
            "supplier_familly": "10003",
            "supplier_axe": "montage",
            "familly_type": "famille statistique Essilor pour les verres",
            "axe_pro": "db81e0d2-c3d3-49ca-9612-87c56dedce5b",
        },
        {
            "supplier_familly": "10004",
            "supplier_axe": "frais de port",
            "familly_type": "famille statistique Essilor pour les verres",
            "axe_pro": "9e43beae-edb6-491d-9a3e-007efb20b009",
        },
        {
            "supplier_familly": "10005",
            "supplier_axe": "verre + monture",
            "familly_type": "famille statistique Essilor pour les verres",
            "axe_pro": "db81e0d2-c3d3-49ca-9612-87c56dedce5b",
        },
        {
            "supplier_familly": "10006",
            "supplier_axe": "publicité",
            "familly_type": "famille statistique Essilor pour les verres",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "10007",
            "supplier_axe": "emballage",
            "familly_type": "famille statistique Essilor pour les verres",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "10009",
            "supplier_axe": "autres",
            "familly_type": "famille statistique Essilor pour les verres",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "10010",
            "supplier_axe": "verre",
            "familly_type": "famille statistique Essilor pour les verres",
            "axe_pro": "db81e0d2-c3d3-49ca-9612-87c56dedce5b",
        },
        {
            "supplier_familly": "10020",
            "supplier_axe": "coloration",
            "familly_type": "famille statistique Essilor pour les verres",
            "axe_pro": "db81e0d2-c3d3-49ca-9612-87c56dedce5b",
        },
        {
            "supplier_familly": "100RF",
            "supplier_axe": "RRRO",
            "familly_type": "famille statistique Essilor pour les verres",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "10040",
            "supplier_axe": "frais de port",
            "familly_type": "famille statistique Essilor pour les verres",
            "axe_pro": "9e43beae-edb6-491d-9a3e-007efb20b009",
        },
        {
            "supplier_familly": "10099",
            "supplier_axe": "remises",
            "familly_type": "famille statistique Essilor pour les verres",
            "axe_pro": "db81e0d2-c3d3-49ca-9612-87c56dedce5b",
        },
        {
            "supplier_familly": "20000",
            "supplier_axe": "monture optique",
            "familly_type": "famille statistique Essilor pour les montures",
            "axe_pro": "1ef4cb07-ccaa-48bf-9534-257beea71b61",
        },
        {
            "supplier_familly": "20001",
            "supplier_axe": "monture optique demi-lune",
            "familly_type": "famille statistique Essilor pour les montures",
            "axe_pro": "1ef4cb07-ccaa-48bf-9534-257beea71b61",
        },
        {
            "supplier_familly": "20010",
            "supplier_axe": "monture solaire",
            "familly_type": "famille statistique Essilor pour les montures",
            "axe_pro": "413b1ce5-f4c1-41eb-8943-9a9d441c3d70",
        },
        {
            "supplier_familly": "20011",
            "supplier_axe": "monture solaire demi-lune",
            "familly_type": "famille statistique Essilor pour les montures",
            "axe_pro": "413b1ce5-f4c1-41eb-8943-9a9d441c3d70",
        },
        {
            "supplier_familly": "20020",
            "supplier_axe": "clip solaire",
            "familly_type": "famille statistique Essilor pour les montures",
            "axe_pro": "413b1ce5-f4c1-41eb-8943-9a9d441c3d70",
        },
        {
            "supplier_familly": "20099",
            "supplier_axe": "autre",
            "familly_type": "famille statistique Essilor pour les montures",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "20090",
            "supplier_axe": "pièces détachées",
            "familly_type": "famille statistique Essilor pour les montures",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "200RF",
            "supplier_axe": "RRRO",
            "familly_type": "famille statistique Essilor pour les montures",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "20040",
            "supplier_axe": "frais de port",
            "familly_type": "famille statistique Essilor pour les montures",
            "axe_pro": "9e43beae-edb6-491d-9a3e-007efb20b009",
        },
        {
            "supplier_familly": "20004",
            "supplier_axe": "frais de port",
            "familly_type": "famille statistique Essilor pour les montures",
            "axe_pro": "9e43beae-edb6-491d-9a3e-007efb20b009",
        },
        {
            "supplier_familly": "30000",
            "supplier_axe": "lentilles souple",
            "familly_type": "famille statistique Essilor pour la contactologie",
            "axe_pro": "522fbe08-77cb-4128-bd48-99ed906fc1ef",
        },
        {
            "supplier_familly": "30001",
            "supplier_axe": "lentilles rigide",
            "familly_type": "famille statistique Essilor pour la contactologie",
            "axe_pro": "522fbe08-77cb-4128-bd48-99ed906fc1ef",
        },
        {
            "supplier_familly": "30002",
            "supplier_axe": "solutions",
            "familly_type": "famille statistique Essilor pour la contactologie",
            "axe_pro": "bdd95f55-7921-4e0b-bf3c-4215bbeeaa76",
        },
        {
            "supplier_familly": "30003",
            "supplier_axe": "suppléments",
            "familly_type": "famille statistique Essilor pour la contactologie",
            "axe_pro": "522fbe08-77cb-4128-bd48-99ed906fc1ef",
        },
        {
            "supplier_familly": "30004",
            "supplier_axe": "frais de port",
            "familly_type": "famille statistique Essilor pour la contactologie",
            "axe_pro": "9e43beae-edb6-491d-9a3e-007efb20b009",
        },
        {
            "supplier_familly": "30005",
            "supplier_axe": "divers",
            "familly_type": "famille statistique Essilor pour la contactologie",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "30006",
            "supplier_axe": "étuis",
            "familly_type": "famille statistique Essilor pour la contactologie",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "30007",
            "supplier_axe": "articles publicitaires",
            "familly_type": "famille statistique Essilor pour la contactologie",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "300RF",
            "supplier_axe": "RRRO",
            "familly_type": "famille statistique Essilor pour la contactologie",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "40001",
            "supplier_axe": "main d'œuvre",
            "familly_type": "famille statistique Essilor pour les instruments",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "40002",
            "supplier_axe": "déplacement",
            "familly_type": "famille statistique Essilor pour les instruments",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "40003",
            "supplier_axe": "pièces détachées",
            "familly_type": "famille statistique Essilor pour les instruments",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "40004",
            "supplier_axe": "machine",
            "familly_type": "famille statistique Essilor pour les instruments",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "40005",
            "supplier_axe": "publicité",
            "familly_type": "famille statistique Essilor pour les instruments",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "40006",
            "supplier_axe": "frais de port",
            "familly_type": "famille statistique Essilor pour les instruments",
            "axe_pro": "9e43beae-edb6-491d-9a3e-007efb20b009",
        },
        {
            "supplier_familly": "40060",
            "supplier_axe": "frais de port",
            "familly_type": "famille statistique Essilor pour les instruments",
            "axe_pro": "9e43beae-edb6-491d-9a3e-007efb20b009",
        },
        {
            "supplier_familly": "40007",
            "supplier_axe": "emballage",
            "familly_type": "famille statistique Essilor pour les instruments",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "40008",
            "supplier_axe": "matériel d'atelier",
            "familly_type": "famille statistique Essilor pour les instruments",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "40009",
            "supplier_axe": "matériel d'optimétrie",
            "familly_type": "famille statistique Essilor pour les instruments",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "40010",
            "supplier_axe": "petit outillage",
            "familly_type": "famille statistique Essilor pour les instruments",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "40011",
            "supplier_axe": "mobilier",
            "familly_type": "famille statistique Essilor pour les instruments",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "40099",
            "supplier_axe": "autres",
            "familly_type": "famille statistique Essilor pour les instruments",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "400RF",
            "supplier_axe": "RRRO",
            "familly_type": "famille statistique Essilor pour les instruments",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "50001",
            "supplier_axe": "jumelles",
            "familly_type": "famille statistique Essilor pour les grossissants",
            "axe_pro": "656200e4-0681-4c4f-b118-126c7263475a",
        },
        {
            "supplier_familly": "50002",
            "supplier_axe": "monoculaire / longue vue",
            "familly_type": "famille statistique Essilor pour les grossissants",
            "axe_pro": "656200e4-0681-4c4f-b118-126c7263475a",
        },
        {
            "supplier_familly": "50003",
            "supplier_axe": "astronomie / téléscope / microscope",
            "familly_type": "famille statistique Essilor pour les grossissants",
            "axe_pro": "656200e4-0681-4c4f-b118-126c7263475a",
        },
        {
            "supplier_familly": "50004",
            "supplier_axe": "opération particulière - lunettes éclispe",
            "familly_type": "famille statistique Essilor pour les grossissants",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "50005",
            "supplier_axe": "basse vision",
            "familly_type": "famille statistique Essilor pour les grossissants",
            "axe_pro": "656200e4-0681-4c4f-b118-126c7263475a",
        },
        {
            "supplier_familly": "50006",
            "supplier_axe": "lunettes pré-montées",
            "familly_type": "famille statistique Essilor pour les grossissants",
            "axe_pro": "656200e4-0681-4c4f-b118-126c7263475a",
        },
        {
            "supplier_familly": "50007",
            "supplier_axe": "loupes",
            "familly_type": "famille statistique Essilor pour les grossissants",
            "axe_pro": "656200e4-0681-4c4f-b118-126c7263475a",
        },
        {
            "supplier_familly": "50008",
            "supplier_axe": "frais de port",
            "familly_type": "famille statistique Essilor pour les grossissants",
            "axe_pro": "9e43beae-edb6-491d-9a3e-007efb20b009",
        },
        {
            "supplier_familly": "50099",
            "supplier_axe": "autres",
            "familly_type": "famille statistique Essilor pour les grossissants",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "500RF",
            "supplier_axe": "RRRO",
            "familly_type": "famille statistique Essilor pour les grossissants",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "60001",
            "supplier_axe": "baromètre, thermomètre, podomètre, boussoles",
            "familly_type": "famille statistique Essilor pour les divers",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "60002",
            "supplier_axe": "étuis",
            "familly_type": "famille statistique Essilor pour les divers",
            "axe_pro": "86e44d1b-6cfc-4457-807d-20fc39d44ebe",
        },
        {
            "supplier_familly": "60003",
            "supplier_axe": "essuies verres",
            "familly_type": "famille statistique Essilor pour les divers",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "60004",
            "supplier_axe": "produits d'entretien (lunettes)",
            "familly_type": "famille statistique Essilor pour les divers",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "60005",
            "supplier_axe": "péniches",
            "familly_type": "famille statistique Essilor pour les divers",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "60006",
            "supplier_axe": "papéterie",
            "familly_type": "famille statistique Essilor pour les divers",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "60007",
            "supplier_axe": "produits de soins et de maquillage",
            "familly_type": "famille statistique Essilor pour les divers",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "60008",
            "supplier_axe": "cordon, chaînette, croacky",
            "familly_type": "famille statistique Essilor pour les divers",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "60009",
            "supplier_axe": "atelier de montage",
            "familly_type": "famille statistique Essilor pour les divers",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "60010",
            "supplier_axe": "frais de port",
            "familly_type": "famille statistique Essilor pour les divers",
            "axe_pro": "9e43beae-edb6-491d-9a3e-007efb20b009",
        },
        {
            "supplier_familly": "60011",
            "supplier_axe": "emballage",
            "familly_type": "famille statistique Essilor pour les divers",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "60012",
            "supplier_axe": "présentoirs",
            "familly_type": "famille statistique Essilor pour les divers",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "60099",
            "supplier_axe": "autres",
            "familly_type": "famille statistique Essilor pour les divers",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
        {
            "supplier_familly": "600RF",
            "supplier_axe": "RRRO",
            "familly_type": "famille statistique Essilor pour les divers",
            "axe_pro": "3f42de75-c47d-40c3-b5ec-785dcaef3d8d",
        },
    ]
    for pro_dict in list_pro:
        axe_pro = SectionSage.objects.get(uuid_identification=pro_dict.get("axe_pro"))
        FamilleAxePro.objects.update_or_create(
            **{**base_pro_dic, **pro_dict, **{"axe_pro": axe_pro}}
        )


if __name__ == "__main__":
    supplier_axes_name()
    fammilles_axes_edi()
    fammilles_axes_essilor()
