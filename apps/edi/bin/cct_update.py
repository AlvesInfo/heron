# pylint: disable=E0401,C0303
"""
FR : Module d'update des cct dans la table edi_import
EN : Module for updating ccts in the edi_import table

Commentaire:

created at: 2022-12-29
created by: Paulo ALVES

modified at: 2022-12-29
modified by: Paulo ALVES
"""
from psycopg2 import sql
from django.db import connection, transaction


@transaction.atomic
def update_cct_edi_import():
    """Fonction d'update des cct depuis book_supplier_cct"""
    with connection.cursor() as cursor:
        sql_update_cct = sql.SQL(
            """
            update edi_ediimport edi
               set cct_uuid_identification = cc.cct_uuid_identification
             from (
               select
                     ei."id", re.cct_uuid_identification
               from edi_ediimport ei
               left join (
                     select
                            ee."id", 
                            ee.third_party_num, 
                            ee.supplier, 
                            ee.code_fournisseur, 
                            ee.maison, 
                            ee.code_maison, 
                            bs.cct_identifier, 
                            bs.cct_uuid_identification
                 from edi_ediimport ee
                 left join (
                        select
                           bsp.third_party_num, 
                           ccm.uuid_identification as cct_uuid_identification, 
                           unnest(string_to_array("cct_identifier", '|')) as cct_identifier
                        from book_suppliercct bsp
                        join accountancy_cctsage ac 
                        on bsp.cct_uuid_identification = ac.uuid_identification 
                        join centers_clients_maison ccm 
                        on ac.cct = ccm.cct
                 ) bs
                 on ee.third_party_num = bs.third_party_num
                 where ee.third_party_num = bs.third_party_num
                 and ee.code_maison = bs.cct_identifier
               ) re
               on ei.id = re.id
               where cct_identifier is not null
            ) cc
            where edi."id" = cc."id"
            and edi.cct_uuid_identification isnull
            """
        )
        cursor.execute(sql_update_cct)
