# pylint: disable=E0401
"""
FR : Module des requêtes sql, pour l'insertion en base des invoices
EN : Module of sql queries, for the insertion in the base of invoices

Commentaire:

created at: 2023-03-11
created by: Paulo ALVES

modified at: 2023-03-11
modified by: Paulo ALVES
"""
from psycopg2 import sql


SQL_FIX_IMPORT_UUID = sql.SQL(
    # insertion d'un uuid si il est manquant
    """
    update "edi_ediimport" edi
    set "import_uuid_identification" = gen_random_uuid() 
    where "import_uuid_identification" isnull
      and "valid" = true
    """
)

SQL_COMMON_DETAILS = sql.SQL(
    # Insertion des détails communs aux factures achats ou ventes
    """
    insert into "invoices_invoicecommondetails"
    (
        "created_at",
        "modified_at",
        "import_uuid_identification",
        "acuitis_order_date",
        "acuitis_order_number",
        "client_name",
        "command_reference",
        "comment",
        "customs_code",
        "delivery_date",
        "delivery_number",
        "ean_code",
        "final_date",
        "first_name",
        "formation_month",
        "heures_formation",
        "initial_date",
        "initial_home",
        "item_weight",
        "last_name",
        "libelle",
        "supplier_initial_libelle",
        "modified_by",
        "origin",
        "personnel_type",
        "qty",
        "reference_article",
        "saisie",
        "saisie_by",
        "serial_number",
        "supplier",
        "unit_weight",
        "uuid_file",
        "bi_id",
        "flow_name",
        "third_party_num",
        "cct",
        "invoice_number",
        "invoice_date",
        "final",
        "purchase_invoice",
        "sale_invoice",
        "invoice_year"
    )
    (
        select 
            now() as "created_at",
            now() as "modified_at",
            "import_uuid_identification",
            "acuitis_order_date",
            coalesce("acuitis_order_number", '') as "acuitis_order_number",
            coalesce("client_name", '') as "client_name",
            coalesce("command_reference", '') as "command_reference",
            coalesce("ee"."comment", '') as "comment",
            coalesce("ee"."customs_code", '') as "customs_code",
            case 
                when "delivery_number" isnull 
                then null 
                else "delivery_date" 
            end as "delivery_date",
            coalesce("delivery_number", '') as "delivery_number",
            coalesce("ee"."ean_code", '') as "ean_code",
            "final_date",
            "first_name",
            "formation_month",
            "heures_formation",
            "initial_date",
            "initial_home",
            "aa"."item_weight",
            "last_name",
            case when "aa"."libelle_heron" is not null and "aa"."libelle_heron" != ''
                then "aa"."libelle_heron"
                else "ee"."libelle"
            end as "libelle",
            "ee"."libelle" as "supplier_initial_libelle",
            "ee"."modified_by",
            "origin",
            "pn"."to_display" as "personnel_type",
            "qty",
            "reference_article",
            coalesce("saisie", false) as "saisie",
            "saisie_by",
            coalesce("serial_number", '') as "serial_number",
            "supplier",
            coalesce("pu"."to_display", 'U') as "unit_weight",
            "uuid_file",
            "bi_id",
            "flow_name",
            "ee"."third_party_num",
            "ccm"."cct",
            "ee"."invoice_number",
            "ee"."invoice_date",
            false as "final",
            "purchase_invoice",
            "sale_invoice",
            "ee"."invoice_year"
         from "edi_ediimport" "ee"
         left join "articles_article" "aa"
                on "aa"."reference" = "ee"."reference_article" 
               and "aa"."third_party_num" = "ee"."third_party_num" 
         left join "parameters_unitchoices" "pu"
           on "ee"."unit_weight" = "pu"."num"
         left join "centers_clients_maison" "ccm" 
           on "ee"."cct_uuid_identification" = "ccm"."uuid_identification" 
         left join "parameters_nature" "pn"
                on "ee"."personnel_type" = "pn"."uuid_identification"
             where "ee"."valid" = true
             order by "ee"."id"
    )
    on conflict do nothing
    """
)

# ACHAT ============================================================================================

