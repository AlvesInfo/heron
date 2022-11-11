# pylint: disable=E0401,R0903
"""
FR : Module de préparation à l'import des factures fournisseurs
EN : Preparation module for importing supplier invoices

Commentaire:

created at: 2021-11-07
created by: Paulo ALVES

modified at: 2021-11-07
modified by: Paulo ALVES
"""
import uuid

from django.db import models
from heron.models import FlagsTable


class EdiImportControl(FlagsTable):
    """Table des saisies de relevé des fournisseurs, pour contrôle des intégrations"""

    statement_without_tax = models.DecimalField(
        null=True, max_digits=20, decimal_places=5, default=0, verbose_name="MOA avec 125"
    )
    statement_amount_tax = models.DecimalField(
        null=True, max_digits=20, decimal_places=5, default=0, verbose_name="MOA avec 150"
    )
    statement_amount_with_tax = models.DecimalField(
        null=True, max_digits=20, decimal_places=5, default=0, verbose_name="MOA avec 128"
    )

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
