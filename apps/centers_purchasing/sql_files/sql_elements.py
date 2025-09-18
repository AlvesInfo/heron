# pylint: disable=E0401,C0413
"""
FR : Raws SQL
EN : Raws SQL

Commentaire:

created at: 2023-08-16
created by: Paulo ALVES

modified at: 2023-08-16
modified by: Paulo ALVES
"""

articles_acuitis_without_accounts = """
        with "amounts" as (
            select 
                "vt"."id",
                "vt"."ccm_vat" as "vat_vat"
            from (
                select
                    "ee"."id",
                    case 
                        when "ccm"."sage_vat_by_default" = '001' and "ee"."vat_rate" = 0 then '001'
                        when "ccm"."sage_vat_by_default" = '001' then "ee"."vat"
                        else "ccm"."sage_vat_by_default"
                    end as "ccm_vat"        
                from "edi_ediimport" "ee" 
                join "centers_clients_maison" "ccm" 
                on "ee"."cct_uuid_identification" = "ccm"."uuid_identification"
                join (
                        select distinct
                            "vtr"."vat_regime", 
                            "vd"."vat",
                            round(("vtr"."rate" / 100)::numeric, 5) as "vat_rate"
                        from "accountancy_vatratsage" "vtr"
                        join (
                            select
                                max("vat_start_date") as "vat_start_date",
                                "vat",
                                "vat_regime"
                            from "accountancy_vatratsage"
                            where "vat_start_date" <= now()::date 
                            group by "vat", "vat_regime"
                        ) "vd"
                        on "vtr"."vat" = "vd"."vat"
                        and "vtr"."vat_start_date" = "vd"."vat_start_date"
                ) avr
                on "avr"."vat" = "ccm"."sage_vat_by_default" 
            ) "vt" 
        ),
        "ventes" as (
            select 
                "ee"."id",
                "ee"."code_center",
                "ee"."third_party_num",
                "bs"."short_name" as "tiers",
                "aa"."reference",
                "aa"."libelle",
                coalesce("pro"."section", 'DIV') as "pro",
                "pc"."name" as "category",
                coalesce("ps"."name", '') as "rubrique", 
                "aa"."uuid_identification"  as "article",
                "amo"."vat_vat",
                "av"."vat_regime" as "vat_reg"
            from "edi_ediimport" "ee" 
            join "amounts" "amo"
              on "amo"."id" = "ee"."id"   
            join "articles_article" "aa" 
              on "ee"."third_party_num" = "aa"."third_party_num" 
             and "ee"."reference_article" = "aa"."reference" 
            left join "articles_articleaccount" "ac"
              on "aa"."uuid_identification" = "ac"."article"
             and "ee"."code_center" = "ac"."child_center"
             and "amo"."vat_vat" = "ac"."vat" 
            join "accountancy_sectionsage" "pro" 
               on "pro"."uuid_identification" = "ee"."axe_pro"
            join "parameters_category" "pc" 
               on "pc"."uuid_identification" = "ee"."uuid_big_category" 
             left join "parameters_subcategory" "ps" 
               on "ps"."uuid_identification" = "ee"."uuid_sub_big_category"
            join "book_society" "bs" 
              on "ee"."third_party_num" = "bs"."third_party_num"
            left join "accountancy_vatsage" "av"
              on "amo"."vat_vat" = "av"."vat"
            where "ee"."sale_invoice" = true
              and "ee"."valid" = true
              and "ac"."sale_account" isnull
        ),
        "achats" as (
            select 
                "ee"."id",
                "ee"."code_center", 
                "ee"."third_party_num", 
                "bs"."short_name" as "tiers",
                "aa"."reference",
                "aa"."libelle",
                coalesce("pro"."section", 'DIV') as "pro",
                "pc"."name" as "category",
                coalesce("ps"."name", '') as "rubrique",
                "aa"."uuid_identification" as "article",
                "ee"."vat" as "vat_vat",
                "av"."vat_regime" as "vat_reg"
            from "edi_ediimport" "ee" 
            left join "book_society" "bs" 
              on "ee"."third_party_num"
               = "bs"."third_party_num" 
            left join "articles_article" "aa"  
              on "ee"."reference_article" = "aa"."reference" 
             and "ee"."third_party_num" = "aa"."third_party_num" 
            left join "articles_articleaccount" "ac" 
              on "aa"."uuid_identification" = "ac"."article" 
             and "ee"."vat" = "ac"."vat"
             and "ee"."code_center" = "ac"."child_center" 
            join "accountancy_sectionsage" "pro" 
               on "pro"."uuid_identification" = "ee"."axe_pro"
            left join "parameters_category" "pc" 
              on "ee"."uuid_big_category"
               = "pc"."uuid_identification" 
            left join "parameters_subcategory" "ps" 
              on "ee"."uuid_sub_big_category" = "ps"."uuid_identification"
            left join "accountancy_vatsage" "av"
              on "ee"."vat" = "av"."vat"
            where "ac"."article" isnull
        ),
        "alls" as (
            select 
                "id",
                "code_center", 
                "third_party_num", 
                "tiers", 
                "reference", 
                "libelle", 
                "pro", 
                "category", 
                "rubrique", 
                "article", 
                "vat_vat",
                "vat_reg"
            from "ventes"
            union all
            select 
                "id",
                "code_center", 
                "third_party_num", 
                "tiers", 
                "reference", 
                "libelle", 
                "pro", 
                "category", 
                "rubrique", 
                "article", 
                "vat_vat",
                "vat_reg"
            from "achats"
        )
        select 
            max("id") as "id",
            "code_center", 
            "third_party_num", 
            "tiers", 
            "reference", 
            "libelle", 
            "pro", 
            "category", 
            "rubrique", 
            "article", 
            "vat_vat",
            "vat_reg"
        from "alls"
        group by "code_center", 
                 "third_party_num", 
                 "tiers", 
                 "reference", 
                 "libelle", 
                 "pro", 
                 "category", 
                 "rubrique", 
                 "article", 
                 "vat_vat",
                 "vat_reg"
        order by "third_party_num",
                 "category", 
                 "rubrique",
                 "pro",
                 "reference",
                 "vat_vat"
"""