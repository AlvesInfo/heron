# pylint: disable=E0401,E1101
"""
FR : Module de post-traitement pour vérification des doublons
EN : Post-processing module for checking duplicates

Commentaire:

created at: 2022-12-16
created by: Paulo ALVES

modified at: 2022-12-16
modified by: Paulo ALVES
"""
from typing import AnyStr

from django.db import connection, transaction

from apps.edi.sql_files.sql_checks import (
    sql_edi_import_duplicates,
    sql_edi_import_duplicates_delete,
    sql_invoices_duplicates,
    sql_invoices_duplicates_delete,
)
from apps.data_flux.models import Trace


@transaction.atomic
def edi_import_duplicate_check():
    """Vérification des doublons de factures dans l'import edi (imports en doubles).
    Doublons causés par le trouple third_party_num, invoice_number, invoice_year
    """
    with connection.cursor() as cursor:
        cursor.execute(sql_edi_import_duplicates)

        for row in cursor.fetchall():
            uuid_identification, errors_array, _ = row

            first_comment = (
                "L'ensemble (<div style='padding-left: 20px;'>"
                if len(errors_array) == 1
                else "Les ensembles (<div style='padding-left: 20px;'>"
            )
            last_comment = (
                "</div>) a dèjà été importé.<br>"
                "Cette facture à été supprimée de l'intégration.<br>"
                if len(errors_array) == 1
                else "</div>) ont dèjà été importés.<br>"
                "Ces factures ont été supprimées de l'intégration.<br>"
            )

            trace_comment = first_comment + ",<br>".join(errors_array) + last_comment

            # On ajoute l'erreur à la trace
            trace = Trace.objects.get(uuid_identification=uuid_identification)
            trace.errors = True
            trace.comment = trace.comment + trace_comment
            trace.save()

        # on marque à delete dans la table EdiImport (edi_edi_import)
        cursor.execute(sql_edi_import_duplicates_delete)


@transaction.atomic
def suppliers_invoices_duplicate_check():
    """Vérification des doublons de factures dans l'import edi déjà existantes,
    dans les factures définitives.
    Doublons causés par le trouple third_party_num, invoice_number, invoice_year
    """
    with connection.cursor() as cursor:
        cursor.execute(sql_invoices_duplicates)

        for row in cursor.fetchall():
            uuid_identification, errors_array, couples = row

            first_comment = (
                "L'ensemble (<div style='padding-left: 20px;'>"
                if len(errors_array) == 1
                else "Les ensembles (<div style='padding-left: 20px;'>"
            )
            last_comment = (
                "</div>) a dèjà été factureé.<br>"
                "Cette facture à été supprimée de l'intégration.<br>"
                if len(errors_array) == 1
                else "</div>) ont dèjà été facturées.<br>"
                "Ces factures ont été supprimées de l'intégration.<br>"
            )

            trace_comment = first_comment + ",<br>".join(errors_array) + last_comment

            # On ajoute l'erreur à la trace
            try:
                trace = Trace.objects.get(uuid_identification=uuid_identification)
                trace.errors = True
                trace.comment = trace.comment + trace_comment
                trace.save()
            except Trace.DoesNotExist:
                pass

        # on marque à delete dans la table EdiImport (edi_edi_import)
        cursor.execute(sql_invoices_duplicates_delete)


def check_invoice_exists(third_party_num: AnyStr, invoice_number: AnyStr, invoice_year: int):
    """Vérification des doublons dans edi_ediimport union all invoices_invoice
    Doublons causés par le trouple third_party_num, invoice_number, invoice_year
    :param third_party_num: Tiers X3
    :param invoice_number: N° de la facture
    :param invoice_year: Année de la facture
    :return: True/False
    """
    with connection.cursor() as cursor:
        sql_check_invoice_exist = """
        select
            1 
        from (
            (
                select 
                    1 as "nbre"
                from "edi_ediimport" "ee" 
                where "ee"."third_party_num" = %(third_party_num)s
                and "ee"."invoice_number" = %(invoice_number)s
                and "ee"."invoice_year" = %(invoice_year)s
                limit 1
            )
            union all
            (
                select 
                    1 as "nbre"
                from "invoices_invoicecommondetails" "ii" 
                where "ii"."third_party_num"= %(third_party_num)s
                and "ii"."invoice_number" = %(invoice_number)s
                and "ii"."invoice_year" = %(invoice_year)s           
                -- Ajouter car si l'on importe après une première génération 
                -- cela efface toute la table
                and "ii"."final"= true
                limit 1
            )
        ) "doublons"
        """
        cursor.execute(
            sql_check_invoice_exist,
            {
                "third_party_num": third_party_num,
                "invoice_number": invoice_number,
                "invoice_year": invoice_year,
            },
        )

        if cursor.fetchall():
            return True

        return False