SQL_PURCHASES_INVOICES = sql.SQL(
    # Insertion des entêtes de factures d'achat
    """
    with "purchases" as (
        select distinct
            "eee"."invoice_number",
            "cpt"."purchase_type_facture" as "invoice_type",
            "eee"."invoice_date",
            "eee"."invoice_month",
            "eee"."invoice_year",
            coalesce("apa"."vat_regime", 'FRA') as "vat_regime",
            "eee"."invoice_amount_without_tax",
            "eee"."invoice_amount_tax",
            "eee"."invoice_amount_with_tax",
            "eee"."third_party_num",
            "eee"."uuid_control",
            "apa"."mode" as "mode_reglement",
            "apa"."type_reglement",
            "icc"."code_center",
            "isb"."code_signboard",
            "eee"."devise",
            "eee"."purchase_invoice",
            "icc"."cpy",
            "icc"."fcy",
            "icc"."code_plan_sage"
        from "edi_ediimport" "eee" 
        left join "centers_clients_maison" "ccm" 
        on "eee"."cct_uuid_identification" = "ccm"."uuid_identification" 
        left join (
            select 
                "uuid_identification", 
                "code_center", 
                "vat_regime_center",
                "cpy",
                "fcy",
                "code_plan_sage"
            from "invoices_centersinvoices" "ici"
            where exists (
                select 1 
                from "invoices_centersinvoices" "cii" 
                group by "code_center" 
                having max("cii"."created_at") = "ici"."created_at"
                and "cii"."code_center" = "ici"."code_center"
            )
        ) "icc" 
        on "icc"."code_center" = "ccm"."center_purchase"
        left join (
            select 
                "bs"."third_party_num", 
                "aa"."mode", 
                "aa"."code" as "type_reglement", 
                "bs"."vat_sheme_supplier" as "vat_regime"
            from "book_society" "bs"
            left join "accountancy_paymentcondition" "aa"
            on "aa"."auuid" = "bs"."payment_condition_supplier"
        ) "apa"
        on "apa"."third_party_num" = "eee"."third_party_num"
        left join (
            select 
                "uuid_identification", 
                "code_signboard" 
            from "invoices_signboardsinvoices" "sci"
            where exists (
                select 1 
                from "invoices_signboardsinvoices" "sii" 
                group by "code_signboard" 
                having max("sii"."created_at") = "sci"."created_at"
            )
        ) "isb" 
        on "isb"."code_signboard" = "ccm"."sign_board" 
        left join "centers_purchasing_typefacture" "cpt"
        on "cpt"."invoice_type" = "eee"."invoice_type"
        and "cpt"."child_center" = "eee"."code_center"  
        where "eee"."purchase_invoice" = true
          and "eee"."valid" = true
    )
    select distinct
        now() as "created_at",
        now() as "modified_at",
        false as "final",
        false as "export",
        gen_random_uuid() as "uuid_identification",
        '' as "invoice_sage_number",
        "invoice_number",
        "invoice_type",
        "invoice_date",
        "invoice_month",
        "invoice_year",
        "vat_regime",
        "invoice_amount_without_tax",
        "invoice_amount_tax",
        "invoice_amount_with_tax",
        "third_party_num",
        -- "uuid_control",
        '1' as "adresse_tiers",
        -- null as "date_echeance",
        "mode_reglement",
        "type_reglement",
        "code_center",
        "code_signboard",
        "devise",
        "purchase_invoice",
        '1' "adresse_tiers_paye",
        null as "created_by",
        null as "modified_by",
        "cpy",
        "fcy",
        date_trunc('month', now())::date as "integration_month",
        "code_plan_sage"
    from "purchases" 
    """
)

