# pylint: disable=
"""
FR : Module des requêtes sql de post-traitement après génération des RFA
EN : Post-processing sql module after generate RFA

Commentaire:

created at: 2024-08-09
created by: Paulo ALVES

modified at: 2024-08-09
modified by: Paulo ALVES
"""

from psycopg2 import sql

rfa_dict = {
    "sql_vat": sql.SQL(
        """
        update "edi_ediimport"
        set "vat_rate" = ("vat_rate"::numeric / 100::numeric)::numeric
        where "uuid_identification" = %(uuid_identification)s
        and ("valid" = false or "valid" isnull)
        """
    ),
    "sql_total_amount_by_invoices": sql.SQL(
        """
        update edi_ediimport ei 
        set "invoice_amount_without_tax" = rec."invoice_amount_without_tax",
            "invoice_amount_tax" = rec."invoice_amount_tax",
            "invoice_amount_with_tax" = rec."invoice_amount_with_tax"
        from (
            select 
                "uuid_identification", 
                "invoice_number", 
                case 
                    when "invoice_type" = '380' 
                        then abs(sum("net_amount")) 
                        else -abs(sum("net_amount"))
                end as "invoice_amount_without_tax", 
                    case 
                    when "invoice_type" = '380' 
                        then abs(sum("vat_amount")) 
                        else -abs(sum("vat_amount"))
                end as "invoice_amount_tax",
                    case 
                    when "invoice_type" = '380' 
                        then abs(sum("amount_with_vat")) 
                        else -abs(sum("amount_with_vat"))
                end as "invoice_amount_with_tax"
            from "edi_ediimport" ee 
            where "uuid_identification" = %(uuid_identification)s
            and ("valid" = false or "valid" isnull)
            group by "uuid_identification" , "invoice_number", "invoice_type"
        ) rec 
        where ei."uuid_identification" = rec."uuid_identification"
        and ei."invoice_number" = rec."invoice_number"
        """
    ),
}

SQL_RFA_INSERTION = sql.SQL(
    """
    with vat as (
        select 
            "rate"
        from "accountancy_vatratsage" "av" 
        where "vat" = '002'
        and exists (
            select 
                1 
            from "accountancy_vatratsage" "avv" 
            group by "avv"."vat" 
            having max("avv"."vat_start_date") = "av"."vat_start_date" 
                and "avv"."vat" = "av"."vat"
        )
    )
    insert into edi_ediimport 
    (
        "uuid_identification",
        "third_party_num",
        "created_at",
        "modified_at",
        "flow_name",
        "supplier_ident",
        "supplier",
        "siret_payeur",
        "code_fournisseur",
        "code_maison",
        "maison",
        "invoice_number",
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
        "axe_pro_supplier",
        "supplier_name",
        "unit_weight",
        "purchase_invoice",
        "sale_invoice",
        "item_weight",
        "origin"
    )
    select
        %(uuid_identification)s as "uuid_identification",
        %(third_party_num)s as "third_party_num",
        now() as "created_at",
        now() as "modified_at",
        %(flow_name)s as "flow_name",
        %(supplier_ident)s as "supplier_ident",
        %(supplier)s as "supplier",
        %(siret_payeur)s as "siret_payeur",
        "mm"."cct" as "code_fournisseur",
        "mm"."cct" as "code_maison",
        "mm"."intitule" as "maison",
        (
            %(invoice_number)s 
            || 
            case when sum(-"ee"."net_amount") <= 0 
                then '381' 
                else '380' 
            end 
        ) as "invoice_number",
        %(invoice_date)s as "invoice_date",
        case 
            when sum(-"ee"."net_amount") <= 0 
            then '381' 
            else '380' 
        end as "invoice_type",
        'EUR' as "devise",
        %(reference_article)s as "reference_article",
        %(libelle)s as "libelle",
        'AA' as "famille",
        case 
            when sum(-"net_amount") <= 0
            then -1 
            else  1
        end as "qty",
        round(
            (sum("ee"."gross_amount"))::numeric, 
            2
        )::numeric as "gross_unit_price",
        round(
            (sum("ee"."net_unit_price") * "rs"."rfa_rate")::numeric, 
            2
        )::numeric as "net_unit_price",
        round(
            (sum(-"ee"."gross_amount"))::numeric, 
            2
        )::numeric as "gross_amount",
        round(
            (sum(-"ee"."net_amount") * "rs"."rfa_rate")::numeric, 
            2
        )::numeric as "net_amount",
        (select "rate" from "vat") as "vat_rate",
        round(
            ((select "rate" from "vat")::numeric/100) 
            * 
            round((sum(-"ee"."net_amount") * "rs"."rfa_rate")::numeric, 2)::numeric, 
            2
        )::numeric as "vat_amount",
        round(
            ((select "rate" from "vat")::numeric/100) 
            * 
            round(
                (sum(-"ee"."net_amount") * "rs"."rfa_rate")::numeric, 2)::numeric, 
                2
            )::numeric 
            + 
            round(
                (sum(-"ee"."net_amount") * "rs"."rfa_rate")::numeric, 
                2
        )::numeric as "amount_with_vat",
        'AA' as "axe_pro_supplier",
        %(supplier)s as "supplier_name",
        11 as "unit_weight",
        false as "purchase_invoice",
        true as "sale_invoice",
        0 as "item_weight",
        12 as "origin"

    from "edi_ediimport" "ee" 

    join "centers_clients_maison" "mm"
    on "ee"."cct_uuid_identification" = "mm"."uuid_identification"

    join "rfa_sectionproexclusion" "pro"
    on "ee"."axe_pro" <> "pro"."axe_pro" 

    join "rfa_sectionrfa" "rfa"
    on "ee"."axe_rfa" <> "rfa"."axe_rfa" 

    join "rfa_signboardexclusion" "ens"
    on "ee"."code_signboard" <> "ens"."signboard"

    join "rfa_supplierrate" "rs" 
    on "ee"."third_party_num" = "rs"."supplier"

    where "ee"."third_party_num" = %(third_party_num)s
    and not exists (
            select 
                1
            from "rfa_clientexclusion" "rf"
            join "centers_clients_maison" "cen"
            on "rf"."cct" = "cen"."cct"
            where "ee"."cct_uuid_identification" = "cen"."uuid_identification"
    )
    group by "mm"."cct", "mm"."intitule", "rs"."rfa_rate"
    having sum("net_amount") <> 0
    order by "mm"."cct"
    """
)

SQL_INSERTION_ICON = sql.SQL(
    """
    insert into parameters_iconoriginchoice 
    (
        "origin",
        "icon",
        "origin_name"
    )
    select
        12 as "origin",
        'cut' as "icon",
        'RFA MENSUELLE' as "origin_name"
    on conflict do nothing 
    """
)