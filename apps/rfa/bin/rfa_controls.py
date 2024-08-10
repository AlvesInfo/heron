# pylint: disable=E0401
"""
FR : Module de contrôles de lancement des rfa
EN : RFA Launch Control Module

Commentaire:

created at: 2024-08-09
created by: Paulo ALVES

modified at: 2024-08-09
modified by: Paulo ALVES
"""
from typing import AnyStr

import pendulum
from django.db import connection
from django.db.models import Q

from apps.edi.models import EdiValidation


def supplier_control_validation() -> AnyStr:
    """Contrôle que tous les fournisseurs ayant des rfa soient validés"""
    sql_control = """
    select 
        ("ei"."third_party_num" || ' - ' || "bs"."name") as "supplier_name"
    from "edi_ediimport" "ei" 
    join "book_society" "bs"
    on "ei"."third_party_num" = "bs"."third_party_num" 
    join "rfa_supplierrate" "rs" 
    on "ei"."third_party_num" = "rs"."supplier"
    left join "edi_ediimportcontrol" "ev" 
    on "ei"."uuid_control" = "ev"."uuid_identification"
    where (
        "ev"."valid" = false 
        or 
        "ev"."valid" is null
    )
    group by 
        "ei"."third_party_num", 
        "bs"."name", 
        "ev"."valid"
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_control)
        results = cursor.fetchall()

    if not results:
        return ""

    elif len(results) == 1:
        fournisseur = results[0][0]
        return f"Les Factures du Fournisseur {fournisseur}, ne sont pas validées"
    else:
        fournisseur = ", ".join([row[0] for row in results])
        return f"Les Factures des Fournisseurs {fournisseur}, ne sont pas validées"


def supplier_control_cct() -> AnyStr:
    """Contrôle que toutes les factures des fournisseurs ayant des rfa aient des CCT"""
    sql_control = """
    select 
        ("ei"."third_party_num" || ' - ' || "bs"."name") as "supplier_name"
    from "edi_ediimport" "ei" 
    join "book_society" "bs"
    on "ei"."third_party_num" = "bs"."third_party_num" 
    join "rfa_supplierrate" "rs" 
    on "ei"."third_party_num" = "rs"."supplier"
    where "ei"."cct_uuid_identification" isnull
    group by 
        "ei"."third_party_num", 
        "bs"."name"
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_control)
        results = cursor.fetchall()

    if not results:
        return ""

    elif len(results) == 1:
        fournisseur = results[0][0]
        return f"Des CCT n'ontpas été renseignés dans les Factures du Fournisseur {fournisseur}"
    else:
        fournisseur = ", ".join([row[0] for row in results])
        return f"Des CCT n'ontpas été renseignés dans les Factures des Fournisseurs {fournisseur}"


def have_rfa_to_be_invoiced() -> AnyStr:
    """Contrôle qu'il y ait des factures de RFA à générer"""
    sql_control = """
    select 
        "ei"."third_party_num" as "signboard"
    from (
        select 
            "third_party_num",
            "code_signboard",
            "cct_uuid_identification",
            case 
                when "flow_name" = 'rfa_flow' 
                then 1 
                else 0
            end as "flow_count"
        from "edi_ediimport"
    ) "ei" 
    join "rfa_supplierrate" "rs" 
    on "ei"."third_party_num" = "rs"."supplier"
    join "rfa_signboardexclusion" "ens"
    on "ei"."code_signboard" != "ens"."signboard"
    join (
        select 
            "cen"."uuid_identification"
        from "rfa_clientexclusion" "rfa"
        join "centers_clients_maison" "cen"
        on "rfa"."cct" = "cen"."cct" 
    ) "cli"
    on "ei"."cct_uuid_identification" != "cli"."uuid_identification"
    group by "ei"."third_party_num"
    having sum("ei"."flow_count") = 0
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_control)
        results = [row[0] for row in cursor.fetchall()]

    return results


def get_axe_rfa_period():
    """Récupération de l'axe rfa du mois de la période en cours"""
    period = EdiValidation.objects.filter(Q(final=False) | Q(final__isnull=True)).first()

    if not period:
        return f"{pendulum.now().year}RFA"

    billing_period = period.billing_period

    return f"{billing_period.year}RFA_{str(billing_period.month).zfill(2)}"


