# pylint: disable=E0401
"""
FR : Module de post-traitement pour vérification des doublons
EN : Post-processing module for checking duplicates

Commentaire:

created at: 2022-12-16
created by: Paulo ALVES

modified at: 2022-12-16
modified by: Paulo ALVES
"""
from apps.core.functions.functions_setups import settings
from django.db import connection, transaction

from apps.edi.sql_files.sql_checks import sql_edi_import_duplicates, sql_invoices_duplicates
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
            uuid_identification, third_party_num, invoice_number, invoice_year = row
            # On ajoute l'erreur à la trace
            trace = Trace.objects.get(uuid_identification=uuid_identification)
            trace.errors = True
            trace.comment = (
                trace.comment + f"Le trouple(\n"
                f"\ttiers X3   : '{third_party_num}', \n"
                f"\tn° fac.    : '{invoice_number}', \n"
                f"\tannée fac. : '{invoice_year}'\n"
                f") a dèjà été importé,\n"
                "Cette facture à été supprimée de l'intégration."
            )
            trace.save()

            # on marque à delete dans la table EdiImport (edi_edi_import)
            EdiImport.objects.filter(
                uuid_identification=uuid_identification,
                third_party_num=third_party_num,
                invoice_number=invoice_number,
                invoice_year=invoice_year,
            ).update(delete=True)


def suppliers_invoices_duplicate_check():
    """Vérification des doublons de factures dans l'import edi déjà existantes,
    dans les factures définitives.
    Doublons causés par le trouple third_party_num, invoice_number, invoice_year
    """
    with connection.cursor() as cursor:
        cursor.execute(sql_invoices_duplicates)

        for row in cursor.fetchall():
            uuid_identification, third_party_num, invoice_number, invoice_year = row
            # On ajoute l'erreur à la trace
            trace = Trace.objects.get(uuid_identification=uuid_identification)
            trace.errors = True
            trace.comment = (
                trace.comment + f"Le trouple(\n"
                f"\ttiers X3   : '{third_party_num}', \n"
                f"\tn° fac.    : '{invoice_number}', \n"
                f" \tannée fac. : '{invoice_year}'\n"
                f") a dèjà été traité et validé,\n"
                "Cette facture à été supprimée de l'intégration."
            )
            trace.save()

            # on marque à delete dans la table EdiImport (edi_edi_import)
            EdiImport.objects.filter(
                uuid_identification=uuid_identification,
                third_party_num=third_party_num,
                invoice_number=invoice_number,
                invoice_year=invoice_year,
            ).update(delete=True)


if __name__ == "__main__":
    edi_import_duplicate_check()
    suppliers_invoices_duplicate_check()
    E = Trace.objects.filter(
        uuid_identification__in=EdiImport.objects.all().values("uuid_identification")
    )
    print(len(E), E)
