# pylint: disable=
"""
FR : Module des requêtes sql de post-traitement après import des fichiers génériques
EN : Post-processing sql module after importing supplier invoice files

Commentaire:

created at: 2022-11-27
created by: Paulo ALVES

modified at: 2022-11-27
modified by: Paulo ALVES
"""
from psycopg2 import sql

post_generic_dict = {
    "sql_update": sql.SQL(
        """
        update "edi_ediimport"
        set 
            "invoice_type" = case when "invoice_type" = 'FA' then '380' else '381' end,
            "purchase_invoice" = true,
            "sale_invoice" = true
        where "uuid_identification" = %(uuid_identification)s
        and ("valid" = false or "valid" isnull)
        """
    ),
    "sql_net_amount_mgdev": sql.SQL(
        """
        update "edi_ediimport" edi
        set
            "net_amount" = case
                                when ("invoice_type" = '381' and "qty" < 0) 
                                  or ("invoice_type" = '380' and "qty" > 0) 
                                then abs("net_amount")::numeric
                                when ("invoice_type" = '381' and "qty" > 0) 
                                  or ("invoice_type" = '380' and "qty" < 0) 
                                then -abs("net_amount")::numeric
                            end
        where "uuid_identification" = %(uuid_identification)s
        and ("valid" = false or "valid" isnull)
        """
    ),
    "sql_maison": sql.SQL(
        """
        update "edi_ediimport" edi
        set
            "maison" = inv."maison"
        from (
            select 
                "invoice_number", 
                max("maison") as maison            
                from edi_ediimport ee 
            group by "invoice_number" 
        ) inv
        where edi."invoice_number" = inv."invoice_number"
        and edi."uuid_identification" = %(uuid_identification)s
        and (edi."valid" = false or edi."valid" isnull)
        """
    ),
    "sql_mg_developpemnt": sql.SQL(
        """
        update "edi_ediimport" edi
        set "famille" = 'PORT'
        where "third_party_num" = 'MGDE001'
          and edi."uuid_identification" = %(uuid_identification)s
          and "reference_article" ilike '%PORT%'
          and ("valid" = false or "valid" isnull)
    """
    ),
    "sql_edi_generique": sql.SQL(
        """
        update "data_flux_trace" dt 
        set "trace_name" = left("trace_name" || sup."supplier", 160)
          from (
            select 
                "uuid_identification", 
                "supplier"
              from "edi_ediimport" ee 
             where "flow_name" = 'Generique'
               and "uuid_identification" = %(uuid_identification)s
             group by "uuid_identification", 
                "supplier"
          ) sup 
        where dt."uuid_identification" = sup."uuid_identification"
          and ("valid" = false or "valid" isnull)
    """
    ),
}
