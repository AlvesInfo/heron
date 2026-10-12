"""FR : Module de contrôles de lancement des rfa.

EN : RFA Launch Control Module.

Commentaire:

created at: 2024-08-09
created by: Paulo ALVES

modified at: 2024-08-09
modified by: Paulo ALVES
"""

import pendulum
from django.db import connection
from django.db.models import Q

from apps.edi.models import EdiValidation


def supplier_control_validation() -> str:
    """Contrôle que tous les fournisseurs ayant des rfa soient validés."""
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

    if len(results) == 1:
        fournisseur = results[0][0]
        return f"Les Factures du Fournisseur {fournisseur}, ne sont pas validées"
    fournisseur = ", ".join([row[0] for row in results])
    return f"Les Factures des Fournisseurs {fournisseur}, ne sont pas validées"


def supplier_control_cct() -> str:
    """Contrôle que toutes les factures des fournisseurs ayant des rfa aient des CCT."""
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

    if len(results) == 1:
        fournisseur = results[0][0]
        return f"Des CCT n'ont pas été renseignés dans les Factures du Fournisseur {fournisseur}"
    fournisseur = ", ".join([row[0] for row in results])
    return f"Des CCT n'ont pas été renseignés dans les Factures des Fournisseurs {fournisseur}"


def have_rfa_to_be_invoiced() -> list:
    """Contrôle qu'il y ait des factures de RFA à générer : fournisseurs ayant un taux de RFA,.

    des factures sur une maison et un axe RFA retenus, hors exclusions (enseigne, client,
    client/fournisseur, axe PRO), et dont les RFA du mois ne sont pas déjà générées.
    Les filtres sont les mêmes que ceux de l'insertion (SQL_RFA_INSERTION).
    """
    sql_control = """
    select
        "ee"."third_party_num" as "supplier"
    from "edi_ediimport" "ee"
    join "centers_clients_maison" "mm"
    on "ee"."cct_uuid_identification" = "mm"."uuid_identification"
    join "rfa_supplierrate" "rs"
    on "ee"."third_party_num" = "rs"."supplier"
    where "ee"."flow_name" <> 'rfa_flow'
    and not exists (
        select 1
        from "rfa_clientexclusion" "rf"
        join "centers_clients_maison" "cen"
        on "rf"."cct" = "cen"."cct"
        where "ee"."cct_uuid_identification" = "cen"."uuid_identification"
    )
    and not exists (
        select 1
        from "rfa_clientsupplierexclusion" "rcs"
        where "ee"."third_party_num" = "rcs"."supplier"
          and "ee"."cct_uuid_identification" = "rcs"."maison_uuid"
    )
    and not exists (
        select 1
        from "rfa_sectionproexclusion" "pro"
        where "ee"."axe_pro" = "pro"."axe_pro"
    )
    and exists (
        select 1
        from "rfa_sectionrfa" "rfa"
        where "ee"."axe_rfa" = "rfa"."axe_rfa"
    )
    and not exists (
        select 1
        from "rfa_signboardexclusion" "ens"
        where "ee"."code_signboard" = "ens"."signboard"
    )
    and not exists (
        select 1
        from "edi_ediimport" "gen"
        where "gen"."third_party_num" = "ee"."third_party_num"
          and "gen"."flow_name" = 'rfa_flow'
    )
    group by "ee"."third_party_num"
    order by "ee"."third_party_num"
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_control)
        return [row[0] for row in cursor.fetchall()]


def get_axe_rfa_period():
    """Récupération de l'axe rfa du mois de la période en cours."""
    period = EdiValidation.objects.filter(Q(final=False) | Q(final__isnull=True)).first()

    if not period:
        return f"{pendulum.now().year}RFA"

    billing_period = period.billing_period

    return f"{billing_period.year}RFA_{str(billing_period.month).zfill(2)}"
