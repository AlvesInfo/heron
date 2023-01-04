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
from pathlib import Path
from functools import lru_cache
from uuid import UUID

import django

BASE_DIR = r"C:\SitesWeb\heron"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")
django.setup()

from apps.accountancy.models import SectionSage
from apps.book.models import Society
from apps.articles.models import Article, ArticleUpdate


@lru_cache(maxsize=512)
def get_axe_pro(axe_pro_copie_de_acuitis):
    return SectionSage.objects.get(section=axe_pro_copie_de_acuitis, axe="PRO")


@lru_cache(maxsize=512)
def get_society(supplier):
    return Society.objects.get(third_party_num=supplier)


def import_articles():
    """Import des articles de la base 'Copie de Acuitis.accdb'"""
    articles_files = Path(BASE_DIR) / "apps/articles/data_fixtures/r_articles_axe_pro.txt"

    with articles_files.open("r", encoding="utf8") as file:
        csv_reader = csv.reader(
            file,
            delimiter=";",
            quotechar='"',
            lineterminator="",
            quoting=csv.QUOTE_MINIMAL,
        )

        for line in csv_reader:
            (
                supplier,
                reference,
                libelle,
                libelle_heron,
                famille_supplier,
                axe_pro_copie_de_acuitis,
                catalog_price,
            ) = line

            if not libelle:
                libelle = reference
            if not libelle_heron:
                libelle_heron = reference

            objet, created = Article.objects.update_or_create(
                supplier=get_society(supplier),
                reference=reference,
                libelle=libelle,
                libelle_heron=libelle_heron,
                famille_supplier=famille_supplier,
                axe_pro=get_axe_pro(axe_pro_copie_de_acuitis),
                catalog_price=catalog_price,
            )
            print(objet, created)


def article_from_article_update():
    for article in ArticleUpdate.objects.all():
        try:
            objet, created = Article.objects.update_or_create(
                supplier=get_society("TECH001"),
                reference=article.reference,
                libelle=article.libelle,
                libelle_heron=article.libelle,
            )
            print(objet, created)
        except django.db.utils.IntegrityError:
            pass


