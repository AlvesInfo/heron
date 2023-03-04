# pylint: disable=E0401
"""
Génération du chiffre d'affaires par clients et par AXE_PRO, issus des ventes Cosium
FR : Module de génération du chiffre d'affaire par clients, issus des ventes Cosium
EN : Module for generating turnover by customers, from Cosium sales

Commentaire:

created at: 2023-03-04
created by: Paulo ALVES

modified at: 2023-03-04
modified by: Paulo ALVES
"""
from typing import AnyStr
from uuid import UUID

from psycopg2 import sql
from django.db import connection, transaction


def set_ca(dte_d: AnyStr, dte_f: AnyStr):
    """Génération du chiffre d'affaires par clients et par AXE_PRO, issus des ventes Cosium
    :param dte_d: Date de début de période au format texte isoformat
    :param dte_f: Date de fin de période au format texte isoformat
    :return:
    """
    with connection.cursor() as cursor:
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
                "unity",
                "purchase_invoice",
                "sale_invoice"
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
               1 as "unity",
               true as "purchase_invoice",
               false as "sale_invoice"
            from "heron_bi_factures_billstatement"
            where "id" > %(min_id)s
            order by "id"
            """
        )
        cursor.execute(
            sql_insert_statment, {"min_id": min_id, "uuid_identification": uuid_identification}
        )