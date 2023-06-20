select
	"si"."code_center" as "centrale",
	"sg"."code_signboard" as "enseigne",
	case when "si"."type_x3" = 1 then 'VENTE' else 'OD ANA' end as "type_vente",
	"si"."cct" as "cct_facturer",
	"ip"."name_cct",
	"si"."third_party_num" as "tiers_facturer",
	"ip"."name_third_party",
	"si"."invoice_number" as "num_fac_acuitis",
	"si"."invoice_date",
	"si"."invoice_amount_without_tax" as "total_ht",
	"si"."invoice_amount_tax" as "total_tva",
	"si"."invoice_amount_with_tax" as "total_ttc",
	"si"."big_category" as "grande_category",
	"ii"."third_party_num" as "tiers_fournisseur",
	"ii"."supplier",
	"si"."invoice_type",
	"ii"."invoice_number" as "num_facture_tiers",
	"ii"."invoice_date" as "date_facture_fournisseur",
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
	"sd"."account" as "compte_x3",
	coalesce("sa"."section", '') as "bu_client",
	case when "sa"."section" isnull then '' else "sd"."account_od_600" end as "account_od_600",
	"sd"."big_category",
	"sd"."sub_category",
	"sd"."base",
	"sd"."grouping_goods"
from "invoices_saleinvoice" "si"
join "invoices_saleinvoicedetail" "sd"
  on "si"."uuid_identification" = "sd"."uuid_invoice"
join "invoices_invoicecommondetails" "ii"
  on "sd"."import_uuid_identification" ="ii"."import_uuid_identification"
join "invoices_signboardsinvoices" "sg"
  on "si"."signboard" = "sg"."uuid_identification"
join "invoices_partiesinvoices" "ip"
  on "si"."parties" = "ip"."uuid_identification"
join "centers_clients_maison" "cm"
  on "si"."cct" = "cm"."cct"
left join "accountancy_sectionsage" "sa"
  on "cm"."axe_bu" = "sa"."uuid_identification"
where not "si"."final"
order by
	"si"."code_center",
	"sg"."code_signboard",
	case when "si"."type_x3" = 1 then 'VENTE' else 'OD ANA' end,
	"si"."cct"
