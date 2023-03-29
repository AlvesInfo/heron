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

SQL_ACCOUNTS_CONTROL = """
select 
    1
from "edi_ediimport" "ee" 
left join "centers_purchasing_accountsaxeprocategory" "cpa" 
on "ee"."uuid_big_category" = "cpa"."uuid_big_category" 
and "ee"."axe_pro" = "cpa"."axe_pro"
and "ee"."vat" = "cpa"."vat"
where "cpa"."uuid_identification" isnull
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
