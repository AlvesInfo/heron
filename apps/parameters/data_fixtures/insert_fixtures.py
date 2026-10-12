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

from apps.core.functions.functions_setups import settings
from apps.parameters.models import SalePriceCategory


def fixtures():
    """Fonction d'ajout de fixtures pour la table Nature."""
    file = Path(settings.APPS_DIR) / "parameters/data_fixtures/sal_price_category.csv"

    with file.open(encoding="utf8") as csv_file:
        csv_rows = csv.reader(csv_file, delimiter=";", quotechar='"')
        list_keys = [
            "name",
            "coefficient",
        ]

        for row in csv_rows:
            with contextlib.suppress(IntegrityError):
                SalePriceCategory.objects.update_or_create(
                    **cast("dict[str, Any]", dict(zip(list_keys, row, strict=False)))
                )


if __name__ == "__main__":
    fixtures()
