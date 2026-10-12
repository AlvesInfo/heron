"""Module d'export du fichier excel pour les centrales Filles

Commentaire:

created at: 2022-05-12
created by: Paulo ALVES

modified at: 2022-05-12
modified by: Paulo ALVES
"""

import io

from django.db import connection
from apps.centers_purchasing.models import PrincipalCenterPurchase, ChildCenterPurchase
from apps.centers_purchasing.excel_outputs.output_excel_filles_columns import columns_list_filles
from apps.core.excel_outputs.generic_list_export import excel_list_export


class GetRows:
    """Class qui renvoie les bonnes colonnes pour le fichier Excel"""

    def __init__(self, filles: ChildCenterPurchase.objects):
        self.filles = filles

        self.query = f"""
        select
            "fille"."code", 
            "fille"."name", 
            "fille"."base_center" || ' -' || "mere"."name", 
            "fille"."generic_coefficient", 
            "fille"."legal_notice",
            "fille"."footer",
            "fille"."comment"
        from {self.filles._meta.db_table} "fille"
        join {PrincipalCenterPurchase._meta.db_table} "mere"
        on "fille"."base_center" = "mere"."code"
        """

    def get_clean_rows(self) -> iter:
        """Retourne les lignes à écrire"""
        with connection.cursor() as cursor:
            cursor.execute(self.query)
            return cursor.fetchall()


def excel_filles_list(
    file_io: io.BytesIO, file_name: str, filles: ChildCenterPurchase.objects
) -> dict:
    """Fonction de génération du fichier de liste des Centrales Filles"""
    titre_list = file_name.split("_")
    titre = " ".join(titre_list[:-4])
    columns = columns_list_filles
    get_clean_rows = GetRows(filles).get_clean_rows

    return excel_list_export(
        file_io,
        file_name,
        sheet_name=titre[:30],
        title=titre,
        columns=columns,
        rows=get_clean_rows(),
        orientation="landscape",
    )
