with "model_od" as (
    select
        *,
        (
            'OD' ||
            right((EXTRACT(YEAR FROM "isd"."date_od"))::text, 2) ||
            LPAD((EXTRACT(MONTH FROM "isd"."date_od"))::text, 2, '0') ||
            LPAD((EXTRACT(DAY FROM "isd"."date_od"))::text, 2, '0') ||
            "isd"."base_sage_invoice_number"
        ) as "od_invoice_num",
        (
            'OD' ||
            right((EXTRACT(YEAR FROM "isd"."date_extourne"))::text, 2) ||
            LPAD((EXTRACT(MONTH FROM "isd"."date_extourne"))::text, 2, '0') ||
            LPAD((EXTRACT(DAY FROM "isd"."date_extourne"))::text, 2, '0') ||
            "isd"."base_sage_invoice_number"
        ) as "extourne_invoice_num",
		'ODINV' as "TYP", -- Type de pièce
		'' as "NUM", -- Numéro de pièce
		%(fcy)s as "FCY", -- Site
		'ODINV' as "JOU", -- Journal
        TO_CHAR("isd"."date_od"::date, 'DDMMYY') as "ACCDAT_OD",
        TO_CHAR("isd"."date_extourne"::date, 'DDMMYY') as "ACCDAT_EXT",
		'STDCO' as "DACDIA", -- Transaction
		'EUR' as "CUR_G", -- Devise de pièce
        left('ODINV - ' || "isd"."facture_heron" , 30) as "DESVCR_OD", -- Libellé
        left('ODINV EXT - ' || "isd"."facture_heron" , 30) as "DESVCR_EXT", -- Libellé
		"isd"."facture_heron" as "BPRVCR", -- Document origine
        left("isd"."third_party_num" || '-' || "isd"."cct" , 30) as "REF" -- reference
    from "od_modelod" "isd"
),
"comptes_collectif" as (
	select
		1 as "classement",

		-- G
	    'AC', -- invoice pour itération
	    "isd"."od_invoice_num" as "invoice", -- invoice pour itération
	    "isd"."TYP", -- Type de pièce
		"isd"."FCY", -- Site
		"isd"."JOU", -- Journal
		"isd"."ACCDAT_OD" as "ACCDAT", -- Date comptable
		"isd"."DACDIA", -- Transaction
		"isd"."CUR_G", -- Devise de pièce
		"isd"."DESVCR_OD" as "DESVCR", -- Libellé
		"isd"."BPRVCR", -- Document origine
		"isd"."REF", -- Référence

		-- D
		'1' as "LIN_D", -- Numéro de ligne
		'2' as "LEDTYP", -- Type de référentiel
		'1' as "IDTLIN", -- Identifiant
		"isd"."FCY" as "FCYLIN", -- Site
		coalesce("acs"."call_code", '') as "SAC", -- Collectif
		'AFR' as "LED", -- Référentiel
		"isd"."code_plan" as "COA", -- Code plan
		"isd"."compte_collectif" as "ACC", -- Comptes généraux
		"isd"."third_party_num" as "BPR", -- Tiers
		case
			when round("isd"."montant_ttc"::numeric, 2)::numeric > 0
			then 1
			else -1
		end as "SNS_D", -- Sens
		"isd"."CUR_G" as "CUR_D", -- Devise de pièce
		round(abs("isd"."montant_ttc"::numeric), 2)::numeric as "AMTCUR_D", -- Montant pièce
		left("isd"."libelle" || '-' || "isd"."cct" , 30) as "DES", -- Libellé
		'' as "TAX", -- Taxe
		"isd"."compte_produit" as "OFFACC", -- Contrepartie

		-- A
		case when "acs"."nb_axes" = 0 then '' else 'A' end as "A", -- Indicateur model import
		'1' as "LIN_A", -- Numéro de ligne
		'BU' as "DIE", -- Code axe BU
		'CCT' as "DIE_01", -- Code axe CCT
		'PRO' as "DIE_03", -- Code axe PRO
		'PRJ' as "DIE_02", -- Code axe PRJ
		'PYS' as "DIE_04", -- Code axe PYS
		'RFA' as "DIE_05", -- Code axe RFA
		"isd"."axe_bu" as "CCE", -- Section analytique BU
		"isd"."cct" as "CCE_01", -- Section analytique CCT
		"isd"."axe_pro" as "CCE_03", -- Section analytique PRO
		"isd"."axe_prj" as "CCE_02", -- Section analytique PRJ
		"isd"."axe_pys" as "CCE_04", -- Section analytique PYS
		"isd"."axe_rfa" as "CCE_05", -- Section analytique RFA
		round(abs("isd"."montant_ttc"::numeric), 2)::numeric as "AMTCUR_A", -- Montant pièce
		1 as "QTY", -- Quantité
		case
			when round("isd"."montant_ttc"::numeric, 2)::numeric > 0
			then 1
			else -1
		end  as "SNS_A" -- Sens

	from "model_od" "isd"
	left join "accountancy_accountsage" "acs"
	 on "isd"."compte_collectif" = "acs"."account"
	and "isd"."code_plan" = "acs"."code_plan_sage"
	where "isd"."montant_ttc" <> 0
),
"comptes_produits" as (
	select
		2 as "classement",

		-- G
	    "isd"."od_invoice_num" as "invoice", -- invoice pour itération
	    "isd"."TYP", -- Type de pièce
		"isd"."FCY", -- Site
		"isd"."JOU", -- Journal
		"isd"."ACCDAT_OD" as "ACCDAT", -- Date comptable
		"isd"."DACDIA", -- Transaction
		"isd"."CUR_G", -- Devise de pièce
		"isd"."DESVCR_OD" as "DESVCR", -- Libellé
		"isd"."BPRVCR", -- Document origine
		"isd"."REF", -- Référence

		-- D
		'1' as "LIN_D", -- Numéro de ligne
		'2' as "LEDTYP", -- Type de référentiel
		'1' as "IDTLIN", -- Identifiant
		"isd"."FCY" as "FCYLIN", -- Site
		coalesce("acs"."call_code", '') as "SAC", -- Collectif
		'AFR' as "LED", -- Référentiel
		"isd"."code_plan" as "COA", -- Code plan
		"isd"."compte_produit" as "ACC", -- Comptes généraux
		'' as "BPR", -- Tiers
		case
			when round("isd"."montant_ht"::numeric, 2)::numeric > 0
			then -1
			else 1
		end as "SNS_D", -- Sens
		"isd"."CUR_G" as "CUR_D", -- Devise de pièce
		round(abs("isd"."montant_ht"::numeric), 2)::numeric as "AMTCUR_D", -- Montant pièce
		left("isd"."libelle" || '-' || "isd"."cct" , 30) as "DES", -- Libellé
		"isd"."vat" as "TAX", -- Taxe
		"isd"."cct" as "OFFACC", -- Contrepartie

		-- A
		case when "acs"."nb_axes" = 0 then '' else 'A' end as "A", -- Indicateur model import
		'1' as "LIN_A", -- Numéro de ligne
		'BU' as "DIE", -- Code axe BU
		'CCT' as "DIE_01", -- Code axe CCT
		'PRO' as "DIE_03", -- Code axe PRO
		'PRJ' as "DIE_02", -- Code axe PRJ
		'PYS' as "DIE_04", -- Code axe PYS
		'RFA' as "DIE_05", -- Code axe RFA
		"isd"."axe_bu" as "CCE", -- Section analytique BU
		"isd"."cct" as "CCE_01", -- Section analytique CCT
		"isd"."axe_pro" as "CCE_03", -- Section analytique PRO
		"isd"."axe_prj" as "CCE_02", -- Section analytique PRJ
		"isd"."axe_pys" as "CCE_04", -- Section analytique PYS
		"isd"."axe_rfa" as "CCE_05", -- Section analytique RFA
		round(abs("isd"."montant_ht"::numeric), 2)::numeric as "AMTCUR_A", -- Montant pièce
		1 as "QTY", -- Quantité
		case
			when round("isd"."montant_ht"::numeric, 2)::numeric > 0
			then -1
			else 1
		end  as "SNS_A" -- Sens

	from "model_od" "isd"
	left join "accountancy_accountsage" "acs"
	 on "isd"."compte_produit" = "acs"."account"
	and "isd"."code_plan" = "acs"."code_plan_sage"
	where "isd"."montant_ht" <> 0
),
"comptes_tva" as (
	select
		3 as "classement",

		-- G
	    "isd"."od_invoice_num" as "invoice", -- invoice pour itération
	    "isd"."TYP", -- Type de pièce
		"isd"."FCY", -- Site
		"isd"."JOU", -- Journal
		"isd"."ACCDAT_OD" as "ACCDAT", -- Date comptable
		"isd"."DACDIA", -- Transaction
		"isd"."CUR_G", -- Devise de pièce
		"isd"."DESVCR_OD" as "DESVCR", -- Libellé
		"isd"."BPRVCR", -- Document origine
		"isd"."REF", -- Référence

		-- D
		'1' as "LIN_D", -- Numéro de ligne
		'2' as "LEDTYP", -- Type de référentiel
		'1' as "IDTLIN", -- Identifiant
		"isd"."FCY" as "FCYLIN", -- Site
		coalesce("acs"."call_code", '') as "SAC", -- Collectif
		'AFR' as "LED", -- Référentiel
		"isd"."code_plan" as "COA", -- Code plan
		"isd"."compte_tva" as "ACC", -- Comptes généraux
		'' as "BPR", -- Tiers
		case
			when round("isd"."montant_tva"::numeric, 2)::numeric > 0
			then -1
			else 1
		end as "SNS_D", -- Sens
		"isd"."CUR_G" as "CUR_D", -- Devise de pièce
		round(abs("isd"."montant_tva"::numeric), 2)::numeric as "AMTCUR_D", -- Montant pièce
		left("isd"."libelle" || '-' || "isd"."cct" , 30) as "DES", -- Libellé
		"isd"."vat" as "TAX", -- Taxe
		"isd"."cct" as "OFFACC", -- Contrepartie

		-- A
		case when "acs"."nb_axes" = 0 then '' else 'A' end as "A", -- Indicateur model import
		'1' as "LIN_A", -- Numéro de ligne
		'BU' as "DIE", -- Code axe BU
		'CCT' as "DIE_01", -- Code axe CCT
		'PRO' as "DIE_03", -- Code axe PRO
		'PRJ' as "DIE_02", -- Code axe PRJ
		'PYS' as "DIE_04", -- Code axe PYS
		'RFA' as "DIE_05", -- Code axe RFA
		"isd"."axe_bu" as "CCE", -- Section analytique BU
		"isd"."cct" as "CCE_01", -- Section analytique CCT
		"isd"."axe_pro" as "CCE_03", -- Section analytique PRO
		"isd"."axe_prj" as "CCE_02", -- Section analytique PRJ
		"isd"."axe_pys" as "CCE_04", -- Section analytique PYS
		"isd"."axe_rfa" as "CCE_05", -- Section analytique RFA
		round(abs("isd"."montant_tva"::numeric), 2)::numeric as "AMTCUR_A", -- Montant pièce
		1 as "QTY", -- Quantité
		case
			when round("isd"."montant_tva"::numeric, 2)::numeric > 0
			then -1
			else 1
		end  as "SNS_A" -- Sens

	from "model_od" "isd"
	left join "accountancy_accountsage" "acs"
	 on "isd"."compte_tva" = "acs"."account"
	and "isd"."code_plan" = "acs"."code_plan_sage"
	where "isd"."montant_tva" <> 0
),
all_od as (
	select
		"classement", "invoice", "TYP", "FCY", "JOU", "ACCDAT", "DACDIA", "CUR_G", "DESVCR",
	    "BPRVCR", "REF", "LIN_D", "LEDTYP", "IDTLIN", "FCYLIN", "SAC", "LED", "COA", "ACC", "BPR", "SNS_D", "CUR_D",
	    "AMTCUR_D", "DES", "TAX", "OFFACC", "A", "LIN_A", "DIE", "DIE_01", "DIE_03", "DIE_02", "DIE_04", "DIE_05",
	    "CCE", "CCE_01", "CCE_03", "CCE_02", "CCE_04", "CCE_05", "AMTCUR_A", "QTY", "SNS_A"
	from comptes_collectif
	union all
		select
		"classement", "invoice", "TYP", "FCY", "JOU", "ACCDAT", "DACDIA", "CUR_G", "DESVCR",
		"BPRVCR", "REF", "LIN_D", "LEDTYP", "IDTLIN", "FCYLIN", "SAC", "LED", "COA", "ACC", "BPR", "SNS_D", "CUR_D",
		"AMTCUR_D", "DES", "TAX", "OFFACC", "A", "LIN_A", "DIE", "DIE_01", "DIE_03", "DIE_02", "DIE_04", "DIE_05",
		"CCE", "CCE_01", "CCE_03", "CCE_02", "CCE_04", "CCE_05", "AMTCUR_A", "QTY", "SNS_A"
	from comptes_produits
	union all
		select
		"classement", "invoice", "TYP", "FCY", "JOU", "ACCDAT", "DACDIA", "CUR_G", "DESVCR",
		"BPRVCR", "REF", "LIN_D", "LEDTYP", "IDTLIN", "FCYLIN", "SAC", "LED", "COA", "ACC", "BPR", "SNS_D", "CUR_D",
		"AMTCUR_D", "DES", "TAX", "OFFACC", "A", "LIN_A", "DIE", "DIE_01", "DIE_03", "DIE_02", "DIE_04", "DIE_05",
		"CCE", "CCE_01", "CCE_03", "CCE_02", "CCE_04", "CCE_05", "AMTCUR_A", "QTY", "SNS_A"
	from comptes_tva
),
"comptes_collectif_ext" as (
	select
		1 as "classement",

		-- G
	    "isd"."extourne_invoice_num" as "invoice", -- invoice pour itération
	    "isd"."TYP", -- Type de pièce
		"isd"."FCY", -- Site
		"isd"."JOU", -- Journal
		"isd"."ACCDAT_EXT" as "ACCDAT", -- Date comptable
		"isd"."DACDIA", -- Transaction
		"isd"."CUR_G", -- Devise de pièce
		"isd"."DESVCR_EXT" as "DESVCR", -- Libellé
		"isd"."BPRVCR", -- Document origine
		"isd"."REF", -- Référence

		-- D
		'1' as "LIN_D", -- Numéro de ligne
		'2' as "LEDTYP", -- Type de référentiel
		'1' as "IDTLIN", -- Identifiant
		"isd"."FCY" as "FCYLIN", -- Site
		coalesce("acs"."call_code", '') as "SAC", -- Collectif
		'AFR' as "LED", -- Référentiel
		"isd"."code_plan" as "COA", -- Code plan
		"isd"."compte_collectif" as "ACC", -- Comptes généraux
		"isd"."third_party_num" as "BPR", -- Tiers
		case
			when round("isd"."montant_ttc"::numeric, 2)::numeric > 0
			then -1
			else 1
		end as "SNS_D", -- Sens
		"isd"."CUR_G" as "CUR_D", -- Devise de pièce
		round(abs("isd"."montant_ttc"::numeric), 2)::numeric as "AMTCUR_D", -- Montant pièce
		left("isd"."libelle" || '-' || "isd"."cct" , 30) as "DES", -- Libellé
		'' as "TAX", -- Taxe
		"isd"."compte_produit" as "OFFACC", -- Contrepartie

		-- A
		case when "acs"."nb_axes" = 0 then '' else 'A' end as "A", -- Indicateur model import
		'1' as "LIN_A", -- Numéro de ligne
		'BU' as "DIE", -- Code axe BU
		'CCT' as "DIE_01", -- Code axe CCT
		'PRO' as "DIE_03", -- Code axe PRO
		'PRJ' as "DIE_02", -- Code axe PRJ
		'PYS' as "DIE_04", -- Code axe PYS
		'RFA' as "DIE_05", -- Code axe RFA
		"isd"."axe_bu" as "CCE", -- Section analytique BU
		"isd"."cct" as "CCE_01", -- Section analytique CCT
		"isd"."axe_pro" as "CCE_03", -- Section analytique PRO
		"isd"."axe_prj" as "CCE_02", -- Section analytique PRJ
		"isd"."axe_pys" as "CCE_04", -- Section analytique PYS
		"isd"."axe_rfa" as "CCE_05", -- Section analytique RFA
		round(abs("isd"."montant_ttc"::numeric), 2)::numeric as "AMTCUR_A", -- Montant pièce
		1 as "QTY", -- Quantité
		case
			when round("isd"."montant_ttc"::numeric, 2)::numeric > 0
			then -1
			else 1
		end  as "SNS_A" -- Sens

	from "model_od" "isd"
	left join "accountancy_accountsage" "acs"
	 on "isd"."compte_collectif" = "acs"."account"
	and "isd"."code_plan" = "acs"."code_plan_sage"
	where "isd"."montant_ttc" <> 0
),
"comptes_produits_ext" as (
	select
		2 as "classement",

		-- G
	    "isd"."extourne_invoice_num" as "invoice", -- invoice pour itération
	    "isd"."TYP", -- Type de pièce
		"isd"."FCY", -- Site
		"isd"."JOU", -- Journal
		"isd"."ACCDAT_EXT" as "ACCDAT", -- Date comptable
		"isd"."DACDIA", -- Transaction
		"isd"."CUR_G", -- Devise de pièce
		"isd"."DESVCR_EXT" as "DESVCR", -- Libellé
		"isd"."BPRVCR", -- Document origine
		"isd"."REF", -- Référence

		-- D
		'1' as "LIN_D", -- Numéro de ligne
		'2' as "LEDTYP", -- Type de référentiel
		'1' as "IDTLIN", -- Identifiant
		"isd"."FCY" as "FCYLIN", -- Site
		coalesce("acs"."call_code", '') as "SAC", -- Collectif
		'AFR' as "LED", -- Référentiel
		"isd"."code_plan" as "COA", -- Code plan
		"isd"."compte_produit" as "ACC", -- Comptes généraux
		'' as "BPR", -- Tiers
		case
			when round("isd"."montant_ht"::numeric, 2)::numeric > 0
			then 1
			else -1
		end as "SNS_D", -- Sens
		"isd"."CUR_G" as "CUR_D", -- Devise de pièce
		round(abs("isd"."montant_ht"::numeric), 2)::numeric as "AMTCUR_D", -- Montant pièce
		left("isd"."libelle" || '-' || "isd"."cct" , 30) as "DES", -- Libellé
		"isd"."vat" as "TAX", -- Taxe
		"isd"."cct" as "OFFACC", -- Contrepartie

		-- A
		case when "acs"."nb_axes" = 0 then '' else 'A' end as "A", -- Indicateur model import
		'1' as "LIN_A", -- Numéro de ligne
		'BU' as "DIE", -- Code axe BU
		'CCT' as "DIE_01", -- Code axe CCT
		'PRO' as "DIE_03", -- Code axe PRO
		'PRJ' as "DIE_02", -- Code axe PRJ
		'PYS' as "DIE_04", -- Code axe PYS
		'RFA' as "DIE_05", -- Code axe RFA
		"isd"."axe_bu" as "CCE", -- Section analytique BU
		"isd"."cct" as "CCE_01", -- Section analytique CCT
		"isd"."axe_pro" as "CCE_03", -- Section analytique PRO
		"isd"."axe_prj" as "CCE_02", -- Section analytique PRJ
		"isd"."axe_pys" as "CCE_04", -- Section analytique PYS
		"isd"."axe_rfa" as "CCE_05", -- Section analytique RFA
		round(abs("isd"."montant_ht"::numeric), 2)::numeric as "AMTCUR_A", -- Montant pièce
		1 as "QTY", -- Quantité
		case
			when round("isd"."montant_ht"::numeric, 2)::numeric > 0
			then 1
			else -1
		end  as "SNS_A" -- Sens

	from "model_od" "isd"
	left join "accountancy_accountsage" "acs"
	 on "isd"."compte_produit" = "acs"."account"
	and "isd"."code_plan" = "acs"."code_plan_sage"
	where "isd"."montant_ht" <> 0
),
"comptes_tva_ext" as (
	select
		3 as "classement",

		-- G
	    "isd"."extourne_invoice_num" as "invoice", -- invoice pour itération
	    "isd"."TYP", -- Type de pièce
		"isd"."FCY", -- Site
		"isd"."JOU", -- Journal
		"isd"."ACCDAT_EXT" as "ACCDAT", -- Date comptable
		"isd"."DACDIA", -- Transaction
		"isd"."CUR_G", -- Devise de pièce
		"isd"."DESVCR_EXT" as "DESVCR", -- Libellé
		"isd"."BPRVCR", -- Document origine
		"isd"."REF", -- Référence

		-- D
		'1' as "LIN_D", -- Numéro de ligne
		'2' as "LEDTYP", -- Type de référentiel
		'1' as "IDTLIN", -- Identifiant
		"isd"."FCY" as "FCYLIN", -- Site
		coalesce("acs"."call_code", '') as "SAC", -- Collectif
		'AFR' as "LED", -- Référentiel
		"isd"."code_plan" as "COA", -- Code plan
		"isd"."compte_tva" as "ACC", -- Comptes généraux
		'' as "BPR", -- Tiers
		case
			when round("isd"."montant_tva"::numeric, 2)::numeric > 0
			then 1
			else -1
		end as "SNS_D", -- Sens
		"isd"."CUR_G" as "CUR_D", -- Devise de pièce
		round(abs("isd"."montant_tva"::numeric), 2)::numeric as "AMTCUR_D", -- Montant pièce
		left("isd"."libelle" || '-' || "isd"."cct" , 30) as "DES", -- Libellé
		"isd"."vat" as "TAX", -- Taxe
		"isd"."cct" as "OFFACC", -- Contrepartie

		-- A
		case when "acs"."nb_axes" = 0 then '' else 'A' end as "A", -- Indicateur model import
		'1' as "LIN_A", -- Numéro de ligne
		'BU' as "DIE", -- Code axe BU
		'CCT' as "DIE_01", -- Code axe CCT
		'PRO' as "DIE_03", -- Code axe PRO
		'PRJ' as "DIE_02", -- Code axe PRJ
		'PYS' as "DIE_04", -- Code axe PYS
		'RFA' as "DIE_05", -- Code axe RFA
		"isd"."axe_bu" as "CCE", -- Section analytique BU
		"isd"."cct" as "CCE_01", -- Section analytique CCT
		"isd"."axe_pro" as "CCE_03", -- Section analytique PRO
		"isd"."axe_prj" as "CCE_02", -- Section analytique PRJ
		"isd"."axe_pys" as "CCE_04", -- Section analytique PYS
		"isd"."axe_rfa" as "CCE_05", -- Section analytique RFA
		round(abs("isd"."montant_tva"::numeric), 2)::numeric as "AMTCUR_A", -- Montant pièce
		1 as "QTY", -- Quantité
		case
			when round("isd"."montant_tva"::numeric, 2)::numeric > 0
			then 1
			else -1
		end  as "SNS_A" -- Sens

	from "model_od" "isd"
	left join "accountancy_accountsage" "acs"
	 on "isd"."compte_tva" = "acs"."account"
	and "isd"."code_plan" = "acs"."code_plan_sage"
	where "isd"."montant_tva" <> 0
),
all_od_ext as (
	select
		"classement", "invoice", "TYP", "FCY", "JOU", "ACCDAT", "DACDIA", "CUR_G", "DESVCR",
	    "BPRVCR", "REF", "LIN_D", "LEDTYP", "IDTLIN", "FCYLIN", "SAC", "LED", "COA", "ACC", "BPR", "SNS_D", "CUR_D",
	    "AMTCUR_D", "DES", "TAX", "OFFACC", "A", "LIN_A", "DIE", "DIE_01", "DIE_03", "DIE_02", "DIE_04", "DIE_05",
	    "CCE", "CCE_01", "CCE_03", "CCE_02", "CCE_04", "CCE_05", "AMTCUR_A", "QTY", "SNS_A"
	from comptes_collectif_ext
	union all
	select
        "classement", "invoice", "TYP", "FCY", "JOU", "ACCDAT", "DACDIA", "CUR_G", "DESVCR",
        "BPRVCR", "REF", "LIN_D", "LEDTYP", "IDTLIN", "FCYLIN", "SAC", "LED", "COA", "ACC", "BPR", "SNS_D", "CUR_D",
        "AMTCUR_D", "DES", "TAX", "OFFACC", "A", "LIN_A", "DIE", "DIE_01", "DIE_03", "DIE_02", "DIE_04", "DIE_05",
        "CCE", "CCE_01", "CCE_03", "CCE_02", "CCE_04", "CCE_05", "AMTCUR_A", "QTY", "SNS_A"
	from comptes_produits_ext
	union all
		select
		"classement", "invoice", "TYP", "FCY", "JOU", "ACCDAT", "DACDIA", "CUR_G", "DESVCR",
		"BPRVCR", "REF", "LIN_D", "LEDTYP", "IDTLIN", "FCYLIN", "SAC", "LED", "COA", "ACC", "BPR", "SNS_D", "CUR_D",
		"AMTCUR_D", "DES", "TAX", "OFFACC", "A", "LIN_A", "DIE", "DIE_01", "DIE_03", "DIE_02", "DIE_04", "DIE_05",
		"CCE", "CCE_01", "CCE_03", "CCE_02", "CCE_04", "CCE_05", "AMTCUR_A", "QTY", "SNS_A"
	from comptes_tva_ext
),
"alls_regroup" as (
	select
        "classement", "invoice", "TYP", "FCY", "JOU", "ACCDAT", "DACDIA", "CUR_G", "DESVCR",
        "BPRVCR", "REF", "LIN_D", "LEDTYP", "IDTLIN", "FCYLIN", "SAC", "LED", "COA", "ACC", "BPR", "SNS_D", "CUR_D",
        "AMTCUR_D", "DES", "TAX", "OFFACC", "A", "LIN_A", "DIE", "DIE_01", "DIE_03", "DIE_02", "DIE_04", "DIE_05",
        "CCE", "CCE_01", "CCE_03", "CCE_02", "CCE_04", "CCE_05", "AMTCUR_A", "QTY", "SNS_A"
	from all_od
	union all
	select
        "classement", "invoice", "TYP", "FCY", "JOU", "ACCDAT", "DACDIA", "CUR_G", "DESVCR",
        "BPRVCR", "REF", "LIN_D", "LEDTYP", "IDTLIN", "FCYLIN", "SAC", "LED", "COA", "ACC", "BPR", "SNS_D", "CUR_D",
        "AMTCUR_D", "DES", "TAX", "OFFACC", "A", "LIN_A", "DIE", "DIE_01", "DIE_03", "DIE_02", "DIE_04", "DIE_05",
        "CCE", "CCE_01", "CCE_03", "CCE_02", "CCE_04", "CCE_05", "AMTCUR_A", "QTY", "SNS_A"
	from all_od_ext
)
select
	"invoice",

	'G' as "G", -- Indicateur model import
	"TYP", "invoice" as "NUM", "FCY", "JOU", "ACCDAT", "DACDIA", "CUR_G", "DESVCR", "BPRVCR", "REF",

	'D' as "D", -- Indicateur model import
	"LIN_D", "LEDTYP", "IDTLIN", "FCYLIN", "SAC", "LED", "COA", "ACC", "BPR", "SNS_D", "CUR_D",
	SUM("AMTCUR_D") as "AMTCUR_D",
	"DES", "TAX", "OFFACC",

	"A",
	'A' as "A", -- Indicateur model import
	"LIN_A", "DIE", "DIE_01", "DIE_03", "DIE_02", "DIE_04", "DIE_05",
	"CCE", "CCE_01", "CCE_03", "CCE_02", "CCE_04", "CCE_05",
	SUM("AMTCUR_A") as "AMTCUR_A",
	"QTY", "SNS_A"
from alls_regroup
group by "classement", "invoice", "TYP", "FCY", "JOU", "ACCDAT", "DACDIA", "CUR_G",
         "DESVCR", "BPRVCR", "REF", "LIN_D", "LEDTYP", "IDTLIN", "FCYLIN", "SAC", "LED", "COA", "ACC", "BPR",
         "SNS_D", "CUR_D", "DES",  "TAX", "OFFACC", "A", "LIN_A",
         "DIE", "DIE_01", "DIE_03", "DIE_02", "DIE_04", "DIE_05",
         "CCE", "CCE_01", "CCE_03", "CCE_02", "CCE_04", "CCE_05", "QTY", "SNS_A"
order by "invoice", "DESVCR", "REF", "DES", "classement", "ACC", "SNS_D"
