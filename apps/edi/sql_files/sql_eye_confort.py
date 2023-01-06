# pylint: disable=
"""
FR : Module des requêtes sql de post-traitement après import des fichiers eye Confort
EN : Post-processing sql module after importing supplier invoice files

Commentaire:

created at: 2022-11-27
created by: Paulo ALVES

modified at: 2022-11-27
modified by: Paulo ALVES
"""
from psycopg2 import sql

post_eye_dict = {
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
            "gross_amount" = case 
                                when "net_amount" = 0 then 0
                                when "net_amount" < 0 
                                    then (abs("gross_amount")::numeric * -1::numeric)
                                when "net_amount" > 0 then abs("gross_amount")::numeric
                            end,
            "gross_unit_price" = abs(
                (
                    case 
                        when "net_amount" = 0 then 0
                        when "net_amount" < 0 
                            then (abs("gross_amount")::numeric * -1::numeric)
                        when "net_amount" > 0 then abs("gross_amount")::numeric
                    end 
                    / 
                    "qty"::numeric
                )::numeric
            ),
            "net_unit_price" = abs(("net_amount"::numeric / "qty"::numeric)::numeric),
            "vat_rate" = 0,
            "vat_amount" = 0,
            "amount_with_vat" = "net_amount"::numeric,
            "purchase_invoice" = true,
            "sale_invoice" = true
        where "uuid_identification" = %(uuid_identification)s
        and ("valid" = false or "valid" isnull)
        """
    ),
}
