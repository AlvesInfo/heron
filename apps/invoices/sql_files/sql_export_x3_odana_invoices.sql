with "groupe_g" as (
	select
		"isi"."uuid_identification",
		"isi"."code_plan_sage",
		"isi"."fcy",
		"isi"."cct",
		"isi"."devise",
		"isi"."big_category",
		"isi"."type_x3",
	  	"isi"."export",

		-- G
	    "isi"."invoice_number", -- invoice_number pour itération
	    "aec"."type_piece" as "TYP", -- Type de pièce
		('ANA' || "isi"."invoice_number") as "NUM", -- Numéro de pièce
		"isi"."fcy" as "FCY", -- Site
		"aec"."journal" as "JOU", -- Journal
		TO_CHAR("isi"."invoice_date"::date, 'DDMMYY') as "ACCDAT", -- Date comptable
		"aec"."transaction" as "DACDIA", -- Transaction
		"isi"."devise" as "CUR_G", -- Devise de pièce
		left('OD ANA - ' || "isi"."big_category_code" , 30) as "DESVCR", -- Libellé
		"isi"."invoice_number" as "BPRVCR", -- Document origine
		"sa"."section" as "bu_client"

	 from "invoices_saleinvoice" "isi"
	 join "accountancy_ecritures" "aec"
	   on "isi"."type_x3" = "aec"."type_x3"
	  and "aec"."ecriture" = 'ODANA'
	 join "centers_clients_maison" "cm"
	   on "isi"."cct" = "cm"."cct"
	 join "accountancy_sectionsage" "sa"
	   on "cm"."axe_bu" = "sa"."uuid_identification"
	-- type de client 2 : "OD ANA", "export" = false
	where "isi"."type_x3" = 2
	  and not "isi"."export"
	  and "isi"."fcy" = %(fcy)s
),
"comptes_700" as (
	select
		--classement
		1 as "classement",

		-- G
	    "isi"."invoice_number", -- invoice_number pour itération
	    "TYP", -- Type de pièce
		"NUM", -- Numéro de pièce
		"FCY", -- Site
		"JOU", -- Journal
		"ACCDAT", -- Date comptable
		"DACDIA", -- Transaction
		"CUR_G", -- Devise de pièce
		"DESVCR", -- Libellé
		"BPRVCR", -- Document origine
		right(
			"isi"."big_category"
			|| ' : '  ||
			"isd"."axe_bu"
			|| ' -> '  ||
			"isi"."cct",
			30
		) as "REF", -- Référence

		-- D
		'1' as "LIN_D", -- Numéro de ligne
		'2' as "LEDTYP", -- Type de référentiel
		'1' as "IDTLIN", -- Identifiant
		"isi"."fcy" as "FCYLIN", -- Site
		coalesce("acs"."call_code", '') as "SAC", -- Collectif
		'AFR' as "LED", -- Référentiel
		"isi"."code_plan_sage" as "COA", -- Code plan
		"isd"."account" as "ACC", -- Comptes généraux
		'' as "BPR", -- Tiers
		case
			when round("isd"."net_amount"::numeric, 2)::numeric > 0
			then -1
			else 1
		end as "SNS_D", -- Sens
		"isi"."devise" as "CUR_D", -- Devise de pièce
		round(abs("isd"."net_amount"::numeric), 2)::numeric as "AMTCUR_D", -- Montant pièce
		right(
			"isi"."big_category"
			|| ' : '  ||
			"isd"."axe_bu"
			|| ' -> '  ||
			"isi"."cct",
			30
		) as "DES", -- Libellé
		'' as "TAX", -- Taxe
		"isi"."cct" as "OFFACC", -- Contrepartie

		-- A
		'1' as "LIN_A", -- Numéro de ligne
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
		round(abs("isd"."net_amount"::numeric), 2)::numeric as "AMTCUR_A", -- Montant pièce
		1 as "QTY", -- Quantité
		case
			when round("isd"."net_amount"::numeric, 2)::numeric > 0
			then -1
			else 1
		end  as "SNS_A" -- Sens

	from "groupe_g" "isi"
	join "invoices_saleinvoicedetail" "isd"
	  on "isi"."uuid_identification" = "isd"."uuid_invoice"
	left join "accountancy_accountsage" "acs"
	 on "isd"."account" = "acs"."account"
	and "isi"."code_plan_sage" = "acs"."code_plan_sage"
	where "isd"."net_amount" <> 0
 ),
