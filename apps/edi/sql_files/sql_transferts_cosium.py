# pylint: disable=E0401,C0303
"""
FR : Module des requêtes sql de post-traitement après import des Tranferts Cosium
EN : Post-processing sql module after importing supplier Cosium Transfers

Commentaire:

created at: 2023-01-14
created by: Paulo ALVES

modified at: 2023-01-14
modified by: Paulo ALVES
"""
from psycopg2 import sql

post_transfert_cosium_dict = {
    "sql_amounts": sql.SQL(
        """
    update "edi_ediimport" "edi"
    set "gross_unit_price" = "net_unit_price",
        "net_amount" = round(("qty"*"net_unit_price")::numeric, 2)::numeric,
        "gross_amount" = round(("qty"*"net_unit_price")::numeric, 2)::numeric,
        "vat_amount" = round(("qty"*"net_unit_price"*"vat_rate")::numeric, 2)::numeric,
        "amount_with_vat" = (
            round(("qty"*"net_unit_price"*"vat_rate")::numeric, 2)::numeric 
            + 
            round(("qty"*"net_unit_price")::numeric, 2)::numeric
        ),
        "purchase_invoice" = false,
        "sale_invoice" = true,
        "origin" = 1
    where "uuid_identification" = %(uuid_identification)s
      and ("valid" = false or "valid" isnull)
    """
    ),
    "sql_articles_cosium": sql.SQL(
        """
        update "edi_ediimport" edi 
        set 
            "axe_bu" = maj."axe_bu",
            "axe_prj" = maj."axe_prj",
            "axe_pro" = maj."axe_pro",
            "axe_pys"  = maj."axe_pys",
            "axe_rfa" = maj."axe_rfa",
            "uuid_big_category" = maj."uuid_big_category",
            "uuid_sub_big_category" = maj."uuid_sub_big_category"
        from (
            select 
                ee."id", 
                aa."axe_bu", 
                aa."axe_prj", 
                aa."axe_pro", 
                aa."axe_pys", 
                aa."axe_rfa",
                aa."uuid_big_category",
                aa."uuid_sub_big_category"
            from "edi_ediimport" ee 
            join "articles_article" aa 
            on ee."reference_article" = aa."reference" 
            and aa."third_party_num" = 'COSI001'
            where ee."uuid_identification" = %(uuid_identification)s
            and (ee."valid" = false or ee."valid" isnull)
        ) maj
        where edi."id" = maj."id" 
        and edi."uuid_identification" = %(uuid_identification)s
        and (edi."valid" = false or edi."valid" isnull)
    """
    ),
    "sql_articles_cosium_acuitis": sql.SQL(
        """
        update "edi_ediimport" edi 
        set 
            "axe_bu" = maj."axe_bu",
            "axe_prj" = maj."axe_prj",
            "axe_pro" = maj."axe_pro",
            "axe_pys"  = maj."axe_pys",
            "axe_rfa" = maj."axe_rfa",
            "uuid_big_category" = maj."uuid_big_category",
            "uuid_sub_big_category" = maj."uuid_sub_big_category"
        from (
            select 
                ee."id", 
                aa."axe_bu", 
                aa."axe_prj", 
                aa."axe_pro", 
                aa."axe_pys", 
                aa."axe_rfa",
                aa."uuid_big_category",
                aa."uuid_sub_big_category"
            from "edi_ediimport" ee 
            join "articles_article" aa 
            on ee."reference_article" = aa."reference" 
            and aa."third_party_num" = 'BBGR002'
            where ee."uuid_identification" = %(uuid_identification)s
            and (ee."valid" = false or ee."valid" isnull)
        ) maj
        where edi."id" = maj."id" 
        and edi."uuid_identification" = %(uuid_identification)s
        and (edi."valid" = false or edi."valid" isnull)
    """
    ),
    "sql_articles_base_cosium": sql.SQL(
        """
        update "edi_ediimport" edi 
        set 
            "axe_bu" = maj."axe_bu",
            "axe_prj" = maj."axe_prj",
            "axe_pro" = maj."axe_pro",
            "axe_pys"  = maj."axe_pys",
            "axe_rfa" = maj."axe_rfa",
            "uuid_big_category" = maj."uuid_big_category",
            "uuid_sub_big_category" = maj."uuid_sub_big_category"
        from (
            select 
                ee.reference_article,
                (select axe_bu from parameters_defaultaxearticle pd limit 1) as axe_bu,
                (select axe_prj from parameters_defaultaxearticle pd limit 1) as axe_prj,
                (select axe_pys  from parameters_defaultaxearticle pd limit 1) as axe_pys,
                bs.axe_pro,
                (select axe_rfa  from parameters_defaultaxearticle pd limit 1) as axe_rfa,
                bs.uuid_big_category,
                bs.uuid_sub_big_category 
            from (
                select 
                reference_article, famille
                from edi_ediimport 
                where (
                    axe_bu is null 
                    or 
                    axe_prj  is null 
                    or 
                    axe_pro  is null 
                    or 
                    axe_pys  is null 
                    or 
                    axe_rfa  is null 
                    or 
                    uuid_big_category  is null 
                )
                and "uuid_identification" = %(uuid_identification)s
                group by reference_article, famille
            ) ee 
            join (
                select 
                    regex_match, axe_pro, uuid_big_category , uuid_sub_big_category 
                from book_supplierfamilyaxes 
                where stat_name = 'COSI001'
            ) bs 
            on ee.famille = bs.regex_match
        ) maj
        where edi."reference_article" = maj."reference_article" 
        and edi."uuid_identification" = %(uuid_identification)s
        and (edi."valid" = false or edi."valid" isnull)
    """
    ),
}
