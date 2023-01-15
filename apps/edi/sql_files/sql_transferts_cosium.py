# pylint: disable=E0401,C0303
"""
FR : Module des requêtes sql de post-traitement après import des Tranferts Cosium
EN : Post-processing sql module after importing supplier Cosium Transfers

Commentaire:

created at: 2023-01-14
created by: Paulo ALVES

modified at: 2023-01-14
modified by: Paulo ALVES
"""
from psycopg2 import sql

post_transfert_cosium_dict = {
    "sql_amounts": sql.SQL(
        """
    update "edi_ediimport" "edi"
    set "gross_unit_price" = "net_unit_price",
        "net_amount" = round(("qty"*"net_unit_price")::numeric, 2)::numeric,
        "gross_amount" = round(("qty"*"net_unit_price")::numeric, 2)::numeric,
        "vat_amount" = round(("qty"*"net_unit_price"*"vat_rate")::numeric, 2)::numeric,
        "amount_with_vat" = (
            round(("qty"*"net_unit_price"*"vat_rate")::numeric, 2)::numeric 
            + 
            round(("qty"*"net_unit_price")::numeric, 2)::numeric
        ),
        "purchase_invoice" = false,
        "sale_invoice" = true
    where "uuid_identification" = %(uuid_identification)s
      and ("valid" = false or "valid" isnull)
    """
    ),
    "sql_update_articles": sql.SQL(
        """
        update "edi_ediimport" edi 
        set 
            "axe_bu_uuid" = maj."axe_bu",
            "axe_prj_uuid" = maj."axe_prj",
            "axe_pro_uuid" = maj."axe_pro",
            "axe_pys_uuid"  = maj."axe_pys",
            "axe_rfa_uuid" = maj."axe_rfa"
        
        from (
            select			
                edi."id",
                (select "axe_bu" from "accountancy_defaultaxearticle" ad limit 1) as "axe_bu",
                (select "axe_prj" from "accountancy_defaultaxearticle" ad limit 1) as "axe_prj",
                (select "axe_pys" from "accountancy_defaultaxearticle" ad limit 1) as "axe_pys",
                (select "axe_rfa" from "accountancy_defaultaxearticle" ad limit 1) as "axe_rfa",
                (
                    select distinct
                        "axe_pro" 
                     from accountancy_defaultaxeproariclecosium adf 
                    where adf."famille" = edi."famille"
                      and adf."type_famille" = edi."axe_pro_supplier"
                ) as "axe_pro"
            from "edi_ediimport" edi
            where edi."uuid_identification" = 'c0077744-a2ee-4e6b-b45a-26e5362e429b'::uuid
              and (edi."valid" = false or edi."valid" isnull)
        ) maj
        where edi."uuid_identification" = %(uuid_identification)s
          and (edi."valid" = false or edi."valid" isnull)
          and  edi."id" = maj."id" 
    """
    ),
}
