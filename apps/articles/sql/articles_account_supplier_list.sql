    select
        "aa"."uuid_identification"::varchar as "article",
        "ac"."child_center" as "code_center",
        "aa"."third_party_num",
        "bs"."short_name" as "tiers",
        "aa"."reference",
        "aa"."libelle",
        coalesce("pro"."section", 'DIV') as "pro",
        "pc"."name" as "category",
        coalesce("ps"."name", '') as "rubrique",
        "ac"."vat" as "vat_vat",
        "av"."vat_regime" as "vat_reg",
        "ac"."purchase_account" as "debit",
        "ac"."sale_account" as "credit"
    from "articles_article" "aa"
    join "articles_articleaccount" "ac"
      on "aa"."uuid_identification" = "ac"."article"
    join "book_society" "bs"
      on "aa"."third_party_num" = "bs"."third_party_num"
    left join "accountancy_sectionsage" "pro"
      on "pro"."uuid_identification" = "aa"."axe_pro"
    left join "parameters_category" "pc"
      on "pc"."uuid_identification" = "aa"."uuid_big_category"
    left join "parameters_subcategory" "ps"
      on "ps"."uuid_identification" = "aa"."uuid_sub_big_category"
    left join "accountancy_vatsage" "av"
      on "ac"."vat" = "av"."vat"
    where "aa"."third_party_num" = %(third_party_num)s
      and "ac"."child_center" <> 'GAF'
    order by "aa"."reference",
             "ac"."vat",
             "ac"."child_center"