SQL_PURCHASES_DETAILS = sql.SQL(
    # insertion des détails spécifiques aux achats
    """
    insert into "invoices_invoicedetail"
    (
        "created_at",
        "modified_at",
        "export",
        "final",
        "final_at",
        "gross_unit_price",
        "net_unit_price",
        "gross_amount",
        "base_discount_01",
        "discount_price_01",
        "base_discount_02",
        "discount_price_02",
        "base_discount_03",
        "discount_price_03",
        "net_amount",
        "vat_amount",
        "amount_with_vat",
        "uuid_invoice",
        "import_uuid_identification",
        "axe_bu",
        "axe_prj",
        "axe_pro",
        "axe_rfa",
        "axe_pys",
        "vat",
        "vat_rate",
        "vat_regime",
        "big_category",
        "sub_category",
        "created_by",
        "modified_by",
        "unit_weight",
        "account",
        "flow_name",
        "bi_id"
    )
    (    
        select 
            now() as "created_at",
            now() as "modified_at",
            false as "export",
            false as "final",
            null as "final_at",
            "gross_unit_price",
            "net_unit_price",
            "gross_amount",
            "base_discount_01",
            "discount_price_01",
            "base_discount_02",
            "discount_price_02",
            "base_discount_03",
            "discount_price_03",
            "net_amount",
            "vat_amount",
            "amount_with_vat",
            "ii"."uuid_identification" as "uuid_invoice",
            "import_uuid_identification",
            "abu"."section" as "axe_bu",
            "prj"."section" as "axe_prj",
            "pro"."section" as "axe_pro",
            "rfa"."section" as "axe_rfa",
            "pys"."section" as "axe_pys",
            "ee"."vat",
            "vat_rate",
            "ee"."vat_regime",
            "pc"."slug_name" as "big_category",
            "ps"."name" as "sub_category",
            "ee"."created_by",
            "ee"."modified_by",
            "ee"."unit_weight",
            "ac"."purchase_account" as "account",
            "flow_name",
            "bi_id"
         from "edi_ediimport" "ee" 
         join "articles_article" "aa" 
           on "ee"."third_party_num" = "aa"."third_party_num" 
          and "ee"."reference_article" = "aa"."reference" 
         left join "articles_articleaccount" "ac"
           on "aa"."uuid_identification" = "ac"."article"
          and "ee"."code_center" = "ac"."child_center"
          and "ee"."vat" = "ac"."vat"
         join "invoices_invoice" "ii"
           on "ii"."third_party_num" = "ii"."third_party_num"
          and "ii"."invoice_number" = "ee"."invoice_number"
          and "ii"."invoice_year" = "ee"."invoice_year"
         left join "accountancy_sectionsage" "abu" 
           on "abu"."uuid_identification" = "ee"."axe_bu"
         left join "accountancy_sectionsage" "prj" 
           on "prj"."uuid_identification" = "ee"."axe_prj"
         left join "accountancy_sectionsage" "pro" 
           on "pro"."uuid_identification" = "ee"."axe_pro"
         left join "accountancy_sectionsage" "pys" 
           on "pys"."uuid_identification" = "ee"."axe_pys"
         left join "accountancy_sectionsage" "rfa" 
           on "rfa"."uuid_identification" = "ee"."axe_rfa"
         left join "parameters_category" "pc" 
           on "pc"."uuid_identification" = "ee"."uuid_big_category" 
         left join "parameters_subcategory" "ps" 
           on "ps"."uuid_identification" = "ee"."uuid_sub_big_category" 
        where "ee"."purchase_invoice" = true
          and "ee"."valid" = true
    )
    on conflict do nothing
    """
)

SQL_PURCHASES_ACCOUNTS = sql.SQL(
    # Mise à jour des comptes X3 comptable
    """
    
    """
)

SQL_PURCHASE_FOR_EXPORT_X3 = sql.SQL(
    """
    update "invoices_invoice" "isv"
    set "type_cours" = "rrr"."type_cours",
        "date_cours" = "rrr"."date_cours",
        "tiers_payeur" = "rrr"."tiers_payeur",
        "date_depart_echeance" = "rrr"."date_depart_echeance",
        "code_plan_sage" = "rrr"."code_plan_sage",
        "regime_tva_tiers" = "rrr"."regime_tva_tiers",
        "invoice_type_name" = "rrr"."invoice_type_name"
    from (
        select 
            "isi"."id",
            '1' as "type_cours",
            "isi"."invoice_date" as "date_cours",
            "isi"."third_party_num" as "tiers_payeur",
            "isi"."invoice_date" as "date_depart_echeance",
            "cpc"."code_plan_sage",
            coalesce("bsi"."vat_sheme_supplier", '') as "regime_tva_tiers",
            case 
                when "cpt"."invoice_type" = '380'
                then 'Facture'
                else 'Avoir'
            end as "invoice_type_name"
        from "invoices_invoice" "isi"
        left join "centers_purchasing_childcenterpurchase" "cpc"
        on "isi"."code_center" = "cpc"."code"
        join "book_society" "bsi"
          on "isi"."third_party_num" = "bsi"."third_party_num" 
        left join "centers_purchasing_typefacture" "cpt"
        on "cpt"."purchase_type_facture" = "isi"."invoice_type"
        and "cpt"."child_center" = "isi"."code_center" 
        where not "isi"."final"    
    ) "rrr"
    where "isv"."id" = "rrr"."id"
    and not "final"
    """
)

