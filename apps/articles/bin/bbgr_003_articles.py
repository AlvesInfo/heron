# pylint: disable=E0401,C0303
"""
FR : Module d'intégration depuis la B.I des articles pour BBGR003 (Monthly)
EN : Integration module from the B.I of articles for BBGR003 (Monthly)

Commentaire:

created at: 2022-12-31
created by: Paulo ALVES

modified at: 2022-12-31
modified by: Paulo ALVES
"""
import os
import platform
import sys

from psycopg2 import sql
from django.db import connection
import django

BASE_DIR = r"/"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")
django.setup()


def insert_bbgr_003_articles():
    """Intégration depuis la B.I des articles pour BBGR002"""

    with connection.cursor() as cursor:

        sql_articles = sql.SQL(
            """
            insert into "articles_article"
            (
                "created_at",
                "modified_at",
                "reference",
                "ean_code",
                "libelle",
                "libelle_heron",
                "brand",
                "item_weight",
                "manufacturer",
                "customs_code",
                "catalog_price",
                "uuid_identification",
                "axe_bu",
                "axe_prj",
                "axe_pys",
                "axe_rfa",
                "axe_pro",
                "made_in",
                "third_party_num",
                "famille_acuitis",
                "uuid_big_category",
                "created_by",
                "packaging_qty",
                "new_article"
            )
            select 
                now() as "created_at",
                now() as "modified_at",
                hba."code_ean" as "reference", 
                hba."code_ean" as "ean_code", 
                hba."designation" as "libelle", 
                hba."description_courte" as "libelle_heron",
                hba."marque" as "brand",
                case when hba."poids" isnull then 0 else hba."poids" end as "item_weight",
                hba."fabricant" as "manufacturer",
                hba."code_douanier" as "customs_code",
                -- px_cession_ht_eur pour BBGR003 et BBGR004
                hba."px_cession_ht_eur" as "catalog_price",
                gen_random_uuid() as uuid_identification,
                d_axes."axe_bu",
                d_axes."axe_prj",
                d_axes."axe_pys",
                d_axes."axe_rfa",
                (
                    select 
                        "axe_pro" 
                     from centers_purchasing_axeprofamilleacuitis adf 
                    where adf."code_famille_acuitis" = hba."famille"
                      and adf."code_rayon_acuitis" = case 
                                                        when hba."code_rayon" isnull 
                                                        then '' 
                                                        else hba."code_rayon" 
                                                    end
                ) as "axe_pro",
                case
                    when hba."made_in" ilike 'Allemagne' then 'DE'
                    when hba."made_in" ilike 'CE' then 'CE'
                    when hba."made_in" ilike 'Chine' then 'CN'
                    when hba."made_in" ilike 'Corée' then 'KR'
                    when hba."made_in" ilike 'France' then 'FR'
                    when hba."made_in" ilike 'Inde' then 'IN'
                    when hba."made_in" ilike 'Italie' then 'IT'
                    when hba."made_in" ilike 'Japan' then 'JP'
                    when hba."made_in" ilike 'Japon' then 'JP'
                    when hba."made_in" ilike 'RPC' then 'CN'
                    when hba."made_in" ilike 'Vietnam' then 'VN'
                    else null
                end "made_in",
                'BBGR003' as "third_party_num",
                hba.famille as "famille_acuitis",
                d_axes."uuid_big_category",
                'd3888b89-0847-4dc2-ae8f-f1da36bde2b7'::uuid as "created_by",
                1 as "packaging_qty",
                true as "new_article"
            from "heron_bi_articles" hba, 
            (
                select
                    "uuid_big_category",
                    "axe_bu", 
                    "axe_prj",
                    "axe_pys",
                    "axe_rfa"
                from "parameters_defaultaxearticle" ad 
                where "slug_name" = 'axes_articles'
                limit 1
            ) d_axes
            where (hba."code_rayon" != 'SAV' and hba."famille" != 'SAV')
            on conflict do nothing
            """
        )
        cursor.execute(sql_articles)


if __name__ == "__main__":
    insert_bbgr_003_articles()
