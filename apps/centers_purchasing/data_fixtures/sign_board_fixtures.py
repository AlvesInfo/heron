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
from apps.centers_purchasing.models import PrincipalCenterPurchase, ChildCenterPurchase, Signboard
from apps.countries.models import Country
from apps.parameters.models import SalePriceCategory


def fixtures():
    """Fonction d'ajout de fixtures pour la table Nature"""
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
                PrincipalCenterPurchase.objects.update_or_create(**dict(zip(list_keys, row)))
            except IntegrityError as error:
                print(error)

    with file_childs.open(encoding="utf8") as csv_file:
        csv_rows = csv.reader(csv_file, delimiter=";", quotechar='"')

        for row in csv_rows:
            try:
                code, base_center, name, generic_coefficient = row
                base_center = PrincipalCenterPurchase.objects.get(code=base_center)
                ChildCenterPurchase.objects.update_or_create(
                    code=code,
                    base_center=base_center,
                    name=name,
                    generic_coefficient=generic_coefficient,
                )
            except IntegrityError as error:
                print(error)

    with file_enseigne.open(encoding="utf8") as csv_file:
        csv_rows = csv.reader(csv_file, delimiter=";", quotechar='"')

        for row in csv_rows:
            code, sale_price_category, name, generic_coefficient, language = row
            sale_price_category = SalePriceCategory.objects.get(name=sale_price_category)
            language = Country.objects.get(country=language)

            try:
                Signboard.objects.update_or_create(
                    code=code,
                    sale_price_category=sale_price_category,
                    name=name,
                    generic_coefficient=generic_coefficient,
                    language=language,
                )
            except IntegrityError as error:
                print(error)


if __name__ == "__main__":
    fixtures()
