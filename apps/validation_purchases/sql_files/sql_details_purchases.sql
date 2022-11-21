select
    supplier,
    invoice_amount_without_tax,
    invoice_amount_tax,
    invoice_amount_with_tax,
    date_month,
    third_party_num,
    pc."name" as big_category,
    ee."id" as pk,
    code_fournisseur,
    code_maison,
    maison,
    invoice_number,
    invoice_date,
    invoice_type,
    devise,
    reference_article,
    libelle,
    qty,
    net_unit_price,
    net_amount,
    vat_rate,
    axe_bu,
    axe_cct,
    axe_prj,
    axe_pro,
    axe_pys,
    axe_rfa,
    '{"pk": "' || ee."id" || '"}' as str_json
from edi_ediimport ee
left join parameters_category pc
on ee.uuid_big_category = pc.uuid_identification
where third_party_num = %(third_party_num)s
  and invoice_number = %(invoice_number)s
  and ee."delete" = False
order by ee."id"