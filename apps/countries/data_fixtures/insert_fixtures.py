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

from django.conf import settings

from django.db.utils import IntegrityError

from apps.countries.models import Country


def validate_boolean(value):
    """Parsing pour les valeurs qui doivent être booléennes en base
    :param value: valeur à parser
    :return: valeur booléenne associée
    """
    if isinstance(value, str):
        if value.lower() in {"0", "false", "no", "n", "non"}:
            return False
        if value.lower() in {"1", "true", "yes", "y", "o", "oui"}:
            return True
    if isinstance(value, (int, float)):
        return value != 0
    return value


def fixtures_pays():
    """Fonction d'ajout de fixtures pour la table Country"""
    file: Path = Path(settings.APPS_DIR) / "countries/data_fixtures/pays_fixtures.csv"

    with file.open(encoding="utf8") as csv_file:
        csv_rows: csv = csv.reader(csv_file, delimiter=";", quotechar='"')
        list_keys: list = [
            "country_iso",
            "country_iso_3",
            "country_insee",
            "country_iso_num",
            "country_deb",
            "country",
            "currency_iso",
            "lang_iso",
            "cee",
            "country_vat_num",
        ]

        for row in csv_rows:
            try:
                row[6] = validate_boolean(row[6])
                Country.objects.update_or_create(**dict(zip(list_keys, row)))
            except IntegrityError:
                pass


if __name__ == "__main__":
    fixtures_pays()
