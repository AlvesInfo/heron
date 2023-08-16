with rfa as (
    select
        "supplier",
        "invoice_number",
		"reference_article",
        "invoice_month",
        "third_party_num",
        "ec"."uuid_identification",
        "ec"."uuid_identification" as "uuid_control",
        case when "ee"."origin" isnull then 'question circle' else "pic"."icon" end as "icon",
        case when "ee"."origin" isnull then 0 else "ee"."origin" end as "origin",
        case when "ee"."origin" isnull then 'INCONNUE' else "pic"."origin_name" end as "origin_name",
        "aa"."section",
        case
	        when "purchase_invoice" = true and "sale_invoice" = true then 'AC/VE'
	        when "purchase_invoice" = true then 'AC'
	        when "sale_invoice" = true then 'VE'
    	end as "achat_vente"
    from "edi_ediimport" "ee"
    left join "edi_ediimportcontrol" "ec"
    on "ee"."uuid_control" = "ec"."uuid_identification"
    left join "parameters_iconoriginchoice" "pic"
    on "ee"."origin" = "pic"."origin"
	join (
		select
			uuid_identification as "axe_rfa",
			"section"
		from "accountancy_sectionsage"
		where "axe" = 'RFA'
		and "section" <> 'NAF'
	) "aa"
	on "ee"."axe_rfa" = "aa"."axe_rfa"
    where ("ee"."delete" = false or "ee"."delete" isnull)
      and "ee"."valid" = true
)
select
	"icon",
	"third_party_num",
	"achat_vente",
	"supplier",
	"invoice_month",
	string_agg(distinct "invoice_number", ', ') as "invoice_number",
	"reference_article",
	"section",

	"uuid_identification",
	"uuid_control",
	"origin",
	"origin_name"
from "rfa"
group by
	"icon",
	"third_party_num",
	"achat_vente",
	"supplier",
	"invoice_month",
	"reference_article",
	"section",

	"uuid_identification",
	"uuid_control",
	"origin",
	"origin_name"
order by
	"supplier",
	"invoice_month",
	"section"