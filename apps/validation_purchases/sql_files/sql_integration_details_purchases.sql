select
    supplier,
    invoice_amount_without_tax,
    invoice_amount_tax,
    invoice_amount_with_tax,
    invoice_month,
    ee.third_party_num,
    pc."name" as big_category,
    ee."id" as pk,
    ac.cct,
    code_fournisseur,
    ee.code_maison,
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
    abu.section as axe_bu,
    acct.section as axe_cct,
    aprj.section as axe_prj,
    apro.section as axe_pro,
    apys.section as axe_pys,
    arfa.section as axe_rfa,
    '{"pk": "' || ee."id" || '"}' as str_json,
    ee.third_party_num || '||' || supplier || '||' || invoice_month as enc_param
from edi_ediimport ee
left join centers_clients_maison ac
on ee.cct_uuid_identification = ac.uuid_identification
left join parameters_category pc
on ee.uuid_big_category = pc.uuid_identification
left join accountancy_sectionsage abu
on ee.axe_bu_uuid = abu.uuid_identification
left join accountancy_sectionsage acct
on ee.cct_uuid_identification = acct.uuid_identification
left join accountancy_sectionsage aprj
on ee.axe_prj_uuid = aprj.uuid_identification
left join accountancy_sectionsage apro
on ee.axe_pro_uuid = apro.uuid_identification
left join accountancy_sectionsage apys
on ee.axe_pys_uuid = apys.uuid_identification
left join accountancy_sectionsage arfa
on ee.axe_rfa_uuid = arfa.uuid_identification
where third_party_num = %(third_party_num)s
  and supplier = %(supplier)s
  and invoice_month = %(invoice_month)s
  and invoice_number = %(invoice_number)s
  and ee."delete" = False
  and ee."valid" = true
order by ee."id"