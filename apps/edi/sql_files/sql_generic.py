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
            "sale_invoice" = true,
            "origin" = 1
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
        and "third_party_num" = 'MGDE001' 
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
          and "reference_article" ilike '%%PORT%%'
          and ("valid" = false or "valid" isnull)
    """
    ),
    "sql_vat": sql.SQL(
        """
        update "edi_ediimport" "edi" 
        set "vat" =  rvat."vat",
            "vat_regime" = "rvat"."vat_regime"
        from (
            select 
                "vat",
                "vat_regime",
                "vat_rate"
            from (
                select 
                    vs."vat", 
                    vs."vat_regime", 
                    (vsr."rate" / 100)::numeric as "vat_rate",
                    ROW_NUMBER() OVER(
                        partition by vs."vat", vs."vat_regime"
                        order by vs."vat", vsr."vat_start_date" desc
                    ) as "vat_index",
                    vsr."vat_start_date"
                from "accountancy_vatsage" vs
                join "accountancy_vatratsage" vsr 
                on vs."vat" = vsr."vat" 
            ) req
            where "vat_index" = 1
            and "vat_regime" = 'FRA'
        ) "rvat"
        where "edi"."uuid_identification" = %(uuid_identification)s
          and "edi"."vat_rate" = rvat."vat_rate" 
          and "edi"."vat" isnull
          and ("edi"."valid" = false or "edi"."valid" isnull)
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


post_generic_internal_dict = {
    "sql_update": sql.SQL(
        """
        update "edi_ediimport"
        set "purchase_invoice" = false,
            "sale_invoice" = true
        where "uuid_identification" = %(uuid_identification)s
        """
    ),
    "sql_vat": sql.SQL(
        """
        update "edi_ediimport" "edi" 
        set "vat" =  rvat."vat",
            "vat_regime" = "rvat"."vat_regime"
        from (
            select 
                "vat",
                "vat_regime",
                "vat_rate"
            from (
                select 
                    vs."vat", 
                    vs."vat_regime", 
                    (vsr."rate" / 100)::numeric as "vat_rate",
                    ROW_NUMBER() OVER(
                        partition by vs."vat", vs."vat_regime"
                        order by vs."vat", vsr."vat_start_date" desc
                    ) as "vat_index",
                    vsr."vat_start_date"
                from "accountancy_vatsage" vs
                join "accountancy_vatratsage" vsr 
                on vs."vat" = vsr."vat" 
            ) req
            where "vat_index" = 1
            and "vat_regime" = 'FRA'
        ) "rvat"
        where "edi"."uuid_identification" = %(uuid_identification)s
          and "edi"."vat_rate" = rvat."vat_rate" 
          and "edi"."vat" isnull
          and ("edi"."valid" = false or "edi"."valid" isnull)
          """
    ),
    "sql_update_bu": sql.SQL(
        """
        update "edi_ediimport" "edi" 
        set "axe_bu" = (
            select 
                "acs"."uuid_identification"
            from "accountancy_sectionsage" "acs"
            where "acs"."axe" = 'BU'
              and "acs"."section" = 'REFAC0'
            limit 1
        )
        where "edi"."uuid_identification" = %(uuid_identification)s
          and "edi"."third_party_num" = 'ZREFAC0' 
          and ("edi"."valid" = false or "edi"."valid" isnull)
        """
    )
}
