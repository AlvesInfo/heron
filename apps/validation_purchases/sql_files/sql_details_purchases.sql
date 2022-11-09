select
    supplier,
    invoice_number,
    invoice_date,
    reference_article,
    libelle,
    net_amount,
    vat_rate,
    invoice_amount_without_tax,
    invoice_amount_tax,
    invoice_amount_with_tax
from edi_ediimport ee
where third_party_num = %(third_party_num)s
  and invoice_number = %(invoice_number)s
order by "id"