# pylint: disable=E0401,C0303
"""
FR : Module des requêtes sql de post-traitement après import des fichiers Starkey
EN : Post-processing sql module after importing supplier invoice files

Commentaire:

created at: 2022-11-27
created by: Paulo ALVES

modified at: 2022-11-27
modified by: Paulo ALVES
"""
from psycopg2 import sql

post_starkey_dict = {
    "sql_update": sql.SQL(
        """
        update "edi_ediimport"
        set 
            "qty" = case 
                        when "net_amount" < 0 then (abs("qty")::numeric * -1::numeric)
                        when "net_amount" > 0 then abs("qty")::numeric
                        else "qty" 
                    end,
            "invoice_type" = case when "invoice_type" = 'FA' then '380' else '381' end,
            "net_unit_price" = abs("net_amount"::numeric / "qty"::numeric)::numeric,
            "gross_unit_price" = abs("gross_unit_price"),
            "gross_amount" = case 
                                when "net_amount" = 0 then 0
                                when "net_amount" < 0 
                                    then (
                                        abs("gross_unit_price"::numeric * "qty"::numeric)::numeric 
                                        * 
                                        -1::numeric
                                    )
                                when "net_amount" > 0 
                                    then (
                                        abs("gross_unit_price"::numeric * "qty"::numeric)::numeric 
                                    )
                            end,
            "purchase_invoice" = true,
            "sale_invoice" = true
        where "uuid_identification" = %(uuid_identification)s
        and ("valid" = false or "valid" isnull)
        """
    ),
}
