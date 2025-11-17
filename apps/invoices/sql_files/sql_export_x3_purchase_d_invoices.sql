select
	"isi"."invoice_sage_number", -- invoice_number pour itération

	-- T
    'T' as "T", -- Indicateur model import
    "isi"."invoice_type" as "PIVTYP", -- Type facture
    "isi"."invoice_sage_number" as "NUM", -- Numéro de pièce
    "isi"."third_party_num" as "BPR", -- Tiers
    "isi"."cpy" as "CPY", -- Société
    "isi"."fcy" as "FCY", -- Site
    case
        when "isi"."invoice_date" >= "isi"."integration_month"
        then TO_CHAR("isi"."invoice_date"::date, 'DDMMYY')
        else TO_CHAR("isi"."integration_month"::date, 'DDMMYY')
    end as "ACCDAT", -- Date comptable
    "isi"."devise" as "CUR", -- Devise
    "isi"."type_cours" as "CURTYP", -- Type de cours
    "isi"."tiers_payeur" as "BPRRAY", -- Tiers Payeur
    TO_CHAR("isi"."date_depart_echeance"::date, 'DDMMYY') as "STRDUDDAT", -- Départ échéance
    "isi"."type_reglement" as "PTE", -- Coniditions de paiement
    "isi"."regime_tva_tiers" as "VAC", -- Régime TVA
    left("isi"."invoice_number", 30) as "BPRVCR", -- Document origine
    '1' as "PBPAINV", -- Adresse
    '1' as "BPAPAY", -- Adresse tiers payé
	left(
		coalesce(
			(
				"isi"."code_signboard"
				|| '-' ||
				"isi"."third_party_num"::varchar
				|| '-' ||
				TO_CHAR("isi"."invoice_date"::date, 'MM/YYYY')
			),
			''
		),
		30
	) as "DES", -- Commentaires
    TO_CHAR("isi"."invoice_date"::date, 'DDMMYY') as "BPRDAT", -- Date origine document

	-- L
    'L' as "L", -- Indicateur model import
   	'1' as "L_LIG", -- Numéro de ligne
    "isi"."fcy" as "L_FCYLIN", -- Site
	"isi"."code_plan_sage" as "COA_00", -- Code plan
	"isi"."code_plan_sage" as "COA_01", -- Code plan
	"isd"."collectif" as "SAC", --Collectif
	"isd"."account" as "ACC_00", -- Comptes généraux
	"isd"."account" as "ACC_01", -- Comptes généraux
	'' as "BPRLIN", -- Tiers
	case
		when "isi"."invoice_type_name" = 'Facture'
		then round("iid"."d_amount"::numeric, 2)::numeric
		else -round("iid"."d_amount"::numeric, 2)
	end as "AMTNOTLIN", -- Montant HT
	'1' as "QTY", -- Quantité
	"isd"."vat" as "VAT", -- Taxe X3
	left(
		coalesce(
			(
				"isi"."code_signboard"
				|| '- ' ||
				"isi"."third_party_num"::varchar
				|| '- ' ||
				TO_CHAR("isi"."invoice_date"::date, 'MM/YYYY')
			),
			''
		),
		30
	) as "DES_L", --Commentaire

	-- A (les DIE et CCE ont un ordre précis BU, CCT, PRO, PRJ, PYS RFA)
	case when "acs"."nb_axes" = 0 then '' else 'A' end as "A", -- Indicateur model import
	'1' as "ANALIG", -- Numéro d'ordre
	'BU' as "DIE", -- Code axe BU
	'CCT' as "DIE_01", -- Code axe CCT
	'PRO' as "DIE_02", -- Code axe PRO
	'PRJ' as "DIE_03", -- Code axe PRJ
	'PYS' as "DIE_04", -- Code axe PYS
	'RFA' as "DIE_05", -- Code axe RFA
	"isd"."axe_bu" as "CCE", -- Section analytique BU
	"icd"."cct" as "CCE_01", -- Section analytique CCT
	"isd"."axe_pro" as "CCE_02", -- Section analytique PRO
	"isd"."axe_prj" as "CCE_03", -- Section analytique PRJ
	"isd"."axe_pys" as "CCE_04", -- Section analytique PYS
	"isd"."axe_rfa" as "CCE_05", -- Section analytique RFA
	case
		when "isi"."invoice_type_name" = 'Facture'
		then sum(round("isd"."net_amount"::numeric, 2))::numeric
		else -sum(round("isd"."net_amount"::numeric, 2))::numeric
	end as "AMT", -- Montant
	'1' as "QTY", -- Quantité


	-- E
	'E' as "E", -- Indicateur model import
	'1' as "DUDLIG", -- Numéro échéance
	TO_CHAR("isi"."date_echeance"::date, 'DDMMYY') as "DUDDAT", -- Date échéance
	"isi"."mode_reglement" as "PAM", -- Mode de règlement
	'1' as "PAMTYP", -- Type de règlement
	case
		when "isi"."invoice_type_name" = 'Facture'
		then (round("isi"."invoice_amount_with_tax"::numeric, 2))::numeric
		else -(round("isi"."invoice_amount_with_tax"::numeric, 2))::numeric
	end as "AMTCUR", -- Montant en devise
	'1' as "BPARAY", -- Adresse tiers

	-- Test Analytique
	case when "acs"."nb_axes" = 0 then false else true end as test_a

