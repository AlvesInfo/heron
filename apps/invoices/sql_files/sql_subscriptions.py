# pylint: disable=E0401,C0303
"""
FR : Module des requêtes sql de traitement des refacturations des abonnements
EN : sql query module for processing subscription re-invoicing

Commentaire:

created at: 2023-03-05
created by: Paulo ALVES

modified at: 2023-03-05
modified by: Paulo ALVES
"""
from psycopg2 import sql

SQL_SUBSCRIPTIONS = sql.SQL(
    """
    select 
        "aa"."third_party_num",
        %(flow_name)s as "flow_name",
        "aa"."third_party_num" as "supplier",
        "aa"."third_party_num" as "supplier_ident",
        "code_cosium" as "code_fournisseur",
        "code_maison",
        "intitule" as "maison",
        "date_ca" as "invoice_date",
        '380' as "invoice_type",
        'EUR' as "devise",
        "aa"."reference" as "reference_article",
        case 
            when "aa"."libelle_heron" is null or "aa"."libelle_heron" = ''
            then "aa"."libelle"
            else "aa"."libelle_heron"
        end as "libelle",
        %(flow_name)s as "famille",
        "qty",
        case 
            when "unity" = 12 
            then "ca_ht_eur"
            else "net_unit_price"
        end as "gross_unit_price",
        case 
            when "unity" = 12
            then "ca_ht_eur"
            else "net_unit_price"
        end as "net_unit_price",
        case 
            when "unity" = 12 
            then round(("qty" * "ca_ht_eur") / 100, 2)::numeric
            else "net_unit_price"
        end as "gross_amount",
        case 
            when "unity" = 12 
            then round(("qty" * "ca_ht_eur") / 100, 2)::numeric
            else "net_unit_price"
        end as "net_amount",
        "vat_rate",
        case 
            when "unity" = 12 
            then round((("qty" * "ca_ht_eur") / 100) * "vat_rate", 2)::numeric
            else round(("net_unit_price" * "vat_rate"), 2)::numeric
        end as "vat_amount",
        case 
            when "unity" = 12 
            then (
                    round(("qty" * "ca_ht_eur") / 100, 2)::numeric
                    +
                    round((("qty" * "ca_ht_eur") / 100) * "vat_rate", 2)::numeric
                )
            else (
                    "net_unit_price"
                    +
                    round(("net_unit_price" * "vat_rate"), 2)::numeric
                )
        end as "amount_with_vat",
        case 
            when "unity" = 12 
            then round(("qty" * "ca_ht_eur") / 100, 2)::numeric
            else "net_unit_price"
        end as "invoice_amount_without_tax",
        case 
            when "unity" = 12 
            then round((("qty" * "ca_ht_eur") / 100) * "vat_rate", 2)::numeric
            else round(("net_unit_price" * "vat_rate"), 2)::numeric
        end as "invoice_amount_tax",
        case 
            when "unity" = 12 
            then (
                    round(("qty" * "ca_ht_eur") / 100, 2)::numeric
                    +
                    round((("qty" * "ca_ht_eur") / 100) * "vat_rate", 2)::numeric
                )
            else (
                    "net_unit_price"
                    +
                    round(("net_unit_price" * "vat_rate"), 2)::numeric
                )
        end as "invoice_amount_with_tax",
        false as "active",
        false as "to_delete",
        false as "to_export",
        true as "valid",
        true as "vat_rate_exists",
        true as "supplier_exists",
        true as "maison_exists",
        true as "article_exists",
        false "axe_pro_supplier_exists",
        "aa".third_party_num as "supplier_name",
        "aa"."axe_bu",
        "aa"."axe_prj",
        "aa"."axe_pro",
        "cc"."axe_pys",
        "aa"."axe_rfa",
        "uuid_big_category",
        false as "acquitted",
        now() as "created_at",
        false as "delete",
        false as "export",
        false as "flag_to_active",
        false as "flag_to_delete",
        false as "flag_to_export",
        false as "flag_to_valid",
        now() as "modified_at",
        false as "flag_to_acquitted",
        date_trunc('month', "date_ca")::date as "invoice_month",
        "cc"."vat",
        date_part('year', "date_ca") as "invoice_year",
        "cc"."vat_regime",
        "cc"."cct_uuid_identification",
        "unity",
        true as "sale_invoice",
        false as "purchase_invoice",
        false as "is_multi_store",
        false as "manual_entry",
        "uuid_sub_big_category",
        "pio"."origin"
    from (
    select 
        *
    from "centers_clients_maisonsubcription"
    where "function" = %(flow_name)s
    ) "ccm" 
    left join (
        select 
            "ca"."code_maison", 
            "ca"."code_cosium", 
            "cm"."intitule",
            "ca"."date_ca", 
            "cm"."cct", 
            "ca"."cct_uuid_identification", 
            "cm"."sage_vat_by_default" as "vat",
            "cm"."sage_plan_code" as "vat_regime",
            sum("ca"."ca_ht_eur") as "ca_ht_eur",
            "ac"."uuid_identification" as "axe_pys"
        from "compta_caclients"  "ca"
        join "centers_clients_maison" "cm" 
        on "ca"."cct_uuid_identification" = "cm"."uuid_identification" 
        left join (
            select 
                "section", "uuid_identification" 
            from "accountancy_sectionsage"
            where "axe" = 'PYS'
        ) "ac" 
        on "cm"."pays" = "ac"."section"
        where "ca"."date_ca" between %(dte_d)s and %(dte_f)s
        group by 
            "ca"."date_ca",
            "cm"."cct", 
            "ca"."cct_uuid_identification",
            "ca"."code_maison", 
            "ca"."code_cosium", 
            "cm"."intitule",
            "cm"."sage_vat_by_default",
            "cm"."sage_plan_code",
            "ac"."uuid_identification"
    ) "cc" 
    on "ccm"."cct" = "cc"."cct"
    join "articles_article" "aa" 
    on "ccm"."article" = "aa"."uuid_identification" 
    left join "parameters_iconoriginchoice" "pio"
    on "ccm"."function" = "pio"."origin_name"
    left join (
    select distinct
        ("vtr"."rate" / 100)::numeric as "vat_rate", "vtr"."vat"
    from "accountancy_vatratsage" "vtr"
    join (
        select 
            max("vat_start_date") as "vat_start_date", 
            "vat"
        from "accountancy_vatratsage"
        where "vat_start_date" <= %(dte_d)s
        group by "vat"
    ) "vd"
    on "vtr"."vat" = "vd"."vat"
    and "vtr"."vat_start_date" = "vd"."vat_start_date"
    ) "av" 
    on "cc"."vat" = "av"."vat" 
"""
)
