select
    big_category,
    third_party_num,
    supplier,
    sum(invoice_amount_without_tax) as invoice_amount_without_tax,
    sum(invoice_amount_with_tax) as invoice_amount_with_tax,
    sum(qty_invoices) as qty_invoices,
    date_month,
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
    big_category || '||' || third_party_num || '||' || supplier || '||' || date_month as enc_param,
    pk,
    (
        '{"third_party_num": "'
        || third_party_num ||
        '", "supplier": "'
        || supplier ||
        '", "big_category": "'
        || big_category ||
        '", "date_month": "'
        || date_month ||
        '", "delete": "'
        || 'false' ||
        '"}'
    ) as str_json
from (
    select
        pc."name" as big_category,
        supplier,
        invoice_number,
        sum(net_amount) as net_amount,
        invoice_amount_without_tax,
        invoice_amount_with_tax,
        date_month,
        1 as qty_invoices,
        third_party_num,
        ec.statement_without_tax,
        ec.statement_with_tax,
        ec."comment",
        ec.uuid_identification,
        ec."id" as pk
    from edi_ediimport ee
    left join parameters_category pc
    on ee.uuid_big_category = pc.uuid_identification
    left join edi_ediimportcontrol ec
    on ee.uuid_control = ec.uuid_identification
    where ee."delete" = False
    group by supplier,
             pc."name",
             invoice_number,
             invoice_amount_without_tax,
             invoice_amount_with_tax,
             date_month,
             uuid_big_category,
             third_party_num,
	         ec.statement_without_tax,
	         ec.statement_with_tax,
        	 ec."comment",
             ec.uuid_identification,
             ec."id"
    ) edi
group by big_category,
         supplier,
         date_month,
         third_party_num,
         statement_without_tax,
         statement_with_tax,
         "comment",
         uuid_identification,
         pk
order by big_category,
         supplier,
         date_month