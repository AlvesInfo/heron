with "real_sales" as(
	select
	    "isi"."invoice_number", -- invoice_number pour itération
	
		-- T
	    'T' as "T", -- Indicateur model import
	    "isi"."invoice_type" as "SIVTYP", -- Type facture
	    "isi"."invoice_sage_number" as "NUM", -- Numéro de pièce
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
		'0' as "QTY_D", -- Quantité
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
		'1' as "QTY_A", -- Quantité
	
		-- Test Analytique
		case when "acs"."nb_axes" = 0 then false else true end as "test_a"
	
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
	        "isi"."invoice_sage_number",
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
),
"delta_sales" as (
	select
	    "cct",
	    "uuid_invoice",
	    "invoice_sage_number", 
	    "invoice_amount_with_tax",
	    sum("net_amount") as "d_amount",
	    "vat",
	    "vat_rate",
	    round(sum("net_amount")::numeric * (1+ "vat_rate"::numeric)::numeric, 2) as "d_ttc",
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
		"cct",
	    "uuid_invoice",
	    "invoice_sage_number", 
	    "invoice_amount_with_tax",
	    "vat",
	    "vat_rate",
	    "account",
	    "iii"."cpy",
		"iii"."fcy"
), 
"delta" as (
	select 
		    "isi"."invoice_number", -- invoice_number pour itération
		
			-- T
		    'T' as "T", -- Indicateur model import
		    "isi"."invoice_type" as "SIVTYP", -- Type facture
		    "isi"."invoice_sage_number" as "NUM", -- Numéro de pièce
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
			'' as "SAC", --Collectif
			'445710' as "ACC_00", -- Comptes généraux
		    '445710' as "ACC_01", -- Comptes généraux
			'' as "BPRLIN", -- Tiers
			'' as "DSP", -- Répartition
			case
				when "isi"."invoice_type_name" = 'Facture'
				then round(("sa"."invoice_amount_with_tax" - sum("d_ttc"))::numeric, 2)
				else -round(("sa"."invoice_amount_with_tax" - sum("d_ttc"))::numeric, 2)
			end as "AMTNOTLIN", -- Montant HT
			'0' as "QTY_D", -- Quantité
			'004' as  "VAT", -- Taxe X3
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
			'' as "A",
			'1' as "ANALIG", -- Numéro d'ordre
			'BU' as "DIE", -- Code axe BU
			'CCT' as "DIE_01", -- Code axe CCT
			'PRO' as "DIE_03", -- Code axe PRO
			'PRJ' as "DIE_02", -- Code axe PRJ
			'PYS' as "DIE_04", -- Code axe PYS
			'RFA' as "DIE_05", -- Code axe RFA
	        '' as  "CCE",
	        '' as  "CCE_01",
	        '' as  "CCE_02",
	        '' as  "CCE_03",
	        '' as  "CCE_04",
	        '' as  "CCE_05",
	        0 as "AMT",
			'1' as "QTY_A", -- Quantité
		
			-- Test Analytique
			false as "test_a"
	
	from "invoices_saleinvoice" "isi"
	join "delta_sales" "sa"
	on "isi"."uuid_identification" = "sa"."uuid_invoice"
	group by   
        -- T
        "isi"."invoice_type",
        "isi"."invoice_sage_number",
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
		"isi"."invoice_type_name",
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

		"sa"."cct",
		"uuid_invoice",
	    "sa"."invoice_sage_number", 
	    "sa"."invoice_amount_with_tax" 
	    
		having "sa"."invoice_amount_with_tax" - sum("d_ttc") != 0
),
"alls" as (
    select 
        "invoice_number", "T" , "SIVTYP" , "NUM" , "BPR" , "CPY" , "FCY" , "ACCDAT" , "CUR" ,
		"CURTYP" , "RATDAT" , "BPRRAY" , "STRDUDDAT" , "VAC" , "BPRVCR" , "BPRSAC" , "DES" ,
        "D" , "D_LIG" , "D_FCYLIN" , "COA_00" , "COA_01" , "SAC" , "ACC_00" , "ACC_01" ,
        "BPRLIN" , "DSP" , "AMTNOTLIN" , "QTY_D" , "VAT" , "DES_D" ,
        "A" , "ANALIG" , "DIE" , "DIE_01" , "DIE_03" , "DIE_02" , "DIE_04" , "DIE_05" ,
		"CCE" , "CCE_01" , "CCE_03" , "CCE_02" , "CCE_04" , "CCE_05" , "AMT" , "QTY_A",
		"test_a"
    from "real_sales"
    union all
    select
        "invoice_number", "T" , "SIVTYP" , "NUM" , "BPR" , "CPY" , "FCY" , "ACCDAT" , "CUR" ,
		"CURTYP" , "RATDAT" , "BPRRAY" , "STRDUDDAT" , "VAC" , "BPRVCR" , "BPRSAC" , "DES" ,
        "D" , "D_LIG" , "D_FCYLIN" , "COA_00" , "COA_01" , "SAC" , "ACC_00" , "ACC_01" ,
        "BPRLIN" , "DSP" , "AMTNOTLIN" , "QTY_D" , "VAT" , "DES_D" ,
        "A" , "ANALIG" , "DIE" , "DIE_01" , "DIE_03" , "DIE_02" , "DIE_04" , "DIE_05" ,
		"CCE" , "CCE_01" , "CCE_03" , "CCE_02" , "CCE_04" , "CCE_05" , "AMT" , "QTY_A",
		"test_a"
	from "delta"
)
select
	"invoice_number", "T" , "SIVTYP" , "NUM" , "BPR" , "CPY" , "FCY" , "ACCDAT" , "CUR" ,
    "CURTYP" , "RATDAT" , "BPRRAY" , "STRDUDDAT" , "VAC" , "BPRVCR" , "BPRSAC" , "DES" ,
    "D" , "D_LIG" , "D_FCYLIN" , "COA_00" , "COA_01" , "SAC" , "ACC_00" , "ACC_01" ,
    "BPRLIN" , "DSP" , "AMTNOTLIN" , "QTY_D" , "VAT" , "DES_D" ,
    "A" , "ANALIG" , "DIE" , "DIE_01" , "DIE_03" , "DIE_02" , "DIE_04" , "DIE_05" ,
    "CCE" , "CCE_01" , "CCE_03" , "CCE_02" , "CCE_04" , "CCE_05" , "AMT" , "QTY_A",
    "test_a"
from "alls"

order by
		"invoice_number",
		"ACC_00",
        "CCE",
		"CCE_01",
        "CCE_02",
        "CCE_03",
        "CCE_04",
        "CCE_05"
