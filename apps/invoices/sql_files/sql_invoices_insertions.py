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

# TODO: Enlever la clause "cct_uuid_identification" is not null des requêtes

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
        "import_uuid_identification",
        "acuitis_order_date",
        "acuitis_order_number",
        "bi_id",
        "client_name",
        "command_reference",
        "comment",
        "customs_code",
        "delivery_date",
        "delivery_number",
        "ean_code",
        "final_date",
        "first_name",
        "flow_name",
        "formation_month",
        "heures_formation",
        "initial_date",
        "initial_home",
        "item_weight",
        "last_name",
        "libelle",
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
        "uuid_file"
    )
    (
        select 
            "import_uuid_identification",
            "acuitis_order_date",
            "acuitis_order_number",
            "bi_id",
            "client_name",
            "command_reference",
            "comment",
            "customs_code",
            "delivery_date",
            "delivery_number",
            "ean_code",
            "final_date",
            "first_name",
            "flow_name",
            "formation_month",
            "heures_formation",
            "initial_date",
            "initial_home",
            "item_weight",
            "last_name",
            "libelle",
            "ee"."modified_by",
            "origin",
            "personnel_type",
            "qty",
            "reference_article",
            coalesce("saisie", false) as "saisie",
            "saisie_by",
            "serial_number",
            "supplier",
            coalesce("pu"."to_display", 'U') as "unit_weight",
            "uuid_file"
         from "edi_ediimport" "ee"
         left join "parameters_unitchoices" "pu"
           on "ee"."unit_weight" = "pu"."num"
        where "ee"."cct_uuid_identification" is not null
          and "ee"."valid" = true
    )
    on conflict do nothing
    """
)


SQL_PURCHASES_INVOICES = sql.SQL(
    # Insertion des entêtes de factures d'achat
    """
    with "purchases" as (
        select distinct
            "eee"."invoice_number",
            "eee"."invoice_type",
            "eee"."invoice_date",
            "eee"."invoice_month",
            "eee"."invoice_year",
            coalesce("apa"."vat_regime", 'FRA') as "vat_regime",
            "eee"."invoice_amount_without_tax",
            "eee"."invoice_amount_tax",
            "eee"."invoice_amount_with_tax",
            "eee"."third_party_num",
            "eee"."uuid_control",
            "apa"."mode_reglement",
            "apa"."type_reglement",
            "icc"."code_center",
            "isb"."code_signboard",
            "eee"."devise",
            "eee"."purchase_invoice"
        from "edi_ediimport" "eee" 
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
            )
        ) "icc" 
        on "icc"."code_center" = "ccm"."center_purchase"
        left join (
            select 
                "bs"."third_party_num", "aa"."mode_reglement" , "aa"."code" as "type_reglement", "bs"."vat_sheme_supplier" as "vat_regime"
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
        where "eee"."cct_uuid_identification" is not null
          and "eee"."purchase_invoice" = true
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
        case 
            when "invoice_type" = '380'
            then 'FAF'
            else 'AVO'
        end as "invoice_type",
        "invoice_date",
        "invoice_month",
        "invoice_year",
        "vat_regime",
        "invoice_amount_without_tax",
        "invoice_amount_tax",
        "invoice_amount_with_tax",
        "third_party_num",
        "uuid_control",
        '1' as "adresse_tiers",
        null as "date_echeance",
        "mode_reglement",
        "type_reglement",
        "code_center",
        "code_signboard",
        "devise",
        "purchase_invoice",
        '1' "adresse_tiers_paye",
        null as "created_by"
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
        "uuid_identification",
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
        "uuid_invoice",
        "unit_weight",
        "account"
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
            "ee"."uuid_identification",
            "import_uuid_identification",
            "abu"."section" as "axe_bu",
            "prj"."section" as "axe_prj",
            "pro"."section" as "axe_pro",
            "rfa"."section" as "axe_rfa",
            "pys"."section" as "axe_pys",
            "vat",
            "vat_rate",
            "ee"."vat_regime",
            "pc"."slug_name" as "big_category",
            "ps"."name" as "sub_category",
            "ee"."created_by",
            "ee"."modified_by",
            "ii"."uuid_identification" as "uuid_invoice",
            "unit_weight",
            -- GERER ICI LES COMPTES X3
            '' as "account"
         from "edi_ediimport" "ee" 
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


SQL_SALES_INVOICES = sql.SQL(
    # Insertion des entêtes de factures de ventes
    """
    with "sales" as (
        select 
            "icc"."vat_regime_center" as "vat_regime",
            "eee"."net_amount",
            "eee"."vat_amount",
            "eee"."amount_with_vat",
            "pcc"."slug_name" as "big_category",
            "ccm"."cct", 
            "icc"."uuid_identification" as "centers",
            "parts"."uuid_identification" as "parties",
            "isb"."uuid_identification" as "signboard",
            "ccm"."third_party_num", 
            "icc"."code_center",
            "isb"."code_signboard",
            "eee"."devise"
        from "edi_ediimport" "eee" 
        left join "centers_clients_maison" "ccm" 
        on "ccm"."uuid_identification" = "eee"."cct_uuid_identification" 
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
        and "parts"."third_party_num" = "ccm"."third_party_num"s
        left join "parameters_category" "pcc" 
        on "pcc"."uuid_identification" = "eee"."uuid_big_category" 
        where "eee"."cct_uuid_identification" is not null
          and "eee"."sale_invoice" = true
          and "eee"."valid" = true
    ) 
    select 
        now() as "created_at",
        now() as "modified_at",
        false as "final",
        false as "export",
        gen_random_uuid() as "uuid_identification",
        '' as "invoice_sage_number",
        '' as "invoice_number",
        case 
            when sum("net_amount") >= 0 
            then 'FAC'
            else 'AVC'
        end as "invoice_type",
        '' as "invoice_date",
        '' as "invoice_month",
        '' as "invoice_year",
        "vat_regime",
        sum("net_amount") as "invoice_amount_without_tax",
        sum("vat_amount") as "invoice_amount_tax",
        sum("amount_with_vat") as "invoice_amount_with_tax",
        "big_category",
        "cct",
        "centers",
        '' as "created_by",
        "parties",
        "signboard",
        "third_party_num",
        "code_center",
        "code_signboard",
        "devise",
        true as "sale_invoice"
    from "sales"
    group by 
        "vat_regime",
        "big_category",
        "cct",
        "centers",
        "parties",
        "signboard",
        "third_party_num",
        "code_center",
        "code_signboard",
        "devise"
    """
)

SQL_SALES_DETAILS = sql.SQL(
    # insertion des détails spécifiques aux ventes
    """
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
        "uuid_identification",
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
        "uuid_invoice",
        "unit_weight",
        "account",
        "base",
        "grouping_goods"
    )
    (	
        select 
            now() as "created_at",
            now() as "modified_at",
            false as "export",
            false as "final",
            null as "final_at",
            -- GERER ICI LES PRIX DE VENTES
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
            "ee"."uuid_identification",
            "import_uuid_identification",
            "abu"."section" as "axe_bu",
            "prj"."section" as "axe_prj",
            "pro"."section" as "axe_pro",
            "rfa"."section" as "axe_rfa",
            "pys"."section" as "axe_pys",
            "vat",
            "vat_rate",
            "ee"."vat_regime",
            "pc"."slug_name" as "big_category",
            "ps"."name" as "sub_category",
            "ee"."created_by",
            "ee"."modified_by",
            "ii"."uuid_identification" as "uuid_invoice",
            "unit_weight",
            -- GERER ICI LES COMPTES X3
            '' as "account",
            "base",
            "grouping_goods"
         from "edi_ediimport" "ee" 
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
         left join (
            select 
                "axe_pro",
                "base",
                "gg"."grouping_goods"
              from "centers_purchasing_axeprogroupinggoods" "ca"
              left join "centers_purchasing_groupinggoods" "gg" 
                on "ca"."grouping_goods" = "gg"."uuid_identification" 
         ) "gr"
         on "gr"."axe_pro" = "ee"."axe_pro"
        where "ee"."cct_uuid_identification" is not null
          and "ee"."sale_invoice" = true
          and "ee"."valid" = true
    )
    on conflict do nothing
    """
)
