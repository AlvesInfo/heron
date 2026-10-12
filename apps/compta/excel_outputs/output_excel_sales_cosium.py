"""Module d'export du fichier excel des ventes Cosium

Commentaire:

created at: 2023-03-07
created by: Paulo ALVES

modified at: 2023-03-07
modified by: Paulo ALVES
"""
import io

import pendulum

from apps.compta.models import VentesCosium
from apps.compta.excel_outputs.columns_excel import columns_sales_cosium
from apps.core.excel_outputs.generic_list_export import excel_list_export


def get_clean_rows(date_debut: str, date_fin: str) -> iter:
    """Retourne les lignes à écrire"""

    clean_rows = [
        (
            sale_dict.get("cct_uuid_identification__pays") or "",
            sale_dict.get("id_vente", ""),
            sale_dict.get("code_cosium", ""),
            (
                (sale_dict.get("cct_uuid_identification__cct__cct") or "")
                + " - "
                + (sale_dict.get("cct_uuid_identification__intitule") or "")
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
    columns = columns_sales_cosium

    return excel_list_export(
        file_io,
        file_name,
        sheet_name='VENTES COSIUM',
        title=titre,
        columns=columns,
        rows=get_clean_rows(date_debut, date_fin),
        orientation="landscape",
        in_memory=True,
    )
