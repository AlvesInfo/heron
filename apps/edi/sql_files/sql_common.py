# pylint: disable=E0401,C0303
"""
FR : Module des requêtes sql de post-traitement après import des fichiers de factures fournisseur
EN : Post-processing sql module after importing supplier invoice files

Commentaire:

created at: 2022-11-27
created by: Paulo ALVES

modified at: 2022-11-27
modified by: Paulo ALVES
"""
from psycopg2 import sql

BASE_SQL_CCT = sql.SQL(
    """
    update "edi_ediimport" edi
    set "cct_uuid_identification" = cc."cct_uuid_identification"
    from (
        select
            ee."id",
            bs."cct_uuid_identification"
        from "edi_ediimport" ee
        left join (
            select
                "third_party_num",
                "uuid_identification",
                "invoice_number"
            from (
                select 
                    "third_party_num",
                    "uuid_identification",
                    "invoice_number",
                    "code_fournisseur"
                from "edi_ediimport"
                group by 
                    "third_party_num",
                    "uuid_identification",
                    "invoice_number",
                    "code_fournisseur"
            ) req
            group by 		
                "third_party_num",
                "uuid_identification",
                "invoice_number"
            having count("code_fournisseur") > 1
        ) er
        on ee."third_party_num" = er."third_party_num"
        and ee."uuid_identification" = er."uuid_identification"
        and ee."invoice_number" = er."invoice_number"
        left join (
            select
               bsp."third_party_num", 
               ccm."uuid_identification" as "cct_uuid_identification", 
               unnest(
                    string_to_array(
                        case 
                            when right("cct_identifier", 1) = '|' 
                            then left("cct_identifier", length("cct_identifier")-1) 
                            else "cct_identifier"
                        end
                        , 
                        '|'
                    )
               ) as "cct_identifier"
            from "book_suppliercct" bsp
            join "accountancy_cctsage" ac 
            on bsp."cct_uuid_identification" = ac."uuid_identification" 
            join "centers_clients_maison" ccm
            on ac."cct" = ccm."cct"
        ) bs
        on ee."third_party_num" = bs."third_party_num"
        where ee."third_party_num" = bs."third_party_num"
        and ee."code_maison" = bs."cct_identifier"
        and ee."cct_uuid_identification" is null
    ) cc
    where edi."id" = cc."id"
    and edi."cct_uuid_identification" isnull
    """
)

