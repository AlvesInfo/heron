# pylint: disable=W0702,W1203
"""Module d'export du fichier excel pour le répertoire des sociétés

Commentaire:

created at: 2022-05-12
created by: Paulo ALVES

modified at: 2022-05-12
modified by: Paulo ALVES
"""

import io

from apps.core.functions.functions_excel import GenericExcel
from apps.book.loggers import EXPORT_EXCEL_LOGGER

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

    def __init__(self, societies: Society.objects):
        self.societies = societies

    def get_clean_rows_tiers(self) -> iter:
        """Renvoie les lignes du query_set avec les colonnes souhaitées et cleannées"""
        return (
            (
                society.third_party_num,
                society.name,
                society.short_name,
                society.corporate_name,
                society.siret_number,
                society.vat_cee_number,
                society.vat_number,
                society.naf_code,
                society.currency,
                society.language,
                society.country.country_name,
                society.reviser,
                society.client_category,
                society.supplier_category,
                society.budget_code,
                "X" if society.is_client else "",
                "X" if society.is_agent else "",
                "X" if society.is_prospect else "",
                "X" if society.is_supplier else "",
                "X" if society.is_various else "",
                "X" if society.is_service_provider else "",
                "X" if society.is_transporter else "",
                "X" if society.is_contractor else "",
                "X" if society.is_physical_person else "",
                society.payment_condition_supplier,
                society.vat_sheme_supplier,
                society.account_supplier_code,
                society.payment_condition_client,
                society.vat_sheme_client,
                society.account_client_code,
            )
            for society in self.societies
        )

    def get_clean_rows_suppliers(self) -> iter:
        """Renvoie les lignes du query_set avec les colonnes souhaitées et cleannées"""
        return (
            (
                society.third_party_num,
                society.name,
                society.short_name,
                society.corporate_name,
                society.siret_number,
                society.vat_cee_number,
                society.vat_number,
                society.naf_code,
                society.currency,
                society.language,
                society.country.country_name,
                society.reviser,
                society.supplier_category,
                society.budget_code,
                society.payment_condition_supplier,
                society.vat_sheme_supplier,
                society.account_supplier_code,
                society.supplier_identifier,
                society.invoice_supplier_name,
                society.comment,
                society.created_by,
                society.modified_by,
                society.delete_by,
                "X" if society.active else "",
                "X" if society.export else "",
            )
            for society in self.societies
        )

    def get_clean_rows_clients(self) -> iter:
        """Renvoie les lignes du query_set avec les colonnes souhaitées et cleannées"""
        return (
            (
                society.third_party_num,
                society.name,
                society.short_name,
                society.corporate_name,
                society.siret_number,
                society.vat_cee_number,
                society.vat_number,
                society.naf_code,
                society.currency,
                society.language,
                society.country.country_name,
                society.reviser,
                society.client_category,
                society.budget_code,
                society.payment_condition_client,
                society.vat_sheme_client,
                society.account_client_code,
                society.sign_board,
                society.sale_price_category,
                society.code_cct,
                society.code_cosium,
                society.code_bbgr,
                society.opening_date,
                society.closing_date,
                society.signature_franchise_date,
                society.agreement_franchise_end_date,
                society.agreement_renew_date,
                society.entry_fee_amount,
                society.renew_fee_amoount,
                society.generic_coefficient,
                society.sage_vat_by_default,
                society.sage_plan_code,
                society.rfa_frequence,
                society.rfa_remise,
                society.siren_number,
                society.credit_account,
                society.debit_account,
                society.prov_account,
                society.extourne_account,
                society.client_identifier,
                society.invoice_client_name,
                society.comment,
                society.created_by,
                society.modified_by,
                society.delete_by,
                society.active,
                society.export,
            )
            for society in self.societies
        )


def excel_liste_societies(
    file_io: io.BytesIO, file_name: str, societies: Society.objects, society_type: str
) -> dict:
    """Fonction de génération du fichier de liste des Tiers, Fournisseurs, Clients"""
    titre_list = file_name.split("_")
    titre = " ".join(titre_list[:3])
    list_excel = [file_io, [titre]]
    excel = GenericExcel(list_excel)
    columns = getattr(SocietiesColumns, f"columns_list_{society_type}")
    get_clean_rows = getattr(GetRows(societies), f"get_clean_rows_{society_type}")

    try:
        titre_page_writer(excel, 1, 0, 0, columns, titre)
        output_day_writer(excel, 1, 1, 0)
        columns_headers_writer(excel, 1, 3, 0, columns)
        f_lignes = [dict_row.get("f_ligne") for dict_row in columns]
        f_lignes_odd = [
            {**dict_row.get("f_ligne"), **{"bg_color": "#EBF1DE"}} for dict_row in columns
        ]
        rows_writer(excel, 1, 4, 0, get_clean_rows(), f_lignes, f_lignes_odd)
        sheet_formatting(
            excel, 1, columns, {"sens": "landscape", "repeat_row": (0, 5), "fit_page": (1, 0)}
        )

    except:
        EXPORT_EXCEL_LOGGER.exception(f"{file_name!r}")
        return {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}

    finally:
        excel.excel_close()

    return {"OK": f"GENERATION DU FICHIER {file_name} TERMINEE AVEC SUCCES"}
