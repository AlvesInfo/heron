# pylint: disable=E0401,C0303
"""
FR : Module des requêtes sql de post-traitement après import des fichiers Technidis
EN : Post-processing sql module after importing supplier invoice files

Commentaire:

created at: 2022-11-27
created by: Paulo ALVES

modified at: 2022-11-27
modified by: Paulo ALVES
"""
from psycopg2 import sql

post_technidis_dict = {
    "sql_update": sql.SQL(
        """
        with "group_technidis" as (
            select 
                case when sum(net_amount) < 0 then '381' else '380' end as "invoice_type", 
                "invoice_number", 
                "uuid_identification"
              from "edi_ediimport" 
             where "uuid_identification" = %(uuid_identification)s
               and ("valid" = false or "valid" isnull)
             group by "invoice_number", "uuid_identification"
        )
        update "edi_ediimport" "ei"
           set "invoice_type" = "gt"."invoice_type",
                "purchase_invoice" = true,
                "sale_invoice" = true
          from "group_technidis" "gt"
         where "ei"."uuid_identification" = "gt"."uuid_identification"
           and "ei"."invoice_number" = "gt"."invoice_number"
        """
    ),
    "sql_update_units": sql.SQL(
        """
        update "edi_ediimport"
        set 
            "qty" = case 
                        when "net_amount" < 0 then (abs("qty")::numeric * -1::numeric)
                        when "net_amount" > 0 then abs("qty")::numeric
                        else "qty" 
                    end,
            "gross_unit_price" = abs("gross_unit_price"),
            "net_unit_price" = abs("net_unit_price"),
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
            "famille" =   case 
                                        when "famille" is null or "famille" = ''
                                        then split_part("reference_article", '-', 1)
                                        else "famille"
                                    end
        where "uuid_identification" = %(uuid_identification)s
        and ("valid" = false or "valid" isnull)
        """
    ),
}
