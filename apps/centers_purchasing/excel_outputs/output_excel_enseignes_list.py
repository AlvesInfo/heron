"""Module d'export du fichier excel pour les centrales Mères

Commentaire:

created at: 2022-05-12
created by: Paulo ALVES

modified at: 2022-05-12
modified by: Paulo ALVES
"""

import io

from django.db import connection
from apps.centers_purchasing.models import Signboard
from apps.centers_purchasing.excel_outputs.output_excel_enseignes_columns import (
    columns_list_enseignes,
)
from apps.core.excel_outputs.generic_list_export import excel_list_export


class GetRows:
    """Class qui renvoie les bonnes colonnes pour le fichier Excel"""

    def __init__(self, meres: Signboard.objects):
        self.meres = meres

        self.query = f"""
        select
            "code", 
            "name", 
            "generic_coefficient", 
            "email_contact",
            "comment"
        from {self.meres._meta.db_table}
        """

    def get_clean_rows(self) -> iter:
        """Retourne les lignes à écrire"""
        with connection.cursor() as cursor:
            cursor.execute(self.query)
            return cursor.fetchall()


def excel_enseignes_list(file_io: io.BytesIO, file_name: str, meres: Signboard.objects) -> dict:
    """Fonction de génération du fichier de liste des Centrales Mère"""
    titre_list = file_name.split("_")
    titre = " ".join(titre_list[:-4])
    columns = columns_list_enseignes
    get_clean_rows = GetRows(meres).get_clean_rows

    return excel_list_export(
        file_io,
        file_name,
        sheet_name=titre[:30],
        title=titre,
        columns=columns,
        rows=get_clean_rows(),
        orientation="landscape",
    )
