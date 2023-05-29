with families as (
	select
		"edi"."third_party_num",
		"bs"."short_name",
		case
			when "edi"."axe_pro" isnull then '' else "ac"."section"
		end as "axe_pro",
		case
			when (date_trunc('month', now())- interval '1 month')::date = "edi"."invoice_month"
			then "edi"."net_amount"
			else 0
		end as "m_00",
		case
			when (date_trunc('month', now())- interval '2 month')::date = "edi"."invoice_month"
			then "edi"."net_amount"
			else 0
		end as "m_01",
		case
			when (date_trunc('month', now())- interval '3 month')::date = "edi"."invoice_month"
			then "edi"."net_amount"
			else 0
		end as "m_02"
	from "edi_ediimport" "edi"
	left join "accountancy_sectionsage" "ac"
	on ("edi"."axe_pro" = "ac"."uuid_identification")
	left join "book_society" "bs"
	on "bs"."third_party_num" = "edi"."third_party_num"
	where not ("edi"."delete" AND "edi"."delete" IS NOT NULL)
	and "edi".invoice_month >= (date_trunc('month', now())- interval '3 month')::date
	and "edi"."valid" = true

	union all

    select
		"sii"."third_party_num",
		"bs"."short_name",
		case
			when siid."axe_pro" isnull then '' else siid."axe_pro"
		end as "axe_pro",
		case
			when (date_trunc('month', now())- interval '1 month')::date = "sii"."invoice_month"
			then "siid"."net_amount"
			else 0
		end as "m_00",
		case
			when (date_trunc('month', now())- interval '2 month')::date = "sii"."invoice_month"
			then "siid"."net_amount"
			else 0
		end as "m_01",
		case
			when (date_trunc('month', now())- interval '3 month')::date = "sii"."invoice_month"
			then "siid"."net_amount"
			else 0
		end as "m_02"
    from "invoices_invoice" "sii"
	left join "book_society" "bs"
	on "bs"."third_party_num" = "sii"."third_party_num"
    join "invoices_invoicedetail" "siid"
    on "sii"."uuid_identification"  = "siid"."uuid_invoice"
	and "sii"."invoice_month" >= (date_trunc('month', now())- interval '3 month')::date
)
select
	"fm"."third_party_num",
	"fm"."short_name" as "supplier",
	"fm"."axe_pro",
	sum("fm"."m_02") as "m_02",
	sum("fm"."m_01") as "m_01",
	sum("fm"."m_00") as "m_00",
	(sum("fm"."m_00")-sum("fm"."m_01"))::numeric as "variation",
	'' as commentaire
from "families" "fm"
GROUP BY "fm"."third_party_num", "fm"."short_name", "fm"."axe_pro"
ORDER BY "fm"."third_party_num", "fm"."short_name", "fm"."axe_pro"