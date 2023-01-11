# pylint: disable=E0401,C0303
"""
FR : Module des requêtes sql de post-traitement après import des fichiers de factures Cosium
EN : Post-processing sql module after importing supplier Cosium invoice files

Commentaire:

created at: 2023-11-11
created by: Paulo ALVES

modified at: 2023-03-11
modified by: Paulo ALVES
"""
from psycopg2 import sql

post_cosium_dict = {
    "sql_ttc_a_zero": sql.SQL(
        """
    update "edi_ediimport" "edi"
    set "net_amount" = 0,
        "gross_amount" = 0,
        "discount_price_01" = -abs("qty" * "net_unit_price")::numeric
    where "uuid_identification" = %(uuid_identification)s
      and ("valid" = false or "valid" isnull)
      and "amount_with_vat" = 0
    """
    ),
    "sql_totaux": sql.SQL(
        """
        update edi_ediimport ei
        set invoice_type = case when req.total_amount < 0 then '381' else '380'end,
            "gross_amount" = case 
                            when req."total_amount" < 0 
                            then -abs("gross_amount") 
                            else abs("gross_amount") 
                        end,
            "qty" = case 
                    when req."total_amount" < 0 
                    then -abs("qty") 
                    else abs("qty") 
                end,
            "purchase_invoice" = true,
            "sale_invoice" = true
        from (
            select 
                "uuid_identification", 
                "invoice_number", 
                "invoice_date", 
                sum("net_amount") as "total_amount"
            from "edi_ediimport" ee
            where ee."uuid_identification" = %(uuid_identification)s
              and ("valid" = false or "valid" isnull)
            group by "uuid_identification", "invoice_number", "invoice_date"
        ) req 
        where req."uuid_identification" = ei."uuid_identification"
        and req."invoice_number" = ei."invoice_number"
        and req."invoice_date" = ei."invoice_date"
        and ei."uuid_identification" = %(uuid_identification)s
        and ("valid" = false or "valid" isnull)
        """
    )
}
