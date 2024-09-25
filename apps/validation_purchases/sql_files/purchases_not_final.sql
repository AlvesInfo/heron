select 
	"si"."code_center",
	"si"."code_signboard",
	"si"."third_party_num",
	"bs"."name",
	"si"."invoice_sage_number",
	"si"."invoice_type",
	"si"."invoice_amount_without_tax",
	"si"."invoice_amount_tax",
	"si"."invoice_amount_with_tax",
	"ii"."cct",
	"ii"."command_reference",
	"ii"."acuitis_order_number",
	"ii"."acuitis_order_date",
	"ii"."delivery_number",
	"ii"."delivery_date",
	"ii"."invoice_number",
	"ii"."invoice_date",
	"ii"."reference_article",
	"ii"."libelle",
	"ii"."qty",
	"sd"."net_unit_price",
	"sd"."net_amount",
	"sd"."vat",
	"sd"."vat_rate",
	"sd"."vat_amount",
	"sd"."amount_with_vat",
	"sd"."axe_bu",
	"sd"."axe_pro",
	"sd"."axe_prj",
	"sd"."axe_pys",
	"sd"."axe_rfa",
	"sd"."account",
	"sd"."big_category",
	coalesce("sd"."sub_category", '') as "sub_category",
	"ii"."client_name",
	"ii"."serial_number"
from "invoices_invoice" "si"
join "invoices_invoicedetail" "sd"
on "si"."uuid_identification" = "sd"."uuid_invoice"
join "invoices_invoicecommondetails" "ii"
on "sd"."import_uuid_identification" = "ii"."import_uuid_identification"
join "book_society" "bs"
on "si"."third_party_num" = "bs"."third_party_num"
join "centers_clients_maison" "cm"
  on "ii"."cct" = "cm"."cct"

where third_party_num in ('SIEM001')
and invoice_date between '2023-09-01' and '2024-06-30'
order by 
	"si"."invoice_month",
	"bs"."name",
	"si"."invoice_number",
	"ii"."cct",
	"ii"."reference_article"
