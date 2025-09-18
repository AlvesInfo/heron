# pylint: disable=W0702,W1203,E0401,E1101
"""Module d'export du fichier excel des ventes Cosium

Commentaire:

created at: 2023-03-07
created by: Paulo ALVES

modified at: 2023-03-07
modified by: Paulo ALVES
"""
import io

import pendulum

from heron.loggers import LOGGER_EXPORT_EXCEL
from apps.core.functions.functions_excel import GenericExcel
from apps.core.excel_outputs.excel_writer import (
    titre_page_writer,
    output_day_writer,
    columns_headers_writer,
    sheet_formatting,
    rows_writer,
)
from apps.compta.models import VentesCosium
from apps.compta.excel_outputs.columns_excel import columns_sales_cosium


def get_clean_rows(date_debut: str, date_fin: str) -> iter:
    """Retourne les lignes à écrire"""

    clean_rows = [
        (
            sale_dict.get("cct_uuid_identification__pays", ""),
            sale_dict.get("id_vente", ""),
            sale_dict.get("code_cosium", ""),
            (
                sale_dict.get("cct_uuid_identification__cct__cct", "")
                + " - "
                + sale_dict.get("cct_uuid_identification__intitule", "")
            ),
            sale_dict.get("famille_cosium", ""),
            sale_dict.get("rayon_cosium", ""),
            sale_dict.get("date_vente", ""),
            sale_dict.get("qte_vente", ""),
            sale_dict.get("pv_net_unitaire", ""),
            sale_dict.get("ca_ht_avt_remise", ""),
            sale_dict.get("ca_ht_ap_remise", ""),
            sale_dict.get("taux_change_moyen", ""),
            sale_dict.get("ca_ht_avt_remise_eur", ""),
            sale_dict.get("ca_ht_ap_remise_eur", ""),
            sale_dict.get("maj_stock", ""),
        )
        for sale_dict in VentesCosium.objects.filter(date_vente__range=(date_debut, date_fin))
        .values(
            "cct_uuid_identification__pays",
            "id_vente",
            "code_cosium",
            "famille_cosium",
            "rayon_cosium",
            "date_vente",
            "qte_vente",
            "pv_net_unitaire",
            "ca_ht_avt_remise",
            "ca_ht_ap_remise",
            "taux_change_moyen",
            "ca_ht_avt_remise_eur",
            "ca_ht_ap_remise_eur",
            "maj_stock",
            "cct_uuid_identification__cct__cct",
            "cct_uuid_identification__intitule",
        )
        .order_by(
            "cct_uuid_identification__pays", "cct_uuid_identification__cct__cct", "date_vente"
        )
    ]

    return clean_rows


def excel_sales_cosium(file_io: io.BytesIO, file_name: str, dte_d: str, dte_f: str) -> dict:
    """Fonction de génération du fichier de liste des ventes Cosium"""
    date_debut = pendulum.parse(dte_d)
    date_debut_texte = date_debut.format("DD/MM/YYYY", locale="fr")
    date_fin = pendulum.parse(dte_f)
    date_fin_texte = date_fin.format("DD/MM/YYYY", locale="fr")
    titre = f"VENTES COSIUM DU {date_debut_texte} AU {date_fin_texte}"
    list_excel = [file_io, ["VENTES COSIUM"]]
    excel = GenericExcel(list_excel, in_memory=True)
    columns = columns_sales_cosium

    try:
        titre_page_writer(excel, 1, 0, 0, columns, titre)
        output_day_writer(excel, 1, 1, 0)
        columns_headers_writer(excel, 1, 3, 0, columns)
        f_lignes = [dict_row.get("f_ligne") for dict_row in columns]
        f_lignes_odd = [
            {**dict_row.get("f_ligne"), **{"bg_color": "#D9D9D9"}} for dict_row in columns
        ]
        rows_writer(excel, 1, 4, 0, get_clean_rows(date_debut, date_fin), f_lignes, f_lignes_odd)
        sheet_formatting(
            excel, 1, columns, {"sens": "landscape", "repeat_row": (0, 5), "fit_page": (1, 0)}
        )

    except:
        LOGGER_EXPORT_EXCEL.exception(f"{file_name!r}")
        return {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}

    finally:
        excel.excel_close()

    return {"OK": f"GENERATION DU FICHIER {file_name} TERMINEE AVEC SUCCES"}
