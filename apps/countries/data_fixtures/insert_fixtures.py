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
    """Fonction d'ajout de fixtures pour la table Country, depuis pays_fixtures.csv
    (nom ; code ; sigle devise ; nom devise ; code devise ; indicatif ; cee ; rang devise).
    Un pays déjà présent n'est pas modifié ; la première ligne d'un code répété est conservée.
    """
    file: Path = Path(settings.APPS_DIR) / "countries/data_fixtures/pays_fixtures.csv"

    with file.open(encoding="utf8") as csv_file:
        csv_rows = csv.reader(csv_file, delimiter=";", quotechar='"')

        for row in csv_rows:
            if not row:
                continue

            name, code, sigle, currency_name, currency_iso, indicatif, cee, _ = (
                value.strip() for value in row
            )
            Country.objects.get_or_create(
                country=code,
                defaults={
                    "country_name": name,
                    "currency_sigle": sigle or None,
                    "currency_name": currency_name or None,
                    "currency_iso": currency_iso or None,
                    "phone_indicatif": indicatif or None,
                    "cee": validate_boolean(cee),
                },
            )


if __name__ == "__main__":
    fixtures_pays()