"comptes_600" as (
	select
		--classement
		2 as "classement",

		-- G
	    "isi"."invoice_number", -- invoice_number pour itération
	    "TYP", -- Type de pièce
		"NUM", -- Numéro de pièce
		"FCY", -- Site
		"JOU", -- Journal
		"ACCDAT", -- Date comptable
		"DACDIA", -- Transaction
		"CUR_G", -- Devise de pièce
		"DESVCR", -- Libellé
		"BPRVCR", -- Document origine
		right(
			"isi"."big_category"
			|| ' : '  ||
			"isd"."axe_bu"
			|| ' -> '  ||
			"isi"."cct",
			30
		) as "REF", -- Référence

		-- D
		'1' as "LIN_D", -- Numéro de ligne
		'2' as "LEDTYP", -- Type de référentiel
		'1' as "IDTLIN", -- Identifiant
		"isi"."fcy" as "FCYLIN", -- Site
		coalesce("acs"."call_code", '') as "SAC", -- Collectif
		'AFR' as "LED", -- Référentiel
		"isi"."code_plan_sage" as "COA", -- Code plan
		"isd"."account_od_600" as "ACC", -- Comptes généraux
		'' as "BPR", -- Tiers
		case
			when round("isd"."net_amount"::numeric, 2)::numeric > 0
			then 1
			else -1
		end as "SNS_D", -- Sens
		"isi"."devise" as "CUR_D", -- Devise de pièce
		round(abs("isd"."net_amount"::numeric), 2)::numeric as "AMTCUR_D", -- Montant pièce
		right(
			"isi"."big_category"
			|| ' : '  ||
			"isd"."axe_bu"
			|| ' -> '  ||
			"isi"."cct",
			30
		) as "DES", -- Libellé
		'' as "TAX", -- Taxe
		"isi"."cct" as "OFFACC", -- Contrepartie

		-- A
		'1' as "LIN_A", -- Numéro de ligne
		'BU' as "DIE", -- Code axe BU
		'CCT' as "DIE_01", -- Code axe CCT
		'PRO' as "DIE_03", -- Code axe PRO
		'PRJ' as "DIE_02", -- Code axe PRJ
		'PYS' as "DIE_04", -- Code axe PYS
		'RFA' as "DIE_05", -- Code axe RFA
		"isi"."bu_client" as "CCE", -- Section analytique BU
		"isi"."cct" as "CCE_01", -- Section analytique CCT
		"isd"."axe_pro" as "CCE_03", -- Section analytique PRO
		"isd"."axe_prj" as "CCE_02", -- Section analytique PRJ
		"isd"."axe_pys" as "CCE_04", -- Section analytique PYS
		"isd"."axe_rfa" as "CCE_05", -- Section analytique RFA
		round(abs("isd"."net_amount"::numeric), 2)::numeric as "AMTCUR_A", -- Montant pièce
		1 as "QTY", -- Quantité
		case
			when round("isd"."net_amount"::numeric, 2)::numeric > 0
			then 1
			else -1
		end  as "SNS_A" -- Sens

	from "groupe_g" "isi"
	join "invoices_saleinvoicedetail" "isd"
	  on "isi"."uuid_identification" = "isd"."uuid_invoice"
	left join "accountancy_accountsage" "acs"
	 on "isd"."account" = "acs"."account"
	and "isi"."code_plan_sage" = "acs"."code_plan_sage"
	where "isd"."net_amount" <> 0
),
"alls" as (
    select
        "classement",
        "c_700"."invoice_number",
        "TYP", "NUM", "FCY", "JOU", "ACCDAT", "DACDIA", "CUR_G",
        "DESVCR", "BPRVCR", "REF", "LIN_D", "LEDTYP", "IDTLIN", "FCYLIN", "SAC", "LED", "COA",
        "c_700"."ACC",
        "BPR",
        "c_700"."SNS_D", "CUR_D",
        "a_700"."AMTCUR_D",
        "DES", "TAX", "OFFACC", "LIN_A", "DIE",
        "DIE_01", "DIE_03", "DIE_02", "DIE_04", "DIE_05", "CCE", "CCE_01", "CCE_03", "CCE_02",
        "CCE_04", "CCE_05", "AMTCUR_A", "QTY", "SNS_A"
    from "comptes_700" "c_700"
    join (
        select
            "invoice_number",
            sum("AMTCUR_D"::numeric) as "AMTCUR_D",
            "SNS_D",
            "ACC"
        from "comptes_700"
        group by
            "invoice_number",
            "SNS_D",
            "ACC"
    ) "a_700"
    on "c_700"."invoice_number" = "a_700"."invoice_number"
    and "c_700"."SNS_D" = "a_700"."SNS_D"
    and "c_700"."ACC" = "a_700"."ACC"

    union all

    select
        "classement",
        "c_600"."invoice_number",
        "TYP", "NUM", "FCY", "JOU", "ACCDAT", "DACDIA", "CUR_G",
        "DESVCR", "BPRVCR", "REF", "LIN_D", "LEDTYP", "IDTLIN", "FCYLIN", "SAC", "LED", "COA",
        "c_600"."ACC",
        "BPR",
        "c_600"."SNS_D", "CUR_D",
        "a_600"."AMTCUR_D",
        "DES", "TAX", "OFFACC", "LIN_A", "DIE",
        "DIE_01", "DIE_03", "DIE_02", "DIE_04", "DIE_05", "CCE", "CCE_01", "CCE_03", "CCE_02",
        "CCE_04", "CCE_05", "AMTCUR_A", "QTY", "SNS_A"
    from "comptes_600" "c_600"
    join (
        select
            "invoice_number",
            sum("AMTCUR_D"::numeric) as "AMTCUR_D",
            "SNS_D",
            "ACC"
        from "comptes_600"
        group by
            "invoice_number",
            "SNS_D",
            "ACC"
    ) "a_600"
    on "c_600"."invoice_number" = "a_600"."invoice_number"
    and "c_600"."SNS_D" = "a_600"."SNS_D"
    and "c_600"."ACC" = "a_600"."ACC"
)
select
        "invoice_number",
        'G' as "G", -- Indicateur model import
        "TYP", "NUM", "FCY", "JOU", "ACCDAT", "DACDIA", "CUR_G",
        "DESVCR", "BPRVCR", "REF",

        'D' as "D", -- Indicateur model import
        "LIN_D", "LEDTYP", "IDTLIN", "FCYLIN", "SAC", "LED", "COA",
        "ACC", "BPR", "SNS_D", "CUR_D", "AMTCUR_D", "DES", "TAX", "OFFACC",

        'A' as "A", -- Indicateur model import
        "LIN_A", "DIE",
        "DIE_01", "DIE_03", "DIE_02", "DIE_04", "DIE_05", "CCE", "CCE_01", "CCE_03", "CCE_02",
        "CCE_04", "CCE_05",
        sum("AMTCUR_A"::numeric) as "AMTCUR_A",
        "QTY", "SNS_A"
from "alls"
group by
        "classement", "invoice_number", "TYP", "NUM", "FCY", "JOU", "ACCDAT", "DACDIA", "CUR_G",
        "DESVCR", "BPRVCR", "REF", "LIN_D", "LEDTYP", "IDTLIN", "FCYLIN", "SAC", "LED", "COA",
        "ACC", "BPR", "SNS_D", "CUR_D", "AMTCUR_D", "DES", "TAX", "OFFACC", "LIN_A", "DIE",
        "DIE_01", "DIE_03", "DIE_02", "DIE_04", "DIE_05", "CCE", "CCE_01", "CCE_03", "CCE_02",
        "CCE_04", "CCE_05",  "QTY", "SNS_A"
order by
        "invoice_number", "classement", "ACC", "SNS_D"