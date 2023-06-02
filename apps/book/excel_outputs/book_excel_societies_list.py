# pylint: disable=W0702,W1203
"""Module d'export du fichier excel pour le répertoire des sociétés

Commentaire:

created at: 2022-05-12
created by: Paulo ALVES

modified at: 2022-05-12
modified by: Paulo ALVES
"""

import io

from heron.loggers import LOGGER_EXPORT_EXCEL
from apps.core.functions.functions_excel import GenericExcel
from apps.core.functions.functions_setups import CNX_STRING
from apps.core.functions.functions_postgresql import cnx_postgresql
from apps.core.excel_outputs.excel_writer import (
    titre_page_writer,
    output_day_writer,
    columns_headers_writer,
    sheet_formatting,
    rows_writer,
)
from apps.book.models import Society
from apps.book.excel_outputs.book_columns import SocietiesColumns


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
            "account_client_code"
            {self.tiers}
        from {self.societies._meta.db_table}
        left join "accountancy_paymentcondition" "ass"
        on "ass"."auuid" = "bs"."payment_condition_supplier" 
        left join "accountancy_paymentcondition" "acc"
        on "acc"."auuid" = "bs"."payment_condition_client"  
        {self.clause}
        """

    def get_clean_rows(self) -> iter:
        """Retourne les lignes à écrire"""
        with cnx_postgresql(CNX_STRING).cursor() as cursor:
            cursor.execute(self.query)
            return cursor.fetchall()


def excel_liste_societies(
    file_io: io.BytesIO, file_name: str, societies: Society.objects, society_type: str
) -> dict:
    """Fonction de génération du fichier de liste des Tiers, Fournisseurs, Clients"""
    titre_list = file_name.split("_")
    titre = " ".join(titre_list[:3])
    list_excel = [file_io, [titre]]
    excel = GenericExcel(list_excel)
    columns = getattr(SocietiesColumns, f"columns_list_{society_type}")
    get_clean_rows = getattr(GetRows(societies, society_type), f"get_clean_rows")

    try:
        titre_page_writer(excel, 1, 0, 0, columns, titre)
        output_day_writer(excel, 1, 1, 0)
        columns_headers_writer(excel, 1, 3, 0, columns)
        f_lignes = [dict_row.get("f_ligne") for dict_row in columns]
        f_lignes_odd = [
            {**dict_row.get("f_ligne"), **{"bg_color": "#D9D9D9"}} for dict_row in columns
        ]
        rows_writer(excel, 1, 4, 0, get_clean_rows(), f_lignes, f_lignes_odd)
        sheet_formatting(
            excel, 1, columns, {"sens": "landscape", "repeat_row": (0, 5), "fit_page": (1, 0)}
        )

    except:
        LOGGER_EXPORT_EXCEL.exception(f"{file_name!r}")
        return {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}

    finally:
        excel.excel_close()

    return {"OK": f"GENERATION DU FICHIER {file_name} TERMINEE AVEC SUCCES"}
