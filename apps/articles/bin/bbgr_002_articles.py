# pylint: disable=E0401,C0303
"""
FR : Module d'intégration depuis la B.I des articles pour BBGR002 (Statment)
EN : Integration module from the B.I of articles for BBGR002 (Statment)

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


def insert_bbgr_002_articles():
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
                "packaging_qty"
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
                -- px_revient_aval pour BBGR002
                hba."px_revient_aval" as "catalog_price",
                gen_random_uuid() as uuid_identification,
                (select "axe_bu" from "accountancy_defaultaxearticle" ad limit 1) as "axe_bu",
                (select "axe_prj" from "accountancy_defaultaxearticle" ad limit 1) as "axe_prj",
                (select "axe_pys" from "accountancy_defaultaxearticle" ad limit 1) as "axe_pys",
                (select "axe_rfa" from "accountancy_defaultaxearticle" ad limit 1) as "axe_rfa",
                (
                    select 
                        "axe_pro" 
                     from accountancy_defaultaxeproaricleacuitis adf 
                    where adf."famille_acuitis" = hba."famille"
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
                'BBGR002' as "third_party_num",
                hba.famille as "famille_acuitis",
                'f2dda460-20db-4b05-8bb8-fa80a1ff146b'::uuid as "uuid_big_category",
                'd3888b89-0847-4dc2-ae8f-f1da36bde2b7'::uuid as "created_by",
                1 as "packaging_qty"
            from "heron_bi_articles" hba 
            where (hba."code_rayon" != 'SAV' and hba."famille" != 'SAV')
            on conflict do nothing
            """
        )
        cursor.execute(sql_articles)


if __name__ == "__main__":
    insert_bbgr_002_articles()
