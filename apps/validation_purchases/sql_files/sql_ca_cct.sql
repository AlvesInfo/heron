with "maisons" as (
    select
        "cct",
        "intitule",
        "uuid_identification",
        "sb"."name" as "signboard",
        "co"."country_name"
    from "centers_clients_maison" "cm"
    join "centers_purchasing_signboard" "sb"
    on "cm"."sign_board" = "sb"."code"
    left join "countries_country" "co"
    on "cm"."pays" = "co"."country"
),
"ventes_heron" as (
	select
		"cct",
	    case
            when (
                "invoice_month"
                =
                (date_trunc('month', now()) - interval '1 month')::date
            )
            then "invoice_amount_without_tax"
            else 0
        end as "M",
        0 as "MC",
	    case
            when (
                "invoice_month"
                =
                (date_trunc('month', now()) - interval '2 month')::date
            )
            then "invoice_amount_without_tax"
            else 0
        end as "M0",
        0 as "M0C",
	    case
            when (
                (
                	"invoice_month"
                	>=
                	(date_trunc('month', now()) - interval '3 month')::date
                )
            )
            then "invoice_amount_without_tax"
            else 0
        end as "TRI",
        0 as "TRIC",
	    case
            when (
                (
                	"invoice_month"
                	>=
                	(date_trunc('month', now()) - interval '12 month')::date
                )
            )
            then "invoice_amount_without_tax"
            else 0
        end as "AN",
        0 as "ANC"
	from "invoices_saleinvoice"
),
"ca_cosium" as (
	select
		"cct",
        0 as "M",
	  	case
			when (
		    	(date_trunc('month', "date_ca"))::date
			    =
			    (date_trunc('month', now()) - interval '1 month')::date
			)
			then "ca_ht_eur"
			else 0
		end as "MC",
		0 as "M0",
		case
			when (
		        (date_trunc('month', "date_ca"))::date
		        =
		        (date_trunc('month', now()) - interval '2 month')::date
		    )
		    then "ca_ht_eur"
		else 0
		end as "M0C",
		0 as "TRI",
		case
			when (
		            (
			          (date_trunc('month', "date_ca"))::date
			          >=
			          (date_trunc('month', now()) - interval '3 month')::date
			        )
		    )
		    then "ca_ht_eur"
			else 0
		end as "TRIC",
		0 as "AN",
		case
			when (
		            (
		              (date_trunc('month', "date_ca"))::date
			          >=
			          (date_trunc('month', now()) - interval '12 month')::date
			        )
		    )
		    then "ca_ht_eur"
			else 0
		end as "ANC"
	from "compta_caclients" "cc"
	join "centers_clients_maison" "cm"
	  on "cc"."cct_uuid_identification" = "cm"."uuid_identification"
),
"alls" as (
	select
		"cct", "M", "MC", "M0", "M0C", "TRI", "TRIC", "AN", "ANC"
	from "ventes_heron"
	union all

	select
		"cct", "M", "MC", "M0", "M0C", "TRI", "TRIC", "AN", "ANC"
	from "ca_cosium"
),
"sum_alls" as (
	select
		"cct",
		sum("MC") as "MC",
		sum("M") as "M",
		case
			when sum("MC") = 0
			then 0
			else round(sum("M")/sum("MC"), 2)::numeric
		end as "PM",
		sum("M0C") as "M0C",
		sum("M0") as "M0",
		case
			when sum("M0C") = 0
			then 0
			else round(sum("M0")/sum("M0C"), 2)::numeric
		end as "POM",
		sum("TRIC") as "TRIC",
		sum("TRI") as "TRI",
		case
			when sum("TRIC") = 0
			then 0
			else round(sum("TRI")/sum("TRIC"), 2)::numeric
		end as "PTM",
		sum("ANC") as "ANC",
		sum("AN") as "AN",
		case
			when sum("ANC") = 0
			then 0
			else round(sum("AN")/sum("ANC"), 2)::numeric
		end as "PAM"
	from "alls"
	group by "cct"
)
select
    "mm"."signboard",
    "mm"."country_name",
	"sa"."cct",
    "mm"."intitule",
    "MC",
    "M",
    "PM",
    "M0C",
    "M0",
    "POM",
    "TRIC",
    "TRI",
    "PTM",
    "ANC",
    "AN",
    "PAM",
    '' as "comment"
from "sum_alls" "sa"
join "maisons" "mm"
  on "sa"."cct" = "mm"."cct"
order by "mm"."signboard",
		 "mm"."country_name",
		 "sa"."cct"