SQL_CONTROL_PURCHASES_INSERTION = sql.SQL(
    """
    select 
        is2.invoice_number
    from invoices_invoice is2 
    join invoices_invoicedetail is3 
    on is2.uuid_identification  = is3.uuid_invoice 
    group by 
        is2.invoice_number, 
        is2.third_party_num,
        is2.invoice_year,
        is2.invoice_amount_without_tax, 
        is2.invoice_amount_tax, 
        is2.invoice_amount_with_tax 
    having     (
            is2.invoice_amount_without_tax 
            - 
            sum(is3.net_amount) 
            + 
            is2.invoice_amount_tax 
            - 
            sum(is3.vat_amount) 
            + 
            is2.invoice_amount_with_tax 
            - 
            sum(is3.amount_with_vat)
    ) != 0
    """
)


SQL_PURCHASE_DETAILS_FOR_EXPORT_X3 = sql.SQL(
    """
    update "invoices_invoicedetail" "isv"
    set "collectif" = "rrr"."collectif"
    from (
        select 
            "isd"."id",
            coalesce("aac"."call_code", '') as "collectif"
        from "invoices_invoice" "isi"
        join "invoices_invoicedetail" "isd"
          on "isi"."uuid_identification" = "isd"."uuid_invoice"
        join "accountancy_accountsage" "aac" 
          on "isi"."code_plan_sage" = "aac"."code_plan_sage" 
         and "isd"."account" = "aac"."account" 
        where not "isi"."final"
    ) "rrr"
    where "isv"."id" = "rrr"."id"
    and not "final"
    """
)

# VENTE ============================================================================================

SQL_CLEAR_INVOICES_SIGNBOARDS = sql.SQL(
    """
    delete from "invoices_signboardsinvoices" "isign"
    where "isign"."id" in (
        select 
            "isi"."id" 
        from "invoices_signboardsinvoices" "isi"
        join (
            select 
                max("id") as "id", "code_signboard", "created_at"
            from "invoices_signboardsinvoices" "inv"
            where exists (
                select 1
                from (
                    select 
                        "code_signboard", max("created_at") as "created_at"
                    from "invoices_signboardsinvoices"
                    group by "code_signboard"
                ) as "req"
                where "req"."code_signboard" = "inv"."code_signboard"
                  and "req"."created_at" = "inv"."created_at"
            )
            group by "code_signboard", "created_at"
            having count(*) >1
        ) "rc" 
        on "rc"."code_signboard" = "isi"."code_signboard"
        and "rc"."created_at" = "isi"."created_at"
        and "rc"."id" != "isi"."id"
    )
"""
)

