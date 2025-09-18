with "maisons" as (
    select
        "cct",
        "intitule",
        "uuid_identification"
    from "centers_clients_maison" "cm"
    join "centers_purchasing_signboard" "sb"
    on "cm"."sign_board" = "sb"."code"
    left join "countries_country" "co"
    on "cm"."pays" = "co"."country"
    where "cct" = %(client)s
),
"edi_details" as (
    select
        "cc"."intitule" as "cct_name",
        "cc"."cct",
        "ee"."third_party_num",
        "ee"."invoice_number",
        "ee"."invoice_date",
        "ee"."invoice_month",
        "ee"."amount_with_vat",
        "ee"."net_amount"
    from "edi_ediimport" "ee"
    join "maisons" "cc"
    on "ee"."cct_uuid_identification" = "cc"."uuid_identification"
    where "ee"."purchase_invoice"
    and "ee"."net_amount" <> 0
    and "ee"."third_party_num" = %(third_party_num)s
)
select distinct
    "cct",
    "cct_name",
    "aa"."third_party_num" || ' - ' || "bs"."name" as "tiers",
    "invoice_number",
    "invoice_date",
    "invoice_month",
    sum("amount_with_vat") as "amount_with_vat",
    sum("net_amount") as "net_amount",
    '' as "comment"
from "edi_details" "aa"
join "book_society" "bs"
on "aa"."third_party_num" = "bs"."third_party_num"
group by "cct",
    	 "cct_name",
    	 "aa"."third_party_num",
    	 "bs"."name",
	     "invoice_number",
	     "invoice_date",
	     "invoice_month"
order by "invoice_date", "invoice_number"