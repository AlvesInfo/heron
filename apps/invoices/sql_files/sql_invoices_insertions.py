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
    """
)

SQL_PURCHASES_DETAILS = sql.SQL(
    # insertion des détails spécifiques aux achats
    """
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
        and "parts"."third_party_num" = "ccm"."third_party_num"
        left join "parameters_category" "pcc" 
        on "pcc"."uuid_identification" = "eee"."uuid_big_category" 
        where "eee"."sale_invoice" = true
          and "eee"."cct_uuid_identification" is not null
          and "eee"."valid" = true
    ) 
    select 
        now() as "created_at",
        now() as "modified_at",
        false as "final",
        false as "export",
        gen_random_uuid() as "uuid_identification",
        '' as "invoice_number",
        case 
            when sum("net_amount") >= 0 
            then '380'
            else '381'
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
    """
)