SQL_SALES_INVOICES = sql.SQL(
    # Insertion des entêtes de factures de ventes
    """
    with "amounts" as (
        select 
            "vt"."id",
            "vt"."ccm_vat" as "vat",
            "vt"."net_amount",
            "vt"."vat_rate",
            round(
                "vt"."net_amount"::numeric * "vt"."vat_rate"::numeric, 2
            )::numeric as "vat_amount",
            (
                round("vt"."net_amount"::numeric * "vt"."vat_rate"::numeric, 2)::numeric 
                + 
                "vt"."net_amount"::numeric
            )::numeric as "amount_with_vat"
        from (
            select
                "eee"."id", 
                "eee"."net_amount",
                case 
                    when "ccm"."sage_vat_by_default" = '001' and "eee"."vat_rate" = 0 
                        then (
                                select distinct
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
                                and "vtr"."vat" = '001'
                        ) 
                    when "ccm"."sage_vat_by_default" = '001' then "eee"."vat_rate"
                    when "ccm"."sage_vat_by_default" != '001' then (
                                select distinct
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
                                and "vtr"."vat" = "ccm"."sage_vat_by_default"
                        ) 
                end as "vat_rate",
                case 
                    when "ccm"."sage_vat_by_default" = '001' and "eee"."vat_rate" = 0 then '001'
                    when "ccm"."sage_vat_by_default" = '001' then "eee"."vat"
                    else "ccm"."sage_vat_by_default"
                end as "ccm_vat"        
            from "edi_ediimport" "eee" 
            join "centers_clients_maison" "ccm" 
            on "eee"."cct_uuid_identification" = "ccm"."uuid_identification"
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
    "sales" as (
        select 
            "icc"."vat_regime_center" as "vat_regime",
            "amo"."net_amount",
            "amo"."vat_amount",
            "amo"."amount_with_vat",
            "pcc"."name" as "big_category",
            "pcc"."code" as "big_category_code",
            "pcc"."slug_name" as "big_category_slug_name",
            "ccm"."cct", 
            "icc"."uuid_identification" as "centers",
            "parts"."uuid_identification" as "parties",
            "isb"."uuid_identification" as "signboard",
            "ccm"."third_party_num", 
            "icc"."code_center",
            "isb"."code_signboard",
            "eee"."devise",
            "bs"."payment_condition_client",
            "pcc"."ranking" as "big_category_ranking",
            -- Case when car la formation doit être facturée à la ligne
            case 
                when "eee"."third_party_num" = 'ZFORM'
                then "eee"."import_uuid_identification"::varchar
                else ''
            end as "formation",
            "icc"."fcy",
            "icc"."cpy",
            "ccm"."center_purchase",
            "ccm"."type_x3"
        from "edi_ediimport" "eee"        
        join "amounts" "amo"
        on "amo"."id" = "eee"."id"
        left join "centers_clients_maison" "ccm" 
        on "eee"."cct_uuid_identification" = "ccm"."uuid_identification" 
        left join "book_society" "bs"
        on "bs"."third_party_num" = "ccm"."third_party_num"  
        left join (
            select 
                "uuid_identification", 
                "code_center", 
                "vat_regime_center",
                "cpy",
                "fcy"
            from "invoices_centersinvoices" "ici"
            where exists (
                select 1 
                from "invoices_centersinvoices" "cii" 
                group by "code_center" 
                having max("cii"."created_at") = "ici"."created_at"
                and "cii"."code_center" = "ici"."code_center"
            )
        ) "icc" 
        on "icc"."code_center" = "ccm"."center_purchase"
        left join (
            select 
                "uuid_identification", 
                "code_signboard" 
            from "invoices_signboardsinvoices" "sci"
            where exists (
                select 1 
                from "invoices_signboardsinvoices" "sii" 
                group by "code_signboard" 
                having max("sii"."created_at") = "sci"."created_at"
                and "sii"."code_signboard" = "sci"."code_signboard"
            )
        ) "isb" 
        on "isb"."code_signboard" = "ccm"."sign_board" 
        left join (
            select 
                "uuid_identification", 
                "cct", 
                "third_party_num" 
            from "invoices_partiesinvoices" "ip"
            where exists (
                select 1 
                  from "invoices_partiesinvoices" "ipi" 
                 where "ipi"."cct" = "ip"."cct"
                   and "ipi"."third_party_num" = "ip"."third_party_num" 
                 group by "cct", 
                          "third_party_num"  
                having max("ipi"."created_at") = "ip"."created_at"
            )
             
        ) "parts"
        on "parts"."cct" = "ccm"."cct"
        and "parts"."third_party_num" = "ccm"."third_party_num"
        left join "parameters_category" "pcc" 
        on "pcc"."uuid_identification" = "eee"."uuid_big_category" 
        where "eee"."sale_invoice" = true
          and "eee"."valid" = true
          and "ccm"."type_x3" in (1, 2)
    ) 
    select 
        now() as "created_at",
        now() as "modified_at",
        false as "final",
        false as "export",
        gen_random_uuid() as "uuid_identification",
        '' as "invoice_number",
        '' as "invoice_sage_number",
        case 
            when sum("net_amount") >= 0 
            then (
                    select "sale_type_facture" 
                    from "centers_purchasing_typefacture" 
                    where "invoice_type" = '380' 
                    and "child_center" = "center_purchase"
                )
            else (
                    select "sale_type_facture" 
                    from "centers_purchasing_typefacture" 
                    where "invoice_type" = '381' 
                    and "child_center" = "center_purchase"
                )
        end as "invoice_type",
        '' as "invoice_date",
        '' as "invoice_month",
        '' as "invoice_year",
        "vat_regime",
        sum("net_amount") as "invoice_amount_without_tax",
        sum("vat_amount") as "invoice_amount_tax",
        sum("amount_with_vat") as "invoice_amount_with_tax",
        "big_category",
        "big_category_code",
        "big_category_slug_name",
        "cct",
        "centers",
        null as "created_by",
        null as "modified_by",
        "parties",
        "signboard",
        "third_party_num",
        "code_center",
        "code_signboard",
        "devise",
        true as "sale_invoice",
        false as "printed",
        "payment_condition_client" as "mode_reglement",
        "big_category_ranking",
        "formation",
        false as "send_email",
        "fcy",
        "cpy",
        case 
            when sum("net_amount") >= 0 then 'Facture' else 'Avoir'
        end as "invoice_type_name",
        "type_x3"
    from "sales"
    group by 
        "vat_regime",
        "big_category",        
        "big_category_code",
        "big_category_slug_name",
        "cct",
        "centers",
        "parties",
        "signboard",
        "third_party_num",
        "code_center",
        "code_signboard",
        "devise",
        "payment_condition_client",
        "big_category_ranking",
        "formation",
        "fcy",
        "cpy",
        "center_purchase",
        "type_x3"
    order by 
        "cct",
        "big_category_ranking"
    """
)

