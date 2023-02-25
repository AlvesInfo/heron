# pylint: disable=E0401,R0903,E1101
"""
FR : Module du modèle de répertoire, des fournisseurs et clients. Les modèles peuvent être liés
     aux modèles Sage de l'application Accountancy, et mis à jours depuis Sage X3
EN : Directory model module, suppliers and customers. Models can be linked
     to the Sage models of the Accountancy application, and updated from Sage X3

Commentaire:

created at: 2021-11-07
created by: Paulo ALVES

modified at: 2021-11-07
modified by: Paulo ALVES
"""
import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.shortcuts import reverse
from apps.parameters.models import FlagsTable, Category, SubCategory
from apps.accountancy.models import SectionSage, CctSage


class StatFamillyAxes(FlagsTable):
    """Nommage des statistiques pour réemploi éventuel"""

    name = models.CharField(unique=True, max_length=35)
    description = models.CharField(null=True, blank=True, max_length=80)

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)


class SupplierFamilyAxes(FlagsTable):
    """Statistiques EDI, pour mettre par défaut les axes_pro, grandes cétagories, rubriques presta,
    poids, unités et code douaniers quand un nouvel article se présente
    """

    class Unit(models.TextChoices):
        """Unit choices"""

        GR = "Grammes", _("Grammes")
        KG = "Kg", _("Kilo")
        U = "U", _("Unité")
        BOITE = "Bte", _("Boite")
        ML = "M", _("Mètre")

    stat_name = models.ForeignKey(
        StatFamillyAxes,
        on_delete=models.PROTECT,
        to_field="name",
        related_name="stat_axes",
        db_column="stat_name",
    )
    # Colonne de la table (edi_ediimport) d'intégration des factures à prende en compte
    invoice_column = models.CharField(default="famille", max_length=150)
    regex_bool = models.BooleanField(default=False)
    regex_match = models.CharField(max_length=150)
    expected_result = models.CharField(max_length=150)
    axe_pro = models.ForeignKey(
        SectionSage,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        limit_choices_to={"axe": "PRO"},
        related_name="family_axe_pro",
        db_column="axe_pro",
        null=True,
    )
    description = models.CharField(null=True, blank=True, max_length=80)
    norme = models.CharField(null=True, blank=True, max_length=80)
    comment = models.TextField(null=True, blank=True)
    big_category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        related_name="supplier_family_big_category",
        db_column="uuid_big_category",
        null=True,
    )
    sub_category = models.ForeignKey(
        SubCategory,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        related_name="supplier_family_sub_category",
        db_column="uuid_sub_big_category",
        null=True,
    )
    item_weight = models.DecimalField(max_digits=20, decimal_places=5, default=0)
    unit_weight = models.CharField(
        null=True, blank=True, max_length=20, choices=Unit.choices, default=Unit.GR
    )
    customs_code = models.CharField(null=True, blank=True, max_length=35)

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{self.stat_name} - {self.invoice_column} - {self.regex_match}"

    class Meta:
        """class Meta du modèle django"""

        ordering = ["stat_name", "invoice_column", "regex_match"]
        unique_together = (("stat_name", "invoice_column", "regex_match", "expected_result"),)
        indexes = [
            models.Index(fields=["stat_name"]),
            models.Index(fields=["invoice_column"]),
            models.Index(fields=["regex_match"]),
            models.Index(fields=["customs_code"]),
            models.Index(fields=["expected_result"]),
            models.Index(fields=["stat_name", "invoice_column", "regex_match", "expected_result"]),
        ]


class SupplierCct(FlagsTable):
    """Identificant des CCT pour chaque Fournisseur
    FR: Table de couples Fournisseur/Identifiant CCT
    EN: Table of Supplier/CCT Identifier pairs
    """

    third_party_num = models.ForeignKey(
        "Society",
        on_delete=models.CASCADE,
        to_field="third_party_num",
        related_name="book_supplier",
        db_column="third_party_num",
        verbose_name="Tiers",
    )
    cct_uuid_identification = models.ForeignKey(
        CctSage,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        related_name="book_cct",
        db_column="cct_uuid_identification",
        verbose_name="CCT x3",
    )
    cct_identifier = models.CharField(
        null=True, blank=True, max_length=150, verbose_name="identifiant cct"
    )

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return (
            f"{self.third_party_num} - {self.cct_uuid_identification.name} - {self.cct_identifier}"
        )

    def get_absolute_url(self):
        """Retourne l'url en cas de success create, update ou delete"""
        return reverse("book:society_update", args=[self.third_party_num.pk])

    class Meta:
        """class Meta du modèle django"""

        ordering = ["third_party_num", "cct_uuid_identification"]
        unique_together = (("third_party_num", "cct_uuid_identification"),)
        indexes = [
            models.Index(fields=["third_party_num"]),
            models.Index(fields=["cct_uuid_identification"]),
            models.Index(fields=["cct_identifier"]),
            models.Index(fields=["third_party_num", "cct_uuid_identification"]),
            models.Index(fields=["third_party_num", "cct_uuid_identification", "cct_identifier"]),
        ]
