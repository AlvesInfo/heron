with "edi_details" as (
    select
        "ee"."third_party_num",
        "bs"."name",
        "ee"."net_amount" as "M_00",
        0 as "M_01",
        0 as "M_02",
        0 as "M_03"
    from "edi_ediimport" "ee"
    join "book_society" "bs"
      on "ee"."third_party_num" = "bs"."third_party_num"
    where "ee"."purchase_invoice"
    and "ee"."net_amount" <> 0
),
"invoices_details" as (
    select
        "ii"."third_party_num",
        "bs"."name",
        0 as "M_00",
        case
            when (
                "ii"."integration_month"
                =
                (date_trunc('month', now()) - interval '2 month')::date
            )
            then "iv"."net_amount"
            else 0
        end as "M_01",
        case
            when (
                "ii"."integration_month"
                =
                (date_trunc('month', now()) - interval '3 month')::date
            )
            then "iv"."net_amount"
            else 0
        end as "M_02",
        case
            when (
                "ii"."integration_month"
                =
                (date_trunc('month', now()) - interval '4 month')::date
            )
            then "iv"."net_amount"
            else 0
        end as "M_03"

    from "invoices_invoice" "ii"
    join "invoices_invoicedetail" "iv"
    on "ii"."uuid_identification" = "iv"."uuid_invoice"
    join "book_society" "bs"
      on "ii"."third_party_num" = "bs"."third_party_num"
    where (
        "ii"."integration_month"
        >
        (
            date_trunc('month', now()) - interval '5 month' + interval '1 month - 1 day'
        )::date
    )
    and "iv"."net_amount" <> 0
    and "ii"."final"
),
"alls" as (
    select
        "third_party_num", "name",
        "M_00", "M_01", "M_02", "M_03",
        ("M_00" - "M_01")::numeric as "variation"
    from "edi_details"
    union all
    select
        "third_party_num", "name",
        "M_00", "M_01", "M_02", "M_03",
        ("M_00" - "M_01")::numeric as "variation"
    from "invoices_details"
)
select
    "third_party_num",
    "name" as "tiers",
    sum("M_03") as "M_03",
    sum("M_02") as "M_02",
    sum("M_01") as "M_01",
    sum("M_00") as "M_00",
    sum("M_00" - "M_01")::numeric as "variation",
    '' as "comment"
from "alls"
group by "third_party_num",
         "name"
order by "third_party_num"