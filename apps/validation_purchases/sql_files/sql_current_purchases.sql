select
	"si"."code_center",
	"si"."code_signboard",
	"si"."third_party_num",
	"bs"."name",
	case
	    when "si"."invoice_type" = '380'
	    then 'FACTURE'
	    else 'AVOIR'
	end as "invoice_type",
	"si"."invoice_amount_without_tax",
	"si"."invoice_amount_tax",
	"si"."invoice_amount_with_tax",
	"cm"."cct",
	"si"."command_reference",
	"si"."acuitis_order_number",
	"si"."acuitis_order_date",
	"si"."delivery_number",
	"si"."delivery_date",
	"si"."invoice_number",
	"si"."invoice_date",
	"si"."reference_article",
	"si"."libelle",
	"si"."qty",
	"si"."net_unit_price",
	"si"."net_amount",
	"si"."vat",
	"si"."vat_rate",
	"si"."vat_amount",
	"si"."amount_with_vat",
	"bu"."section" as "axe_bu",
	"pro"."section" as "axe_pro",
	"prj"."section" as "axe_prj",
	"pys"."section" as "axe_pys",
	"rfa"."section" as "axe_rfa",
	"sb"."name" as "big_category",
	coalesce("sd"."name", '') as "sub_category",
	"si"."client_name",
	"si"."serial_number"
from "edi_ediimport" "si"
left join "parameters_category" "sb"
on "sb"."uuid_identification" = "si"."uuid_big_category"
left join "parameters_subcategory" "sd"
on "sd"."uuid_identification" = "si"."uuid_sub_big_category"
left join "book_society" "bs"
on "si"."third_party_num" = "bs"."third_party_num"
left join "centers_clients_maison" "cm"
  on "si"."cct_uuid_identification" = "cm"."uuid_identification"
left join (
    select
        "uuid_identification", "section"
    from "accountancy_sectionsage"
    where "axe" = 'BU'
) "bu"
on "si"."axe_bu" = "bu"."uuid_identification"
left join (
    select
        "uuid_identification", "section"
    from "accountancy_sectionsage"
    where "axe" = 'PRO'
) "pro"
on "si"."axe_pro" = "pro"."uuid_identification"
left join (
    select
        "uuid_identification", "section"
    from "accountancy_sectionsage"
    where "axe" = 'PRJ'
) "prj"
on "si"."axe_prj" = "prj"."uuid_identification"
left join (
    select
        "uuid_identification", "section"
    from "accountancy_sectionsage"
    where "axe" = 'PYS'
) "pys"
on "si"."axe_pys" = "pys"."uuid_identification"
left join (
    select
        "uuid_identification", "section"
    from "accountancy_sectionsage"
    where "axe" = 'RFA'
) "rfa"
on "si"."axe_rfa" = "rfa"."uuid_identification"
order by
	"si"."invoice_month",
	"bs"."name",
	"si"."invoice_number",
	"cm"."cct",
	"si"."reference_article"