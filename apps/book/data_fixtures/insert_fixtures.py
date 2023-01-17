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
from apps.book.models import Society
from apps.parameters.models import Nature

def fixtures_nature():
    """Fonction d'ajout de fixtures pour la table Nature"""
    file: Path = Path(settings.APPS_DIR) / "book/data_fixtures/nature_fixtures.csv"

    with file.open(encoding="utf8") as csv_file:
        csv_rows = csv.reader(csv_file, delimiter=";", quotechar='"')
        list_keys = [
            "name",
            "to_display",
            "active",
        ]

        for row in csv_rows:
            try:
                Nature.objects.update_or_create(**dict(zip(list_keys, row)))
            except IntegrityError:
                pass


def copy_client():
    """Insertion des adresses par défault de sage X3, dans l'adresse client pour les centrales"""
    clients = Society.objects.filter(is_client=True)

    for client in clients:
        adress = client.society_society.filter(default_adress=True).first()

        if adress:
            client.immeuble = adress.line_01
            client.adresse = adress.line_02
            client.code_postal = adress.postal_code
            client.ville = adress.city
            client.pays = adress.country
            client.telephone = adress.phone_number_01
            client.mobile = adress.mobile_number
            client.email = adress.email_01
            client.save()


if __name__ == "__main__":
    fixtures_nature()
    copy_client()
