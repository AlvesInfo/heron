# pylint: disable=E0401,C0303
"""
FR : Module de génération du fichier BBGR Statment
EN : BBGR Statement file generation module

Commentaire:

created at: 2022-04-10
created by: Paulo ALVES

modified at: 2022-04-10
modified by: Paulo ALVES
"""
from pathlib import Path

from psycopg2 import sql
from django.db import connection

from apps.core.functions.functions_setups import settings


def generate_bbgr_stament_file():
    """Génération du ficfier csv du statment"""

    with connection.cursor() as cursor:
        # ID Minimum pour le premier import
        historic_id = 1947055
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
                from suppliers_invoices_invoice sii 
                join suppliers_invoices_invoicedetail sii2 
                on sii.uuid_identification  = sii2.uuid_invoice 
                where sii.flow_name = 'BbgrStatment'
            ) req
            """
        )
        cursor.execute(sql_id, {"historic_id": historic_id})

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
        cursor.execute(sql_id, {"historic_id": historic_id})
        test_have_lines = cursor.fetchone()
        print("vérification BBGR statment")
        if test_have_lines:
            print("Génération du fichier BBGR Statment")
            file_path = Path(settings.BBGR_STATMENT) / f"bbgr_statment_sup_{min_id}.csv"

            if file_path.exists():
                file_path.unlink()

            sql_statment = sql.SQL(
                """
                COPY (
                    select
                       'BbgrStatment' as "supplier_ident",
                       '9524514' as "siret_payeur",
                       "boutique_bbgr" as "code_fournisseur",
                       "boutique_acuitis" as "code_maison",
                       "nom_boutique" as "maison",
                       "ref_cde_acuitis" as "acuitis_order_number",
                       "livraison" as "delivery_number",
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
                       "article_facturation" as "libelle",
                       "type_article" as "famille",
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
                       "id" as "bi_id"
                    from "heron_bi_factures_billstatement"
                    where "id" > %(min_id)s
                ) TO %(file_path)s DELIMITER ';' CSV HEADER ENCODING 'UTF8';
                """
            )
            cursor.execute(sql_statment, {"min_id": min_id, "file_path": str(file_path.resolve())})


if __name__ == "__main__":
    generate_bbgr_stament_file()
