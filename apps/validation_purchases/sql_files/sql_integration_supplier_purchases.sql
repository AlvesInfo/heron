select
    pc."name" as big_category,
    ee.third_party_num,
    supplier,
    case when max(ac.cct) isnull then '' else max(cct) end as axe_cct,
    case when max(ee.code_maison) isnull then '' else replace(max(ee.code_maison), '|', '') end as code_maison,
    replace(left(max(maison), 100), '|', '') as maison,
    case when ee."invoice_type" = '380' then 'FAF' else 'AVO' end as type_invoice,
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
        || ee.third_party_num ||
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
        ee.third_party_num || '||' ||
        supplier || '||' ||
        invoice_month || '||' ||
        invoice_number
    ) as enc_param,
    ee.uuid_identification,
    ee.invoice_year,
    case when ee."invoice_type" = '380' then 'darkblue' else 'brown' end as color_invoice,
    ee."is_multi_store"
from edi_ediimport ee
left join parameters_category pc
on ee.uuid_big_category = pc.uuid_identification
left join centers_clients_maison ac
on ee.cct_uuid_identification = ac.uuid_identification
where ee.third_party_num = %(third_party_num)s
  and supplier = %(supplier)s
  and pc."name" = %(big_category)s
  and date_trunc('month', invoice_date)::date = %(invoice_month)s
  and (ee."delete" = false or ee."delete" isnull)
group by supplier,
         pc."name",
         invoice_number,
         invoice_date,
         invoice_amount_without_tax,
         invoice_amount_tax,
         invoice_amount_with_tax,
         invoice_month,
         uuid_big_category,
         ee.third_party_num,
         ee.uuid_identification,
         ee.invoice_year,
         ee."invoice_type",
         ee."is_multi_store"
order by invoice_number