with families as (
	select
		edi."third_party_num",
		edi."supplier",
		case
			when edi."axe_pro_uuid" isnull then '' else ac."name"
		end as "axe_pro",
		case
			when (date_trunc('month', now())- interval '1 month')::date = edi."invoice_month"
			then edi."net_amount"
			else 0
		end as "m_00",
		case
			when (date_trunc('month', now())- interval '2 month')::date = edi."invoice_month"
			then edi."net_amount"
			else 0
		end as "m_01",
		case
			when (date_trunc('month', now())- interval '3 month')::date = edi."invoice_month"
			then edi."net_amount"
			else 0
		end as "m_02"
	from "edi_ediimport" edi
	left join "accountancy_sectionsage" ac
	on (edi."axe_pro_uuid" = ac."uuid_identification")
	where not (edi."delete" AND edi."delete" IS NOT NULL)
	and edi.invoice_month >= (date_trunc('month', now())- interval '3 month')::date

	union all

    select
		sii."third_party_num",
		sii."supplier",
		case
			when siid."axe_pro_uuid" isnull then '' else ac."name"
		end as "axe_pro",
		case
			when (date_trunc('month', now())- interval '1 month')::date = sii."invoice_month"
			then siid."net_amount"
			else 0
		end as "m_00",
		case
			when (date_trunc('month', now())- interval '2 month')::date = sii."invoice_month"
			then siid."net_amount"
			else 0
		end as "m_01",
		case
			when (date_trunc('month', now())- interval '3 month')::date = sii."invoice_month"
			then siid."net_amount"
			else 0
		end as "m_02"
    from suppliers_invoices_invoice sii
    join suppliers_invoices_invoicedetail siid
    on sii.uuid_identification  = siid.uuid_invoice
    left join "accountancy_sectionsage" ac
	ON (siid."axe_pro_uuid" = ac."uuid_identification")
	and sii.invoice_month >= (date_trunc('month', now())- interval '3 month')::date
)
select
	fm."third_party_num",
	fm."supplier",
	fm."axe_pro",
	sum(fm."m_02") as "m_02",
	sum(fm."m_01") as "m_01",
	sum(fm."m_00") as "m_00",
	(sum(fm."m_00")-sum(fm."m_01"))::numeric as variation,
	'' as commentaire
from families fm
GROUP BY fm."third_party_num", fm."supplier", fm."axe_pro"
ORDER BY fm."third_party_num", fm."supplier", fm."axe_pro"