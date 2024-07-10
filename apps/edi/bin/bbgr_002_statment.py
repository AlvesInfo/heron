# pylint: disable=E0401,C0303
"""
FR : Module de génération du fichier BBGR Statment
EN : BBGR Statement file generation module

Commentaire:

created at: 2022-12-10
created by: Paulo ALVES

modified at: 2022-12-10
modified by: Paulo ALVES
"""
from uuid import UUID

from psycopg2 import sql
from django.db import connection, transaction

# from apps.core.functions.functions_setups import settings


HISTORIC_STATMENT_ID = 1993598


@transaction.atomic
def insert_bbgr_stament_file(uuid_identification: UUID):
    """Intégration des lignes de la table des Statment
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
                where flow_name = 'BbgrStatment'
                union all 
                select 
                    coalesce(max(bi_id), %(historic_id)s) as max_id 
                from invoices_invoice sii 
                join invoices_invoicedetail sii2 
                on sii.uuid_identification  = sii2.uuid_invoice 
                where sii2.flow_name = 'BbgrStatment'
            ) req
            """
        )
        cursor.execute(sql_id, {"historic_id": HISTORIC_STATMENT_ID})

        min_id = cursor.fetchone()[0]

        # On vérifie si il existe des lignes à importer
        sql_id = sql.SQL(
            """
            select
                "id"
            from "heron_bi_factures_billstatement"
            where "id" > %(historic_id)s
            limit 1
            """
        )
        cursor.execute(sql_id, {"historic_id": min_id})
        test_have_lines = cursor.fetchone()
        print("vérification BBGR statment")

        if test_have_lines:
            print("intégration des lignes BBGR Statment")
            sql_insert_statment = sql.SQL(
                """
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
                    "acuitis_order_number",
                    "delivery_number",
                    "delivery_date",
                    "invoice_number",
                    "invoice_date",
                    "invoice_type",
                    "devise",
                    "reference_article",
                    "ean_code",
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
                    "unit_weight",
                    "purchase_invoice",
                    "sale_invoice",
                    "item_weight"
                )
                select
                    %(uuid_identification)s as "uuid_identification",
                    now() as "created_at",
                    now() as "modified_at",
                   'BbgrStatment' as "flow_name",
                   'BbgrStatment' as "supplier_ident",
                   '9524514' as "siret_payeur",
                   "boutique_bbgr" as "code_fournisseur",
                   "boutique_acuitis" as "code_maison",
                   "nom_boutique" as "maison",
                   "ref_cde_acuitis" as "acuitis_order_number",
                   case when "livraison" = '0' then '' else "livraison" end as "delivery_number",
                   "date_livraison" as "delivery_date",
                   "transaction" as "invoice_number",
                   "date_transaction" as "invoice_date",
                   case 
                        when "type_transaction" = 'INV' 
                        then '380' 
                        else '381' 
                    end as "invoice_type",
                   'EUR' as "devise",
                   "article" as "reference_article",
                   "article" as "ean_code",
                   case 
                        when left("article_facturation", 1) = ANY('{1,2,3,4,5,6,7,8,9}') 
                        then right("article_facturation", length("article_facturation")-14) 
                        else "article_facturation" 
                    end as "libelle",
                   case 
                        when "famille" is null or "famille" = '' 
                        then "article" 
                        else "famille" 
                   end as "famille",
                   "qte_facturee" as "qty",
                   "prix_unitaire" as "gross_unit_price",
                   "prix_unitaire" as "net_unit_price",
                   "montant_ht" as "gross_amount",
                   "montant_ht" as "net_amount",
                   "code_tva" as "vat_rate",
                   "montant_tva" as "vat_amount",
                   "montant_ttc" as "amount_with_vat",
                   "statistique" as "axe_pro_supplier",
                   'BBGR STATMENT' as "supplier_name",
                   "id" as "bi_id",
                   1 as "unit_weight",
                   true as "purchase_invoice",
                   false as "sale_invoice",
                   0 as "item_weight"
                from "heron_bi_factures_billstatement"
                where "id" > %(min_id)s
                order by "id"
                """
            )
            cursor.execute(
                sql_insert_statment, {"min_id": min_id, "uuid_identification": uuid_identification}
            )


if __name__ == "__main__":
    insert_bbgr_stament_file("3b0183a3-e2f9-4a1a-9c47-aa753c300a1e")
