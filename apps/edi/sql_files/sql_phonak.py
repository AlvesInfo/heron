# pylint: disable=E0401,C0303
"""
FR : Module des requêtes sql de post-traitement après import des fichiers Phonak
EN : Post-processing sql module after importing supplier invoice files

Commentaire:

created at: 2022-11-27
created by: Paulo ALVES

modified at: 2022-11-27
modified by: Paulo ALVES
"""
from psycopg2 import sql

post_phonak_dict = {
    "sql_update": sql.SQL(
        """
        update "edi_ediimport"
        set 
            "invoice_type" = case when "invoice_type" = 'FA' then '380' else '381' end,
            "gross_unit_price" = ("gross_amount"::numeric / "qty"::numeric)::numeric,
            "net_unit_price" = ("net_amount"::numeric / "qty"::numeric)::numeric,
            "purchase_invoice" = true,
            "client_invoice" = true
        where "uuid_identification" = %(uuid_identification)s
        and ("valid" = false or "valid" isnull)
        """
    ),
    "sql_net_amount": sql.SQL(
        """
        update "edi_ediimport" edi
        set
            "net_amount" = case
                                when ("invoice_type" = '381' and "qty" < 0) 
                                  or ("invoice_type" = '380' and "qty" < 0) 
                                then -abs("net_amount")::numeric
                                when ("invoice_type" = '381' and "qty" > 0) 
                                  or ("invoice_type" = '380' and "qty" > 0) 
                                then abs("net_amount")::numeric
                            end
        where "uuid_identification" = %(uuid_identification)s
        and ("valid" = false or "valid" isnull)
        """
    ),
    "sql_mulitiple_dates": sql.SQL(
        """
        update "edi_ediimport" edi
        set
            "invoice_date" = inv."invoice_date"
        from (
            select 
                invoice_number, 
                (
                    date_trunc('month', max(invoice_date)) 
                    + interval '1 month - 1 day'
                )::date as invoice_date 
            from edi_ediimport ee 
            group by invoice_number 
        ) inv
        where edi."invoice_number" = inv."invoice_number"
        and edi."uuid_identification" = %(uuid_identification)s
        and (edi."valid" = false or edi."valid" isnull)
        """
    ),
}