from "invoices_invoice" "isi"
join "invoices_invoicedetail" "isd"
 on "isi"."uuid_identification" = "isd"."uuid_invoice"
join (
        select
            sum("net_amount") as "d_amount",
            "uuid_invoice",
            "vat",
            "account",
            "iii"."cpy",
    		"iii"."fcy"
        from "invoices_invoicedetail" "idd"
        join "invoices_invoice" "iii"
        on "iii"."uuid_identification" = "idd"."uuid_invoice"
        where not "iii"."export"
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
join (
	select
		"import_uuid_identification",
		"cct"
	  from "invoices_invoicecommondetails"
) "icd"
on "isd"."import_uuid_identification" = "icd"."import_uuid_identification"
left join "accountancy_accountsage" "acs"
 on "isd"."account" = "acs"."account"
and "isi"."code_plan_sage" = "acs"."code_plan_sage"

-- "export" = false
where not "isi"."export"
 and "isi"."fcy" = %(fcy)s

group by
        -- T
        "isi"."invoice_type",
        "isi"."invoice_sage_number",
        "isi"."third_party_num",
        "isi"."cpy",
        "isi"."fcy",
        "isi"."invoice_date",
        "isi"."devise",
        "isi"."type_cours",
        "isi"."tiers_payeur",
        TO_CHAR("isi"."date_depart_echeance"::date, 'DDMMYY'),
        "isi"."regime_tva_tiers",
        "isi"."invoice_number",
        "isi"."code_signboard",
        left(
            coalesce(
                (
                    "isi"."code_signboard"
                    || '- ' ||
                    "isi"."third_party_num"::varchar
                    || '- ' ||
                    TO_CHAR("isi"."invoice_date"::date, 'MM/YYYY')
                ),
                ''
            ),
            30
        ),

        -- D
        "isi"."fcy",
        "isi"."code_plan_sage",
        "isd"."collectif",
        "isd"."account",
        "iid"."d_amount",
        "isi"."invoice_type_name",
        "isd"."vat",
        left(
            coalesce(
                (
                    "isi"."code_signboard"
                    || '- ' ||
                    "isi"."third_party_num"::varchar
                    || '- ' ||
                    TO_CHAR("isi"."invoice_date"::date, 'MM/YYYY')
                ),
                ''
            ),
            30
        ),
        "isi"."integration_month",

        -- A
        "acs"."nb_axes",
        "isd"."axe_bu",
        "icd"."cct",
        "isd"."axe_prj",
        "isd"."axe_pro",
        "isd"."axe_pys",
        "isd"."axe_rfa",

        -- E
        "isi"."mode_reglement",
        "isi"."type_reglement",
        "isi"."date_echeance",
        "isi"."invoice_amount_with_tax",
        "isi"."invoice_date"

order by
		"isi"."invoice_number",
		"isd"."account",
        "icd"."cct",
        case
			when "isi"."invoice_type_name" = 'Facture'
			then round("iid"."d_amount"::numeric, 2)::numeric
			else -round("iid"."d_amount"::numeric, 2)
		end,
		"isd"."vat",
		"isd"."axe_bu",
        "isd"."axe_prj",
        "isd"."axe_pro",
        "isd"."axe_pys",
        "isd"."axe_rfa"