"""Module d'export du fichier excel pour le répertoire des sociétés

Commentaire:

created at: 2022-05-12
created by: Paulo ALVES

modified at: 2022-05-12
modified by: Paulo ALVES
"""

import io

from django.db import connection
from apps.book.models import Society
from apps.book.excel_outputs.book_columns import SocietiesColumns
from apps.core.excel_outputs.generic_list_export import excel_list_export


class GetRows:
    """Class pour choix des méthodes get_clean rows en fonction du type des sociétés"""

    def __init__(self, societies: Society.objects, society_type: str):
        self.societies = societies

        if society_type == "clients":
            self.clause = "where is_client = true"
            self.tiers = """
                case when is_client = true then 'X' else '' end as is_client
            """
        elif society_type == "suppliers":
            self.clause = "where is_supplier = true"
            self.tiers = """
                case when is_supplier = true then 'X' else '' end as is_supplier
            """
        else:
            self.clause = ""
            self.tiers = """
                case when is_client = true then 'X' else '' end as is_client,
                case when is_agent = true then 'X' else '' end as is_agent,
                case when is_prospect = true then 'X' else '' end as is_prospect,
                case when is_supplier = true then 'X' else '' end as is_supplier,
                case when is_various = true then 'X' else '' end as is_various,
                case when is_service_provider = true then 'X' else '' end as is_service_provider,
                case when is_transporter = true then 'X' else '' end as is_transporter,
                case when is_contractor = true then 'X' else '' end as is_contractor,
                case when is_physical_person = true then 'X' else '' end as is_physical_person
            """

        self.query = f"""
        select
            "third_party_num", 
            bs."name", 
            bs."short_name", 
            "corporate_name", 
            "invoice_entete",
            "siret_number", 
            "vat_cee_number", 
            "vat_number", 
            "client_category", 
            "supplier_category", 
            "naf_code", 
            "currency", 
            "country", 
            "language", 
            "budget_code", 
            "reviser", 
            "ass"."name" as "payment_condition_supplier", 
            "vat_sheme_supplier", 
            "account_supplier_code", 
            "acc"."name" as "payment_condition_client", 
            "vat_sheme_client", 
            "account_client_code",
            {self.tiers},
            "email_01",
            "email_02",
            "email_03",
            "email_04",
            "email_05"
        from {self.societies._meta.db_table} "bs"
        left join "accountancy_paymentcondition" "ass"
        on "ass"."auuid" = "bs"."payment_condition_supplier" 
        left join "accountancy_paymentcondition" "acc"
        on "acc"."auuid" = "bs"."payment_condition_client"  
        {self.clause}
        """

    def get_clean_rows(self) -> iter:
        """Retourne les lignes à écrire"""
        with connection.cursor() as cursor:
            cursor.execute(self.query)
            return cursor.fetchall()


def excel_liste_societies(
    file_io: io.BytesIO, file_name: str, societies: Society.objects, society_type: str
) -> dict:
    """Fonction de génération du fichier de liste des Tiers, Fournisseurs, Clients"""
    titre_list = file_name.split("_")
    titre = " ".join(titre_list[:3])
    columns = getattr(SocietiesColumns, f"columns_list_{society_type}")
    get_clean_rows = GetRows(societies, society_type).get_clean_rows

    return excel_list_export(
        file_io,
        file_name,
        sheet_name=titre,
        title=titre,
        columns=columns,
        rows=get_clean_rows(),
        orientation="landscape",
    )
