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
        ("av"."rate" / 100)::numeric as "vat_rate",
        "cc"."cct",
        '81bc8c6b-27fd-440d-8ec8-e19067b65078'::uuid as "uuid_identification",
        "aa"."third_party_num",
        'ROYALTIES' as "flow_name",
        "aa"."third_party_num" as "supplier",
        "aa"."third_party_num" as "supplier_ident",
        "code_cosium" as "code_fournisseur",
        "code_maison",
        "intitule" as "maison",
        '0' as "invoice_number",
        "date_ca" as "invoice_date",
        '380' as "invoice_type",
        'EUR' as "devise",
        "aa"."reference" as "reference_article",
        case 
            when "aa"."libelle_heron" is null or "aa"."libelle_heron" = ''
            then "aa"."libelle"
            else "aa"."libelle_heron"
        end as "libelle",
        'ROYALTIES' as "famille",
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
            then round("ca_ht_eur" / 100, 2)::numeric
            else "net_unit_price"
        end as "gross_amount",
        case 
            when "unity" = 12 
            then round("ca_ht_eur" / 100, 2)::numeric
            else "net_unit_price"
        end as "net_amount",
        0 as "vat_rate",
        0 as "vat_amount",
        0 as "amount_with_vat",
        case 
            when "unity" = 12 
            then round(ca_ht_eur / 100, 2)::numeric
            else "net_unit_price"
        end as "invoice_amount_without_tax",
        0 as "invoice_amount_tax",
        0 as "invoice_amount_with_tax",
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
        "aa"."axe_pys",
        "aa"."axe_rfa",
        "uuid_big_category",
        false as "acquitted",
        now() as "created_at",
        "cc"."created_by",
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
        date_part('year', "date_ca"),
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
        where "function" = 'ROYALTIES'
    ) "ccm" 
    left join (
        select 
            "ca"."code_maison", 
            "ca"."code_cosium", 
            "cm"."intitule",
            "ca"."date_ca", 
            "cm"."cct", 
            "ca"."cct_uuid_identification", 
            "ca"."created_by",
            "cm"."sage_vat_by_default" as "vat",
            "cm"."sage_plan_code" as "vat_regime",
            sum("ca"."ca_ht_eur") as "ca_ht_eur"
        from "compta_caclients"  "ca"
        join "centers_clients_maison" "cm" 
        on "ca"."cct_uuid_identification" = "cm"."uuid_identification" 
        join "accountancy_vatsage" "av" 
        -- ATTENTION -------------------------------------------------------------------------------
        on "cm".sage_vat_by_default = "av".
        where "ca"."date_ca" between '2023-01-01' and '2023-01-31'
        group by 
            "ca"."date_ca",
            "cm"."cct", 
            "ca"."cct_uuid_identification",
            "ca"."code_maison", 
            "ca"."code_cosium", 
            "cm"."intitule",
            "ca"."created_by",
            "cm"."sage_vat_by_default",
            "cm"."sage_plan_code"
    ) "cc" 
    on "ccm"."cct" = "cc"."cct"
    join "articles_article" "aa" 
    on "ccm"."article" = "aa"."uuid_identification" 
    left join "parameters_iconoriginchoice" "pio"
    on "ccm"."function" = "pio"."origin_name"
    left join (
        select distinct
            "vtr"."rate", "vtr"."vat"
        from "accountancy_vatratsage" "vtr"
        join (
            select 
                max("vat_start_date") as "vat_start_date", 
                "vat"
            from "accountancy_vatratsage"
            where "vat_start_date" <= '2023-01-01'
            group by "vat"
        ) "vd"
        on "vtr"."vat" = "vd"."vat"
        and "vtr"."vat_start_date" = "vd"."vat_start_date"
    ) "av" 
    on "cc"."vat" = "av"."vat" 
"""
)
