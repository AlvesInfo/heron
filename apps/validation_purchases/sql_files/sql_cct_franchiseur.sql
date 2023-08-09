        with "maisons" as (
            select
                "cct",
                "intitule",
                "uuid_identification"
            from "centers_clients_maison"
            where "type_x3" = 2
        ),
        "edi_details" as (
            select
                "cc"."cct" || ' - ' || "cc"."intitule" as "cct_name",
                "bs"."third_party_num" || ' - ' || "bs"."short_name" as "tiers",
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
            from "book_society" "bs"
            join "edi_ediimport" "ee"
            on "bs"."third_party_num" = "ee"."third_party_num"
            join "maisons" "cc"
            on "ee"."cct_uuid_identification" = "cc"."uuid_identification"
            where "ee"."purchase_invoice"
            and "ee"."net_amount" <> 0
        ),
        "invoices_details" as (
            select
                "cc"."cct" || ' - ' || "cc"."intitule" as "cct_name",
                "bs"."third_party_num" || ' - ' || "bs"."short_name" as "tiers",
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
                end as "M_03",
                case
                    when (
                        "ii"."integration_month"
                        =
                        (date_trunc('month', now()) - interval '5 month')::date
                    )
                    then "iv"."net_amount"
                    else 0
                end as "M_04",
                case
                    when (
                        "ii"."integration_month"
                        =
                        (date_trunc('month', now()) - interval '6 month')::date
                    )
                    then "iv"."net_amount"
                    else 0
                end as "M_05",
                case
                    when (
                        "ii"."integration_month"
                        =
                        (date_trunc('month', now()) - interval '7 month')::date
                    )
                    then "iv"."net_amount"
                    else 0
                end as "M_06",
                case
                    when (
                        "ii"."integration_month"
                        =
                        (date_trunc('month', now()) - interval '8 month')::date
                    )
                    then "iv"."net_amount"
                    else 0
                end as "M_07",
                case
                    when (
                        "ii"."integration_month"
                        =
                        (date_trunc('month', now()) - interval '9 month')::date
                    )
                    then "iv"."net_amount"
                    else 0
                end as "M_08",
                case
                    when (
                        "ii"."integration_month"
                        =
                        (date_trunc('month', now()) - interval '10 month')::date
                    )
                    then "iv"."net_amount"
                    else 0
                end as "M_09",
                case
                    when (
                        "ii"."integration_month"
                        =
                        (date_trunc('month', now()) - interval '11 month')::date
                    )
                    then "iv"."net_amount"
                    else 0
                end as "M_10",
                case
                    when (
                        "ii"."integration_month"
                        =
                        (date_trunc('month', now()) - interval '12 month')::date
                    )
                    then "iv"."net_amount"
                    else 0
                end as "M_11"

            from "book_society" "bs"
            join "invoices_invoice" "ii"
            on "bs"."third_party_num"  = "ii"."third_party_num"
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
                    date_trunc('month', now()) - interval '13 month' + interval '1 month - 1 day'
                )::date
            )
            and "iv"."net_amount" <> 0
            and "ii"."final"
        ),
        "alls" as (
            select
                "cct_name", "tiers",
                "M_00", "M_01", "M_02", "M_03", "M_04", "M_05",
                "M_06", "M_07", "M_08", "M_09", "M_10", "M_11",
                ("M_00" + "M_01" + "M_02" + "M_03" + "M_04" + "M_05")::numeric as "M6_MONTH"
            from "edi_details"
            union all
            select
                "cct_name", "tiers",
                "M_00", "M_01", "M_02", "M_03", "M_04", "M_05",
                "M_06", "M_07", "M_08", "M_09", "M_10", "M_11",
                ("M_00" + "M_01" + "M_02" + "M_03" + "M_04" + "M_05")::numeric as "M6_MONTH"
            from "invoices_details"
        )
        select
            "cct_name",
            "tiers",
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
        group by "cct_name",
                 "tiers"
        order by "cct_name",
                 "tiers"