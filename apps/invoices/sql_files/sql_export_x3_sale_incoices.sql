select
    "isi"."invoice_number", -- invoice_number pour itération

	-- T
    'T' as "T", -- Indicateur model import
    "isi"."invoice_type" as "SIVTYP", -- Type facture
    ("isi"."fcy" || "isi"."invoice_number") as "NUM", -- Numéro de pièce
    "isi"."third_party_num" as "BPR", -- Tiers
    "isi"."cpy" as "CPY", -- Société
    "isi"."fcy" as "FCY", -- Site
    TO_CHAR("isi"."invoice_date"::date, 'DDMMYY') as "ACCDAT", -- Date comptable
    "isi"."devise" as "CUR", -- Devise
    "isi"."type_cours" as "CURTYP", -- Type de cours
    TO_CHAR("isi"."date_cours"::date, 'DDMMYY') as "RATDAT", -- Date cours
    "isi"."tiers_payeur" as "BPRRAY", -- Tiers Payeur
    TO_CHAR("isi"."date_depart_echeance"::date, 'DDMMYY') as "STRDUDDAT", -- Départ échéance
    "isi"."regime_tva_maison" as "VAC", -- Régime TVA
    "isi"."invoice_number" as "BPRVCR", -- Document origine
	"isi"."collectif" as "BPRSAC", -- Collectif
	left(
		coalesce(
			(
				"isi"."code_signboard"
				|| '-' ||
				"isi"."cct"::varchar
				|| '-' ||
                TO_CHAR("isi"."invoice_date"::date, 'MM/YYYY')
			),
			''
		),
		30
	) as "DES", -- Commentaires

	-- D
    'D' as "D", -- Indicateur model import
   	'1' as "D_LIG", -- Numéro de ligne
    "isi"."fcy" as "D_FCYLIN", -- Site
	"isi"."code_plan_sage" as "COA_00", -- Code plan
    "isi"."code_plan_sage" as "COA_01", -- Code plan
	coalesce("acs"."call_code", '') as "SAC", --Collectif
	"isd"."account" as "ACC_00", -- Comptes généraux
    "isd"."account" as "ACC_01", -- Comptes généraux
	'' as "BPRLIN", -- Tiers
	'' as "DSP", -- Répartition
	case
		when "isi"."invoice_type_name" = 'Facture'
		then round("iid"."d_amount"::numeric, 2)::numeric
		else -round("iid"."d_amount"::numeric, 2)
	end as "AMTNOTLIN", -- Montant HT
	'0' as "QTY", -- Quantité
	"isd"."vat" as "VAT", -- Taxe X3
			left(
		coalesce(
			(
				"isi"."code_signboard"
				|| '-' ||
				"isi"."cct"::varchar
				|| '-' ||
                TO_CHAR("isi"."invoice_date"::date, 'MM/YYYY')
			),
			''
		),
		30
	) as "DES_D", --Commentaire

	-- A
	case when "acs"."nb_axes" = 0 then '' else 'A' end as "A", -- Indicateur model import
	'1' as "ANALIG", -- Numéro d'ordre
	'BU' as "DIE", -- Code axe BU
	'CCT' as "DIE_01", -- Code axe CCT
	'PRO' as "DIE_03", -- Code axe PRO
	'PRJ' as "DIE_02", -- Code axe PRJ
	'PYS' as "DIE_04", -- Code axe PYS
	'RFA' as "DIE_05", -- Code axe RFA
	"isd"."axe_bu" as "CCE", -- Section analytique BU
	"isi"."cct" as "CCE_01", -- Section analytique CCT
	"isd"."axe_pro" as "CCE_03", -- Section analytique PRO
	"isd"."axe_prj" as "CCE_02", -- Section analytique PRJ
	"isd"."axe_pys" as "CCE_04", -- Section analytique PYS
	"isd"."axe_rfa" as "CCE_05", -- Section analytique RFA
	case
		when "isi"."invoice_type_name" = 'Facture'
		then sum(round("isd"."net_amount"::numeric, 2))::numeric
		else -sum(round("isd"."net_amount"::numeric, 2))::numeric
	end as "AMT", -- Montant
	'1' as "QTY", -- Quantité

	-- Test Analytique
	case when "acs"."nb_axes" = 0 then false else true end as test_a

from "invoices_saleinvoice" "isi"
join "invoices_saleinvoicedetail" "isd"
 on "isi"."uuid_identification" = "isd"."uuid_invoice"
join (
        select
            sum("net_amount") as "d_amount",
            "uuid_invoice",
            "vat",
            "account",
            "iii"."cpy",
    		"iii"."fcy"
        from "invoices_saleinvoicedetail" "idd"
        join "invoices_saleinvoice" "iii"
        on "iii"."uuid_identification" = "idd"."uuid_invoice"
        where  "iii"."type_x3" = 1
          and not "iii"."export"
		  and "iii"."fcy" = %(fcy)s
        group by
            "uuid_invoice",
            "vat",
            "account",
            "iii"."cpy",
    		"iii"."fcy"
   ) "iid"
 on "isi"."uuid_identification" = "iid"."uuid_invoice"
and "isd"."account" = "iid"."account"
and "isd"."vat" = "iid"."vat"
and "isi"."cpy" = "iid"."cpy"
and "isi"."fcy" = "iid"."fcy"
left join "accountancy_accountsage" "acs"
 on "isd"."account" = "acs"."account"
and "isi"."code_plan_sage" = "acs"."code_plan_sage"

-- type de client 1 : "VENTE" , "export" = false
where "isi"."type_x3" = 1
 and not "isi"."export"
 and "isi"."fcy" = %(fcy)s

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
                    "isi"."code_signboard"
                    || '-' ||
                    "isi"."cct"::varchar
                    || '-' ||
                    TO_CHAR("isi"."invoice_date"::date, 'MM/YYYY')
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
        "iid"."d_amount",
        "isi"."invoice_type_name",
        "isd"."vat",
        left(
            coalesce(
                (
                    "isi"."code_signboard"
                    || '-' ||
                    "isi"."cct"::varchar
                    || '-' ||
                    TO_CHAR("isi"."invoice_date"::date, 'MM/YYYY')
                ),
                ''
            ),
            30
        ),

        -- A
        "acs"."nb_axes",
        "isd"."axe_bu",
        "isi"."cct",
        "isd"."axe_prj",
        "isd"."axe_pro",
        "isd"."axe_pys",
        "isd"."axe_rfa"

order by
		"isi"."invoice_number",
		"isd"."account",
        "isi"."cct",
		"isd"."axe_bu",
        "isd"."axe_prj",
        "isd"."axe_pro",
        "isd"."axe_pys",
        "isd"."axe_rfa"