SQL_SALES_FOR_EXPORT_X3 = sql.SQL(
    """
    update "invoices_saleinvoice" "isv"
    set "regime_tva_maison" = "rrr"."regime_tva_maison",
        "collectif" = "rrr"."collectif",
        "type_cours" = "rrr"."type_cours",
        "date_cours" = "rrr"."date_cours",
        "tiers_payeur" = "rrr"."tiers_payeur",
        "date_depart_echeance" = "rrr"."date_depart_echeance",
        "code_plan_sage" = "rrr"."code_plan_sage"
    from (
        select 
            "isi"."id",
            "avs"."vat_regime" as "regime_tva_maison",
            case 
                when "isi"."invoice_amount_without_tax" < 0
                then coalesce("aac"."call_code", '')
                else coalesce("acc"."call_code", '')
            end as "collectif",
            '1' as "type_cours",
            "isi"."invoice_date" as "date_cours",
            "isi"."third_party_num" as "tiers_payeur",
            "isi"."invoice_date" as "date_depart_echeance",
            "cpc"."code_plan_sage"
        from "invoices_saleinvoice" "isi"
        left join "centers_clients_maison" "ccm"
        on "isi"."cct" = "ccm"."cct" 
        left join "accountancy_accountsage" "aac" 
        on "ccm"."debit_account" = "aac"."uuid_identification" 
        left join "accountancy_accountsage" "acc"
        on "ccm"."credit_account" = "acc"."uuid_identification" 
        left join "accountancy_vatsage" "avs"
        on "ccm"."sage_vat_by_default" = "avs"."vat" 
        left join "centers_purchasing_childcenterpurchase" "cpc"
        on "isi"."code_center" = "cpc"."code"
        where not "isi"."final"
    ) "rrr"
    where "isv"."id" = "rrr"."id"
      and not "final"
    """
)

