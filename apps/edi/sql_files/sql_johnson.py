# pylint: disable=E0401,C0303
"""
FR : Module des requêtes sql de post-traitement après import des fichiers Johnson
EN : Post-processing sql module after importing supplier invoice files

Commentaire:

created at: 2022-11-27
created by: Paulo ALVES

modified at: 2022-11-27
modified by: Paulo ALVES
"""
from psycopg2 import sql

post_johnson_dict = {
    "sql_update": sql.SQL(
        """
        update "edi_ediimport"
        set 
            "invoice_number" = split_part("invoice_number", '.', 1),
            "invoice_type" = case when "qty" >= 0 then '380' else '381' end,
            "gross_unit_price" = ("net_amount"::numeric / "qty"::numeric)::numeric,
            "net_unit_price" = ("net_amount"::numeric / "qty"::numeric)::numeric,
            "gross_amount" = "net_amount"::numeric,
            "purchase_invoice" = true,
            "sale_invoice" = true,
            "origin" = 1
        where "uuid_identification" = %(uuid_identification)s
        and ("valid" = false or "valid" isnull)
        """
    ),
    "sql_update_vat_rate": sql.SQL(
        """
        update "edi_ediimport" "ed" 
        set "vat_rate" = "req"."taux_tva" 
        from (
            select
                case 
                    when "net_amount" isnull or "net_amount" = 0 then 0
                    when round("amount_with_vat"::numeric/"net_amount"::numeric, 2) 
                            between 1.19 and 1.21 
                            then .2 
                    when round("amount_with_vat"::numeric/"net_amount"::numeric, 2) 
                            between 1.045 and 1.065 
                            then .055
                end as "taux_tva",
                "uuid_identification", 
                "edi"."id"
            from "edi_ediimport" "edi"
            where "uuid_identification" = %(uuid_identification)s
            and ("valid" = false or "valid" isnull)
        ) "req" 
        where "req"."id" = "ed"."id"
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
                                when "net_amount" < 0 then (
                                    abs("gross_amount")::numeric * -1::numeric
                                )
                                when "net_amount" > 0 then abs("gross_amount")::numeric
                            end,
            "reference_article" = case
                                    when right("reference_article", 2) = '.0' 
                                    then left("reference_article", length("reference_article") - 2)
                                    else "reference_article"
                                  end 
        where "uuid_identification" = %(uuid_identification)s
        and ("valid" = false or "valid" isnull)
        """
    ),
}
