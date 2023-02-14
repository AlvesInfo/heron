# pylint: disable=E0401,C0303
"""
FR : Module des requêtes sql de post-traitement après import des fichiers Interson Protac
EN : Post-processing sql module after importing supplier invoice files

Commentaire:

created at: 2022-11-27
created by: Paulo ALVES

modified at: 2022-11-27
modified by: Paulo ALVES
"""
from psycopg2 import sql

post_interson_dict = {
    "sql_update": sql.SQL(
        """
        update "edi_ediimport"
        set 
            "invoice_type" = case when "invoice_type" = 'FA' then '380' else '381' end,
            "gross_amount" = ("gross_unit_price"::numeric * "qty"::numeric)::numeric,
            "net_amount" = round("net_unit_price"::numeric * "qty"::numeric, 2)::numeric,
            "reference_article" = case 
                                    when "reference_article" = '' or "reference_article" is null 
                                    then left("libelle", 35)
                                    else "reference_article"
                                  end,
            "purchase_invoice" = true,
            "sale_invoice" = true,
            "famille" = case 
                            when (
                                    "reference_article" ilike 'Chronopost%%' 
                                    or 
                                    "reference_article" ilike '%%port%%'
                                )
                                and
                                (
                                    "famille" is null or "famille" = ''
                                )
                            then 'PORT'
                            else "famille"
                        end
        where "uuid_identification" = %(uuid_identification)s
        and ("valid" = false or "valid" isnull)
        """
    ),
    "sql_bl_date": sql.SQL(
        """
        update "edi_ediimport" "edi" 
        set
            "delivery_number" = "sd"."single_delivery_number",
            "delivery_date" = "sd"."single_date"::date
        from (
            select
                "id",
                case 
                    when "delivery_number" ilike '%% du %%'  
                        and is_date(split_part("delivery_number", ' du ', 2))
                    then split_part(delivery_number, ' du ', 1) 
                else "delivery_number"
                end as "single_delivery_number",
                case 
                    when "delivery_number" ilike '%% du %%' 
                        and is_date(split_part("delivery_number", ' du ', 2))
                    then TO_DATE(split_part("delivery_number", ' du ', 2),'DD/MM/YYYY')::varchar
                    else null 
                end as "single_date"
    
            from "edi_ediimport" r
            where 
                case 
                    when "delivery_number" ilike '%% du %%' 
                        and is_date(split_part("delivery_number", ' du ', 2))
                    then TO_DATE(split_part("delivery_number", ' du ', 2),'DD/MM/YYYY')::varchar
                    else null 
                end is not null
            and "uuid_identification" = %(uuid_identification)s
            and ("valid" = false or "valid" isnull)
        ) "sd"
        where "edi"."id" = "sd"."id"
        """
    ),
}
