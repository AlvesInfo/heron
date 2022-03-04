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

from apps.periods.models import Periode


def fixtures_periodes():
    """Fonction d'ajout de fixtures pour la table Périodes"""
    file = Path(settings.APPS_DIR) / "periods/data_fixtures/periodes_fixtures.csv"

    with file.open(encoding="utf8") as csv_file:
        csv_rows = csv.reader(csv_file, delimiter=";", quotechar='"')
        list_keys = ["annee", "type_periode", "libelle", "date_debut", "date_fin"]

        for row in csv_rows:
            try:
                Periode.objects.update_or_create(**dict(zip(list_keys, row[:6])))
            except IntegrityError:
                pass


if __name__ == "__main__":
    fixtures_periodes()
