select
    pc."name" as big_category,
    supplier,
    invoice_number,
    invoice_amount_without_tax,
    invoice_amount_with_tax,
    date_trunc('month', invoice_date)::date as date_month,
    1 as qty_invoices,
    third_party_num,
    invoice_amount_tax,
    invoice_date
from edi_ediimport ee
left join parameters_category pc
on ee.uuid_big_category = pc.uuid_identification
where third_party_num = %(third_party_num)s
  and pc."name" = %(big_category)s
  and date_trunc('month', invoice_date)::date = %(month)s
group by supplier,
         pc."name",
         invoice_number,
         invoice_date,
         invoice_amount_without_tax,
         invoice_amount_tax,
         invoice_amount_with_tax,
         date_trunc('month', invoice_date)::date,
         uuid_big_category,
         third_party_num