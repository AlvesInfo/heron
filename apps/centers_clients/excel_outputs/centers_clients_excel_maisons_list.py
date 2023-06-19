# pylint: disable=W0702,W1203,E1101
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
            row.get("cct__cct", ""),

            row.get("center_purchase__code", ""),
            row.get("sign_board", ""),

            row.get("intitule", ""),
            row.get("intitule_court", ""),

            row.get("client_familly", ""),

            row.get("code_maison", ""),
            row.get("code_cosium", ""),
            row.get("refrence_cosium", ""),
            row.get("code_bbgr", ""),
            row.get("opening_date", ""),
            row.get("closing_date", ""),
            row.get("signature_franchise_date", ""),
            row.get("agreement_franchise_end_date", ""),
            row.get("agreement_renew_date", ""),
            row.get("entry_fee_amount", ""),
            row.get("renew_fee_amoount", ""),

            row.get("sale_price_category__name", ""),

            row.get("generic_coefficient", ""),

            row.get("credit_account__account", ""),
            row.get("debit_account__account", ""),
            row.get("prov_account__account", ""),
            row.get("extourne_account__account", ""),
            row.get("sage_vat_by_default__vat", ""),
            row.get("sage_plan_code", ""),

            row.get("rfa_frequence", ""),
            row.get("rfa_remise", ""),
            row.get("invoice_client_name", ""),

            row.get("currency", ""),
            row.get("language", ""),

            row.get("third_party_num__third_party_num", ""),
            row.get("third_party_num__immeuble", ""),
            row.get("third_party_num__adresse", ""),
            row.get("third_party_num__code_postal", ""),
            row.get("third_party_num__ville", ""),
            row.get("third_party_num__pays__country_name", ""),
            row.get("third_party_num__telephone", ""),
            row.get("third_party_num__mobile", ""),
            row.get("third_party_num__email", ""),
            row.get("immeuble", ""),
            row.get("adresse", ""),
            row.get("code_postal", ""),
            row.get("ville", ""),

            row.get("pays__country_name", ""),

            row.get("telephone", ""),
            row.get("mobile", ""),
            row.get("email", ""),
            row.get("type_x3__name", ""),
            row.get("axe_bu__section", ""),
        )
        for row in Maison.objects.all().values(
            "cct__cct",
            "center_purchase__code",
            "sign_board",
            "intitule",
            "intitule_court",
            "client_familly",
            "code_maison",
            "code_cosium",
            "reference_cosium",
            "code_bbgr",
            "opening_date",
            "closing_date",
            "signature_franchise_date",
            "agreement_franchise_end_date",
            "agreement_renew_date",
            "entry_fee_amount",
            "renew_fee_amoount",
            "sale_price_category__name",
            "generic_coefficient",
            "credit_account__account",
            "debit_account__account",
            "prov_account__account",
            "extourne_account__account",
            "sage_vat_by_default__vat",
            "sage_plan_code",
            "rfa_frequence",
            "rfa_remise",
            "invoice_client_name",
            "currency",
            "language",
            "third_party_num__third_party_num",
            "third_party_num__immeuble",
            "third_party_num__adresse",
            "third_party_num__code_postal",
            "third_party_num__ville",
            "third_party_num__pays__country_name",
            "third_party_num__telephone",
            "third_party_num__mobile",
            "third_party_num__email",
            "immeuble",
            "adresse",
            "code_postal",
            "ville",
            "pays__country_name",
            "telephone",
            "mobile",
            "email",
            "integrable",
            "chargeable",
            "type_x3__name",
            "axe_bu__section",
        )
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
