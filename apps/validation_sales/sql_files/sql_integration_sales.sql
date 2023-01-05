select
    big_category,
    third_party_num,
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
    case when sum(net_amount) != sum(invoice_amount_without_tax) then true else false end as error,
    uuid_identification,
    big_category || '||' || third_party_num || '||' || supplier || '||' || invoice_month as enc_param,
    pk,
    (
        '{"third_party_num": "'
        || third_party_num ||
        '", "supplier": "'
        || supplier ||
        '", "big_category": "'
        || big_category ||
        '", "invoice_month": "'
        || invoice_month ||
        '", "delete": "'
        || 'false' ||
        '"}'
    ) as str_json,
    case when min(cct_error) = 0 then 1 else 0 end as cct_error,
    uuid_category
from (
    select
        pc."name" as big_category,
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
        ec."comment",
        ec.uuid_identification,
        ec."id" as pk,
        case when ee.cct_uuid_identification is null then 0 else 1 end as cct_error,
        pc.uuid_identification as uuid_category
    from edi_ediimport ee
    left join parameters_category pc
    on ee.uuid_big_category = pc.uuid_identification
    left join edi_ediimportcontrol ec
    on ee.uuid_control = ec.uuid_identification
    where (ee."delete" = false or ee."delete" isnull)
      and "sale_invoice" = true
    group by supplier,
             pc."name",
             invoice_number,
             invoice_amount_without_tax,
             invoice_amount_with_tax,
             invoice_month,
             uuid_big_category,
             third_party_num,
	         ec.statement_without_tax,
	         ec.statement_with_tax,
        	 ec."comment",
             ec.uuid_identification,
             ec."id",
        	 ee.cct_uuid_identification,
             pc.uuid_identification
    ) edi
group by big_category,
         supplier,
         invoice_month,
         third_party_num,
         statement_without_tax,
         statement_with_tax,
         "comment",
         uuid_identification,
         pk,
         uuid_category
order by big_category,
         third_party_num,
         supplier,
         invoice_month