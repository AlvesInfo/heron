# pylint: disable=E0401
"""
FR : Module des utilitaires pour la validation
EN : Utilities Modul for validation

Commentaire:

created at: 2023-25-25
created by: Paulo ALVES

modified at: 2023-25-25
modified by: Paulo ALVES
"""
from typing import AnyStr
from uuid import uuid4
from copy import deepcopy

from django.db import connection
from django.db.models import Q, Count

from apps.edi.models import EdiImport
from apps.data_flux.models import Trace


def set_is_multi_store(third_party_num: AnyStr, invoice_number: AnyStr, invoice_year: int):
    """
    Update des lignes de factures edi_ediimport, sur le champ multistore
    :param third_party_num: Tiers X3
    :param invoice_number: N° de Facture
    :param invoice_year: Année de facture
    :return:
    """
    with connection.cursor() as cursor:
        sql_update = """
        update "edi_ediimport" "edi"
        set "is_multi_store"= case 
                                when "req"."nbre" = 1 
                                then false
                                else true
                              end
        from (
            select 
                sum("nbre") as "nbre",
                "third_party_num",
                "invoice_number",
                "invoice_year"
            from (
                select 
                    1 as nbre, 
                    "third_party_num",
                    "invoice_number",
                    "invoice_year"
                from "edi_ediimport" 
                where"third_party_num" = %(third_party_num)s
                  and "invoice_number" = %(invoice_number)s
                  and "invoice_year" = %(invoice_year)s
                group by "cct_uuid_identification",
                         "third_party_num",
                         "invoice_number",
                         "invoice_year"
            ) "regroup"
            group by "third_party_num",
                     "invoice_number",
                     "invoice_year"
        ) "req"
        where "edi"."third_party_num" = "req"."third_party_num"
          and "edi"."invoice_number" = "req"."invoice_number"
          and "edi"."invoice_year" = "req"."invoice_year"
        """
        cursor.execute(
            sql_update,
            {
                "third_party_num": third_party_num,
                "invoice_number": invoice_number,
                "invoice_year": invoice_year,
            },
        )


def verify_supplier_ident():
    """Vérification qu'il ne manque pas les identifiants fournisseurs dans les imports edi.
    S'il y en a qui n'existent pas alors on supprime la trace et on en crée une nouvelle
    et les lignes dans edi import sont supprimées"""
    rows_list = (
        EdiImport.objects.filter(
            Q(third_party_num="")
            | Q(third_party_num__isnull=True)
            | Q(supplier_ident="")
            | Q(supplier_ident__isnull=True)
        )
        .values("uuid_identification", "third_party_num", "flow_name", "supplier", "supplier_ident")
        .annotate(dcount=Count("uuid_identification"))
    )

    for row_dict in rows_list:
        uuid_edi_import = str(row_dict.get("uuid_identification"))
        trace = Trace.objects.get(uuid_identification=uuid_edi_import)
        new_trace = deepcopy(trace)
        new_trace.pk = None
        new_trace.uuid_identification = uuid4()
        new_trace.errors = True
        new_trace.invoices = True
        new_trace.comment = (
            f"Le fichier {trace.file_name}, "
            "ne contenait pas l'identifiant du fournisseur l'import' a été effacé"
        )
        new_trace.save()
        EdiImport.objects.filter(uuid_identification=uuid_edi_import).delete()


def flag_invoices():
    """Falg de la colonne invoices à True, pour les éléments qui auraient eu une erreur"""
    sql_update = """
    update "data_flux_trace" "dt"
    set "invoices" = true 
    from (
        select 
            "uuid_identification"
        from "edi_ediimport" "ee"
        group by "uuid_identification"
    ) "req"
    where ("invoices" = false or "invoices" isnull)
    and "dt"."uuid_identification" = "req"."uuid_identification"
    """
    with connection.cursor() as cursor:
        cursor.execute(sql_update)
