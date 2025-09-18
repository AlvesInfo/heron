# pylint: disable=E0401,R0903
"""
FR : Module des pièces comptable
EN : Accounting documents module

Commentaire:

created at: 2023-06-18
created by: Paulo ALVES

modified at: 2023-06-18
modified by: Paulo ALVES
"""
import uuid

from django.db import models

from heron.models import FlagsTable
from apps.accountancy.models import CodePlanSage


class Pieces(FlagsTable):
    """
    Table des types de pièces Sage X3
    """

    type_piece = models.CharField(unique=True, max_length=15)
    description = models.CharField(blank=True, null=True, max_length=255)
    legislation = models.ForeignKey(
        CodePlanSage,
        on_delete=models.PROTECT,
        to_field="code_plan_sage",
        related_name="piece_code_plan",
        db_column="legislation",
    )


class Journaux(FlagsTable):
    """
    Table des journaux Sage X3
    """

    journal = models.CharField(unique=True, max_length=15)
    description = models.CharField(blank=True, null=True, max_length=255)
    legislation = models.ForeignKey(
        CodePlanSage,
        on_delete=models.PROTECT,
        to_field="code_plan_sage",
        related_name="journal_code_plan",
        db_column="legislation",
    )


class Transactions(FlagsTable):
    """
    Table des transactions Sage X3
    """

    transaction = models.CharField(unique=True, max_length=15)
    description = models.CharField(blank=True, null=True, max_length=255)
    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)


class Ecritures(FlagsTable):
    """
    Table des écritures ex.: ODANA
    """

    ecriture = models.CharField(unique=True, max_length=15)
    type_x3 = models.IntegerField()
    description = models.CharField(blank=True, null=True, max_length=255)
    type_piece = models.ForeignKey(
        Pieces,
        on_delete=models.PROTECT,
        to_field="type_piece",
        related_name="type_piece_ecriture",
        db_column="type_piece",
    )
    journal = models.ForeignKey(
        Journaux,
        on_delete=models.PROTECT,
        to_field="journal",
        related_name="journal_ecriture",
        db_column="journal",
    )
    transaction = models.ForeignKey(
        Transactions,
        on_delete=models.PROTECT,
        to_field="transaction",
        related_name="transaction_ecriture",
        db_column="transaction",
    )
