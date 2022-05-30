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
from apps.centers_clients.models import Maison, SalePriceCategory
from apps.book.models import Society
from apps.centers_clients.excel_outputs.centers_clients_columns import columns_list_maisons


def get_clean_rows():
    """Retourne les lignes à écrire"""

    query = f"""
    select 
        "maison"."cct", 
        "maison"."center_purchase",
        "maison"."sign_board", 
        "maison"."intitule", 
        "maison"."intitule_court", 
        "maison"."client_familly", 
        "maison"."code_maison", 
        "maison"."code_cosium", 
        "maison"."code_bbgr", 
        "maison"."opening_date", 
        "maison"."closing_date", 
        "maison"."signature_franchise_date", 
        "maison"."agreement_franchise_end_date", 
        "maison"."agreement_renew_date", 
        "maison"."entry_fee_amount", 
        "maison"."renew_fee_amoount", 
        "sp"."name", 
        "maison"."generic_coefficient", 
        "maison"."credit_account", 
        "maison"."debit_account", 
        "maison"."prov_account", 
        "maison"."extourne_account", 
        "maison"."sage_vat_by_default", 
        "maison"."sage_plan_code", 
        "maison"."rfa_frequence", 
        "maison"."rfa_remise", 
        "maison"."invoice_client_name", 
        "maison"."currency", 
        "maison"."language", 
        "maison"."tiers",
        "society"."immeuble",
        "society"."adresse",
        "society"."code_postal",
        "society"."ville",
        "society"."pays",
        "society"."telephone",
        "society"."mobile",
        "society"."email",
        "maison"."immeuble",
        "maison"."adresse",
        "maison"."code_postal",
        "maison"."ville",
        "maison"."pays",
        "maison"."telephone",
        "maison"."mobile",
        "maison"."email"
    from "{Maison._meta.db_table}" "maison"
    join "{Society._meta.db_table}" "society"
    on "maison"."tiers" = "society"."third_party_num"
    left join "{SalePriceCategory._meta.db_table}" "sp"
    on "maison"."uuid_sale_price_category" = "sp"."uuid_identification"
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
        LOGGER_EXPORT_EXCEL.exception(f"{file_name!r}")
        return {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}

    finally:
        excel.excel_close()

    return {"OK": f"GENERATION DU FICHIER {file_name} TERMINEE AVEC SUCCES"}
