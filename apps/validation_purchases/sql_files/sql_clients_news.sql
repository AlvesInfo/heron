        with "maisons" as (
            select
                "cct",
                "intitule",
                "opening_date",
                "uuid_identification"
            from "centers_clients_maison"
            where "opening_date" > (date_trunc('month', now()) - interval '12 month 1 day')::date
        ),
        "edi_details" as (
            select
                "cc"."cct" || ' - ' || "cc"."intitule" as "cct_name",
                "cc"."opening_date",
                "bs"."third_party_num" || ' - ' || "bs"."short_name" as "tiers",
                "ee"."net_amount" as "M_00",
                0 as "M_01",
                0 as "M_02",
                0 as "M_03",
                0 as "M_04",
                0 as "M_05"
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
                "cc"."opening_date",
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
                end as "M_05"

            from "book_society" "bs"
            join "invoices_invoice" "ii"
            on "bs"."third_party_num"  = "ii"."third_party_num"
            join "invoices_invoicedetail" "iv"
            on "ii"."uuid_identification" = "iv"."uuid_invoice"
            join "invoices_invoicecommondetails" "ic"
            on "iv"."import_uuid_identification" = "ic"."import_uuid_identification"
            join "maisons" "cc"
            on "ic"."cct" = "cc"."cct"
            where  (
                "ii"."integration_month"
                >=
                (
                    (date_trunc('month', now()) - interval '6 month')::date
                )::date
            )
            and "iv"."net_amount" <> 0
            and "ii"."final"
        ),
        "alls" as (
            select
                "cct_name", "tiers", "opening_date",
                "M_00", "M_01", "M_02", "M_03", "M_04", "M_05",
                ("M_00" + "M_01" + "M_02" + "M_03" + "M_04" + "M_05")::numeric as "M6_MONTH"
            from "edi_details"
            union all
            select
                "cct_name", "tiers", "opening_date",
                "M_00", "M_01", "M_02", "M_03", "M_04", "M_05",
                ("M_00" + "M_01" + "M_02" + "M_03" + "M_04" + "M_05")::numeric as "M6_MONTH"
            from "invoices_details"
        )
        select
            "cct_name",
            "opening_date",
            "cct_name",
            "tiers",
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
                 "opening_date",
                 "tiers"
        order by "opening_date" desc,
                 "cct_name",
                 "tiers"