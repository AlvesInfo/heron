# pylint: disable=E0401,C0303
"""
FR : Module de génération du fichier BBGR Receptions
EN : BBGR Receptions file generation module

Commentaire:

created at: 2023-01-04
created by: Paulo ALVES

modified at: 2023-01-04
modified by: Paulo ALVES
"""
from uuid import UUID

from psycopg2 import sql
from django.db import connection, transaction

from apps.core.functions.functions_setups import settings

HISTORIC_RECEPTIONS_ID = 17732


@transaction.atomic
def insert_bbgr_receptions_file(uuid_identification: UUID):
    """Intégration des lignes de la table des Réceptions
    :param uuid_identification: uuid_identification de la trace
    :return:
    """

    with connection.cursor() as cursor:
        # ID Minimum pour le premier import
        sql_id = sql.SQL(
            """
            select 
                max(max_id) as max_id
            from (
                select  
                    coalesce(max(bi_id), %(historic_id)s) as max_id 
                from edi_ediimport ee 
                where flow_name = 'BbgrReceptions'
                union all 
                select 
                    coalesce(max(bi_id), %(historic_id)s) as max_id 
                from suppliers_invoices_invoice sii 
                join suppliers_invoices_invoicedetail sii2 
                on sii.uuid_identification  = sii2.uuid_invoice 
                where sii.flow_name = 'BbgrReceptions'
            ) req
            """
        )
        cursor.execute(sql_id, {"historic_id": HISTORIC_RECEPTIONS_ID})

        min_id = cursor.fetchone()[0]

        # On vérifie si il existe des lignes à importer
        sql_id = sql.SQL(
            """
            select
                "id"
            from heron_bi_receptions_bbgr br
            where "id" > %(historic_id)s
            limit 1
            """
        )
        cursor.execute(sql_id, {"historic_id": HISTORIC_RECEPTIONS_ID})
        test_have_lines = cursor.fetchone()
        print("vérification BBGR Réceptions")

        if test_have_lines:
            print("intégration des lignes BBGR Réceptions")
            sql_insert_retours = sql.SQL(
                """
                with vat as (
                    select 
                        rate
                    from accountancy_vatratsage av 
                    where vat = '001'
                    and exists (
                        select 1 
                        from accountancy_vatratsage avv 
                        group by avv.vat 
                        having max(avv.vat_start_date) = av.vat_start_date and avv.vat = av.vat
                    )
                )
                insert into edi_ediimport 
                (
                    "uuid_identification",
                    "created_at",
                    "modified_at",
                    "flow_name",
                    "supplier_ident",
                    "siret_payeur",
                    "code_fournisseur",
                    "code_maison",
                    "maison",
                    "delivery_number",
                    "delivery_date",
                    "invoice_number",
                    "invoice_date",
                    "invoice_type",
                    "devise",
                    "reference_article",
                    "libelle",
                    "famille",
                    "qty",
                    "gross_unit_price",
                    "net_unit_price",
                    "gross_amount",
                    "net_amount",
                    "vat_rate",
                    "vat_amount",
                    "amount_with_vat",
                    "axe_pro_supplier",
                    "supplier_name",
                    "bi_id",
                    "unity",
                    "purchase_invoice",
                    "client_invoice"
                )
                select
                    %(uuid_identification)s as "uuid_identification",
                    now() as "created_at",
                    now() as "modified_at",
                   'BbgrReceptions' as "flow_name",
                   'BbgrReceptions' as "supplier_ident",
                   '9524514' as "siret_payeur",
                   'CAHA' as "code_fournisseur",
                   'CAHA' as "code_maison",
                   'ACUITIS' as "maison",
                   'BL-'||max(id) as "delivery_number",
                   date_trunc('month', entered_date) as "delivery_date",
                   max("id") as "invoice_number",
                   date_trunc('month', entered_date) as "invoice_date",
                   case 
                        when sum("entered_valorise") >= 0 
                        then '380' 
                        else '381' 
                    end as "invoice_type",
                   'EUR' as "devise",
                   "type_article"||'-'||"famille" as "reference_article",
                   "type_article"||'-'||"famille" as "libelle",
                   "famille" as "famille",
                   1 as "qty",
                   sum("entered_valorise") as "gross_unit_price",
                   sum("entered_valorise") as "net_unit_price",
                   sum("entered_valorise") as "gross_amount",
                   sum("entered_valorise") as "net_amount",
                   (select rate from vat) as "vat_rate",
                   round(
                        ((select rate from vat)::numeric/100) 
                        * 
                        sum("entered_valorise")::numeric, 2
                    )::numeric as "vat_amount",
                   round(
                        ((select rate from vat)::numeric/100) 
                        * 
                        sum("entered_valorise")::numeric, 2
                    )::numeric + sum("entered_valorise") as "amount_with_vat",
                   "type_article" as "axe_pro_supplier",
                   'BBGR RECEPTIONS' as "supplier_name",
                   max("id") as "bi_id",
                   11 as "unity",
                   false as "purchase_invoice",
                   true as "client_invoice"
                from "heron_bi_receptions_bbgr"
                where "id" > %(min_id)s
                group by "famille", "type_article", date_trunc('month', entered_date) 
                order by max("id")
                """
            )
            cursor.execute(
                sql_insert_retours, {"min_id": min_id, "uuid_identification": uuid_identification}
            )


if __name__ == "__main__":
    insert_bbgr_receptions_file("3b0183a3-e2f9-4a1a-9c47-aa753c300a1e")