def get_rfa():
    sql_wid = """
    with vat as (
        select 
            "rate"
        from "accountancy_vatratsage" "av" 
        where "vat" = '002'
        and exists (
            select 
                1 
            from "accountancy_vatratsage" "avv" 
            group by "avv"."vat" 
            having max("avv"."vat_start_date") = "av"."vat_start_date" 
                and "avv"."vat" = "av"."vat"
        )
    )
    select
        '%(uuid_identification)s' as "uuid_identification",
        '%(third_party_num)s' as "third_party_num",
        now() as "created_at",
        now() as "modified_at",
        'rfa_flow' as "flow_name",
        '%(supplier_identify)s' as "supplier_ident",
        '%(supplier)s' as "supplier",
        '%(siret_payeur)s' as "siret_payeur",
        "mm"."cct" as "code_fournisseur",
        "mm"."cct" as "code_maison",
        "mm"."intitule_court" as "maison",
        '%(invoice_number)s' as "invoice_number",
        '%(invoice_date)s' as "invoice_date",
        case 
            when sum(-"ee"."net_amount") <= 0 
            then '381' 
            else '380' 
        end as "invoice_type",
        'EUR' as "devise",
        '%(reference_article)s' as "reference_article",
        '%(libelle)s' as "libelle",
        'AA' as "famille",
        case 
            when sum(-"net_amount") <= 0
            then -1 
            else  1
        end as "qty",
        round(
            (sum("ee"."gross_unit_price") * "rs"."rfa_rate")::numeric, 
            2
        )::numeric as "gross_unit_price",
        round(
            (sum("ee"."net_unit_price") * "rs"."rfa_rate")::numeric, 
            2
        )::numeric as "net_unit_price",
        round(
            (sum(-"ee"."gross_amount") * "rs"."rfa_rate")::numeric, 
            2
        )::numeric as "gross_amount",
        round(
            (sum(-"ee"."net_amount") * "rs"."rfa_rate")::numeric, 
            2
        )::numeric as "net_amount",
        round(sum(-"ee"."net_amount"), 2)::numeric as "anet_amount",
        (select "rate" from "vat") as "vat_rate",
        round(
            ((select "rate" from "vat")::numeric/100) 
            * 
            round((sum(-"ee"."net_amount") * "rs"."rfa_rate")::numeric, 2)::numeric, 
            2
        )::numeric as "vat_amount",
        round(
            ((select "rate" from "vat")::numeric/100) 
            * 
            round(
                (sum(-"ee"."net_amount") * "rs"."rfa_rate")::numeric, 2)::numeric, 
                2
            )::numeric 
            + 
            round(
                (sum(-"ee"."net_amount") * "rs"."rfa_rate")::numeric, 
                2
        )::numeric as "amount_with_vat",
        'AA' as "axe_pro_supplier",
        '%(supplier)s' as "supplier_name",
        11 as "unit_weight",
        false as "purchase_invoice",
        true as "sale_invoice",
        0 as "item_weight"
       
    from "edi_ediimport" "ee" 
    
    join "centers_clients_maison" "mm"
    on "ee"."cct_uuid_identification" = "mm"."uuid_identification"
    
    join "rfa_sectionproexclusion" "pro"
    on "ee"."axe_pro" <> "pro"."axe_pro" 
    
    join "rfa_sectionrfa" "rfa"
    on "ee"."axe_rfa" <> "rfa"."axe_rfa" 
    
    join "rfa_signboardexclusion" "ens"
    on "ee"."code_signboard" <> "ens"."signboard"
    
    join "rfa_supplierrate" "rs" 
    on "ee"."third_party_num" = "rs"."supplier"
    
    where "ee"."third_party_num" = 'WIDE001'
    and not exists (
            select 
                1
            from "rfa_clientexclusion" "rf"
            join "centers_clients_maison" "cen"
            on "rf"."cct" = "cen"."cct"
            where "ee"."cct_uuid_identification" = "cen"."uuid_identification"
    )
    group by "mm"."cct", "mm"."intitule_court", "rs"."rfa_rate"
    having sum("net_amount") <> 0
    order by "mm"."cct"
    """
    with connection.cursor() as cursor:
        cursor.execute(sql_wid)
        return cursor.fetchall()
