with "maisons" as (
    select
        "cct",
        "intitule",
        "closing_date",
        "opening_date",
        "uuid_identification",
        "sb"."name" as "signboard",
        "co"."country_name",
        "cm"."type_x3"
    from "centers_clients_maison" "cm"
    join "centers_purchasing_signboard" "sb"
    on "cm"."sign_board" = "sb"."code"
    left join "countries_country" "co"
    on "cm"."pays" = "co"."country"
),
"edi_details" as (
    select
        "cc"."signboard",
        "cc"."country_name",
        "cc"."cct" || ' - ' || "cc"."intitule" as "cct_name",
        "cc"."cct",
        "cc"."opening_date",
        "cc"."closing_date",
        "ee"."net_amount" as "M_00",
        0 as "M_01",
        0 as "M_02",
        0 as "M_03",
        "cc"."type_x3"
    from "edi_ediimport" "ee"
    join "maisons" "cc"
    on "ee"."cct_uuid_identification" = "cc"."uuid_identification"
    where "ee"."purchase_invoice"
    and "ee"."net_amount" <> 0
),
"invoices_details" as (
    select
        "cc"."signboard",
        "cc"."country_name",
        "cc"."cct" || ' - ' || "cc"."intitule" as "cct_name",
        "cc"."cct",
        "cc"."opening_date",
        "cc"."closing_date",
        case
            when (
                "ii"."integration_month"
                =
                (date_trunc('month', %(initial_date)s) - interval '0 month')::date
            )
            then "iv"."net_amount"
            else 0
        end as "M_00",
        case
            when (
                "ii"."integration_month"
                =
                (date_trunc('month', %(initial_date)s) - interval '1 month')::date
            )
            then "iv"."net_amount"
            else 0
        end as "M_01",
        case
            when (
                "ii"."integration_month"
                =
                (date_trunc('month', %(initial_date)s) - interval '2 month')::date
            )
            then "iv"."net_amount"
            else 0
        end as "M_02",
        case
            when (
                "ii"."integration_month"
                =
                (date_trunc('month', %(initial_date)s) - interval '3 month')::date
            )
            then "iv"."net_amount"
            else 0
        end as "M_03",
        "cc"."type_x3"

    from "invoices_invoice" "ii"
    join "invoices_invoicedetail" "iv"
    on "ii"."uuid_identification" = "iv"."uuid_invoice"
    join "invoices_invoicecommondetails" "ic"
    on "iv"."import_uuid_identification" = "ic"."import_uuid_identification"
    join "maisons" "cc"
    on "ic"."cct" = "cc"."cct"
    where (
        "ii"."integration_month"
        >
        (
            date_trunc('month', %(initial_date)s) - interval '4 month' + interval '1 month - 1 day'
        )::date
    )
    and "iv"."net_amount" <> 0
    and "ii"."final"
),
"alls" as (
    select
        "signboard", "country_name", "cct", "cct_name", "opening_date", "closing_date",
        "M_00", "M_01", "M_02", "M_03",
        ("M_00" - "M_01")::numeric as "variation",
        "type_x3"
    from "edi_details"
    union all
    select
        "signboard", "country_name", "cct", "cct_name", "opening_date", "closing_date",
        "M_00", "M_01", "M_02", "M_03",
        ("M_00" - "M_01")::numeric as "variation",
        "type_x3"
    from "invoices_details"
)
select
    "signboard",
    "country_name",
    "cct_name",
    "ct"."name" as "type_vente",
    "opening_date",
    "closing_date",
    sum("M_03") as "M_03",
    sum("M_02") as "M_02",
    sum("M_01") as "M_01",
    sum("M_00") as "M_00",
    sum("M_00" - "M_01")::numeric as "variation",
    '' as "comment",
    "cct"
from "alls" "al"
left join "centers_clients_typevente" "ct"
  on "al"."type_x3" = "ct"."num"
group by "signboard",
         "country_name",
         "cct",
         "cct_name",
         "opening_date",
         "closing_date",
    	 "ct"."name"
order by "signboard",
         "country_name",
         "cct_name"
