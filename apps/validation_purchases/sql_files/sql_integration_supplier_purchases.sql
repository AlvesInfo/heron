select
    pc."name" as big_category,
    supplier,
    invoice_number,
    case when sum(net_amount) != invoice_amount_without_tax then true else false end as error,
    sum(net_amount) as net_amount,
    (invoice_amount_without_tax-sum(net_amount)) as delta,
    invoice_amount_without_tax,
    invoice_amount_with_tax,
    date_month,
    1 as qty_invoices,
    third_party_num,
    invoice_amount_tax,
    invoice_date,
    max(ee."id") as pk
from edi_ediimport ee
left join parameters_category pc
on ee.uuid_big_category = pc.uuid_identification
where third_party_num = %(third_party_num)s
  and pc."name" = %(big_category)s
  and date_trunc('month', invoice_date)::date = %(date_month)s
  and ee."delete" = False
group by supplier,
         pc."name",
         invoice_number,
         invoice_date,
         invoice_amount_without_tax,
         invoice_amount_tax,
         invoice_amount_with_tax,
         date_month,
         uuid_big_category,
         third_party_num