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
select 
    1
from edi_ediimport ee 
left join articles_article aa 
on aa.reference = ee.reference_article 
left join articles_articleaccount aa2 
on aa2.article = aa.uuid_identification 
and aa2.vat = ee.vat 
where aa2.article isnull
limit 1
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
