# pylint: disable=E0401,C0303
"""
FR : Module de génération du fichier BBGR Retours
EN : BBGR Returns file generation module

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

HISTORIC_RETOURS_ID = 2074484


@transaction.atomic
def insert_bbgr_retours_file(uuid_identification: UUID):
    """Intégration des lignes de la table des Retours
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
                where flow_name = 'BbgrRetours'
                union all 
                select 
                    coalesce(max(bi_id), %(historic_id)s) as max_id 
                from invoices_invoicecommondetails 
                where flow_name = 'BbgrRetours'
            ) req
            """
        )
        cursor.execute(sql_id, {"historic_id": HISTORIC_RETOURS_ID})

        min_id = cursor.fetchone()[0]

        # On vérifie si il existe des lignes à importer
        sql_id = sql.SQL(
            """
            select
                "id"
            from heron_bi_factures_monthlydelivery hbfm 
            where type_article in ('FRAIS_RETOUR', 'DECOTE')
            and "id" > %(historic_id)s
            limit 1
            """
        )
        cursor.execute(sql_id, {"historic_id": min_id})
        test_have_lines = cursor.fetchone()
        print("vérification BBGR Retours")

        if test_have_lines:
            print("intégration des lignes BBGR Retours")
            sql_insert_retours = sql.SQL(
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
                   'BbgrRetours' as "flow_name",
                   'BbgrRetours' as "supplier_ident",
                   '9524514' as "siret_payeur",
                   "code_fournisseur",
                   "code_maison",
                   "maison",
                   "acuitis_order_number",
                   "delivery_number",
                   "delivery_date",
                   "invoice_number",
                   "invoice_date",
                   "invoice_type",
                   'EUR' as "devise",
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
                   'BBGR RETOURS' as "supplier_name",
                   "bi_id",
                   1 as "unit_weight",
                   false as "purchase_invoice",
                   true as "sale_invoice",
                   0 as "item_weight"
                from (
                    select
                       "boutique_bbgr" as "code_fournisseur",
                       "boutique_acuitis" as "code_maison",
                       "nom_boutique" as "maison",
                       "customer_po_number" as "acuitis_order_number",
                       case 
                            when "livraison" = '0' 
                            then '' 
                            else "livraison" 
                       end as "delivery_number",
                       "date_livraison" as "delivery_date",
                       coalesce(
                            case when "livraison" = '' then null else "livraison" end,
                            case when "no_facture_acuitis" = '' then null else "no_facture_acuitis" end, 
                            max("id")::varchar
                        ) as "invoice_number",
                       "date_mouvement" as "invoice_date",
                       case 
                            when sum("qte_expediee") > 0
                            then '380' 
                            else '381' 
                        end as "invoice_type",
                       'FRAIS_RETOUR' as "reference_article",
                       null as "ean_code",
                       'Frais de retour' as "libelle",
                       'FRAIS_RETOUR' as "famille",
                       sum("qte_expediee") as "qty",
                       "prix_unitaire" as "gross_unit_price",
                       "prix_unitaire" as "net_unit_price",
                       sum("montant_ht") as "gross_amount",
                       sum("montant_ht") as "net_amount",
                       "taux_tva" as "vat_rate",
                       0 as "vat_amount",
                       0 as "amount_with_vat",
                       "statistique" as "axe_pro_supplier",
                       max("id") as "bi_id"
                    from "heron_bi_factures_monthlydelivery"
                    where "id" > %(min_id)s
                    and "type_article" = 'FRAIS_RETOUR'
                    group by 
                        "boutique_bbgr",
                        "boutique_acuitis",
                        "nom_boutique",
                        "customer_po_number", 
                        "livraison",
                        "date_livraison",
                        "no_facture_acuitis",
                        "date_mouvement",
                        "famille",
                        "prix_unitaire",
                        "taux_tva",
                        "statistique"
                            
                   union all 
                               
                   select
                   "boutique_bbgr" as "code_fournisseur",
                   "boutique_acuitis" as "code_maison",
                   "nom_boutique" as "maison",
                   "customer_po_number" as "acuitis_order_number",
                   "livraison" as "delivery_number",
                   "date_livraison" as "delivery_date",
                   coalesce(
                        case when "livraison" = '' then null else "livraison" end,
                        case when "no_facture_acuitis" = '' then null else "no_facture_acuitis" end, 
                        "id"::varchar
                    ) as "invoice_number",
                   "date_mouvement" as "invoice_date",
                   case 
                        when "qte_expediee" > 0
                        then '380' 
                        else '381' 
                    end as "invoice_type",
                   case
                        when left("description", 11) = 'Décote de 1' then 'D1-'||"article"
                        when left("description", 11) = 'Décote de 2' then 'D2-'||"article"
                        else 'D3-'||"article"
                   end as "reference_article",
                   "article" as "ean_code",
                   "description" as "libelle",
                   "famille" as "famille",
                   "qte_expediee" as "qty",
                   "prix_unitaire" as "gross_unit_price",
                   "prix_unitaire" as "net_unit_price",
                   "montant_ht" as "gross_amount",
                   "montant_ht" as "net_amount",
                   "taux_tva" as "vat_rate",
                   0 as "vat_amount",
                   0 as "amount_with_vat",
                   "statistique" as "axe_pro_supplier",
                   "id" as "bi_id"
                from "heron_bi_factures_monthlydelivery"
                where "id" > %(min_id)s
                and "type_article"= 'DECOTE'
            ) retours 
            order by "bi_id"
            """
            )
            cursor.execute(
                sql_insert_retours, {"min_id": min_id, "uuid_identification": uuid_identification}
            )


if __name__ == "__main__":
    insert_bbgr_retours_file("3b0183a3-e2f9-4a1a-9c47-aa753c300a1e")
