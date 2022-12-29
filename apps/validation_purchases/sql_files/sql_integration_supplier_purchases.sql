select
    pc."name" as big_category,
    third_party_num,
    supplier,
    case when max(ac.cct) isnull then '' else max(cct) end as axe_cct,
    case when max(code_maison) isnull then '' else replace(max(code_maison), '|', '') end as code_maison,
    replace(left(max(maison), 100), '|', '') as maison,
    invoice_number,
    invoice_date,
    sum(net_amount) as net_amount,
    (invoice_amount_without_tax-sum(net_amount)) as delta,
    invoice_amount_without_tax,
    invoice_amount_tax,
    invoice_amount_with_tax,
    invoice_month,
    case when sum(net_amount) != invoice_amount_without_tax then true else false end as error,
    max(ee."id") as pk,
    (
        '{"third_party_num": "'
        || third_party_num ||
        '", "invoice_number": "'
        || invoice_number ||
        '", "invoice_month": "'
        || invoice_month ||
        '", "delete": "'
        || 'false' ||
        '"}'
    ) as str_json,
    (
        pc."name" || '||' ||
        third_party_num || '||' ||
        supplier || '||' ||
        invoice_month || '||' ||
        invoice_number
    ) as enc_param,
    ee.uuid_identification,
    ee.invoice_year
from edi_ediimport ee
left join parameters_category pc
on ee.uuid_big_category = pc.uuid_identification
left join accountancy_cctsage ac
on ee.cct_uuid_identification = ac.uuid_identification
where third_party_num = %(third_party_num)s
  and supplier = %(supplier)s
  and pc."name" = %(big_category)s
  and date_trunc('month', invoice_date)::date = %(invoice_month)s
  and ee."delete" = False
group by supplier,
         pc."name",
         invoice_number,
         invoice_date,
         invoice_amount_without_tax,
         invoice_amount_tax,
         invoice_amount_with_tax,
         invoice_month,
         uuid_big_category,
         third_party_num,
         ee.uuid_identification,
         ee.invoice_year
order by invoice_number