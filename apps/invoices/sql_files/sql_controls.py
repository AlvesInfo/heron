# pylint: disable
"""
FR : Module des requêtes SQL pour les contrôles
EN : SQL queries module for controls

Commentaire:

created at: 2023-03-12
created by: Paulo ALVES

modified at: 2023-03-12
modified by: Paulo ALVES
"""

SQL_ARTICLES_NEWS = """
SELECT 1 
FROM articles_article 
WHERE new_article
LIMIT 1
"""

SQL_ARTCILES_EDI_CONTROL = """
select 
     1
from "edi_ediimport" "ee"
where (
    "ee"."axe_bu" isnull
    or 
    "ee"."axe_prj" isnull 
    or 
    "ee"."axe_pro" isnull 
    or 
    "ee"."axe_pys" isnull 
    or 
    "ee"."axe_rfa" isnull 
)
limit 1
"""

SQL_TIERS_CONTROL = """
select 
    1
from "edi_ediimport" "ee"
where ("ee"."third_party_num" isnull or "ee"."third_party_num" = '')
limit 1
"""

SQL_GROUPING_CONTROL = """
select 
    "aa"."section"
from (
    select 
        "axe_pro", "acs"."section" 
    from "articles_article" "art"
    join "accountancy_sectionsage" "acs" 
    on "art"."axe_pro" = "acs"."uuid_identification" 
    group by "axe_pro", "acs"."section" 
) "aa" 
left join "centers_purchasing_axeprogroupinggoods" "cp" 
on "aa"."axe_pro" = "cp"."axe_pro"
where "aa"."axe_pro" is not null
and "cp"."axe_pro" isnull
limit 1
"""

SQL_ACCOUNTS_EDI_IMPORT_CONTROL = """
select 
    "as3"."section", 
    "pc"."name" as "category", 
    coalesce("ps"."name"::varchar, '') as "sub_category", 
    "ee"."vat"
from "edi_ediimport" "ee" 
left join "parameters_category" "pc" 
on "pc"."uuid_identification" = "ee"."uuid_big_category" 
left join "parameters_subcategory" "ps" 
on "ps"."uuid_identification" = "ee"."uuid_sub_big_category"
left join "centers_purchasing_accountsaxeprocategory" "cpa" 
on "ee"."uuid_big_category" = "cpa"."uuid_big_category" 
and "ee"."axe_pro" = "cpa"."axe_pro"
and "ee"."vat" = "cpa"."vat"
and (
        coalesce("ee"."uuid_sub_big_category", '2399a57d-20d3-4e8c-9bb7-95be586cbd49'::uuid) 
        = 
        coalesce("cpa"."uuid_sub_category", '2399a57d-20d3-4e8c-9bb7-95be586cbd49'::uuid)
    )
left join (
    select 
        "uuid_identification", "section" 
    from "accountancy_sectionsage" "as2" 
    where "axe" = 'PRO'
) "as3" 
on "ee"."axe_pro" = "as3"."uuid_identification"
where "cpa"."uuid_identification" isnull
group by  "as3"."section", "pc"."name", coalesce("ps"."name"::varchar, ''), "ee"."vat"
order by "as3"."section", "pc"."name", coalesce("ps"."name"::varchar, ''), "ee"."vat"
"""

SQL_ACCOUNTS_ARTICLES = """
SELECT 1
FROM edi_ediimport ee
WHERE EXISTS (
    SELECT 1 
    FROM articles_article aa
    WHERE aa.reference = ee.reference_article
)
AND NOT EXISTS (
    SELECT 1 
    FROM articles_article aa
    JOIN articles_articleaccount aa2 
      ON aa2.article = aa.uuid_identification
    WHERE aa.reference = ee.reference_article
      AND aa2.vat = ee.vat
)
LIMIT 1
"""

SQL_VAT_CONTROL = """
select 
     1
from "edi_ediimport" "ee"
where "ee"."vat" isnull
limit 1
"""

SQL_VAT_REGIME_CONTROL = """
select 
     1
from "edi_ediimport" "ee"
where ("ee"."vat_regime" isnull or "ee"."vat_regime"='')
limit 1
"""

SQL_CCT_CONTROL = """
select 
     1
from "edi_ediimport" "ee"
where "ee"."cct_uuid_identification" isnull
limit 1
"""

SQL_CATEGORY_CONTROL = """
select 
     1
from "edi_ediimport" "ee"
where "ee"."uuid_big_category" isnull
limit 1
"""

SQL_CENTER_CONTROL = """
select 
     1
from "edi_ediimport" "ee"
where "ee"."code_center" isnull
limit 1
"""

SQL_SIGNBOARD_CONTROL = """
select 
     1
from "edi_ediimport" "ee"
where "ee"."code_signboard" isnull
limit 1
"""

SQL_SUB_CATEGORY_CONTROL = """
select 
     1
from "edi_ediimport" "ee"
join parameters_subcategory ps 
on "ee"."uuid_big_category" = ps."uuid_big_category"
where "ee"."uuid_sub_big_category" isnull
limit 1
"""

SQL_SALES_AXE_BU = """
select 
    "axe_bu"
from (
    select 
        "cct", 
        "axe_bu"
    from "centers_clients_maison"
    where "type_x3" = 2
) rr
where "axe_bu" isnull
"""

SQL_VALIDATIONS = """
SELECT 1
FROM edi_edivalidation
WHERE not final
  AND NOT (
    integration
    AND families
    AND franchiseurs
    AND clients_news
    AND subscriptions
    AND refac_cct
    AND suppliers
    AND validation_ca
    AND rfa
  )
ORDER BY created_at DESC
LIMIT 1
"""

SQL_FAMILLES = """
SELECT 1
FROM edi_edivalidation
WHERE not final
  AND NOT families
ORDER BY created_at DESC
LIMIT 1
"""

SQL_INTEGRATIONS_CONTROLS = """
SELECT 1
FROM edi_ediimport ee
LEFT JOIN edi_ediimportcontrol ec
  ON ec.uuid_identification = ee.uuid_control
WHERE ec.uuid_identification IS NULL
   OR (
       COALESCE(ec.statement_with_tax, 0) <> 0 
       AND COALESCE(ec.statement_without_tax) <> 0
       AND COALESCE(ec.comment, '') = ''
   )
LIMIT 1;
"""

SQL_INTEGRATIONS = """
SELECT 1
FROM edi_ediimportcontrol ee
WHERE ee.valid IS NOT TRUE
LIMIT 1
"""

VALIDATION_SQL = """
SELECT 1
FROM edi_edivalidation
WHERE not final
  AND NOT {to_validate}
ORDER BY created_at DESC
LIMIT 1
"""

SQL_FRANCHISEUR = VALIDATION_SQL.format(to_validate="franchiseurs")

SQL_CLIENT_NEWS = VALIDATION_SQL.format(to_validate="clients_news")

SQL_ABONNEMENTS = VALIDATION_SQL.format(to_validate="subscriptions")

SQL_RFA = VALIDATION_SQL.format(to_validate="rfa")

SQL_CCT_M = VALIDATION_SQL.format(to_validate="refac_cct")

SQL_SUPPLIERS_M = VALIDATION_SQL.format(to_validate="suppliers")

SQL_CA_COSIUM = VALIDATION_SQL.format(to_validate="validation_ca")
