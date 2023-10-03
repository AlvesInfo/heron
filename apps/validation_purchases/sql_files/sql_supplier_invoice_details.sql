select
    "ee"."third_party_num",
    "ee"."supplier",
    case
    	when "ee"."invoice_type" = '380'
    	then 'Facture'
    	else 'Avoir'
    end as  "type_facture",
    "ee"."invoice_number",
    "ee"."invoice_date",
    "ee"."invoice_amount_without_tax",
    "ee"."invoice_amount_tax",
    "ee"."invoice_amount_with_tax",
    "ee"."code_fournisseur",
    "ac"."cct" as "axe_cct",
    "ac"."intitule_court",
    "ee"."delivery_number",
    "ee"."delivery_date",
    "ee"."devise",
    "ee"."reference_article",
    "ee"."libelle",
    "ee"."qty",
    coalesce("ee"."gross_unit_price", "ee"."net_unit_price") as "gross_unit_price",
    case
    	when coalesce("ee"."gross_unit_price", "ee"."net_unit_price") = 0
    	then 0
    	else round((1 - ("ee"."net_unit_price" / coalesce("ee"."gross_unit_price", "ee"."net_unit_price"))), 2)::numeric
    end as "discount_price_01",
    "ee"."net_unit_price",
    "ee"."net_amount",
    "ee"."vat_rate",
    "ee"."vat_amount",
    "ee"."amount_with_vat",
    "abu"."section" as "axe_bu",
    "aprj"."section" as "axe_prj",
    "apro"."section" as "axe_pro",
    "apys"."section" as "axe_pys",
    "arfa"."section" as "axe_rfa",
    "pc"."name" as "big_category",
    coalesce("sc"."name", '') as "sub_category",
    "ee"."first_name",
    "ee"."last_name"
from "edi_ediimport" "ee"
left join "centers_clients_maison" "ac"
       on "ee"."cct_uuid_identification" = "ac"."uuid_identification"
left join "parameters_category" "pc"
       on "ee"."uuid_big_category" = "pc"."uuid_identification"
left join "parameters_subcategory" "sc"
       on "sc"."uuid_identification" = "ee"."uuid_sub_big_category"
left join "accountancy_sectionsage" "abu"
       on "ee"."axe_bu" = "abu"."uuid_identification"
left join "accountancy_sectionsage" "aprj"
       on "ee"."axe_prj" = "aprj"."uuid_identification"
left join "accountancy_sectionsage" "apro"
       on "ee"."axe_pro" = "apro"."uuid_identification"
left join "accountancy_sectionsage" "apys"
       on "ee"."axe_pys" = "apys"."uuid_identification"
left join "accountancy_sectionsage" "arfa"
       on "ee"."axe_rfa" = "arfa"."uuid_identification"
where "ee"."third_party_num" = %(third_party_num)s
  and "ee"."invoice_month" = %(invoice_month)s
  and "ee"."supplier" = %(supplier)s
  and "ee"."flow_name" = %(flow_name)s
order by "ee"."id"