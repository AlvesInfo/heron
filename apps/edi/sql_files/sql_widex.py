# pylint: disable=E0401,C0303
"""
FR : Module des requêtes sql de post-traitement après import des fichiers Widex
EN : Post-processing sql module after importing supplier invoice files

Commentaire:

created at: 2022-11-27
created by: Paulo ALVES

modified at: 2022-11-27
modified by: Paulo ALVES
"""
from psycopg2 import sql

post_widex_dict = {
    "sql_update": sql.SQL(
        """
        update "edi_ediimport"
        set 
            "invoice_type" = case when "invoice_type" = 'FA' then '380' else '381' end,
            "famille" = case 
                            when "famille" = '' or "famille" is null 
                            then "reference_article" 
                            else "famille" 
                        end,
            "gross_amount" = case 
                                when "gross_amount" is null or "gross_amount" = 0 
                                then "net_amount"::numeric 
                                else "gross_amount"::numeric 
                            end,
            "gross_unit_price" = (
                case 
                    when "gross_amount" is null or "gross_amount" = 0 
                    then "net_amount"::numeric 
                    else "gross_amount"::numeric 
                end 
                / "qty"::numeric
            )::numeric,
            "net_unit_price" = ("net_amount"::numeric / "qty"::numeric)::numeric,
            "purchase_invoice" = true,
            "sale_invoice" = true,
            "origin" = 1
        where "uuid_identification" = %(uuid_identification)s
        and ("valid" = false or "valid" isnull)
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
                                when "net_amount" = 0 
                                    then 0
                                when "net_amount" < 0 
                                    then (abs("gross_amount")::numeric * -1::numeric)
                                when "net_amount" > 0 
                                    then abs("gross_amount")::numeric
                            end
        where "uuid_identification" = %(uuid_identification)s
        and ("valid" = false or "valid" isnull)
        """
    ),
    "sql_invoices_amounts": sql.SQL(
        """
        update edi_ediimport edi
        set 
            "invoice_amount_without_tax" = r_som."invoice_amount_without_tax",
            "invoice_amount_tax" = r_som."invoice_amount_tax",
            "invoice_amount_with_tax" = r_som."invoice_amount_with_tax"
        from (
            select 
                "uuid_identification",
                "invoice_number",
                sum("net_amount") as "invoice_amount_without_tax",
                (sum("amount_with_vat")- sum("net_amount")) as "invoice_amount_tax",
                sum("amount_with_vat") as "invoice_amount_with_tax"
            from "edi_ediimport" ee 
            where "uuid_identification" = %(uuid_identification)s
              and ("valid" = false or "valid" isnull)
            group by "uuid_identification", "invoice_number"
        ) r_som
        where edi."uuid_identification" = r_som."uuid_identification"
        and edi."invoice_number" = r_som."invoice_number"
        """
    ),
    "sql_articles_wsau": sql.SQL(
        """
        update "articles_article" "aa"
        set "libelle_heron" = ''
        where "third_party_num" = 'WSAU003'
        and "libelle_heron" <> '' or "libelle_heron" isnull
        """
    ),
    "sql_marque": sql.SQL(
        """
        update "edi_ediimport" "ee"
        set "libelle" = left("ee"."supplier_ident" || ' - ' || "ee"."libelle", 150)
        where "uuid_identification" = %(uuid_identification)s
        and ("valid" = false or "valid" isnull)
        """
    )
}
