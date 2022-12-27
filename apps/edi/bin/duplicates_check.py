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
from django.db import connection, transaction

from apps.core.functions.functions_setups import settings


from apps.edi.sql_files.sql_checks import (
    sql_edi_import_duplicates,
    sql_edi_import_duplicates_to_delete,
    sql_invoices_duplicates,
    sql_invoices_duplicates_to_delete,
)
from apps.data_flux.models import Trace
from apps.edi.models import EdiImport


@transaction.atomic
def edi_import_duplicate_check():
    """Vérification des doublons de factures dans l'import edi (imports en doubles).
    Doublons causés par le trouple third_party_num, invoice_number, invoice_year
    """
    with connection.cursor() as cursor:
        cursor.execute(sql_edi_import_duplicates)

        for row in cursor.fetchall():
            uuid_identification, errors_array, couples = row

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
                "Ces factures ont étté supprimées de l'intégration.<br>"
            )

            trace_comment = first_comment + ",<br>".join(errors_array) + last_comment

            # On ajoute l'erreur à la trace
            trace = Trace.objects.get(uuid_identification=uuid_identification)
            trace.errors = True
            trace.comment = trace.comment + trace_comment
            trace.save()

        # on marque à delete dans la table EdiImport (edi_edi_import)
        cursor.execute(sql_edi_import_duplicates_to_delete)


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
                "</div>) a dèjà été importé.<br>"
                "Cette facture à été supprimée de l'intégration.<br>"
                if len(errors_array) == 1
                else "</div>) ont dèjà été importés.<br>"
                "Ces factures ont étté supprimées de l'intégration.<br>"
            )

            trace_comment = first_comment + ",<br>".join(errors_array) + last_comment

            # On ajoute l'erreur à la trace
            trace = Trace.objects.get(uuid_identification=uuid_identification)
            trace.errors = True
            trace.comment = trace.comment + trace_comment
            trace.save()

        # on marque à delete dans la table EdiImport (edi_edi_import)
        cursor.execute(sql_invoices_duplicates_to_delete)


if __name__ == "__main__":
    edi_import_duplicate_check()
    suppliers_invoices_duplicate_check()
    E = Trace.objects.filter(
        uuid_identification__in=EdiImport.objects.all().values("uuid_identification")
    )
    print(len(E), E)
