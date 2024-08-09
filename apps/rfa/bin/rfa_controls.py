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

from django.db import connection, connections

from heron.settings import DEBUG


def supplier_control_validation() -> AnyStr:
    """Contrôle que tous les founrisseurs ayant des rfa soient validés"""
    sql_control = """
    select 
        "ei"."third_party_num" || ' - ' || "bs"."name"
    from "edi_ediimport" "ei" 
    left join "book_society" "bs"
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

    if DEBUG:
        with connections["heron"].cursor() as cursor:
            cursor.execute(sql_control)
            results = cursor.fetchall()
    else:
        with connection.cursor() as cursor:
            cursor.execute(sql_control)
            results = cursor.fetchall()

    if not results:
        return ""

    elif len(results) == 1:
        fournisseur = results[0][0]
        return f"Les Factures du Fournisseur {fournisseur}, ne sont validées"
    else:
        fournisseur = ", ".join([row[0] for row in results])
        return f"Les Factures des Fournisseurs {fournisseur}, ne sont validées"
