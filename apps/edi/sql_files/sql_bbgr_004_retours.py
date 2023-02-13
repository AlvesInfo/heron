# pylint: disable=
"""
FR : Module des requêtes sql de post-traitement après import des fichiers BBGR Retours
EN : Post-processing sql module after importing supplier invoice files

Commentaire:

created at: 2022-11-27
created by: Paulo ALVES

modified at: 2022-11-27
modified by: Paulo ALVES
"""
from psycopg2 import sql

bbgr_004_retours_dict = {
    "sql_vat": sql.SQL(
        """
        update "edi_ediimport"
        set 
            "vat_rate" = ("vat_rate"::numeric / 100::numeric)::numeric
        where "uuid_identification" = %(uuid_identification)s
        and ("valid" = false or "valid" isnull)
        """
    ),
    "sql_vat_amount": sql.SQL(
        """
        update "edi_ediimport"
        set 
            "vat_amount" = round("vat_rate" * "net_amount", 2)::numeric,
            "amount_with_vat" = (
                round("vat_rate" * "net_amount", 2)::numeric
                +
                "net_amount"
            )::numeric
        where "uuid_identification" = %(uuid_identification)s
        and ("valid" = false or "valid" isnull)
        """
    ),
    "sql_total_amount_by_invoices": sql.SQL(
        """
        update edi_ediimport ei 
        set 
            "invoice_amount_without_tax" = rec."invoice_amount_without_tax",
            "invoice_amount_tax" = rec."invoice_amount_tax",
            "invoice_amount_with_tax" = rec."invoice_amount_with_tax"
        from (
            select 
                "uuid_identification", 
                "invoice_number", 
                case 
                    when "invoice_type" = '380' 
                        then abs(sum("net_amount")) 
                        else -abs(sum("net_amount"))
                end as "invoice_amount_without_tax", 
                    case 
                    when "invoice_type" = '380' 
                        then abs(sum("vat_amount")) 
                        else -abs(sum("vat_amount"))
                end as "invoice_amount_tax",
                    case 
                    when "invoice_type" = '380' 
                        then abs(sum("amount_with_vat")) 
                        else -abs(sum("amount_with_vat"))
                end as "invoice_amount_with_tax"
            from "edi_ediimport" ee 
            where "uuid_identification" = %(uuid_identification)s
            and ("valid" = false or "valid" isnull)
            group by "uuid_identification" , "invoice_number", "invoice_type"
        ) rec 
        where ei."uuid_identification" = rec."uuid_identification"
        and ei."invoice_number" = rec."invoice_number"
        """
    ),
}
