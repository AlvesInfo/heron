/*
    Equivalent SQL de la vue MaisonUpdate (apps/centers_clients/views/maisons_views.py:125)
    rendue par apps/centers_clients/templates/centers_clients/client_update_table.html

    Les alias correspondent aux libellés affichés dans le template.
    Paramètre : %(pk)s  ->  centers_clients_maison.id  (url maisons_update/<int:pk>/)

    N.B. : les colonnes "Devise", "Plan X3" et "Catégorie Client" sont lues directement
    sur centers_clients_maison : leurs FK utilisent un to_field dont la valeur est
    exactement celle que renvoie le __str__ du modèle cible (Currency.code,
    CodePlanSage.code_plan_sage, ClientFamilly.name), la jointure est donc inutile.
*/
select
    -- ============================ CENTRE DE COÛT ============================
    "cc"."cct"                                              as "CCT X3",
    "cc"."intitule"                                         as "Intitulé",
    "cc"."intitule_court"                                   as "Intitulé court",
    case when "cc"."third_party_num" is not null
         then concat("cc"."third_party_num", ' - ', "bs"."name")
    end                                                     as "Tiers Client X3",
    "cc"."code_maison"                                      as "Code maison B.I",
    "cc"."code_bbgr"                                        as "Code BBGR B.I",
    "cc"."code_cosium"                                      as "Code cosium B.I",
    "cc"."reference_cosium"                                 as "Référence Cosium",
    "ctv"."name"                                            as "Type Vente",
    case
        when coalesce("acs"."active", false) then null
        else 'Attention ce CCT n''est pas actif dans X3'
    end                                                     as "Actif X3",

    -- ============================= IDENTIFIANTS =============================
    "cc"."siren_number"                                     as "N° Siren",
    "cc"."siret_number"                                     as "N° Siret",
    "cc"."vat_cee_number"                                   as "N° TVA Intra.",

    -- =============================== ADRESSE ================================
    "cc"."immeuble"                                         as "Immeuble",
    "cc"."adresse"                                          as "Adresse",
    "cc"."code_postal"                                      as "Code Postal",
    "cc"."ville"                                            as "Ville",
    "co"."country_name"                                     as "Pays",
    "cc"."telephone"                                        as "Téléphone",
    "cc"."mobile"                                           as "Mobile",
    -- emails de l'adresse principale (address_code = '1') du Tiers X3 (contexte
    -- "adresse_principale_sage"), affichés en lecture seule
    coalesce("ba"."email_01", '')                           as "Email 01 - Tiers Client X3",
    coalesce("ba"."email_02", '')                           as "Email 02 - Tiers Client X3",
    coalesce("ba"."email_03", '')                           as "Email 03 - Tiers Client X3",
    coalesce("ba"."email_04", '')                           as "Email 04 - Tiers Client X3",
    coalesce("ba"."email_05", '')                           as "Email 05 - Tiers Client X3",
    "cc"."email"                                            as "Email - Client Heron",

    -- =============================== CENTRALE ===============================
    case when "cc"."sign_board" is not null
         then concat("cps"."code", ' - ', "cps"."name")
    end                                                     as "Enseigne",
    "cc"."client_familly"                                   as "Catégorie Client",
    "cc"."opening_date"                                     as "Date Ouverture",
    "cc"."closing_date"                                     as "Date Fermeture",
    "cc"."signature_franchise_date"                         as "Date signature contrat",
    "cc"."agreement_franchise_end_date"                     as "Date signature fin de contrat",
    "cc"."agreement_renew_date"                             as "Date renouvellement contrat",
    "cc"."currency"                                         as "Devise",
    "cl"."name"                                             as "Langue",
    case when "cc"."sage_vat_by_default" is not null
         then concat("avs"."vat", ' - ', "avs"."vat_regime")
    end                                                     as "TVA X3",
    case "cc"."rfa_frequence"
        when 0 then '---------'
        when 1 then 'Mensuel'
        when 2 then 'Trimestriel'
        when 3 then 'Semestriel'
        when 4 then 'Annuel'
    end                                                     as "Fréquence RFA",
    case "cc"."rfa_remise"
        when 0 then '---------'
        when 1 then 'Fournisseur Total'
        when 2 then 'Famille Article'
        when 3 then 'Article'
    end                                                     as "Remise RFA",
    "cc"."sage_plan_code"                                   as "Plan X3",
    case when "cc"."axe_bu" is not null
         then concat("ass"."section", ' - ', "ass"."name")
    end                                                     as "AXE BU",

    -- ============================= REFACTURATION ============================
    "cc"."entry_fee_amount"                                 as "Droit d'entrée",
    "cc"."renew_fee_amoount"                                as "Droit Renouvellement",
    "psc"."name"                                            as "Catégorie de prix",
    "cc"."generic_coefficient"                              as "Coéf. vente",
    case when "cc"."credit_account" is not null
         then concat("cre"."account", ' - ', "cre"."code_plan_sage")
    end                                                     as "Compte au Crédit",
    case when "cc"."debit_account" is not null
         then concat("deb"."account", ' - ', "deb"."code_plan_sage")
    end                                                     as "Compte au Débit",
    case when "cc"."prov_account" is not null
         then concat("pro"."account", ' - ', "pro"."code_plan_sage")
    end                                                     as "Compte sur Provision",
    case when "cc"."extourne_account" is not null
         then concat("ext"."account", ' - ', "ext"."code_plan_sage")
    end                                                     as "Compte sur Extourne",
    case when "cc"."budget_code" is not null
         then concat("atd"."code", ' - ', "atd"."name")
    end                                                     as "Code budgetaire"

