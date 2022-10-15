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
                supplier=get_society('TECH001'),
                reference=article.reference,
                libelle=article.libelle,
                libelle_heron=article.libelle,
            )
            print(objet, created)
        except django.db.utils.IntegrityError:
            pass


if __name__ == "__main__":
    # import_articles()
    article_from_article_update()
