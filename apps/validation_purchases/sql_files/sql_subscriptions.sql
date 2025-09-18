        with "maisons" as (
            select
                "cct",
                "intitule",
                "closing_date",
                "uuid_identification",
                "sb"."name" as "signboard"
            from "centers_clients_maison" "cm"
            join "centers_purchasing_signboard" "sb"
            on "cm"."sign_board" = "sb"."code"
        ),
        "edi_details" as (
            select
                (
                    "ee"."third_party_num"
                    || ' - ' ||
                    "ee"."flow_name"
                    || ' - ' ||
                    "ee"."reference_article"
                ) as "tiers",
                "cc"."cct" || ' - ' || "cc"."intitule" as "cct_name",
                "cc"."signboard",
                "cc"."closing_date",
                "ee"."net_amount" as "M_00",
                0 as "M_01",
                0 as "M_02",
                0 as "M_03",
                0 as "M_04",
                0 as "M_05",
                0 as "M_06",
                0 as "M_07",
                0 as "M_08",
                0 as "M_09",
                0 as "M_10",
                0 as "M_11"
            from "maisons" "cc"
            join "edi_ediimport" "ee"
            on "ee"."cct_uuid_identification" = "cc"."uuid_identification"
            where "ee"."sale_invoice"
            and "ee"."net_amount" <> 0
            and "ee"."flow_name" in  (
                select
                    "function"
                from "centers_clients_maisonsubcription" "cs"
                group by "function"
            )
        ),
        "invoices_details" as (
            select
                (
                    "ic"."third_party_num"
                    || ' - ' ||
                    "ic"."flow_name"
                    || ' - ' ||
                    "ic"."reference_article"
                )as "tiers",
                "cc"."cct" || ' - ' || "cc"."intitule" as "cct_name",
                "cc"."signboard",
                "cc"."closing_date",
                0 as "M_00",
                case
                    when (
                        "si"."invoice_month"
                        =
                        (date_trunc('month', now()) - interval '2 month')::date
                    )
                    then "iv"."net_amount"
                    else 0
                end as "M_01",
                case
                    when (
                        "si"."invoice_month"
                        =
                        (date_trunc('month', now()) - interval '3 month')::date
                    )
                    then "iv"."net_amount"
                    else 0
                end as "M_02",
                case
                    when (
                        "si"."invoice_month"
                        =
                        (date_trunc('month', now()) - interval '4 month')::date
                    )
                    then "iv"."net_amount"
                    else 0
                end as "M_03",
                case
                    when (
                        "si"."invoice_month"
                        =
                        (date_trunc('month', now()) - interval '5 month')::date
                    )
                    then "iv"."net_amount"
                    else 0
                end as "M_04",
                case
                    when (
                        "si"."invoice_month"
                        =
                        (date_trunc('month', now()) - interval '6 month')::date
                    )
                    then "iv"."net_amount"
                    else 0
                end as "M_05",
                case
                    when (
                        "si"."invoice_month"
                        =
                        (date_trunc('month', now()) - interval '7 month')::date
                    )
                    then "iv"."net_amount"
                    else 0
                end as "M_06",
                case
                    when (
                        "si"."invoice_month"
                        =
                        (date_trunc('month', now()) - interval '8 month')::date
                    )
                    then "iv"."net_amount"
                    else 0
                end as "M_07",
                case
                    when (
                        "si"."invoice_month"
                        =
                        (date_trunc('month', now()) - interval '9 month')::date
                    )
                    then "iv"."net_amount"
                    else 0
                end as "M_08",
                case
                    when (
                        "si"."invoice_month"
                        =
                        (date_trunc('month', now()) - interval '10 month')::date
                    )
                    then "iv"."net_amount"
                    else 0
                end as "M_09",
                case
                    when (
                        "si"."invoice_month"
                        =
                        (date_trunc('month', now()) - interval '11 month')::date
                    )
                    then "iv"."net_amount"
                    else 0
                end as "M_10",
                case
                    when (
                        "si"."invoice_month"
                        =
                        (date_trunc('month', now()) - interval '12 month')::date
                    )
                    then "iv"."net_amount"
                    else 0
                end as "M_11"
            from "book_society" "bs"
            join "invoices_invoicecommondetails" "ic"
            on "bs"."third_party_num" = "ic"."third_party_num"
            join "invoices_saleinvoicedetail" "iv"
            on "iv"."import_uuid_identification" = "ic"."import_uuid_identification"
            join "invoices_saleinvoice" "si"
            on "iv"."uuid_invoice" = "si"."uuid_identification"
            join "maisons" "cc"
            on "si"."cct" = "cc"."cct"
            where (
                "si"."invoice_month"
                >
                (
                    date_trunc('month', now()) - interval '13 month' + interval '1 month - 1 day'
                )::date
            )
            and "ic"."flow_name" in  (
                select
                    "function"
                from "centers_clients_maisonsubcription" "cs"
                group by "function"
            )
            and "iv"."net_amount" <> 0
            and "si"."final"
        ),
        "alls" as (
            select
                "tiers", "cct_name", "signboard",
                coalesce("closing_date"::varchar, '') as "closing_date",
                "M_00", "M_01", "M_02", "M_03", "M_04", "M_05",
                "M_06", "M_07", "M_08", "M_09", "M_10", "M_11",
                ("M_00" + "M_01" + "M_02" + "M_03" + "M_04" + "M_05")::numeric as "M6_MONTH"
            from "edi_details"
            union all
            select
                "tiers", "cct_name", "signboard",
                coalesce("closing_date"::varchar, '') as "closing_date",
                "M_00", "M_01", "M_02", "M_03", "M_04", "M_05",
                "M_06", "M_07", "M_08", "M_09", "M_10", "M_11",
                ("M_00" + "M_01" + "M_02" + "M_03" + "M_04" + "M_05")::numeric as "M6_MONTH"
            from "invoices_details"
        ),
        "group_alls" as (
            select
                "tiers",
                "cct_name",
                "closing_date",
                sum("M_11") as "M_11",
                sum("M_10") as "M_10",
                sum("M_09") as "M_09",
                sum("M_08") as "M_08",
                sum("M_07") as "M_07",
                sum("M_06") as "M_06",
                sum("M_05") as "M_05",
                sum("M_04") as "M_04",
                sum("M_03") as "M_03",
                sum("M_02") as "M_02",
                sum("M_01") as "M_01",
                sum("M_00") as "M_00",
                SUM("M_00" + "M_01" + "M_02" + "M_03" + "M_04" + "M_05")::numeric as "M6_MONTH",
                '' as "comment"
            from "alls"
            group by "tiers",
                     "cct_name",
                     "closing_date"
        ),
        "maisons_alls" as (
            select
                "tiers",
                "cct" || ' - ' || "intitule" as "cct_name",
                "signboard",
                coalesce("closing_date"::varchar, '') as "closing_date"
            from "maisons" , (
                select
                    "tiers"
                from "group_alls"
                group by "tiers"
            ) "rr"
        )
        select
            "ma"."tiers", "ma"."tiers", "ma"."cct_name", "ma"."signboard", "ma"."closing_date",
            "M_11", "M_10", "M_09", "M_08", "M_07", "M_06", "M_05",
            "M_04", "M_03", "M_02", "M_01", "M_00", "M6_MONTH", "comment"
        from "maisons_alls" "ma"
        left join "group_alls" "ga"
         on "ma"."tiers" = "ga"."tiers"
        and "ma"."cct_name" = "ga"."cct_name"
        order by "ma"."tiers",
                 "ma"."cct_name"