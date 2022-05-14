# pylint: disable=W0702,W1203
"""Module d'export du fichier excel pour le répertoire des sociétés

Commentaire:

created at: 2022-05-12
created by: Paulo ALVES

modified at: 2022-05-12
modified by: Paulo ALVES
"""

import io

from heron.loggers import EXPORT_EXCEL_LOGGER
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
from apps.centers_clients.models import Maison
from apps.centers_clients.excel_outputs.centers_clients_columns import columns_list_maisons


def get_clean_rows():
    """Retourne les lignes à écrire"""

    query = f"""
    select 
        cct,
        center_purchase,
        sign_board,
        intitule,
        intitule_court,
        client_familly,
        code_maison,
        code_cosium,
        code_bbgr,
        opening_date,
        closing_date,
        signature_franchise_date,
        agreement_franchise_end_date,
        agreement_renew_date,
        entry_fee_amount,
        renew_fee_amoount,
        sale_price_category,
        generic_coefficient,
        credit_account,
        debit_account,
        prov_account,
        extourne_account,
        sage_vat_by_default,
        sage_plan_code,
        rfa_frequence,
        rfa_remise,
        invoice_client_name,
        currency,
        country,
        "language"
    from {Maison._meta.db_table}
    """
    with cnx_postgresql(CNX_STRING).cursor() as cursor:
        cursor.execute(query)
        return cursor.fetchall()


def excel_liste_maisons(
    file_io: io.BytesIO, file_name: str
) -> dict:
    """Fonction de génération du fichier de liste des maisons"""
    list_excel = [file_io, ["LISTE DES MAISONS"]]
    excel = GenericExcel(list_excel)
    columns = columns_list_maisons

    try:
        titre_page_writer(excel, 1, 0, 0, columns, "LISTE DES MAISONS")
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
