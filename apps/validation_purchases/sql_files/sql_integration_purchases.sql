select
    big_category,
    supplier,
    sum(invoice_amount_without_tax) as invoice_amount_without_tax,
    sum(invoice_amount_with_tax) as invoice_amount_with_tax,
    sum(qty_invoices) as qty_invoices,
    date_month,
    '' as sep,
    '' as fournisseur,
    '' as amount_invoice_ttc,
    '' as amount_invoice_ht,
    '' as sep_delta,
    '' as delta_ttc,
    '' as delta_ht,
    '' as comment,
    third_party_num
from (
    select
        pc."name" as big_category,
        supplier,
        invoice_number,
        invoice_amount_without_tax,
        invoice_amount_with_tax,
        date_trunc('month', invoice_date)::date as date_month,
        1 as qty_invoices,
        third_party_num
    from edi_ediimport ee
    left join parameters_category pc
    on ee.uuid_big_category = pc.uuid_identification
    group by supplier,
             pc."name",
             invoice_number,
             invoice_amount_without_tax,
             invoice_amount_with_tax,
             date_trunc('month', invoice_date)::date,
             uuid_big_category,
             third_party_num
    ) edi
group by big_category,
         supplier,
         date_month,
         third_party_num
order by big_category,
         supplier,
         date_month
