"""Module d'imports de fixtures en base au premier démarrage de l'application.

Commentaire:

created at: 2022-03-03
created by: Paulo ALVES

modified at: 2022-03-03
modified by: Paulo ALVES
"""

import csv
from pathlib import Path
from typing import Any, cast

from django.db.utils import IntegrityError

from apps.centers_purchasing.models import ChildCenterPurchase, PrincipalCenterPurchase, Signboard
from apps.core.functions.functions_setups import settings
from apps.parameters.models import SalePriceCategory
from heron.loggers import LOGGER_IMPORT


def fixtures():
    """Fonction d'ajout de fixtures pour la table Nature."""
    file_mere = Path(settings.APPS_DIR) / "centers_purchasing/data_fixtures/centrale_mere.csv"
    file_childs = Path(settings.APPS_DIR) / "centers_purchasing/data_fixtures/centrales_filles.csv"
    file_enseigne = Path(settings.APPS_DIR) / "centers_purchasing/data_fixtures/enseignes.csv"

    with file_mere.open(encoding="utf8") as csv_file:
        csv_rows = csv.reader(csv_file, delimiter=";", quotechar='"')
        list_keys = [
            "code",
            "name",
            "generic_coefficient",
        ]

        for row in csv_rows:
            try:
                PrincipalCenterPurchase.objects.update_or_create(
                    **cast("dict[str, Any]", dict(zip(list_keys, row, strict=False)))
                )
            except IntegrityError:
                LOGGER_IMPORT.exception("Erreur d'intégrité à l'insertion des fixtures")

    with file_childs.open(encoding="utf8") as csv_file:
        csv_rows = csv.reader(csv_file, delimiter=";", quotechar='"')

        for row in csv_rows:
            try:
                code, base_center, name, generic_coefficient = row
                base_center_obj = PrincipalCenterPurchase.objects.get(code=base_center)
                ChildCenterPurchase.objects.update_or_create(
                    code=code,
                    base_center=base_center_obj,
                    name=name,
                    generic_coefficient=generic_coefficient,
                )
            except IntegrityError:
                LOGGER_IMPORT.exception("Erreur d'intégrité à l'insertion des fixtures")

    with file_enseigne.open(encoding="utf8") as csv_file:
        csv_rows = csv.reader(csv_file, delimiter=";", quotechar='"')

        for row in csv_rows:
            # La cinquième colonne (langue) n'a pas de champ dans le modèle Signboard
            code, sale_price_category, name, generic_coefficient, *_ = row
            sale_price_category_obj = SalePriceCategory.objects.get(name=sale_price_category)

            try:
                Signboard.objects.update_or_create(
                    code=code,
                    sale_price_category=sale_price_category_obj,
                    name=name,
                    generic_coefficient=generic_coefficient,
                )
            except IntegrityError:
                LOGGER_IMPORT.exception("Erreur d'intégrité à l'insertion des fixtures")


if __name__ == "__main__":
    fixtures()