l = [
    {
        "active": "fasle",
        "delete": "fasle",
        "export": "fasle",
        "valid": "fasle",
        "flag_to_active": "fasle",
        "flag_to_delete": "fasle",
        "flag_to_export": "fasle",
        "flag_to_valid": "fasle",
        "reference": "ACCESSORIES-ACCESS OPTIQUE",
        "libelle": "ACCESSORIES-ACCESS OPTIQUE",
        "libelle_heron": "ACCESSORIES-ACCESS OPTIQUE",
        "axe_pro_supplier": "ACCESSORIES",
        "new_article": "false",
        "axe_bu": UUID("71c82478-affe-45d5-8113-13f745bab0e1"),
        "axe_prj": UUID("522e0110-35e6-4f31-8588-1d4dcc5ae378"),
        "axe_pys": UUID("fe60f32f-c879-484d-9aa4-200cc222cdbd"),
        "third_party_num": "BBGR001",
        "famille_supplier": "ACCESS OPTIQUE",
        "big_category": "f2dda460-20db-4b05-8bb8-fa80a1ff146b",
        "acquitted": "false",
        "flag_to_acquitted": "false",
        "created_by": "d3888b89-0847-4dc2-ae8f-f1da36bde2b7",
        "famille_acuitis": "ACCESS OPTIQUE",
    },
    {
        "active": "fasle",
        "delete": "fasle",
        "export": "fasle",
        "valid": "fasle",
        "flag_to_active": "fasle",
        "flag_to_delete": "fasle",
        "flag_to_export": "fasle",
        "flag_to_valid": "fasle",
        "reference": "ACCESSORIES-CONSOMMABLE",
        "libelle": "ACCESSORIES-CONSOMMABLE",
        "libelle_heron": "ACCESSORIES-CONSOMMABLE",
        "axe_pro_supplier": "ACCESSORIES",
        "new_article": "false",
        "axe_bu": UUID("71c82478-affe-45d5-8113-13f745bab0e1"),
        "axe_prj": UUID("522e0110-35e6-4f31-8588-1d4dcc5ae378"),
        "axe_pys": UUID("fe60f32f-c879-484d-9aa4-200cc222cdbd"),
        "third_party_num": "BBGR001",
        "famille_supplier": "CONSOMMABLE",
        "big_category": "f2dda460-20db-4b05-8bb8-fa80a1ff146b",
        "acquitted": "false",
        "flag_to_acquitted": "false",
        "created_by": "d3888b89-0847-4dc2-ae8f-f1da36bde2b7",
        "famille_acuitis": "CONSOMMABLE",
    },
    {
        "active": "fasle",
        "delete": "fasle",
        "export": "fasle",
        "valid": "fasle",
        "flag_to_active": "fasle",
        "flag_to_delete": "fasle",
        "flag_to_export": "fasle",
        "flag_to_valid": "fasle",
        "reference": "ACCESSORIES-MONTURE OPT",
        "libelle": "ACCESSORIES-MONTURE OPT",
        "libelle_heron": "ACCESSORIES-MONTURE OPT",
        "axe_pro_supplier": "ACCESSORIES",
        "new_article": "false",
        "axe_bu": UUID("71c82478-affe-45d5-8113-13f745bab0e1"),
        "axe_prj": UUID("522e0110-35e6-4f31-8588-1d4dcc5ae378"),
        "axe_pys": UUID("fe60f32f-c879-484d-9aa4-200cc222cdbd"),
        "third_party_num": "BBGR001",
        "famille_supplier": "MONTURE OPT",
        "big_category": "f2dda460-20db-4b05-8bb8-fa80a1ff146b",
        "acquitted": "false",
        "flag_to_acquitted": "false",
        "created_by": "d3888b89-0847-4dc2-ae8f-f1da36bde2b7",
        "famille_acuitis": "MONTURE OPT",
    },
    {
        "active": "fasle",
        "delete": "fasle",
        "export": "fasle",
        "valid": "fasle",
        "flag_to_active": "fasle",
        "flag_to_delete": "fasle",
        "flag_to_export": "fasle",
        "flag_to_valid": "fasle",
        "reference": "AUDIO-ACCESS AUDIO",
        "libelle": "AUDIO-ACCESS AUDIO",
        "libelle_heron": "AUDIO-ACCESS AUDIO",
        "axe_pro_supplier": "AUDIO",
        "new_article": "false",
        "axe_bu": UUID("71c82478-affe-45d5-8113-13f745bab0e1"),
        "axe_prj": UUID("522e0110-35e6-4f31-8588-1d4dcc5ae378"),
        "axe_pys": UUID("fe60f32f-c879-484d-9aa4-200cc222cdbd"),
        "third_party_num": "BBGR001",
        "famille_supplier": "ACCESS AUDIO",
        "big_category": "f2dda460-20db-4b05-8bb8-fa80a1ff146b",
        "acquitted": "false",
        "flag_to_acquitted": "false",
        "created_by": "d3888b89-0847-4dc2-ae8f-f1da36bde2b7",
        "famille_acuitis": "ACCESS AUDIO",
    },
    {
        "active": "fasle",
        "delete": "fasle",
        "export": "fasle",
        "valid": "fasle",
        "flag_to_active": "fasle",
        "flag_to_delete": "fasle",
        "flag_to_export": "fasle",
        "flag_to_valid": "fasle",
        "reference": "AUDIO-CONSOMMABLE",
        "libelle": "AUDIO-CONSOMMABLE",
        "libelle_heron": "AUDIO-CONSOMMABLE",
        "axe_pro_supplier": "AUDIO",
        "new_article": "false",
        "axe_bu": UUID("71c82478-affe-45d5-8113-13f745bab0e1"),
        "axe_prj": UUID("522e0110-35e6-4f31-8588-1d4dcc5ae378"),
        "axe_pys": UUID("fe60f32f-c879-484d-9aa4-200cc222cdbd"),
        "third_party_num": "BBGR001",
        "famille_supplier": "CONSOMMABLE",
        "big_category": "f2dda460-20db-4b05-8bb8-fa80a1ff146b",
        "acquitted": "false",
        "flag_to_acquitted": "false",
        "created_by": "d3888b89-0847-4dc2-ae8f-f1da36bde2b7",
        "famille_acuitis": "CONSOMMABLE",
    },
    {
        "active": "fasle",
        "delete": "fasle",
        "export": "fasle",
        "valid": "fasle",
        "flag_to_active": "fasle",
        "flag_to_delete": "fasle",
        "flag_to_export": "fasle",
        "flag_to_valid": "fasle",
        "reference": "CASES-CONSOMMABLE",
        "libelle": "CASES-CONSOMMABLE",
        "libelle_heron": "CASES-CONSOMMABLE",
        "axe_pro_supplier": "CASES",
        "new_article": "false",
        "axe_bu": UUID("71c82478-affe-45d5-8113-13f745bab0e1"),
        "axe_prj": UUID("522e0110-35e6-4f31-8588-1d4dcc5ae378"),
        "axe_pys": UUID("fe60f32f-c879-484d-9aa4-200cc222cdbd"),
        "third_party_num": "BBGR001",
        "famille_supplier": "CONSOMMABLE",
        "big_category": "f2dda460-20db-4b05-8bb8-fa80a1ff146b",
        "acquitted": "false",
        "flag_to_acquitted": "false",
        "created_by": "d3888b89-0847-4dc2-ae8f-f1da36bde2b7",
        "famille_acuitis": "CONSOMMABLE",
    },
    {
        "active": "fasle",
        "delete": "fasle",
        "export": "fasle",
        "valid": "fasle",
        "flag_to_active": "fasle",
        "flag_to_delete": "fasle",
        "flag_to_export": "fasle",
        "flag_to_valid": "fasle",
        "reference": "CONTACT-CONTACTO SOL",
        "libelle": "CONTACT-CONTACTO SOL",
        "libelle_heron": "CONTACT-CONTACTO SOL",
        "axe_pro_supplier": "CONTACT",
        "new_article": "false",
        "axe_bu": UUID("71c82478-affe-45d5-8113-13f745bab0e1"),
        "axe_prj": UUID("522e0110-35e6-4f31-8588-1d4dcc5ae378"),
        "axe_pys": UUID("fe60f32f-c879-484d-9aa4-200cc222cdbd"),
        "third_party_num": "BBGR001",
        "famille_supplier": "CONTACTO SOL",
        "big_category": "f2dda460-20db-4b05-8bb8-fa80a1ff146b",
        "acquitted": "false",
        "flag_to_acquitted": "false",
        "created_by": "d3888b89-0847-4dc2-ae8f-f1da36bde2b7",
        "famille_acuitis": "CONTACTO SOL",
    },
    {
        "active": "fasle",
        "delete": "fasle",
        "export": "fasle",
        "valid": "fasle",
        "flag_to_active": "fasle",
        "flag_to_delete": "fasle",
        "flag_to_export": "fasle",
        "flag_to_valid": "fasle",
        "reference": "FRAMES-ACCESS OPTIQUE",
        "libelle": "FRAMES-ACCESS OPTIQUE",
        "libelle_heron": "FRAMES-ACCESS OPTIQUE",
        "axe_pro_supplier": "FRAMES",
        "new_article": "false",
        "axe_bu": UUID("71c82478-affe-45d5-8113-13f745bab0e1"),
        "axe_prj": UUID("522e0110-35e6-4f31-8588-1d4dcc5ae378"),
        "axe_pys": UUID("fe60f32f-c879-484d-9aa4-200cc222cdbd"),
        "third_party_num": "BBGR001",
        "famille_supplier": "ACCESS OPTIQUE",
        "big_category": "f2dda460-20db-4b05-8bb8-fa80a1ff146b",
        "acquitted": "false",
        "flag_to_acquitted": "false",
        "created_by": "d3888b89-0847-4dc2-ae8f-f1da36bde2b7",
        "famille_acuitis": "ACCESS OPTIQUE",
    },
    {
        "active": "fasle",
        "delete": "fasle",
        "export": "fasle",
        "valid": "fasle",
        "flag_to_active": "fasle",
        "flag_to_delete": "fasle",
        "flag_to_export": "fasle",
        "flag_to_valid": "fasle",
        "reference": "FRAMES-CONSOMMABLE",
        "libelle": "FRAMES-CONSOMMABLE",
        "libelle_heron": "FRAMES-CONSOMMABLE",
        "axe_pro_supplier": "FRAMES",
        "new_article": "false",
        "axe_bu": UUID("71c82478-affe-45d5-8113-13f745bab0e1"),
        "axe_prj": UUID("522e0110-35e6-4f31-8588-1d4dcc5ae378"),
        "axe_pys": UUID("fe60f32f-c879-484d-9aa4-200cc222cdbd"),
        "third_party_num": "BBGR001",
        "famille_supplier": "CONSOMMABLE",
        "big_category": "f2dda460-20db-4b05-8bb8-fa80a1ff146b",
        "acquitted": "false",
        "flag_to_acquitted": "false",
        "created_by": "d3888b89-0847-4dc2-ae8f-f1da36bde2b7",
        "famille_acuitis": "CONSOMMABLE",
    },
    {
        "active": "fasle",
        "delete": "fasle",
        "export": "fasle",
        "valid": "fasle",
        "flag_to_active": "fasle",
        "flag_to_delete": "fasle",
        "flag_to_export": "fasle",
        "flag_to_valid": "fasle",
        "reference": "FRAMES-MONTURE OPT",
        "libelle": "FRAMES-MONTURE OPT",
        "libelle_heron": "FRAMES-MONTURE OPT",
        "axe_pro_supplier": "FRAMES",
        "new_article": "false",
        "axe_bu": UUID("71c82478-affe-45d5-8113-13f745bab0e1"),
        "axe_prj": UUID("522e0110-35e6-4f31-8588-1d4dcc5ae378"),
        "axe_pys": UUID("fe60f32f-c879-484d-9aa4-200cc222cdbd"),
        "third_party_num": "BBGR001",
        "famille_supplier": "MONTURE OPT",
        "big_category": "f2dda460-20db-4b05-8bb8-fa80a1ff146b",
        "acquitted": "false",
        "flag_to_acquitted": "false",
        "created_by": "d3888b89-0847-4dc2-ae8f-f1da36bde2b7",
        "famille_acuitis": "MONTURE OPT",
    },
    {
        "active": "fasle",
        "delete": "fasle",
        "export": "fasle",
        "valid": "fasle",
        "flag_to_active": "fasle",
        "flag_to_delete": "fasle",
        "flag_to_export": "fasle",
        "flag_to_valid": "fasle",
        "reference": "FRAMES-MONTURE SOL",
        "libelle": "FRAMES-MONTURE SOL",
        "libelle_heron": "FRAMES-MONTURE SOL",
        "axe_pro_supplier": "FRAMES",
        "new_article": "false",
        "axe_bu": UUID("71c82478-affe-45d5-8113-13f745bab0e1"),
        "axe_prj": UUID("522e0110-35e6-4f31-8588-1d4dcc5ae378"),
        "axe_pys": UUID("fe60f32f-c879-484d-9aa4-200cc222cdbd"),
        "third_party_num": "BBGR001",
        "famille_supplier": "MONTURE SOL",
        "big_category": "f2dda460-20db-4b05-8bb8-fa80a1ff146b",
        "acquitted": "false",
        "flag_to_acquitted": "false",
        "created_by": "d3888b89-0847-4dc2-ae8f-f1da36bde2b7",
        "famille_acuitis": "MONTURE SOL",
    },
    {
        "active": "fasle",
        "delete": "fasle",
        "export": "fasle",
        "valid": "fasle",
        "flag_to_active": "fasle",
        "flag_to_delete": "fasle",
        "flag_to_export": "fasle",
        "flag_to_valid": "fasle",
        "reference": "PLV-ACCESS AUDIO",
        "libelle": "PLV-ACCESS AUDIO",
        "libelle_heron": "PLV-ACCESS AUDIO",
        "axe_pro_supplier": "PLV",
        "new_article": "false",
        "axe_bu": UUID("71c82478-affe-45d5-8113-13f745bab0e1"),
        "axe_prj": UUID("522e0110-35e6-4f31-8588-1d4dcc5ae378"),
        "axe_pys": UUID("fe60f32f-c879-484d-9aa4-200cc222cdbd"),
        "third_party_num": "BBGR001",
        "famille_supplier": "ACCESS AUDIO",
        "big_category": "f2dda460-20db-4b05-8bb8-fa80a1ff146b",
        "acquitted": "false",
        "flag_to_acquitted": "false",
        "created_by": "d3888b89-0847-4dc2-ae8f-f1da36bde2b7",
        "famille_acuitis": "ACCESS AUDIO",
    },
    {
        "active": "fasle",
        "delete": "fasle",
        "export": "fasle",
        "valid": "fasle",
        "flag_to_active": "fasle",
        "flag_to_delete": "fasle",
        "flag_to_export": "fasle",
        "flag_to_valid": "fasle",
        "reference": "PLV-ACCESS OPTIQUE",
        "libelle": "PLV-ACCESS OPTIQUE",
        "libelle_heron": "PLV-ACCESS OPTIQUE",
        "axe_pro_supplier": "PLV",
        "new_article": "false",
        "axe_bu": UUID("71c82478-affe-45d5-8113-13f745bab0e1"),
        "axe_prj": UUID("522e0110-35e6-4f31-8588-1d4dcc5ae378"),
        "axe_pys": UUID("fe60f32f-c879-484d-9aa4-200cc222cdbd"),
        "third_party_num": "BBGR001",
        "famille_supplier": "ACCESSOIRES",
        "big_category": "f2dda460-20db-4b05-8bb8-fa80a1ff146b",
        "acquitted": "false",
        "flag_to_acquitted": "false",
        "created_by": "d3888b89-0847-4dc2-ae8f-f1da36bde2b7",
        "famille_acuitis": "ACCESSOIRES",
    },
    {
        "active": "fasle",
        "delete": "fasle",
        "export": "fasle",
        "valid": "fasle",
        "flag_to_active": "fasle",
        "flag_to_delete": "fasle",
        "flag_to_export": "fasle",
        "flag_to_valid": "fasle",
        "reference": "PLV-ACCESSOIRES",
        "libelle": "PLV-ACCESSOIRES",
        "libelle_heron": "PLV-ACCESSOIRES",
        "axe_pro_supplier": "PLV",
        "new_article": "false",
        "axe_bu": UUID("71c82478-affe-45d5-8113-13f745bab0e1"),
        "axe_prj": UUID("522e0110-35e6-4f31-8588-1d4dcc5ae378"),
        "axe_pys": UUID("fe60f32f-c879-484d-9aa4-200cc222cdbd"),
        "third_party_num": "BBGR001",
        "famille_supplier": "ACCESS OPTIQUE",
        "big_category": "f2dda460-20db-4b05-8bb8-fa80a1ff146b",
        "acquitted": "false",
        "flag_to_acquitted": "false",
        "created_by": "d3888b89-0847-4dc2-ae8f-f1da36bde2b7",
        "famille_acuitis": "ACCESS OPTIQUE",
    },
    {
        "active": "fasle",
        "delete": "fasle",
        "export": "fasle",
        "valid": "fasle",
        "flag_to_active": "fasle",
        "flag_to_delete": "fasle",
        "flag_to_export": "fasle",
        "flag_to_valid": "fasle",
        "reference": "PLV-AUDITION",
        "libelle": "PLV-AUDITION",
        "libelle_heron": "PLV-AUDITION",
        "axe_pro_supplier": "PLV",
        "new_article": "false",
        "axe_bu": UUID("71c82478-affe-45d5-8113-13f745bab0e1"),
        "axe_prj": UUID("522e0110-35e6-4f31-8588-1d4dcc5ae378"),
        "axe_pys": UUID("fe60f32f-c879-484d-9aa4-200cc222cdbd"),
        "third_party_num": "BBGR001",
        "famille_supplier": "AUDITION",
        "big_category": "f2dda460-20db-4b05-8bb8-fa80a1ff146b",
        "acquitted": "false",
        "flag_to_acquitted": "false",
        "created_by": "d3888b89-0847-4dc2-ae8f-f1da36bde2b7",
        "famille_acuitis": "AUDITION",
    },
    {
        "active": "fasle",
        "delete": "fasle",
        "export": "fasle",
        "valid": "fasle",
        "flag_to_active": "fasle",
        "flag_to_delete": "fasle",
        "flag_to_export": "fasle",
        "flag_to_valid": "fasle",
        "reference": "PLV-CONSOMMABLE",
        "libelle": "PLV-CONSOMMABLE",
        "libelle_heron": "PLV-CONSOMMABLE",
        "axe_pro_supplier": "PLV",
        "new_article": "false",
        "axe_bu": UUID("71c82478-affe-45d5-8113-13f745bab0e1"),
        "axe_prj": UUID("522e0110-35e6-4f31-8588-1d4dcc5ae378"),
        "axe_pys": UUID("fe60f32f-c879-484d-9aa4-200cc222cdbd"),
        "third_party_num": "BBGR001",
        "famille_supplier": "CONSOMMABLE",
        "big_category": "f2dda460-20db-4b05-8bb8-fa80a1ff146b",
        "acquitted": "false",
        "flag_to_acquitted": "false",
        "created_by": "d3888b89-0847-4dc2-ae8f-f1da36bde2b7",
        "famille_acuitis": "CONSOMMABLE",
    },
    {
        "active": "fasle",
        "delete": "fasle",
        "export": "fasle",
        "valid": "fasle",
        "flag_to_active": "fasle",
        "flag_to_delete": "fasle",
        "flag_to_export": "fasle",
        "flag_to_valid": "fasle",
        "reference": "PLV-PLV",
        "libelle": "PLV-PLV",
        "libelle_heron": "PLV-PLV",
        "axe_pro_supplier": "PLV",
        "new_article": "false",
        "axe_bu": UUID("71c82478-affe-45d5-8113-13f745bab0e1"),
        "axe_prj": UUID("522e0110-35e6-4f31-8588-1d4dcc5ae378"),
        "axe_pys": UUID("fe60f32f-c879-484d-9aa4-200cc222cdbd"),
        "third_party_num": "BBGR001",
        "famille_supplier": "PLV",
        "big_category": "f2dda460-20db-4b05-8bb8-fa80a1ff146b",
        "acquitted": "false",
        "flag_to_acquitted": "false",
        "created_by": "d3888b89-0847-4dc2-ae8f-f1da36bde2b7",
        "famille_acuitis": "PLV",
    },
]
from django import forms


class ArtForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = [
            "active",
            "delete",
            "export",
            "valid",
            "flag_to_active",
            "flag_to_delete",
            "flag_to_export",
            "flag_to_valid",
            "reference",
            "libelle",
            "libelle_heron",
            "axe_pro_supplier",
            "new_article",
            "axe_bu",
            "axe_prj",
            "axe_pys",
            "third_party_num",
            "famille_supplier",
            "big_category",
            "acquitted",
            "flag_to_acquitted",
            "acquitted_by",
            "created_by",
            "famille_acuitis",
        ]


def main():
    for art_dict in l:
        f = ArtForm(art_dict)
        if f.is_valid():
            f.save()
        else:
            print(art_dict.get("reference"), " : ", f.errors)


if __name__ == "__main__":
    # import_articles()
    # article_from_article_update()
    main()
