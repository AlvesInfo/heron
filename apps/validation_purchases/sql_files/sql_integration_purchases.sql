select
    third_party_num,
    case
        when "purchase_invoice" = true and "sale_invoice" = true then 'AC/VE'
        when "purchase_invoice" = true then 'AC'
        when "sale_invoice" = true then 'VE'
    end as achat_vente,
    supplier,
    sum(invoice_amount_without_tax) as invoice_amount_without_tax,
    sum(invoice_amount_with_tax) as invoice_amount_with_tax,
    sum(qty_invoices) as qty_invoices,
    invoice_month,
    '' as sep,
    coalesce(statement_without_tax, 0) as amount_invoice_ht,
    coalesce(statement_with_tax, 0) as amount_invoice_ttc,
    '' as sep_delta,
    sum(invoice_amount_without_tax) - coalesce(statement_without_tax, 0) as delta_ht,
    sum(invoice_amount_with_tax) - coalesce(statement_with_tax, 0) as delta_ttc,
    "comment",
    sum(net_amount) as net_amount,
    case
	    when sum(net_amount) != sum(invoice_amount_without_tax) then true
	    else false
	end as error,
    uuid_identification,
    third_party_num || '||' || supplier || '||' || invoice_month as enc_param,
    pk,
    (
        '{"third_party_num": "'
        || third_party_num ||
        '", "supplier": "'
        || supplier ||
        '", "invoice_month": "'
        || invoice_month ||
        '", "delete": "'
        || 'false' ||
        '"}'
    ) as str_json,
    case when min(cct_error) = 0 then 1 else 0 end as cct_error
from (
    select
        supplier,
        invoice_number,
        sum(net_amount) as net_amount,
        invoice_amount_without_tax,
        invoice_amount_with_tax,
        invoice_month,
        1 as qty_invoices,
        third_party_num,
        ec.statement_without_tax,
        ec.statement_with_tax,
        string_agg(distinct ec."comment", ', ') as "comment",
        ec.uuid_identification,
        ec."id" as pk,
        sum(cct_error) as cct_error,
        "purchase_invoice",
        "sale_invoice",
        case when "is_multi_store" then 0 else 1 end as "is_multi_store"
    from edi_ediimport ee
    left join edi_ediimportcontrol ec
    on ee.uuid_control = ec.uuid_identification
    left join (
    	select
			ei."id", case when ei.cct_uuid_identification is null then 1 else 0 end as cct_error
    	from edi_ediimport ei
    ) as cc
    on ee.id = cc.id
    where (ee."delete" = false or ee."delete" isnull)
    group by supplier,
             invoice_number,
             invoice_amount_without_tax,
             invoice_amount_with_tax,
             invoice_month,
             uuid_big_category,
             third_party_num,
	         ec.statement_without_tax,
	         ec.statement_with_tax,
             ec.uuid_identification,
             ec."id",
            "purchase_invoice",
            "sale_invoice",
            is_multi_store
) edi
group by supplier,
         invoice_month,
         third_party_num,
         statement_without_tax,
         statement_with_tax,
         "comment",
         uuid_identification,
         pk,
        "purchase_invoice",
        "sale_invoice"
order by third_party_num,
         supplier,
         invoice_month