# pylint: disable=E0401,C0303
"""
FR : Module des requêtes sql de post-traitement après import des fichiers Prodition
EN : Post-processing sql module after importing supplier invoice files

Commentaire:

created at: 2022-11-27
created by: Paulo ALVES

modified at: 2022-11-27
modified by: Paulo ALVES
"""
from psycopg2 import sql

post_prodition_dict = {
    "sql_libele": sql.SQL(
        """
        update "edi_ediimport"
        set 
            "qty" = case when "qty" = 0 then 1::numeric else "qty" end,
            "libelle"= case 
                            when "libelle" is null or "libelle" = ''
                            then "famille" 
                            else "libelle" 
                        end,
            "purchase_invoice" = true,
            "sale_invoice" = true
        where "uuid_identification" = %(uuid_identification)s
        and ("valid" = false or "valid" isnull)
        """
    ),
    "sql_update": sql.SQL(
        """
        update "edi_ediimport"
        set 
            "invoice_type" = case when "invoice_type" = 'FA' then '380' else '381' end,
            "reference_article"= case 
                                    when "reference_article" is null or "reference_article" = ''
                                    then "famille" 
                                    else "reference_article" 
                                end,
            "libelle"= case 
                            when "libelle" is null or "libelle" = ''
                            then "reference_article" 
                            else "libelle" 
                        end,
            "gross_unit_price" = ("gross_amount"::numeric / "qty"::numeric)::numeric,
            "net_unit_price" = ("net_amount"::numeric / "qty"::numeric)::numeric
        where "uuid_identification" = %(uuid_identification)s 
        and ("valid" = false or "valid" isnull)
        """
    ),
}
