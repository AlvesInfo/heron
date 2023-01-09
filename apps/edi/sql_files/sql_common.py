# pylint: disable=E0401,C0303
"""
FR : Module des requêtes sql de post-traitement après import des fichiers de factures fournisseur
EN : Post-processing sql module after importing supplier invoice files

Commentaire:

created at: 2022-11-27
created by: Paulo ALVES

modified at: 2022-11-27
modified by: Paulo ALVES
"""
from psycopg2 import sql

BASE_SQL_CCT = sql.SQL(
    """
    update "edi_ediimport" edi
    set "cct_uuid_identification" = cc."cct_uuid_identification"
    from (
        select
            ee."id",
            bs."cct_uuid_identification"
        from "edi_ediimport" ee
        left join (
            select
                "third_party_num",
                "uuid_identification",
                "invoice_number"
            from (
                select 
                    "third_party_num",
                    "uuid_identification",
                    "invoice_number",
                    "code_fournisseur"
                from "edi_ediimport"
                group by 
                    "third_party_num",
                    "uuid_identification",
                    "invoice_number",
                    "code_fournisseur"
            ) req
            group by 		
                "third_party_num",
                "uuid_identification",
                "invoice_number"
            having count("code_fournisseur") > 1
        ) er
        on ee."third_party_num" = er."third_party_num"
        and ee."uuid_identification" = er."uuid_identification"
        and ee."invoice_number" = er."invoice_number"
        left join (
            select
               bsp."third_party_num", 
               ccm."uuid_identification" as "cct_uuid_identification", 
               unnest(
                    string_to_array(
                        case 
                            when right("cct_identifier", 1) = '|' 
                            then left("cct_identifier", length("cct_identifier")-1) 
                            else "cct_identifier"
                        end
                        , 
                        '|'
                    )
               ) as "cct_identifier"
            from "book_suppliercct" bsp
            join "accountancy_cctsage" ac 
            on bsp."cct_uuid_identification" = ac."uuid_identification" 
            join "centers_clients_maison" ccm
            on ac."cct" = ccm."cct"
        ) bs
        on ee."third_party_num" = bs."third_party_num"
        where ee."third_party_num" = bs."third_party_num"
        and ee."code_maison" = bs."cct_identifier"
        and er."invoice_number" isnull
    ) cc
    where edi."id" = cc."id"
    and edi."cct_uuid_identification" isnull
    """
)

