# pylint: disable=E0401
"""Module d'imports de fixtures en base au premier démarrage de l'application

Commentaire:

created at: 2022-03-03
created by: Paulo ALVES

modified at: 2022-03-03
modified by: Paulo ALVES
"""
from pathlib import Path
import csv
from django.db.utils import IntegrityError

from apps.core.functions.functions_setups import settings
from apps.parameters.models import SalePriceCategory


def fixtures():
    """Fonction d'ajout de fixtures pour la table Nature"""
    file = Path(settings.APPS_DIR) / "parameters/data_fixtures/sal_price_category.csv"

    with file.open(encoding="utf8") as csv_file:
        csv_rows = csv.reader(csv_file, delimiter=";", quotechar='"')
        list_keys = [
            "name",
            "coefficient",
        ]

        for row in csv_rows:
            try:
                SalePriceCategory.objects.update_or_create(**dict(zip(list_keys, row)))
            except IntegrityError:
                pass


if __name__ == "__main__":
    fixtures()