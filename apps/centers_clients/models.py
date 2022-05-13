# pylint: disable=E0401,R0903
"""
FR : Module du modèle des maisons
EN : Houses model module

Commentaire:

created at: 2022-04-07
created by: Paulo ALVES

modified at: 2022-04-07
modified by: Paulo ALVES
"""
import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from heron.models import FlagsTable

from apps.accountancy.models import (
    SectionSage
)
from apps.book.models import Society
from apps.centers_purchasing.models import Signboard
from apps.parameters.models import SalePriceCategory
from apps.countries.models import Country


class ClientFamilly(FlagsTable):
    name = models.CharField(unique=True, max_length=80)
    comment = models.CharField(null=True, blank=True, max_length=255)

    def save(self, *args, **kwargs):
        """
        FR : Avant la sauvegarde on clean les données
        EN : Before the backup we clean the data
        """
        self.name = self.name.capitalize()

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        """class Meta du modèle django"""

        ordering = ["name"]


class Maison(FlagsTable):
    cct = models.OneToOneField(
        SectionSage,
        on_delete=models.PROTECT,
        limit_choices_to={"axe": "CCT"},
        related_name="maison_cct",
        verbose_name="code maison",
        db_column="cct",
    )
    sign_board = models.ForeignKey(
        Signboard,
        on_delete=models.PROTECT,
        to_field="name",
        related_name="maison_sign_board",
        db_column="sign_board",
    )
    intitule = models.CharField(max_length=30)
    intitule_court = models.CharField(max_length=12)
    client_familly = models.ForeignKey(
        ClientFamilly,
        on_delete=models.PROTECT,
        to_field="name",
        related_name="maison_client_familly",
        db_column="client_familly",
    )
    code_maison = models.CharField(max_length=15)

    def save(self, *args, **kwargs):
        """
        FR : Avant la sauvegarde on clean les données
        EN : Before the backup we clean the data
        """

        if not self.code_maison:
            self.code_maison = self.cct__section

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code_maison} - {self.intitule}"

    class Meta:
        ordering = ["code_maison"]


class NotExportMaisonSupllier(FlagsTable):
    cct = models.ForeignKey(
        Maison,
        on_delete=models.PROTECT,
        to_field="cct",
        related_name="maison_supplier",
        verbose_name="code maison",
        db_column="cct",
    )
    society = models.ForeignKey(
        Society,
        on_delete=models.CASCADE,
        to_field="third_party_num",
        related_name="supplier_maison",
        verbose_name="Fournisseur",
        db_column="society",
    )

    def __str__(self):
        return f"{self.cct} - {self.society}"

    class Meta:
        ordering = ["cct", "society__name"]
        unique_together = (("cct", "society"),)

