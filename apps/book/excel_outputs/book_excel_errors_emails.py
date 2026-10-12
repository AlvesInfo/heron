"""Module d'export du fichier excel pour le répertoire des sociétés.

Commentaire:

created at: 2022-05-12
created by: Paulo ALVES

modified at: 2022-05-12
modified by: Paulo ALVES
"""

import io

from apps.book.bin.checks import check_emails
from apps.core.excel_outputs.excel_writer import (
    f_entetes,
    f_ligne,
)
from apps.core.excel_outputs.generic_list_export import excel_list_export

COLUMNS = [
    {
        "entete": "Tiers X3",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "center",
        },
        "width": 10,
    },
    {
        "entete": "Email en erreur",
        "f_entete": {
            **f_entetes,
            "bg_color": "#dce7f5",
        },
        "f_ligne": {
            **f_ligne,
            "align": "left",
        },
        "width": 50,
    },
]


def get_rows():
    """Renvoie les résultats de la requête nécessaire à l'export excel.

    :return: resultats de la requête.
    """
    return [
        (emails_dict["third_party_num"], emails_dict["email"]) for emails_dict in check_emails()
    ]


def excel_errors_emails(file_io: io.BytesIO, file_name: str) -> dict:
    """Fonction de génération du fichier de liste des identificant pour les cct, pour un tiers X3."""
    titre = "Emails tiers en erreur dans Sage X3 (Tiers)"
    get_clean_rows = get_rows()

    return excel_list_export(
        file_io,
        file_name,
        sheet_name="Emails",
        title=titre,
        columns=COLUMNS,
        rows=get_clean_rows,
        odd_color="#E0E0E0",
    )
