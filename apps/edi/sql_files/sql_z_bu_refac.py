# pylint: disable=E0401,C0303
"""
FR : Module des requêtes sql de post-traitement après import des fichiers requête Sql Sage BU REFAC0
EN : Post-processing sql module after importing Query Sage BU REFAC0 files

Commentaire:

created at: 2023-02-21
created by: Paulo ALVES

modified at: 2023-02-21
modified by: Paulo ALVES
"""
from psycopg2 import sql

post_z_bu_refac = {
    "sql_update": sql.SQL(
        """
        update "edi_ediimport"
        set "devise" = 'EUR',
            "gross_unit_price" = "net_unit_price",
            "gross_amount" = ("qty" * "net_unit_price")::numeric,
            "net_amount" = ("qty" * "net_unit_price")::numeric,
            "vat_regime" = 'FRA',
            "sale_invoice" = true,
            "purchase_invoice" = false,
            "manual_entry" = false,
            "famille" = "reference_article"
        where "uuid_identification" = %(uuid_identification)s
        and ("valid" = false or "valid" isnull)
        """
    ),
    "sql_name": sql.SQL(
        """
        update "edi_ediimport" edi
        set "supplier" = req."short_name",
            "supplier_ident" = "third_party_num",
            "supplier_name" = req."short_name"
        from (
            select 
                "third_party_num",
                "short_name"
            from book_society bs 
        ) req
        where "uuid_identification" = %(uuid_identification)s
        and ("valid" = false or "valid" isnull)
        and edi."third_party_num" = req."third_party_num"
        """
    ),
    "sql_vat": sql.SQL(
        """
        update edi_ediimport edi 
        set "vat_rate" =  rvat."vat_rate"
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
        ) rvat
        where edi."uuid_identification" = %(uuid_identification)s
          and edi."vat" = rvat."vat" 
          and edi."vat_regime" = rvat."vat_regime"
          and rvat."vat_index" = 1
          and (edi."valid" = false or edi."valid" isnull)
    """
    ),
}