SQL_SALES_DETAILS = sql.SQL(
    # insertion des détails spécifiques aux ventes
    """
    with "amounts" as (
        select 
            "vt"."id",
            "vt"."ccm_vat" as "vat",
            "vt"."net_amount",
            "vt"."vat_rate",
            round(
                "vt"."net_amount"::numeric * "vt"."vat_rate"::numeric, 2
            )::numeric as "vat_amount",
            (
                round("vt"."net_amount"::numeric * "vt"."vat_rate"::numeric, 2)::numeric 
                + 
                "vt"."net_amount"::numeric
            )::numeric as "amount_with_vat"
        from (
            select
                "eee"."id", 
                "eee"."net_amount",
                case 
                    when "ccm"."sage_vat_by_default" = '001' and "eee"."vat_rate" = 0 
                        then (
                                select distinct
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
                                and "vtr"."vat" = '001'
                        ) 
                    when "ccm"."sage_vat_by_default" = '001' then "eee"."vat_rate"
                    when "ccm"."sage_vat_by_default" != '001' then (
                                select distinct
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
                                and "vtr"."vat" = "ccm"."sage_vat_by_default"
                        ) 
                end as "vat_rate",
                case 
                    when "ccm"."sage_vat_by_default" = '001' and "eee"."vat_rate" = 0 then '001'
                    when "ccm"."sage_vat_by_default" = '001' then "eee"."vat"
                    else "ccm"."sage_vat_by_default"
                end as "ccm_vat"        
            from "edi_ediimport" "eee" 
            join "centers_clients_maison" "ccm" 
            on "eee"."cct_uuid_identification" = "ccm"."uuid_identification"
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
    )
    insert into "invoices_saleinvoicedetail"
    (
        "created_at",
        "modified_at",
        "export",
        "final",
        "final_at",
        "gross_unit_price",
        "net_unit_price",
        "gross_amount",
        "base_discount_01",
        "discount_price_01",
        "base_discount_02",
        "discount_price_02",
        "base_discount_03",
        "discount_price_03",
        "net_amount",
        "vat_amount",
        "amount_with_vat",
        "import_uuid_identification",
        "axe_bu",
        "axe_prj",
        "axe_pro",
        "axe_rfa",
        "axe_pys",
        "vat",
        "vat_rate",
        "vat_regime",
        "big_category",
        "sub_category",
        "base",
        "grouping_goods",
        "created_by",
        "modified_by",
        "uuid_invoice",
        "unit_weight",
        "account",
        "ranking",
        "account_od_600",
    )
    (    
        select 
            now() as "created_at",
            now() as "modified_at",
            false as "export",
            false as "final",
            "isi"."final_at",
            "det"."gross_unit_price",
            "det"."net_unit_price",
            "det"."gross_amount",
            "det"."base_discount_01",
            "det"."discount_price_01",
            "det"."base_discount_02",
            "det"."discount_price_02",
            "det"."base_discount_03",
            "det"."discount_price_03",
            "det"."net_amount",
            "det"."vat_amount",
            "det"."amount_with_vat",
            "det"."import_uuid_identification",
            "det"."axe_bu",
            "det"."axe_prj",
            "det"."axe_pro",
            "det"."axe_rfa",
            "det"."axe_pys",
            "det"."vat",
            "det"."vat_rate",
            "det"."vat_regime",
            "det"."big_category",
            "det"."sub_category",
            "det"."base",
            "det"."grouping_goods",
            "det"."created_by",
            "det"."modified_by",
            "isi"."uuid_identification" as "uuid_invoice",
            "det"."unit_weight",
            "det"."account",
            "det"."ranking",
            "det"."account_od_600"
        from (
            select 
                -- TODO: GERER ICI LES PRIX DE VENTES
                "gross_unit_price",
                "net_unit_price",
                "gross_amount",
                coalesce("base_discount_01", 0) as "base_discount_01",
                coalesce("discount_price_01", 0) as "discount_price_01",
                coalesce("base_discount_02", 0) as "base_discount_02",
                coalesce("discount_price_02", 0) as "discount_price_02",
                coalesce("base_discount_03", 0) as "base_discount_03",
                coalesce("discount_price_03", 0) as "discount_price_03",
                "amo"."net_amount",
                "amo"."vat_amount",
                "amo"."amount_with_vat",
                "import_uuid_identification",
                "abu"."section" as "axe_bu",
                "prj"."section" as "axe_prj",
                -- TODO: A CHANGER LORS DES VRAI IMPORTS
                coalesce("pro"."section", 'DIV') as "axe_pro",
                "rfa"."section" as "axe_rfa",
                "ccm"."pays" as "axe_pys",
                "amo"."vat"::varchar,
                "amo"."vat_rate",
                "eee"."vat_regime",
                "pc"."slug_name" as "big_category",
                coalesce("ps"."name", '') as "sub_category",
                -- TODO: A CHANGER LORS DES VRAI IMPORTS
                coalesce("base", '606 - CONSOMMABLES') as "base",
                -- TODO: A CHANGER LORS DES VRAI IMPORTS
                coalesce("grouping_goods", 'CONSOMMABLES') as "grouping_goods",
                "eee"."created_by",
                "eee"."modified_by",
                "eee"."unit_weight",
                "ac"."sale_account" as "account",
                "ac"."purchase_account" as "account_od_600",
                "eee"."devise",
                "ccm"."cct", 
                "icc"."uuid_identification" as "centers",
                "parts"."uuid_identification" as "parties",
                "isb"."uuid_identification" as "signboard",
                "ccm"."third_party_num" as "client_third_party_num", 
                "icc"."code_center",
                "isb"."code_signboard",
                "gr"."ranking",
                -- Case when car la formation doit être facturée à la ligne
                case 
                    when "eee"."third_party_num" = 'ZFORM'
                    then "eee"."import_uuid_identification"::varchar
                    else ''
                end as "formation",
                "ccm"."type_x3"
            from "edi_ediimport" "eee"    
            join "articles_article" "aa" 
              on "eee"."third_party_num" = "aa"."third_party_num" 
             and "eee"."reference_article" = "aa"."reference" 
            left join "articles_articleaccount" "ac"
              on "aa"."uuid_identification" = "ac"."article"
             and "eee"."code_center" = "ac"."child_center"
             and "eee"."vat" = "ac"."vat" 
            join "amounts" "amo"
            on "amo"."id" = "eee"."id"
            left join "centers_clients_maison" "ccm" 
            on "eee"."cct_uuid_identification" = "ccm"."uuid_identification" 
            left join (
                select 
                    "uuid_identification", 
                    "code_center", 
                    "vat_regime_center"
                from "invoices_centersinvoices" "ici"
                where exists (
                    select 1 
                    from "invoices_centersinvoices" "cii" 
                    group by "code_center" 
                    having max("cii"."created_at") = "ici"."created_at"
                    and "cii"."code_center" = "ici"."code_center"
                )
            ) "icc" 
            on "icc"."code_center" = "ccm"."center_purchase"
            left join (
                select 
                    "uuid_identification", 
                    "code_signboard" 
                from "invoices_signboardsinvoices" "sci"
                where exists (
                    select 1 
                    from "invoices_signboardsinvoices" "sii" 
                    group by "code_signboard" 
                    having max("sii"."created_at") = "sci"."created_at"
                    and "sii"."code_signboard" = "sci"."code_signboard"
                )
            ) "isb" 
            on "isb"."code_signboard" = "ccm"."sign_board" 
            left join (
                select 
                    "uuid_identification", 
                    "cct", 
                    "third_party_num" 
                from "invoices_partiesinvoices" "ip"
                where exists (
                    select 1 
                      from "invoices_partiesinvoices" "ipi" 
                     where "ipi"."cct" = "ip"."cct"
                       and "ipi"."third_party_num" = "ip"."third_party_num" 
                     group by "cct", 
                              "third_party_num"  
                    having max("ipi"."created_at") = "ip"."created_at"
                )
            ) "parts"
            on "parts"."cct" = "ccm"."cct"
            and "parts"."third_party_num" = "ccm"."third_party_num"
            left join "accountancy_sectionsage" "abu" 
               on "abu"."uuid_identification" = "eee"."axe_bu"
             left join "accountancy_sectionsage" "prj" 
               on "prj"."uuid_identification" = "eee"."axe_prj"
             left join "accountancy_sectionsage" "pro" 
               on "pro"."uuid_identification" = "eee"."axe_pro"
             left join "accountancy_sectionsage" "pys" 
               on "pys"."uuid_identification" = "eee"."axe_pys"
             left join "accountancy_sectionsage" "rfa" 
               on "rfa"."uuid_identification" = "eee"."axe_rfa"
            left join "parameters_category" "pc" 
               on "pc"."uuid_identification" = "eee"."uuid_big_category" 
             left join "parameters_subcategory" "ps" 
               on "ps"."uuid_identification" = "eee"."uuid_sub_big_category" 
            left join (
                select 
                    "axe_pro",
                    "base",
                    "gg"."grouping_goods",
                    "gg"."ranking"
                  from "centers_purchasing_axeprogroupinggoods" "ca"
                  left join "centers_purchasing_groupinggoods" "gg" 
                    on "ca"."grouping_goods" = "gg"."uuid_identification" 
             ) "gr"
             on "gr"."axe_pro" = "eee"."axe_pro"
            where "eee"."sale_invoice" = true
              and "eee"."valid" = true
        ) det 
        join (
            select 
                "uuid_identification",
                "big_category_slug_name",
                "cct",
                "centers",
                "parties",
                "signboard",
                "third_party_num",
                "code_center",
                "code_signboard",
                "devise",
                "formation",
                "type_x3",
                "final_at"
            from "invoices_saleinvoice"  
            where not "final" and not "export"
        ) "isi" 
        on "isi"."big_category_slug_name" = "det"."big_category"
        and "isi"."cct" = "det"."cct"
        and "isi"."code_center" = "det"."code_center"
        and "isi"."code_signboard" = "det"."code_signboard"
        and "isi"."devise" = "det"."devise"
        and "isi"."formation" = "det"."formation"
        and "isi"."type_x3" = "det"."type_x3"
     )
    on conflict do nothing
    """
)

SQL_SALESS_ACCOUNTS = sql.SQL(
    # Mise à jour des comptes X3 comptable
    """
    """
)

SQL_CONTROL_SALES_INSERTION = sql.SQL(
    """
    select 
        is2.invoice_number
    from invoices_saleinvoice is2 
    join invoices_saleinvoicedetail is3 
    on is2.uuid_identification  = is3.uuid_invoice 
    group by 
        is2.invoice_number, 
        is2.invoice_amount_without_tax, 
        is2.invoice_amount_tax, 
        is2.invoice_amount_with_tax 
    having     (
            is2.invoice_amount_without_tax 
            - 
            sum(is3.net_amount) 
            + 
            is2.invoice_amount_tax 
            - 
            sum(is3.vat_amount) 
            + 
            is2.invoice_amount_with_tax 
            - 
            sum(is3.amount_with_vat)
    ) != 0
    """
)
