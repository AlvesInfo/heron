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
from apps.book.models import Nature


def fixtures_nature():
    """Fonction d'ajout de fixtures pour la table Nature"""
    file: Path = Path(settings.APPS_DIR) / "book/data_fixtures/nature_fixtures.csv"

    with file.open(encoding="utf8") as csv_file:
        csv_rows = csv.reader(csv_file, delimiter=";", quotechar='"')
        list_keys = [
            "category",
            "to_display",
            "for_contact",
        ]

        for row in csv_rows:
            try:
                Nature.objects.update_or_create(**dict(zip(list_keys, row)))
            except IntegrityError:
                pass


if __name__ == "__main__":
    fixtures_nature()