post_common_dict = {
    "sql_round_amount": sql.SQL(
        """
    update "edi_ediimport" "edi"
    set "net_amount" = round("net_amount"::numeric, 2):: numeric,
        "code_maison" = case 
                            when (
                                "code_maison" isnull 
                                or 
                                "code_maison" = '' 
                                or 
                                left("code_maison", 3) = 'TEL'
                            )
                            then 
                                case 
                                    when "code_fournisseur" isnull or "code_fournisseur" = ''
                                    then ''
                                    else "code_fournisseur"
                                end
                            else "code_maison"    
                        end
    where ("valid" = false or "valid" isnull)
    """
    ),
    "sql_supplier_update": sql.SQL(
        """
    update "edi_ediimport" "edi"
    set 
        "supplier_name" = "tiers"."name",
        "third_party_num" = "tiers"."third_party_num",
        "supplier" = case 
                        when "supplier" = '' or "supplier" isnull 
                        then "tiers"."name" 
                        else "supplier" 
                     end,
        "uuid_big_category" = case 
                                when "uuid_big_category" is null
                                then'f2dda460-20db-4b05-8bb8-fa80a1ff146b'::uuid
                                else "uuid_big_category"
                              end
    from (
        select 
            left("name", 35) as "name",
            "third_party_num",
            unnest(string_to_array("centers_suppliers_indentifier", '|')) as "identifier"
            from "book_society" bs
    ) "tiers"
    where ("edi"."third_party_num" is null or "edi"."third_party_num" = '')
    and "edi"."supplier_ident" = "tiers"."identifier"
    and ("edi"."valid" = false or "edi"."valid" isnull)
    """
    ),
    "sql_fac_update_except_edi": sql.SQL(
        """
update "edi_ediimport" edi
set
    "invoice_amount_without_tax" = edi_fac."invoice_amount_without_tax",
    "invoice_amount_with_tax" = edi_fac."invoice_amount_with_tax",
    "invoice_amount_tax" = (
                                edi_fac."invoice_amount_with_tax" 
                                - 
                                edi_fac."invoice_amount_without_tax"
                            ),
    "reference_article" = case 
                            when "reference_article" isnull or "reference_article" = '' 
                            then "ean_code"
                            else "reference_article"
                          end
from (
    select 
        "uuid_identification", 
        "invoice_number",
        case 
            when invoice_type = '381' 
            then -abs(sum("mont_HT"))::numeric
            else abs(sum("mont_HT"))::numeric
        end as "invoice_amount_without_tax",
        case 
            when invoice_type = '381'
            then -abs(sum("mont_TTC"))::numeric 
            else abs(sum("mont_TTC"))::numeric    
        end as "invoice_amount_with_tax"
    from (
        select 
            "uuid_identification", 
            "invoice_number", 
            "invoice_type",
            round(sum("net_amount")::numeric, 2) as "mont_HT",
            (
                round(sum("net_amount")::numeric, 2) +
                round(round(sum("net_amount")::numeric, 2) * "vat_rate"::numeric, 2)
            ) as "mont_TTC",
            "vat_rate"
        from "edi_ediimport"                
        where (
            flow_name not in ('Edi', 'Widex', 'WidexGa', 'BbgrRetours') 
            -- Spécifique pour ophtalmic qui n'additionnent pas le port avec le total 
            -- comme spécifié dans la norme edi
            or third_party_num = 'OPHT001'
        )
        and ("valid" = false or "valid" isnull)
        group by "uuid_identification", "invoice_number", "vat_rate", "invoice_type"
    ) as "tot_amount"
    group by "uuid_identification", "invoice_number", "invoice_type"
) edi_fac
where edi."uuid_identification" = edi_fac."uuid_identification"
  and edi."invoice_number" = edi_fac."invoice_number"
"""
    ),
    "sql_reference": sql.SQL(
        """
    update edi_ediimport 
    set reference_article = libelle 
    where (reference_article isnull or reference_article = '')
      and ("valid" = false or "valid" isnull)
    """
    ),
    "sql_vat": sql.SQL(
        """
        update edi_ediimport edi
           set vat = rvat.vat,
            vat_regime = rvat.vat_sheme_supplier
         from (
            select 
                rs."id" , 
                rs.vat_sheme_supplier,
                rs.vat_rate,
                rv.vat
            from (
                select 
                    ei."id", 
                    vat_sheme_supplier, 
                    vat_rate
                from edi_ediimport ei
                join book_society bs
                on ei.third_party_num = bs.third_party_num
                where vat_sheme_supplier is not null
                  and (ei."valid" = false or ei."valid" isnull)
            ) rs
            join (
                select 
                    min(r_vat.vat) as vat, r_vat.vat_regime, (r_rate.rate/100)::numeric as vat_rate
                from (
                    select 
                        avr.vat, avr.rate
                    from accountancy_vatratsage avr
                    join (
                        select 
                            av.vat, max(av.vat_start_date) as vat_start_date 
                        from accountancy_vatratsage av 
                        group by
                            av.vat
                    ) rg
                    on avr.vat = rg.vat
                    and avr.vat_start_date = rg.vat_start_date
                ) r_rate		
                join (
                    select 
                        avm.vat, avm.vat_regime
                    from accountancy_vatsage avm
                    where (vat_regime is not null and vat_regime != '')
                ) r_vat
                on r_rate.vat = r_vat.vat
                group by r_vat.vat_regime, r_rate.rate
            ) rv 
            on rs.vat_sheme_supplier = rv.vat_regime
            and rs.vat_rate = rv.vat_rate
         ) rvat
        where edi."id" = rvat."id"
        and (edi."valid" = false or edi."valid" isnull)
    """
    ),
    "sql_vat_rate": sql.SQL(
        """
    with ranks as (
        select
            uuid_identification,
            invoice_number,
            third_party_num,
            sum(net_amount::numeric)::numeric as net_amount,
            vat_rate,
            invoice_amount_without_tax,
            invoice_amount_tax,
            invoice_amount_with_tax,
            vat,
            RANK () OVER ( 
                partition by third_party_num, invoice_number
                ORDER BY third_party_num, invoice_number, vat_rate
            ) vat_rank

        from edi_ediimport ee
        where ("valid" = false or "valid" isnull)
        group by
            uuid_identification,
            third_party_num,
            invoice_number,
            vat_rate,
            invoice_amount_without_tax,
            invoice_amount_tax,
            invoice_amount_with_tax,
            third_party_num, 
            vat
    ),
    max_ranks as (
        select
            uuid_identification,
            invoice_number,
            third_party_num,
            max(vat_rank) as max_rank
        from ranks
        group by
            uuid_identification,
            invoice_number,
            third_party_num
    ),
    not_max_rank as (
        select 
            rk.uuid_identification,
            rk.third_party_num,
            rk.invoice_number,
            rk.net_amount,
            rk.vat_rate,
            rk.invoice_amount_without_tax,
            rk.invoice_amount_tax,
            rk.invoice_amount_with_tax,
            rk.vat_rank,
            rk.vat,
            mr.max_rank,
            case 
                when rk.vat_rank != mr.max_rank
                then round(rk.net_amount::numeric * rk.vat_rate::numeric, 2)::numeric 
                else 0::numeric
            end as tax,
            case 
                when rk.vat_rank != mr.max_rank
                then (
                    round(rk.net_amount::numeric * rk.vat_rate::numeric, 2)::numeric 
                    + 
                    net_amount::numeric
                )
                else 0::numeric
            end as with_tax

        from ranks rk
        join max_ranks mr
        on rk.uuid_identification = mr.uuid_identification
        and rk.third_party_num = mr.third_party_num
        and rk.invoice_number = mr.invoice_number
    ),
    yes_max_rank as (
        select 
            uuid_identification,
            third_party_num,
            invoice_number,
            vat,
            (invoice_amount_tax::numeric - sum(tax::numeric))::numeric as tax,
            (invoice_amount_with_tax::numeric - sum(with_tax::numeric))::numeric as with_tax,
            max(max_rank) as vat_rank
        from not_max_rank
        group by 
            uuid_identification,
            third_party_num,
            invoice_number,
            invoice_amount_tax,
            invoice_amount_with_tax,
            vat
    )
    insert into edi_ediimporttax
    (
        created_at,
        modified_at,
        created_by,
        uuid_identification,
        uuid_edi_import,
        third_party_num,
        invoice_number,
        total_without_tax,
        vat_rate,
        total_tax,
        total_with_tax,
        vat_rank,
        vat
    )
    select
        now() as created_at,
        now() as modified_at,
        %(automat_user)s::uuid as created_by,
        gen_random_uuid() as uuid_identification,
        nm.uuid_identification as uuid_edi_import,
        nm.third_party_num,
        nm.invoice_number,
        net_amount as total_without_tax,
        nm.vat_rate,
        case 
            when (nm.vat_rank = nm.max_rank)
            then ym.tax
            else nm.tax
        end as total_tax,
        case 
            when (nm.vat_rank = nm.max_rank)
            then ym.with_tax
            else nm.with_tax
        end as total_with_tax,
        nm.vat_rank,
        nm.vat
    from not_max_rank nm
    left join yes_max_rank ym
    on nm.uuid_identification = ym.uuid_identification
    and nm.invoice_number = ym.invoice_number
    and nm.vat_rank = ym.vat_rank
    order by 
        nm.uuid_identification,
        nm.third_party_num,
        nm.invoice_number,
        nm.vat,
        vat_rate
    """
    ),
    "sql_cct": sql.SQL(
        """
        {}
          and ("valid" = false or "valid" isnull)
    """
    ).format(BASE_SQL_CCT),
    "sql_update_articles": sql.SQL(
        """
        update "edi_ediimport" edi 
        set 
            "axe_bu_uuid" = maj."axe_bu",
            "axe_prj_uuid" = maj."axe_prj",
            "axe_pro_uuid" = maj."axe_pro",
            "axe_pys_uuid"  = maj."axe_pys",
            "axe_rfa_uuid" = maj."axe_rfa"
        from (
            select 
                ee."id", 
                aa."axe_bu", 
                aa."axe_prj", 
                aa."axe_pro", 
                aa."axe_pys", 
                aa."axe_rfa" 
            from "edi_ediimport" ee 
            join "articles_article" aa 
            on ee."reference_article" = aa."reference" 
            and ee."third_party_num" = aa."third_party_num"
            where (ee."valid" = false or ee."valid" isnull)
            and ee."axe_pro_uuid" isnull
            and aa."axe_pro" is not null
        ) maj
        where edi."id" = maj."id" 
        and (edi."valid" = false or edi."valid" isnull)
    """
    ),
    "sql_is_multi_store": sql.SQL(
        """
        update "edi_ediimport" edi
        set 
            "is_multi_store" = ms."is_multi_store"
        from (
            select
                "third_party_num",
                "uuid_identification",
                "invoice_number",
                case when count("code_fournisseur") > 1 then true else false end as "is_multi_store"
            from (
                select 
                    "third_party_num",
                    "uuid_identification",
                    "invoice_number",
                    "code_fournisseur"
                from "edi_ediimport"
                where "is_multi_store" isnull
                group by 
                    "third_party_num",
                    "uuid_identification",
                    "invoice_number",
                    "code_fournisseur"
            ) req
            group by 		
                "third_party_num",
                "uuid_identification",
                "invoice_number"
        ) ms 
        where edi."third_party_num" = ms."third_party_num"
        and edi."uuid_identification" = ms."uuid_identification"
        and edi."invoice_number" = ms."invoice_number"
        and edi."is_multi_store" isnull
        and ("valid" = false or "valid" isnull)
    """
    ),
    "sql_validate": sql.SQL(
        """
        update "edi_ediimport" edi
        set "valid"=true, "vat_rate_exists" = false, "supplier_exists" = false,
            "maison_exists" = false, "article_exists" = false, "axe_pro_supplier_exists" = false,
            "acuitis_order_date" = case 
                                    when "acuitis_order_date" = '1900-01-01' 
                                    then null
                                    else "acuitis_order_date"
                                   end,
            "delivery_date" = case 
                                when "delivery_date" = '1900-01-01' 
                                then null
                                else "delivery_date"
                               end,
            "invoice_month" = date_trunc('month', invoice_date)::date,
            "invoice_year" = date_part('year', invoice_date),
            "delete" = false,
            "unity" =  case
                            when "unity" isnull then 1 else "unity" 
                       end,
            "created_by" = %(created_by)s
        where ("valid" = false or "valid" isnull)
    """
    ),
}
