with "real_purchase" as(
	select
		"isi"."invoice_number", -- invoice_number pour itération

		-- T
	    'T' as "T", -- Indicateur model import
	    "cpt"."purchase_type_facture" as "PIVTYP", -- Type facture
	    ('SD00' || "isi"."invoice_number") as "NUM", -- Numéro de pièce
	    'ACAF001' as "BPR", -- Tiers
	    'SDOAF' as "CPY", -- Société
	    'SD00' as "FCY", -- Site
	    TO_CHAR("isi"."invoice_date"::date, 'DDMMYY') as "ACCDAT", -- Date comptable
	    "isi"."devise" as "CUR", -- Devise
	    "isi"."type_cours" as "CURTYP", -- Type de cours
	    'ACAF001' as "BPRRAY", -- Tiers Payeur
	    TO_CHAR("isi"."date_depart_echeance"::date, 'DDMMYY') as "STRDUDDAT", -- Départ échéance
	    'FRPRE30FM' as "PTE", -- Coniditions de paiement
	    'FGA' as "VAC", -- Régime TVA
	    left("isi"."invoice_number", 30) as "BPRVCR", -- Document origine
	    '1' as "PBPAINV", -- Adresse
	    '1' as "BPAPAY", -- Adresse tiers payé
		left(
			coalesce(
				(
					'AC00 - ' ||
					"isi"."cct"::varchar
					|| '-' ||
					TO_CHAR("isi"."invoice_date"::date, 'MM/YYYY')
				),
				''
			),
			30
		) as "DES", -- Commentaires

		-- L
	    'L' as "L", -- Indicateur model import
	   	'1' as "L_LIG", -- Numéro de ligne
	    'SD00' as "L_FCYLIN", -- Site
		'FRA' as "COA_00", -- Code plan
		'AFR' as "COA_01", -- Code plan
		"iid"."call_code" as "SAC", --Collectif
		"iid"."account" as "ACC_00", -- Comptes gÃ©nÃ©raux
		"iid"."account" as "ACC_01", -- Comptes gÃ©nÃ©raux
		'' as "BPRLIN", -- Tiers
		case
			when "isi"."invoice_type_name" = 'Facture'
			then round("iid"."d_amount"::numeric, 2)::numeric
			else -round("iid"."d_amount"::numeric, 2)
		end as "AMTNOTLIN", -- Montant HT
		'0' as "QTY_L", -- Quantité
		"isd"."vat" as "VAT", -- Taxe X3
		left(
			coalesce(
				(
					'AC00 - ' ||
					"isi"."cct"::varchar
					|| '- ' ||
					TO_CHAR("isi"."invoice_date"::date, 'MM/YYYY')
				),
				''
			),
			30
		) as "DES_L", --Commentaire

		-- A (les DIE et CCE ont un ordre précis BU, CCT, PRO, PRJ, PYS RFA)
		case when "iid"."nb_axes" = 0 then '' else 'A' end as "A", -- Indicateur model import
		'1' as "ANALIG", -- Numéro d'ordre
		'BU' as "DIE", -- Code axe BU
		'CCT' as "DIE_01", -- Code axe CCT
		'PRO' as "DIE_02", -- Code axe PRO
		'PRJ' as "DIE_03", -- Code axe PRJ
		'PYS' as "DIE_04", -- Code axe PYS
		'RFA' as "DIE_05", -- Code axe RFA
		'SUCC' as "CCE", -- Section analytique BU
		"isi"."cct" as "CCE_01", -- Section analytique CCT
		"isd"."axe_pro" as "CCE_02", -- Section analytique PRO
		"isd"."axe_prj" as "CCE_03", -- Section analytique PRJ
		"isd"."axe_pys" as "CCE_04", -- Section analytique PYS
		"isd"."axe_rfa" as "CCE_05", -- Section analytique RFA
		case
			when "isi"."invoice_type_name" = 'Facture'
			then sum(round("isd"."net_amount"::numeric, 2))::numeric
			else -sum(round("isd"."net_amount"::numeric, 2))::numeric
		end as "AMT", -- Montant
		'0' as "QTY_A", -- Quantité

		-- E
		'E' as "E", -- Indicateur model import
		'1' as "DUDLIG", -- Numéro échéance
        to_char(
	        (
	            date_trunc('month', "isi"."invoice_date")
	            +
	            interval '2 month - 1 day'
	        )::date,
	        'DDMMYY'
        ) as "DUDDAT", -- Date échéance
		'PRE' as "PAM", -- Mode de règlement
		'1' as "PAMTYP", -- Type de règlement
		case
			when "isi"."invoice_type_name" = 'Facture'
			then (round("isi"."invoice_amount_with_tax"::numeric, 2))::numeric
			else -(round("isi"."invoice_amount_with_tax"::numeric, 2))::numeric
		end as "AMTCUR", -- Montant en devise
		'1' as "BPARAY", -- Adresse tiers

		-- Test Analytique
		case when "iid"."nb_axes" = 0 then false else true end as test_a

	from "invoices_saleinvoice" "isi"
	join "invoices_saleinvoicedetail" "isd"
	  on "isi"."uuid_identification" = "isd"."uuid_invoice"
	join "invoices_invoicecommondetails" "iic"
	  on "isd"."import_uuid_identification" = "iic"."import_uuid_identification"
	left join "articles_article" "aat"
	  on "iic"."reference_article" = "aat"."reference"
	 and "iic"."third_party_num" = "aat"."third_party_num"
	left join (
		select
			"article",
			"purchase_account",
			"vat"
		from "articles_articleaccount"
		where "child_center" = 'ACF'
	) "acc"
	  on "aat"."uuid_identification" = "acc"."article"
	 and "isd"."vat" = "acc"."vat"
	left join "accountancy_accountsage" "aaa"
	  on "acc"."purchase_account" = "aaa"."account"
	 and "aaa"."code_plan_sage" = 'FRA'
	left join (
	        select
	            sum("net_amount") as "d_amount",
	            "uuid_invoice",
	            "iii"."vat",
	            "acc"."purchase_account" as "account",
	            "idd"."cpy",
	    		"idd"."fcy",
	    		coalesce("aaa"."call_code", '') as "call_code" ,
	    		"aaa"."nb_axes"
	        from "invoices_saleinvoice" "idd"
	        join "invoices_saleinvoicedetail" "iii"
	        on "idd"."uuid_identification" = "iii"."uuid_invoice"
	        join "invoices_invoicecommondetails" "iic"
	          on "iii"."import_uuid_identification" = "iic"."import_uuid_identification"
	        join "articles_article" "aat"
	          on "iic"."reference_article" = "aat"."reference"
	         and "iic"."third_party_num" = "aat"."third_party_num"
	        join (
	        	select
	        		"article",
	        		"purchase_account",
	        		"vat"
	        	from "articles_articleaccount"
	        	where "child_center" = 'ACF'
	        ) "acc"
	          on "aat"."uuid_identification" = "acc"."article"
	         and "iii"."vat" = "acc"."vat"
	        join "accountancy_accountsage" "aaa"
	          on "acc"."purchase_account" = "aaa"."account"
	         and "aaa"."code_plan_sage" = 'FRA'
	        where not "idd"."export"
			  and "idd"."third_party_num" = 'SDOAF'
	        group by
	            "uuid_invoice",
	            "iii"."vat",
	            "acc"."purchase_account",
	            "idd"."cpy",
	    		"idd"."fcy",
	    		"aaa"."call_code",
	    		"aaa"."nb_axes"
	   ) "iid"
	  on "isi"."uuid_identification" = "iid"."uuid_invoice"
	 and "acc"."purchase_account" = "iid"."account"
	 and "isd"."vat" = "iid"."vat"
	 and "isi"."cpy" = "iid"."cpy"
	 and "isi"."fcy" = "iid"."fcy"
	join "centers_purchasing_typefacture" "cpt"
	  on "isi"."invoice_type_name" = "cpt"."invoice_name"
	 and "cpt"."child_center" = 'ACF'

	-- type de client 1 : "VENTE" , "export" = false
	where not "isi"."export"
	  and "isi"."type_x3" = 1
	  and "isi"."third_party_num" = 'SDOAF'

	group by
	        -- T
	        "cpt"."purchase_type_facture",
	        "isi"."third_party_num",
	        TO_CHAR("isi"."invoice_date"::date, 'DDMMYY'),
	        "isi"."devise",
	        "isi"."type_cours",
	        TO_CHAR("isi"."date_depart_echeance"::date, 'DDMMYY'),
	        "isi"."invoice_number",

	        -- D
	        "iid"."call_code",
	        "iid"."account",
	        "iid"."d_amount",
	        "isi"."invoice_type_name",
	        "isd"."vat",
	        "isi"."cct",

	        -- A
	        "iid"."nb_axes",
	        "isd"."axe_prj",
	        "isd"."axe_pro",
	        "isd"."axe_pys",
	        "isd"."axe_rfa",

	        -- E
	        "isi"."mode_reglement",
	        "isi"."date_echeance",
	        "isi"."invoice_amount_with_tax",
	        "isi"."invoice_date"
),
"delta_invoices" as (
	select
		"uuid_invoice",
		"invoice_number",
		round(("invoice_amount_with_tax" - sum("delta_ttc"))::numeric, 2) as "d_ttc"
	from (
		select
		    "uuid_invoice",
		    "iii"."invoice_number",
		    "acc"."vat",
		    "vat_rate",
		    "acc"."purchase_account",
 		    round(sum("net_amount")::numeric * (1+ "vat_rate"::numeric)::numeric, 2) as "delta_ttc",
 		    sum("net_amount") as "net_amount",
		    "iii"."invoice_amount_with_tax"
		from "invoices_saleinvoicedetail" "idd"
		join "invoices_saleinvoice" "iii"
		on "iii"."uuid_identification" = "idd"."uuid_invoice"
		join "invoices_invoicecommondetails" "iic"
	  	on "idd"."import_uuid_identification" = "iic"."import_uuid_identification"
		left join "articles_article" "aat"
		  on "iic"."reference_article" = "aat"."reference"
		 and "iic"."third_party_num" = "aat"."third_party_num"
		left join (
			select
				"article",
				"purchase_account",
				"vat"
			from "articles_articleaccount"
			where "child_center" = 'ACF'
		) "acc"
	  on "aat"."uuid_identification" = "acc"."article"
	 and "idd"."vat" = "acc"."vat"
		where  "iii"."type_x3" = 1
		  and not "iii"."export"
		  and "iii"."third_party_num" = 'SDOAF'
		group by
		    "uuid_invoice",
		    "iii"."invoice_number",
		    "acc"."vat",
		    "vat_rate",
		    "acc"."purchase_account",
		    "iii"."invoice_amount_with_tax"
	) det
	group by "uuid_invoice",
		    "invoice_number",
		    "invoice_amount_with_tax"
),
"delta" as (
	select
		"isi"."invoice_number", -- invoice_number pour itération

		-- T
	    'T' as "T", -- Indicateur model import
	    "cpt"."purchase_type_facture" as "PIVTYP", -- Type facture
	    ('SD00' || "isi"."invoice_number") as "NUM", -- Numéro de pièce
	    'ACAF001' as "BPR", -- Tiers
	    'SDOAF' as "CPY", -- Société
	    'SD00' as "FCY", -- Site
	    TO_CHAR("isi"."invoice_date"::date, 'DDMMYY') as "ACCDAT", -- Date comptable
	    "isi"."devise" as "CUR", -- Devise
	    "isi"."type_cours" as "CURTYP", -- Type de cours
	    'ACAF001' as "BPRRAY", -- Tiers Payeur
	    TO_CHAR("isi"."date_depart_echeance"::date, 'DDMMYY') as "STRDUDDAT", -- Départ échéance
	    'FRPRE30FM' as "PTE", -- Coniditions de paiement
	    'FGA' as "VAC", -- Régime TVA
	    left("isi"."invoice_number", 30) as "BPRVCR", -- Document origine
	    '1' as "PBPAINV", -- Adresse
	    '1' as "BPAPAY", -- Adresse tiers payé
		left(
			coalesce(
				(
					'AC00 - ' ||
					"isi"."cct"::varchar
					|| '-' ||
					TO_CHAR("isi"."invoice_date"::date, 'MM/YYYY')
				),
				''
			),
			30
		) as "DES", -- Commentaires

		-- L
	    'L' as "L", -- Indicateur model import
	   	'1' as "L_LIG", -- Numéro de ligne
	    'SD00' as "L_FCYLIN", -- Site
		'FRA' as "COA_00", -- Code plan
		'AFR' as "COA_01", -- Code plan
		'' as "SAC", --Collectif
		'445660' as "ACC_00", -- Comptes généraux
	    '445660' as "ACC_01", -- Comptes généraux
		'' as "BPRLIN", -- Tiers
			case
				when "isi"."invoice_type_name" = 'Facture'
				then sum("d_ttc")
				else -sum("d_ttc")
			end as "AMTNOTLIN", -- Montant HT
			'0' as "QTY_L", -- Quantité
			'004' as  "VAT", -- Taxe X3
		left(
			coalesce(
				(
					'AC00 - ' ||
					"isi"."cct"::varchar
					|| '- ' ||
					TO_CHAR("isi"."invoice_date"::date, 'MM/YYYY')
				),
				''
			),
			30
		) as "DES_L", --Commentaire

		-- A (les DIE et CCE ont un ordre précis BU, CCT, PRO, PRJ, PYS RFA)
		'A' as "A", -- Indicateur model import
		'1' as "ANALIG", -- Numéro d'ordre
		'BU' as "DIE", -- Code axe BU
		'CCT' as "DIE_01", -- Code axe CCT
		'PRO' as "DIE_02", -- Code axe PRO
		'PRJ' as "DIE_03", -- Code axe PRJ
		'PYS' as "DIE_04", -- Code axe PYS
		'RFA' as "DIE_05", -- Code axe RFA
        'REFAC' as  "CCE",
        'DIV' as  "CCE_01",
        'DIV' as  "CCE_02",
        'NAF' as  "CCE_03",
        'FR' as  "CCE_04",
        'NAF' as  "CCE_05",
		case
			when "isi"."invoice_type_name" = 'Facture'
			then sum("d_ttc")
			else -sum("d_ttc")
		end as "AMT",
		'0' as "QTY_A", -- Quantité

		-- E
		'E' as "E", -- Indicateur model import
		'1' as "DUDLIG", -- Numéro échéance
        to_char(
	        (
	            date_trunc('month', "isi"."invoice_date")
	            +
	            interval '2 month - 1 day'
	        )::date,
	        'DDMMYY'
        ) as "DUDDAT", -- Date échéance
		'PRE' as "PAM", -- Mode de règlement
		'1' as "PAMTYP", -- Type de règlement
		case
			when "isi"."invoice_type_name" = 'Facture'
			then (round("isi"."invoice_amount_with_tax"::numeric, 2))::numeric
			else -(round("isi"."invoice_amount_with_tax"::numeric, 2))::numeric
		end as "AMTCUR", -- Montant en devise
		'1' as "BPARAY", -- Adresse tiers

		-- Test Analytique
		true as "test_a"

	from "invoices_saleinvoice" "isi"
	join "delta_invoices" "sa"
	on "isi"."uuid_identification" = "sa"."uuid_invoice"
	join "centers_purchasing_typefacture" "cpt"
	  on "isi"."invoice_type_name" = "cpt"."invoice_name"
	 and "cpt"."child_center" = 'ACF'
	group by
        -- T
        "cpt"."purchase_type_facture",
        "isi"."third_party_num",
        TO_CHAR("isi"."invoice_date"::date, 'DDMMYY'),
        "isi"."devise",
        "isi"."type_cours",
        TO_CHAR("isi"."date_depart_echeance"::date, 'DDMMYY'),
        "isi"."invoice_number",
        "isi"."cct",
         isi.invoice_date,
          isi.invoice_type_name,
          isi.invoice_amount_with_tax

 		having "isi"."invoice_amount_with_tax" - sum("d_ttc") != 0
),
"alls" as (
    select
		"invoice_number", "T", "PIVTYP", "NUM", "BPR", "CPY", "FCY", "ACCDAT", "CUR",
		"CURTYP", "BPRRAY", "STRDUDDAT", "PTE", "VAC", "BPRVCR", "PBPAINV", "BPAPAY", "DES",
		"L", "L_LIG", "L_FCYLIN", "COA_00", "COA_01", "SAC", "ACC_00", "ACC_01", "BPRLIN",
		"AMTNOTLIN", "QTY_L", "VAT", "DES_L",
		"A", "ANALIG", "DIE", "DIE_01", "DIE_02", "DIE_03", "DIE_04", "DIE_05",
		"CCE", "CCE_01", "CCE_02", "CCE_03", "CCE_04", "CCE_05", "AMT",
		"QTY_A", "E", "DUDLIG", "DUDDAT", "PAM", "PAMTYP", "AMTCUR", "BPARAY",
		"test_a"
    from "real_purchase"
    union all
    select
		"invoice_number", "T", "PIVTYP", "NUM", "BPR", "CPY", "FCY", "ACCDAT", "CUR",
		"CURTYP", "BPRRAY", "STRDUDDAT", "PTE", "VAC", "BPRVCR", "PBPAINV", "BPAPAY", "DES",
		"L", "L_LIG", "L_FCYLIN", "COA_00", "COA_01", "SAC", "ACC_00", "ACC_01", "BPRLIN",
		"AMTNOTLIN", "QTY_L", "VAT", "DES_L",
		"A", "ANALIG", "DIE", "DIE_01", "DIE_02", "DIE_03", "DIE_04", "DIE_05",
		"CCE", "CCE_01", "CCE_02", "CCE_03", "CCE_04", "CCE_05", "AMT",
		"QTY_A", "E", "DUDLIG", "DUDDAT", "PAM", "PAMTYP", "AMTCUR", "BPARAY",
		"test_a"
	from "delta"
)
select
		"invoice_number", "T", "PIVTYP", "NUM", "BPR", "CPY", "FCY", "ACCDAT", "CUR",
		"CURTYP", "BPRRAY", "STRDUDDAT", "PTE", "VAC", "BPRVCR", "PBPAINV", "BPAPAY", "DES",
		"L", "L_LIG", "L_FCYLIN", "COA_00", "COA_01", "SAC", "ACC_00", "ACC_01", "BPRLIN",
		"AMTNOTLIN", "QTY_L", "VAT", "DES_L",
		"A", "ANALIG", "DIE", "DIE_01", "DIE_02", "DIE_03", "DIE_04", "DIE_05",
		"CCE", "CCE_01", "CCE_02", "CCE_03", "CCE_04", "CCE_05", "AMT",
		"QTY_A", "E", "DUDLIG", "DUDDAT", "PAM", "PAMTYP", "AMTCUR", "BPARAY",
		"test_a"
from "alls"

order by
		"invoice_number",
		"ACC_00",
		"AMTNOTLIN",
		"VAT",
        "CCE",
		"CCE_01",
        "CCE_02",
        "CCE_03",
        "CCE_04",
        "CCE_05"