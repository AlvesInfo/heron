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
from apps.centers_clients.models import ClientFamilly


def fixtures():
    """Fonction d'ajout de fixtures pour la table ClientFamilly"""
    file: Path = Path(settings.APPS_DIR) / "centers_clients/data_fixtures/famillies.csv"

    with file.open(encoding="utf8") as csv_file:
        csv_rows = csv.reader(csv_file, delimiter=";", quotechar='"')
        list_keys = [
            "name",
        ]

        for row in csv_rows:
            try:
                ClientFamilly.objects.update_or_create(**dict(zip(list_keys, row)))
            except IntegrityError:
                pass


if __name__ == "__main__":
    fixtures()
