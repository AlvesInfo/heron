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
                -- px_cession_ht_eur pour BBGR003 et BBGR004
                hba."px_cession_ht_eur" as "catalog_price",
                gen_random_uuid() as uuid_identification,
                '71c82478-affe-45d5-8113-13f745bab0e1'::uuid as "axe_bu",
                '522e0110-35e6-4f31-8588-1d4dcc5ae378'::uuid as "axe_prj",
                'fe60f32f-c879-484d-9aa4-200cc222cdbd'::uuid as "axe_pys",
                null as "axe_rfa",
                case 
                    when hba."famille" = 'ACCESS AUDIO' 
                        then '402ea144-43f1-4e99-8719-b62e3fcf7d66'::uuid 
                    when hba."famille" = 'ACCESS OPTIQUE' 
                        then '6cb598af-288f-4ac5-bee0-12c7a3315078'::uuid 
                    when hba."famille" = 'ACCESSOIRES' 
                        then '6cb598af-288f-4ac5-bee0-12c7a3315078'::uuid 
                    when hba."famille" = 'AIDES AUDITIVES' 
                        then '9a3e9ef1-e462-4330-b5e2-54d993c70af9'::uuid
                    when hba."famille" = 'CONSOMMABLE' 
                        then '68fe5983-33ef-4eff-8e31-502108ebfd80'::uuid
                    when hba."famille" = 'CONTACTO SOL' and hba."code_rayon" = 'SOLUTIONS' 
                        then '672b9f6e-5212-4c07-8729-e6dd3e5bda05'::uuid
                    when hba."famille" = 'CONTACTO SOL' 
                        then 'b8508869-39a1-4b2a-a9b3-2224bccda573'::uuid
                    when hba."famille" = 'MONTURE OPT' 
                        then 'a3e93cfb-503c-45db-9144-b18aea6807b3'::uuid
                    when hba."famille" = 'MONTURE SOL' 
                        then '40336fdc-ab66-4039-b7a5-2cfbcff9930d'::uuid
                    when hba."famille" = 'PILES' 
                        then 'acf1be0d-54ac-4dcd-8b04-aa61f9942e2d'::uuid
                    when hba."famille" = 'SAV' 
                        then '6cb598af-288f-4ac5-bee0-12c7a3315078'::uuid
                    when hba."famille" = 'VERRES' 
                        then 'e009ed01-e2c8-4caa-85b4-6b66c3d08394'::uuid
                    else 'bdb926d6-5ffd-4a6c-973d-8de57e2be71b'::uuid
                end as "axe_pro",
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
    insert_bbgr_003_articles()
