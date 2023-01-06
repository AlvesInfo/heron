# pylint: disable=E0401,C0303
"""
FR : Module des requêtes sql de post-traitement après import des fichiers Newson
EN : Post-processing sql module after importing supplier invoice files

Commentaire:

created at: 2022-11-27
created by: Paulo ALVES

modified at: 2022-11-27
modified by: Paulo ALVES
"""
from psycopg2 import sql

post_newson_dict = {
    "sql_update": sql.SQL(
        """
        update "edi_ediimport"
        set 
            "invoice_type" = case when "invoice_type" = 'FA' then '380' else '381' end,
            "gross_unit_price" = ("gross_amount"::numeric / "qty"::numeric)::numeric,
            "net_unit_price" = ("net_amount"::numeric / "qty"::numeric)::numeric,
            "famille" = left("reference_article", 2),
            "net_amount" = case
                                when ("invoice_type" = '381' and "qty" < 0) 
                                  or ("invoice_type" = '380' and "qty" > 0) 
                                then abs(round("net_amount", 2)::numeric)::numeric
                                when ("invoice_type" = '381' and "qty" > 0) 
                                  or ("invoice_type" = '380' and "qty" < 0) 
                                then -abs("net_amount")::numeric
                            end,
            "amount_with_vat" = round(round("amount_with_vat", 2) * (1 + "vat_rate"), 2)::numeric,
            "purchase_invoice" = true,
            "sale_invoice" = true
        where "uuid_identification" = %(uuid_identification)s
        and ("valid" = false or "valid" isnull)
        """
    ),
}
