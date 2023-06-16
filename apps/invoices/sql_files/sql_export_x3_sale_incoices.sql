select
	-- T
    'T' as "T",
    "isi"."invoice_type" as "SIVTYP",
    "isi"."invoice_number" as "NUM",
    "isi"."third_party_num" as "BPR",
    "isi"."cpy" as "CPY",
    "isi"."fcy" as "FCY",
    TO_CHAR("isi"."invoice_date"::date, 'DDMMYY') as "ACCDAT",
    "isi"."devise" as "CUR",
    "isi"."type_cours" as "CURTYP",
    TO_CHAR("isi"."date_cours"::date, 'DDMMYY') as "RATDAT",
    "isi"."tiers_payeur" as "BPRRAY",
    TO_CHAR("isi"."date_depart_echeance"::date, 'DDMMYY') as "STRDUDDAT",
    "isi"."regime_tva_maison" as "VAC",
    "isi"."invoice_number" as "BPRVCR",
	"isi"."collectif" as "BPRSAC",
	left(
		coalesce(
			(
				"isb"."code_signboard"
				|| '- ' ||
				"isi"."cct"::varchar
				|| '- ' ||
				"isi"."invoice_month"::varchar
			),
			''
		),
		30
	) as "DES",

	-- D
    'D' as "D",
   	'1' as "D_LIG", -- Numéro de ligne
    "isi"."fcy" as "D_FCYLIN", -- Site
	"isi"."code_plan_sage" as "COA_00", -- Code plan
	coalesce("acs"."call_code", '') as "SAC", --Collectif
	"isd"."account" as "ACC_00", -- Comptes généraux
	'' as "BPRLIN", -- Tiers
	'' as "DSP", -- Répartition
	case
		when "isi"."invoice_type_name" = 'Facture'
		then sum("isd"."net_amount")::numeric
		else -sum("isd"."net_amount")::numeric
	end as "AMTNOTLIN", -- Montant HT
	'0' as "QTY", -- Quantité
	"isd"."vat" as "VAT", -- Taxe X3
			left(
		coalesce(
			(
				"isb"."code_signboard"
				|| '- ' ||
				"isi"."cct"::varchar
				|| '- ' ||
				"isi"."invoice_month"::varchar
			),
			''
		),
		30
	) as "DES", --Commentaire

	-- A
	'A' as "A",
	'1' as "ANALIG", -- Numéro d'ordre
	'BU' as "DIE", -- Code axe BU
	'CCT' as "DIE_01", -- Code axe CCT
	'PRJ' as "DIE_02", -- Code axe PRJ
	'PRO' as "DIE_03", -- Code axe PRO
	'PYS' as "DIE_04", -- Code axe PYS
	'RFA' as "DIE_04", -- Code axe RFA
	"isd"."axe_bu" as "CCE", -- Section analytique BU
	"isi"."cct" as "CCE_01", -- Section analytique CCT
	"isd"."axe_prj" as "CCE_02", -- Section analytique PRJ
	"isd"."axe_pro" as "CCE_03", -- Section analytique PRO
	"isd"."axe_pys" as "CCE_04", -- Section analytique PYS
	"isd"."axe_rfa" as "CCE_04", -- Section analytique RFA
	case
		when "isi"."invoice_type_name" = 'Facture'
		then sum("isd"."net_amount")::numeric
		else -sum("isd"."net_amount")::numeric
	end as "AMT", -- Montant
	'1' as "QTY" -- Quantité

   from "invoices_saleinvoice" "isi"
   join "invoices_saleinvoicedetail" "isd"
     on "isi"."uuid_identification" = "isd"."uuid_invoice"
   join "invoices_signboardsinvoices" "isb"
     on "isi"."signboard" = "isb"."uuid_identification"
   left join "accountancy_accountsage" "acs"
     on "isd"."account" = "acs"."account"
    and "isi"."code_plan_sage" = "acs"."code_plan_sage"


   -- type de client 1 : "VENTE" et "export" = false
   where type_x3 = 1
     and not "isi"."export"
group by
        -- T
        "isi"."invoice_type",
        "isi"."invoice_number",
        "isi"."third_party_num",
        "isi"."cpy",
        "isi"."fcy",
        TO_CHAR("isi"."invoice_date"::date, 'DDMMYY'),
        "isi"."devise",
        "isi"."type_cours",
        TO_CHAR("isi"."date_cours"::date, 'DDMMYY'),
        "isi"."tiers_payeur",
        TO_CHAR("isi"."date_depart_echeance"::date, 'DDMMYY'),
        "isi"."regime_tva_maison",
        "isi"."invoice_number",
        "isi"."collectif",
        left(
            coalesce(
                (
                    "isb"."code_signboard"
                    || '- ' ||
                    "isi"."cct"::varchar
                    || '- ' ||
                    "isi"."invoice_month"::varchar
                ),
                ''
            ),
            30
        ),

        -- D
        "isi"."fcy",
        "isi"."code_plan_sage",
        coalesce("acs"."call_code", ''),
        "isd"."account",
        "isi"."invoice_type_name",
        "isd"."vat",
        left(
            coalesce(
                (
                    "isb"."code_signboard"
                    || '- ' ||
                    "isi"."cct"::varchar
                    || '- ' ||
                    "isi"."invoice_month"::varchar
                ),
                ''
            ),
            30
        ),

        -- A
        "isd"."axe_bu",
        "isi"."cct",
        "isd"."axe_prj",
        "isd"."axe_pro",
        "isd"."axe_pys",
        "isd"."axe_rfa"
order by
		"isi"."invoice_number",
		"isd"."axe_bu",
        "isi"."cct",
        "isd"."axe_prj",
        "isd"."axe_pro",
        "isd"."axe_pys",
        "isd"."axe_rfa"