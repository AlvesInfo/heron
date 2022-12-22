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

    return [
        (
            str(row.cct),
            str(row.center_purchase),
            str(row.sign_board),
            row.intitule,
            row.intitule_court,
            str(row.client_familly),
            row.code_maison,
            row.code_cosium,
            row.code_bbgr,
            row.opening_date,
            row.closing_date,
            row.signature_franchise_date,
            row.agreement_franchise_end_date,
            row.agreement_renew_date,
            row.entry_fee_amount,
            row.renew_fee_amoount,
            str(row.sale_price_category),
            row.generic_coefficient,
            str(row.credit_account),
            str(row.debit_account),
            str(row.prov_account),
            str(row.extourne_account),
            str(row.sage_vat_by_default),
            str(row.sage_plan_code),
            row.rfa_frequence,
            row.rfa_remise,
            row.invoice_client_name,
            str(row.currency),
            str(row.language),
            row.tiers.third_party_num,
            row.tiers.immeuble,
            row.tiers.adresse,
            row.tiers.code_postal,
            row.tiers.ville,
            str(row.tiers.pays),
            row.tiers.telephone,
            row.tiers.mobile,
            row.tiers.email,
            row.immeuble,
            row.adresse,
            row.code_postal,
            row.ville,
            str(row.pays),
            row.telephone,
            row.mobile,
            row.email,
        )
        for row in Maison.objects.all()
    ]


def excel_liste_maisons(file_io: io.BytesIO, file_name: str) -> dict:
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
