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
    insert into "edi_ediimport"
    (
        "uuid_identification",
        "invoice_number",
        "third_party_num",
        "flow_name",
        "supplier",
        "supplier_ident",
        "code_fournisseur",
        "code_maison",
        "maison",
        "invoice_date",
        "invoice_type",
        "devise",
        "reference_article",
        "libelle",
        "famille",
        "qty",
        "gross_unit_price",
        "net_unit_price",
        "gross_amount",
        "net_amount",
        "vat_rate",
        "vat_amount",
        "amount_with_vat",
        "invoice_amount_without_tax",
        "invoice_amount_tax",
        "invoice_amount_with_tax",
        "active",
        "to_delete",
        "to_export",
        "valid",
        "vat_rate_exists",
        "supplier_exists",
        "maison_exists",
        "article_exists",
        "axe_pro_supplier_exists",
        "supplier_name",
        "axe_bu",
        "axe_prj",
        "axe_pro",
        "axe_pys",
        "axe_rfa",
        "uuid_big_category",
        "acquitted",
        "created_at",
        "created_by",
        "delete",
        "export",
        "flag_to_active",
        "flag_to_delete",
        "flag_to_export",
        "flag_to_valid",
        "modified_at",
        "flag_to_acquitted",
        "invoice_month",
        "vat",
        "invoice_year",
        "vat_regime",
        "cct_uuid_identification",
        "unit_weight",
        "sale_invoice",
        "purchase_invoice",
        "is_multi_store",
        "manual_entry",
        "uuid_sub_big_category",
        "origin"
    )
    select
        %(uuid_identification)s as "uuid_identification",
        (%(flow_name)s||'_'||"ccm"."cct"||'_'||%(dte_f)s) as "invoice_number",
        "aa"."third_party_num",
        %(flow_name)s as "flow_name",
        ("aa"."third_party_num"||'_'||%(flow_name)s) as "supplier",
        ("aa"."third_party_num"||'_'||%(flow_name)s) as "supplier_ident",
        "code_cosium" as "code_fournisseur",
        "ccm"."cct" as code_maison,
        "intitule" as "maison",
         %(dte_f)s  as "invoice_date",
        '380' as "invoice_type",
        'EUR' as "devise",
        "aa"."reference" as "reference_article",
        case
            when "aa"."libelle_heron" is null or "aa"."libelle_heron" = ''
            then "aa"."libelle"
            else "aa"."libelle_heron"
        end as "libelle",
        %(flow_name)s as "famille",
        case
            when "unit_weight" = 12
            then round("qty" / 100, 2)::numeric
            else "qty"
        end as "qty",
        case
            when "unit_weight" = 12
            then case when "ca_ht_eur" isnull then 0 else "ca_ht_eur" end
            else "net_unit_price"
        end as "gross_unit_price",
        case
            when "unit_weight" = 12
            then case when "ca_ht_eur" isnull then 0 else "ca_ht_eur" end
            else "net_unit_price"
        end as "net_unit_price",
        case
            when "unit_weight" = 12
            then round(
                (
                    "qty" 
                    * 
                    case when "ca_ht_eur" isnull then 0 else "ca_ht_eur" end
                ) / 100, 2
            )::numeric
            else "net_unit_price"
        end as "gross_amount",
        case
            when "unit_weight" = 12
            then round(
                (
                    "qty" 
                    * 
                    case when "ca_ht_eur" isnull then 0 else "ca_ht_eur" end
                ) / 100, 2
            )::numeric
            else "net_unit_price"
        end as "net_amount",
        "vat_rate",
        case
            when "unit_weight" = 12
            then round((
                (
                    "qty" 
                    * 
                    case when "ca_ht_eur" isnull then 0 else "ca_ht_eur" end
                ) / 100) * "vat_rate", 2
            )::numeric
            else round(("net_unit_price" * "vat_rate"), 2)::numeric
        end as "vat_amount",
        case
            when "unit_weight" = 12
            then (
                    round(
                        (
                            "qty" 
                            * 
                            case when "ca_ht_eur" isnull then 0 else "ca_ht_eur" end
                        ) / 100, 2
                    )::numeric
                    +
                    round((
                        (
                            "qty" 
                            * 
                            case when "ca_ht_eur" isnull then 0 else "ca_ht_eur" end
                        ) / 100) * "vat_rate", 2
                    )::numeric
                )
            else (
                    "net_unit_price"
                    +
                    round(("net_unit_price" * "vat_rate"), 2)::numeric
                )
        end as "amount_with_vat",
        case
            when "unit_weight" = 12
            then round(
                (
                    "qty" 
                    * 
                    case when "ca_ht_eur" isnull then 0 else "ca_ht_eur" end
                ) / 100, 2
            )::numeric
            else "net_unit_price"
        end as "invoice_amount_without_tax",
        case
            when "unit_weight" = 12
            then round((
                (
                    "qty" 
                    * 
                    case when "ca_ht_eur" isnull then 0 else "ca_ht_eur" end
                ) / 100) * "vat_rate", 2
            )::numeric
            else round(("net_unit_price" * "vat_rate"), 2)::numeric
        end as "invoice_amount_tax",
        case
            when "unit_weight" = 12
            then (
                    round(
                        (
                            "qty" 
                            * 
                            case when "ca_ht_eur" isnull then 0 else "ca_ht_eur" end
                        ) / 100, 2
                    )::numeric
                    +
                    round((
                        (   
                            "qty" 
                            * 
                            case when "ca_ht_eur" isnull then 0 else "ca_ht_eur" end) / 100
                        ) * "vat_rate", 2
                    )::numeric
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
        ("aa"."third_party_num"||'_'||%(flow_name)s) as "supplier_name",
        "aa"."axe_bu",
        "aa"."axe_prj",
        "aa"."axe_pro",
        "ccm"."axe_pys",
        "aa"."axe_rfa",
        "uuid_big_category",
        false as "acquitted",
        now() as "created_at",
        %(created_by)s as "created_by",
        false as "delete",
        false as "export",
        false as "flag_to_active",
        false as "flag_to_delete",
        false as "flag_to_export",
        false as "flag_to_valid",
        now() as "modified_at",
        false as "flag_to_acquitted",
        %(dte_d)s as "invoice_month",
        "ccm"."vat",
        date_part('year', %(dte_f)s::date) as "invoice_year",
        "ccm"."vat_regime",
        "ccm"."cct_uuid_identification",
        "unit_weight",
        true as "sale_invoice",
        false as "purchase_invoice",
        false as "is_multi_store",
        false as "manual_entry",
        "uuid_sub_big_category",
        "pio"."origin"
    from (
        select
            "cs".qty,
            "cs"."unit_weight",
            "cs"."net_unit_price",
            "cs"."article",
            "cs"."function",
            "cs"."for_signboard",
            "cm"."sage_vat_by_default" as "vat",
            "cm"."sage_plan_code" as "vat_regime",
            "cm"."intitule",
            "cm"."cct",
            "ac"."uuid_identification" as "axe_pys",
            "cm"."uuid_identification" as "cct_uuid_identification"
        from "centers_clients_maisonsubcription" "cs"
        join "centers_clients_maison" "cm"
        on "cs"."cct" = "cm"."cct"
        left join (
            select
                "section", "uuid_identification"
            from "accountancy_sectionsage"
            where "axe" = 'PYS'
        ) "ac"
        on "cm"."pays" = "ac"."section"
        where "function" = %(flow_name)s
    ) "ccm"
    left join (
        select
            "ca"."code_maison",
            "ca"."code_cosium",
            "ca"."date_ca",
            "ca"."cct_uuid_identification",
            sum("ca"."ca_ht_eur") as "ca_ht_eur",
            "cm"."cct"
        from "compta_caclients"  "ca"
        join "centers_clients_maison" "cm" 
        on "ca"."cct_uuid_identification" = "cm"."uuid_identification" 
        where "ca"."date_ca" between %(dte_d)s and %(dte_f)s
        group by
            "ca"."date_ca",
            "ca"."cct_uuid_identification",
            "ca"."code_maison",
            "ca"."code_cosium",
            "cm"."cct"
    ) "cc"
    on "ccm"."cct" = "cc"."cct"
    left join "articles_article" "aa"
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
    on "ccm"."vat" = "av"."vat"
"""
)