from "centers_clients_maison" "cc"

    -- cct x3 (to_field=cct) -> pour le flag "actif dans X3"
    left join "accountancy_cctsage" "acs"
           on "acs"."cct" = "cc"."cct"

    -- tiers client x3 (to_field=third_party_num)
    left join "book_society" "bs"
           on "bs"."third_party_num" = "cc"."third_party_num"

    -- adresse principale sage : society.society_society.filter(address_code="1").first()
    -- (unique_together (society, address_code) => 1 ligne au maximum)
    left join "book_address" "ba"
           on "ba"."society" = "cc"."third_party_num"
          and "ba"."address_code" = '1'

    -- type de vente (to_field=num)
    left join "centers_clients_typevente" "ctv"
           on "ctv"."num" = "cc"."type_x3"

    -- pays (to_field=country)
    left join "countries_country" "co"
           on "co"."country" = "cc"."pays"

    -- enseigne (to_field=code)
    left join "centers_purchasing_signboard" "cps"
           on "cps"."code" = "cc"."sign_board"

    -- langue (to_field=code, mais __str__ renvoie name)
    left join "countries_language" "cl"
           on "cl"."code" = "cc"."language"

    -- tva x3 par défaut (to_field=vat)
    left join "accountancy_vatsage" "avs"
           on "avs"."vat" = "cc"."sage_vat_by_default"

    -- axe bu (to_field=uuid_identification)
    left join "accountancy_sectionsage" "ass"
           on "ass"."uuid_identification" = "cc"."axe_bu"

    -- catégorie de prix (db_column=uuid_sale_price_category, to_field=uuid_identification)
    left join "parameters_salepricecategory" "psc"
           on "psc"."uuid_identification" = "cc"."uuid_sale_price_category"

    -- comptes x3 (to_field=uuid_identification)
    left join "accountancy_accountsage" "cre"
           on "cre"."uuid_identification" = "cc"."credit_account"
    left join "accountancy_accountsage" "deb"
           on "deb"."uuid_identification" = "cc"."debit_account"
    left join "accountancy_accountsage" "pro"
           on "pro"."uuid_identification" = "cc"."prov_account"
    left join "accountancy_accountsage" "ext"
           on "ext"."uuid_identification" = "cc"."extourne_account"

    -- code budgetaire : pas de to_field => référence la pk (id) de accountancy_tabdivsage
    left join "accountancy_tabdivsage" "atd"
           on "atd"."id" = "cc"."budget_code"

where "cc"."id" = %(pk)s
