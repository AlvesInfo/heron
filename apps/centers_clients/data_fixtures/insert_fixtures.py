"""Module d'imports de fixtures en base au premier démarrage de l'application.

Commentaire:

created at: 2022-03-03
created by: Paulo ALVES

modified at: 2022-03-03
modified by: Paulo ALVES
"""

import contextlib
import csv
from pathlib import Path
from typing import Any, cast

from django.db.utils import IntegrityError

from apps.centers_clients.models import ClientFamilly
from apps.core.functions.functions_setups import settings


def fixtures():
    """Fonction d'ajout de fixtures pour la table ClientFamilly."""
    file: Path = Path(settings.APPS_DIR) / "centers_clients/data_fixtures/famillies.csv"

    with file.open(encoding="utf8") as csv_file:
        csv_rows = csv.reader(csv_file, delimiter=";", quotechar='"')
        list_keys = [
            "name",
        ]

        for row in csv_rows:
            with contextlib.suppress(IntegrityError):
                ClientFamilly.objects.update_or_create(
                    **cast("dict[str, Any]", dict(zip(list_keys, row, strict=False)))
                )


if __name__ == "__main__":
    fixtures()
