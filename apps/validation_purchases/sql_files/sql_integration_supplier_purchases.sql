select
    ee.third_party_num,
    supplier,
    case
	    when ee."is_multi_store" and sum(cct_error) = count("ee"."id") then ''
    	when ee."is_multi_store" and sum(cct_error) != count("ee"."id") then ''
	    when not ee."is_multi_store" and sum(cct_error) = count("ee"."id") then max(cct)
    	else ''
	end as axe_cct,
    case
	   	when ee."is_multi_store" and sum(cct_error) = count("ee"."id") then ''
    	when ee."is_multi_store" and sum(cct_error) != count("ee"."id") then ''
	    else replace(max(ee.code_maison), '|', '')
	end as code_maison,
	case
	   	when ee."is_multi_store" and sum(cct_error) = count("ee"."id") then 'Multi Magasins !'
    	when ee."is_multi_store" and sum(cct_error) != count("ee"."id") then 'Multi Magasins !'
	    else replace(left(max(maison), 100), '|', '')
	end as maison,
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
        ee.third_party_num || '||' ||
        supplier || '||' ||
        invoice_month || '||' ||
        invoice_number
    ) as enc_param,
    ee.uuid_identification,
    ee.invoice_year,
    case when ee."invoice_type" = '380' then 'darkblue' else 'brown' end as color_invoice,
    ee."is_multi_store",
    sum(cct_error) as nb_code_fournisseur,
    count("ee"."id") as nb_lignes,
    case
    	when ee."is_multi_store" and sum(cct_error) = count("ee"."id") then 'lightskyblue'
    	when ee."is_multi_store" and sum(cct_error) != count("ee"."id") then 'tan'
	    when not ee."is_multi_store" and sum(cct_error) = count("ee"."id") then 'lavender'
    	else 'lightpink'
    end as cct_color,
    case
    	when ee."is_multi_store" and sum(cct_error) = count("ee"."id") then false
    	when ee."is_multi_store" and sum(cct_error) != count("ee"."id") then false
	    when not ee."is_multi_store" and sum(cct_error) = count("ee"."id") then true
    	else true
    end as clickable
from edi_ediimport ee
left join centers_clients_maison ac
on ee.cct_uuid_identification = ac.uuid_identification
left join (
	select
		ei."id", case when ei.cct_uuid_identification is null then 0 else 1 end as cct_error
	from edi_ediimport ei
) as cc
on ee.id = cc.id
where ee.third_party_num = %(third_party_num)s
  and supplier = %(supplier)s
  and date_trunc('month', invoice_date)::date = %(invoice_month)s
  and (ee."delete" = false or ee."delete" isnull)
group by supplier,
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
order by ee."invoice_type" desc,
         "invoice_number"