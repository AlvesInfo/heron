# pylint: disable=E0401,C0303
"""
FR : Module des requêtes sql de post-traitement après import des fichiers Signia
EN : Post-processing sql module after importing supplier invoice files

Commentaire:

created at: 2022-11-27
created by: Paulo ALVES

modified at: 2022-11-27
modified by: Paulo ALVES
"""
from psycopg2 import sql

post_signia_dict = {
    "sql_update_units": sql.SQL(
        """
        update "edi_ediimport"
        set 
            "qty" = case when "qty" = 0 then 1::numeric else "qty" end
        where "uuid_identification" = %(uuid_identification)s
        and ("valid" = false or "valid" isnull)
        """
    ),
    "sql_update": sql.SQL(
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
                                when "net_amount" < 0 then (abs("gross_amount")::numeric * -1::numeric)
                                when "net_amount" > 0 then abs("gross_amount")::numeric
                            end,
            "famille" = case
                            when "libelle" ilike 'DELIVERY%%' then 'PORT'
                            when "libelle" ilike '%%FREIGHT%%' then 'PORT'
                            when "libelle" ilike 'WARRANTY%%' then 'WARRANTY'
                            when "libelle" ilike 'DISCOUNT INSTANT' then 'RFA'
                            else "famille"
                        end,
            "invoice_type" = case 
                                when "invoice_type" = '301' then '380' 
                                when "invoice_type" = '307' then '380' 
                                when "invoice_type" = '302' then '381' 
                                when "invoice_type" = '304' then '381' 
                                when "invoice_type" = '400' then '381' 
                                -- 400 = RFA
                                else '380' 
                            end,
            "purchase_invoice" = true,
            "sale_invoice" = true
        where "uuid_identification" = %(uuid_identification)s
        and ("valid" = false or "valid" isnull)
        """
    ),
    "sql_update_bl": sql.SQL(
        """
        update "edi_ediimport" "ei"
        set "delivery_number" = "req"."delivery_number"
        from (
            select 
                max("delivery_number") as "delivery_number", 
                "invoice_number", 
                "uuid_identification"
            from "edi_ediimport"
            where "uuid_identification" = %(uuid_identification)s
            and ("valid" = false or "valid" isnull)
            group by "invoice_number", "uuid_identification"
            HAVING 
                max("delivery_number") != '' 
            and max("delivery_number") is not null
        ) "req" 
        where 
            "ei"."invoice_number" = "req"."invoice_number"
        and	"ei"."uuid_identification"= "req"."uuid_identification"
        """
    ),
}