post_common_dict = {
    "sql_round_amount": sql.SQL(
        """
    update "edi_ediimport" "edi"
    set "net_amount" = round("net_amount"::numeric, 2):: numeric,
        "code_maison" = case 
                            when (
                                "code_maison" isnull 
                                or 
                                "code_maison" = '' 
                                or 
                                left("code_maison", 3) = 'TEL'
                            )
                            then 
                                case 
                                    when "code_fournisseur" isnull or "code_fournisseur" = ''
                                    then ''
                                    else "code_fournisseur"
                                end
                            else "code_maison"    
                        end
    where "uuid_identification" = %(uuid_identification)s
    and ("valid" = false or "valid" isnull)
    """
    ),
    "sql_supplier_update": sql.SQL(
        """
    update "edi_ediimport" "edi"
    set 
        "supplier_name" = "tiers"."name",
        "third_party_num" = "tiers"."third_party_num",
        "supplier" = case 
                        when "supplier" = '' or "supplier" isnull 
                        then "tiers"."name" 
                        else "supplier" 
                     end,
        "uuid_big_category" = case 
                                when "uuid_big_category" is null
                                then'f2dda460-20db-4b05-8bb8-fa80a1ff146b'::uuid
                                else "uuid_big_category"
                              end
    from (
        select 
            left("name", 35) as "name",
            "third_party_num",
            unnest(string_to_array("centers_suppliers_indentifier", '|')) as "identifier"
            from "book_society" bs
    ) "tiers"
    where "uuid_identification" = %(uuid_identification)s
    and ("edi"."third_party_num" is null or "edi"."third_party_num" = '')
    and "edi"."supplier_ident" = "tiers"."identifier"
    and ("edi"."valid" = false or "edi"."valid" isnull)
    """
    ),
    "sql_fac_update_except_edi": sql.SQL(
        """
        update "edi_ediimport" edi
        set
            "invoice_amount_without_tax" = edi_fac."invoice_amount_without_tax",
            "invoice_amount_with_tax" = edi_fac."invoice_amount_with_tax",
            "invoice_amount_tax" = (
                                        edi_fac."invoice_amount_with_tax" 
                                        - 
                                        edi_fac."invoice_amount_without_tax"
                                    ),
            "reference_article" = case 
                                    when "reference_article" isnull or "reference_article" = '' 
                                    then "ean_code"
                                    else "reference_article"
                                  end
        from (
            select 
                "uuid_identification", 
                "invoice_number",
                case 
                    when invoice_type = '381' 
                    then -abs(sum("mont_HT"))::numeric
                    else abs(sum("mont_HT"))::numeric
                end as "invoice_amount_without_tax",
                case 
                    when invoice_type = '381'
                    then -abs(sum("mont_TTC"))::numeric 
                    else abs(sum("mont_TTC"))::numeric    
                end as "invoice_amount_with_tax"
            from (
                select 
                    "uuid_identification", 
                    "invoice_number", 
                    "invoice_type",
                    round(sum("net_amount")::numeric, 2) as "mont_HT",
                    (
                        round(sum("net_amount")::numeric, 2) +
                        round(round(sum("net_amount")::numeric, 2) * "vat_rate"::numeric, 2)
                    ) as "mont_TTC",
                    "vat_rate"
                from "edi_ediimport"                
                where "uuid_identification" = %(uuid_identification)s
                  and (
                    flow_name not in ('Edi', 'Widex', 'WidexGa', 'BbgrRetours') 
                    -- Spécifique pour ophtalmic qui n'additionnent pas le port avec le total 
                    -- comme spécifié dans la norme edi
                    or third_party_num = 'OPHT001'
                  )
                  and ("valid" = false or "valid" isnull)
                group by "uuid_identification", "invoice_number", "vat_rate", "invoice_type"
            ) as "tot_amount"
            group by "uuid_identification", "invoice_number", "invoice_type"
        ) edi_fac
        where edi."uuid_identification" = %(uuid_identification)s
        and edi."uuid_identification" = edi_fac."uuid_identification"
        and edi."invoice_number" = edi_fac."invoice_number"
        """
    ),
    "sql_reference": sql.SQL(
        """
        update edi_ediimport 
        set reference_article = libelle 
        where "uuid_identification" = %(uuid_identification)s
          and (reference_article isnull or reference_article = '')
          and ("valid" = false or "valid" isnull)
    """
    ),
    "sql_vat_regime": sql.SQL(
        """
        update "edi_ediimport" edi 
        set "vat_regime" = rvat."vat_sheme_supplier"
        from (
            select 
                "third_party_num",
                case 
                    when "vat_sheme_supplier" isnull or "vat_sheme_supplier" = '' 
                    then 'FRA' 
                    else "vat_sheme_supplier"
                end
            from "book_society" bs 
        ) rvat
        where edi."uuid_identification" = %(uuid_identification)s
          and edi."third_party_num" =rvat."third_party_num"
          and (edi."vat_regime" isnull or edi."vat_regime" = '')
          and (edi."valid" = false or edi."valid" isnull)
        """
    ),
    "sql_vat": sql.SQL(
        """
        update edi_ediimport edi 
        set "vat" = rvat."vat"
        from (
            select 
                vs."vat", 
                vs."vat_regime", 
                (vsr."rate" / 100)::numeric as "vat_rate",
                ROW_NUMBER() OVER(
                    partition by vs."vat_regime", vsr."rate" 
                    order by vs."vat"
                ) as "vat_index"
            from "accountancy_vatsage" vs
            join "accountancy_vatratsage" vsr 
            on vs."vat" = vsr."vat" 
            group by vs."vat", 
                     vs."vat_regime", 
                     vsr."rate"
        ) rvat
        where edi."uuid_identification" = %(uuid_identification)s
          and edi."vat_rate" = rvat."vat_rate" 
          and edi."vat_regime" = rvat."vat_regime"
          and rvat."vat_index" = 1
          and (edi."valid" = false or edi."valid" isnull)
    """
    ),
    "sql_cct": sql.SQL(
        """
        {}
          and edi."uuid_identification" = %(uuid_identification)s
          and ("valid" = false or "valid" isnull)
    """
    ).format(BASE_SQL_CCT),
    "sql_update_articles": sql.SQL(
        """
        update "edi_ediimport" edi 
        set 
            "axe_bu" = maj."axe_bu",
            "axe_prj" = maj."axe_prj",
            "axe_pro" = maj."axe_pro",
            "axe_pys"  = maj."axe_pys",
            "axe_rfa" = maj."axe_rfa"
        from (
            select 
                ee."id", 
                aa."axe_bu", 
                aa."axe_prj", 
                aa."axe_pro", 
                aa."axe_pys", 
                aa."axe_rfa" 
            from "edi_ediimport" ee 
            join "articles_article" aa 
            on ee."reference_article" = aa."reference" 
            and ee."third_party_num" = aa."third_party_num"
            where ee."uuid_identification" = %(uuid_identification)s
            and (ee."valid" = false or ee."valid" isnull)
            and ee."axe_pro" isnull
            and aa."axe_pro" is not null
        ) maj
        where edi."id" = maj."id" 
        and edi."uuid_identification" = %(uuid_identification)s
        and (edi."valid" = false or edi."valid" isnull)
    """
    ),
    "sql_is_multi_store_true": sql.SQL(
        """
        update "edi_ediimport" edi
        set 
            "is_multi_store" = true
        from (
             select  
                "third_party_num",
                "uuid_identification",
                "invoice_number"
            from (
                select 
                    "third_party_num",
                    "uuid_identification",
                    "invoice_number",
                    case 
                        when "code_fournisseur" = '' or "code_fournisseur" is null 
                        then "code_maison"
                        else "code_fournisseur"
                    end as "code_fournisseur"
                    
                from "edi_ediimport"
                where "uuid_identification" = %(uuid_identification)s
                  and "is_multi_store" isnull
                group by 
                    "third_party_num",
                    "uuid_identification",
                    "invoice_number",
                    case 
                        when "code_fournisseur" = '' or "code_fournisseur" is null 
                        then "code_maison"
                        else "code_fournisseur"
                    end 
             ) req 
             group by 
                    "third_party_num",
                    "uuid_identification",
                    "invoice_number"
               having count("code_fournisseur") >1
        ) ms 
        where edi."uuid_identification" = %(uuid_identification)s
          and edi."third_party_num" = ms."third_party_num"
          and edi."uuid_identification" = ms."uuid_identification"
          and edi."invoice_number" = ms."invoice_number"
          and ("valid" = false or "valid" isnull)
    """
    ),
    "sql_is_multi_store_false": sql.SQL(
        """
        update "edi_ediimport" edi
        set 
            "is_multi_store" = false
        where edi."uuid_identification" = %(uuid_identification)s
          and edi."is_multi_store" isnull
          and ("valid" = false or "valid" isnull)
    """
    ),
    "sql_alls_381": sql.SQL(
        """
        update "edi_ediimport" edi
        set "qty" = case when "net_amount" < 0 then -abs("qty") else abs("qty") end,
            "gross_amount" = case 
                                when "net_amount" < 0 
                                then -abs("gross_amount") 
                                else abs("gross_amount") 
                            end
        where "uuid_identification" = %(uuid_identification)s
          and "third_party_num" <> 'PREC001'
          and "invoice_type" = '381'
          and ("valid" = false or "valid" isnull)
    """
    ),
    "vat_per_line": sql.SQL(
        """
        update "edi_ediimport" ei 
        set "vat_amount" = r."vat_amount",
            "amount_with_vat" = r."amount_with_vat"
        from (
            select 
                "id", 
                round("net_amount" * "vat_rate", 2)::numeric as "vat_amount", 
                (
                    "net_amount" 
                    + 
                    round("net_amount" * "vat_rate", 2)::numeric
                )::numeric as "amount_with_vat" 
             from "edi_ediimport" ee
            where "uuid_identification" = %(uuid_identification)s
              and ("valid" = false or "valid" isnull)
        ) r 
        where ei."id" = r."id"
          and ei."uuid_identification" = %(uuid_identification)s
          and (ei."valid" = false or ei."valid" isnull)
    """
    ),
    "sql_delta_vat": sql.SQL(
        """
        with "alls" as (
            select 
                "uuid_identification", 
                "third_party_num", 
                "invoice_number", 
                sum("amount_with_vat") as "sum_amount_with_vat",
                "invoice_amount_with_tax",
                ("invoice_amount_with_tax" - sum("amount_with_vat")) as "delta",
                count(*) as nb_lignes,
                string_agg("id"::varchar, '|' order by vat_rate desc, net_amount desc) as alls_id,
                abs(("invoice_amount_with_tax" - sum("amount_with_vat")) * 100)::int as nb_iterate
             from "edi_ediimport" ee
             where "uuid_identification" = %(uuid_identification)s
              and ("valid" = false or "valid" isnull)
             group by "uuid_identification", 
                      "third_party_num", 
                      "invoice_number",
                      "invoice_amount_with_tax" 
            having sum("amount_with_vat") <> "invoice_amount_with_tax" 
        ),
        rows_filter as (
            select
                ee."id", 
                ee."vat_amount",
                ee."amount_with_vat",
                aa."nb_iterate",
                ROW_NUMBER() over(
                    partition by ee."uuid_identification", 
                                 ee."third_party_num", 
                                 ee."invoice_number" 
                    order by ee."vat_rate" desc, 
                             ee."net_amount" desc, ee."id"
                ) as row_id,
                case when aa."delta" > 0 then 0.01 else -0.01 end as "vat_amount_addition"
            from "edi_ediimport" ee 
            join "alls" aa
            on ee."uuid_identification" = aa."uuid_identification"
            and ee."third_party_num" = aa."third_party_num"
            and ee."invoice_number" = aa."invoice_number" 
            where ee."uuid_identification" = %(uuid_identification)s
              and ee."vat_rate" != 0
              and (ee."valid" = false or ee."valid" isnull)
        )
        update "edi_ediimport" eei
        set "vat_amount" = rq."vat_amount_add",
            "amount_with_vat" = rq."amount_with_vat_add"
        from (
            select 
                    "id", 
                    ("vat_amount" + "vat_amount_addition")::numeric as "vat_amount_add",
                    ("amount_with_vat" + "vat_amount_addition") as "amount_with_vat_add"
            from rows_filter
            where "row_id" <= "nb_iterate"
        ) rq
        where eei."id" = rq."id"
          and eei."uuid_identification" = %(uuid_identification)s
          and (eei."valid" = false or eei."valid" isnull)
    """
    ),
    "sql_none": sql.SQL(
        """
        update "edi_ediimport" edi
        set "acuitis_order_date" = case 
                                        when "acuitis_order_date" = '1900-01-01'
                                        then null 
                                        else "acuitis_order_date"
                                    end,
            "delivery_number" = case
                                     when "delivery_number" = 'None'
                                        then null 
                                        else "delivery_number"
                                    end
        where "uuid_identification" = %(uuid_identification)s
          and ("valid" = false or "valid" isnull)
    """
    ),
    "sql_delivery_number": sql.SQL(
        """
        update "edi_ediimport" "edi"
        set "delivery_number" = "req"."delivery_number",
            "comment" = "edi"."comment" || ' ' || "req"."commentaire"
        
        from (
            select 
                "id", 
                array_to_string(
                    (string_to_array("delivery_number", ' '))[1:1], ' '
                ) as "delivery_number",
                array_to_string(
                    (
                        string_to_array("delivery_number", ' ')
                    )[3:array_length(string_to_array("delivery_number", ' '), 1)], 
                    ' '
                ) as "commentaire"
             from "edi_ediimport" "ee" 
            where "delivery_number" is not null and "delivery_number" !=''
              and array_length(string_to_array("delivery_number", ' '), 1) > 1
              and "uuid_identification" = %(uuid_identification)s
              and ("valid" = false or "valid" isnull)
        ) "req" 
        where "edi"."id" = "req"."id"
          and "edi"."uuid_identification" = %(uuid_identification)s
          and ("edi"."valid" = false or "edi"."valid" isnull)
    """
    ),
    "sql_validate": sql.SQL(
        """
        update "edi_ediimport" edi
        set "valid"=true, "vat_rate_exists" = false, "supplier_exists" = false,
            "maison_exists" = false, "article_exists" = false, "axe_pro_supplier_exists" = false,
            "acuitis_order_date" = case 
                                    when "acuitis_order_date" = '1900-01-01' 
                                    then null
                                    else "acuitis_order_date"
                                   end,
            "delivery_date" = case 
                                when "delivery_date" = '1900-01-01' 
                                then null
                                else "delivery_date"
                               end,
            "invoice_month" = date_trunc('month', invoice_date)::date,
            "invoice_year" = date_part('year', invoice_date),
            "delete" = false,
            "unity" =  case
                            when "unity" isnull then 1 else "unity" 
                       end,
            "packaging_qty" = abs("packaging_qty"),
            "gross_unit_price" = abs("gross_unit_price"),
            "net_unit_price" = abs("net_unit_price"),
            "packaging_amount" = abs("packaging_amount"),
            "transport_amount" = abs("transport_amount"),
            "insurance_amount" = abs("insurance_amount"),
            "fob_amount" = abs("fob_amount"),
            "fees_amount" = abs("fees_amount"),
            "manual_entry" = false,
            "created_by" = %(created_by)s
        where "uuid_identification" = %(uuid_identification)s
          and ("valid" = false or "valid" isnull)
    """
    ),
}
