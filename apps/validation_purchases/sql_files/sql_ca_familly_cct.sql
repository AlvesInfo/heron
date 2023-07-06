with "maisons" as (
    select
        "cct",
        "intitule_court" as "intitule",
        "uuid_identification",
        "sb"."name" as "signboard",
        "co"."country_name"
    from "centers_clients_maison" "cm"
    join "centers_purchasing_signboard" "sb"
    on "cm"."sign_board" = "sb"."code"
    left join "countries_country" "co"
    on "cm"."pays" = "co"."country"
    where "cct" = %(client)s
),
"familles" as (
	select
		"uuid_identification",
		"section",
		"name" as "axe_pro"
	from "accountancy_sectionsage"
	where "axe" = 'PRO'
),
"ventes_heron" as (
	select
		"cct",
		"fa"."axe_pro",
	    case
            when (
                "invoice_month"
                =
                (date_trunc('month', now()) - interval '1 month')::date
            )
            then "net_amount"
            else 0
        end as "M",
        0 as "MC",
	    case
            when (
                "invoice_month"
                =
                (date_trunc('month', now()) - interval '2 month')::date
            )
            then "net_amount"
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
            then "net_amount"
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
            then "net_amount"
            else 0
        end as "AN",
        0 as "ANC"
	from "invoices_saleinvoice" "si"
	join "invoices_saleinvoicedetail" "sd"
	  on "si"."uuid_identification" = "sd"."uuid_invoice"
	left join "familles" "fa"
	  on "sd"."axe_pro" = "fa"."section"
),
"ca_cosium" as (
	select
		"cct",
		"fa"."axe_pro",
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
	left join "familles" "fa"
	  on "cc"."axe_pro" = "fa"."uuid_identification"
),
"alls" as (
	select
		"cct", "axe_pro", "M", "MC", "M0", "M0C", "TRI", "TRIC", "AN", "ANC"
	from "ventes_heron"
	union all

	select
		"cct", "axe_pro", "M", "MC", "M0", "M0C", "TRI", "TRIC", "AN", "ANC"
	from "ca_cosium"
),
"sum_alls" as (
	select
		"cct",
		"axe_pro",
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
	group by "cct",
			 "axe_pro"
)
select
    "mm"."signboard",
    "mm"."country_name",
	"sa"."cct",
    "mm"."intitule",
	"axe_pro",
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
    "PAM"
from "sum_alls" "sa"
join "maisons" "mm"
  on "sa"."cct" = "mm"."cct"
order by "mm"."signboard",
		 "mm"."country_name",
		 "sa"."cct",
		 "axe_pro"
