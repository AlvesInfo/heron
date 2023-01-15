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
                ee."id", 
                aa."axe_bu", 
                aa."axe_prj", 
                aa."axe_pro", 
                aa."axe_pys", 
                aa."axe_rfa" 
            from "edi_ediimport" ee 
            join "articles_article" aa 
            on ee."reference_article" = aa."reference" 
            and ee."third_party_num" = aa."third_party_num"
            where (ee."valid" = false or ee."valid" isnull)
            and ee."axe_pro_uuid" isnull
            and aa."axe_pro" is not null
        ) maj
        where edi."id" = maj."id" 
        and (edi."valid" = false or edi."valid" isnull)
    """
    ),
}
