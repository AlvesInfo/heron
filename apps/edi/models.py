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

from heron.models import DatesTable, FlagsTable
from apps.book.models import Society
from apps.parameters.models import BaseInvoiceTable, BaseInvoiceDetailsTable, Category
from apps.validation_purchases.models import EdiImportControl


class EdiImport(FlagsTable, BaseInvoiceTable, BaseInvoiceDetailsTable):
    """
    Table de préparation à l'import des factures fournisseurs edi et spécifique
    FR : Table Import EDI
    EN : Edi Import table
    """
    uuid_identification = models.UUIDField(default=uuid.uuid4, editable=False)
    third_party_num = models.CharField(null=True, max_length=15, verbose_name="tiers X3")
    flow_name = models.CharField(max_length=80)
    supplier = models.CharField(null=True, blank=True, max_length=35)
    supplier_name = models.CharField(null=True, blank=True, max_length=80)
    supplier_ident = models.CharField(null=True, blank=True, max_length=20)
    siret_payeur = models.CharField(null=True, blank=True, max_length=20)
    code_fournisseur = models.CharField(null=True, blank=True, max_length=30)
    code_maison = models.CharField(null=True, blank=True, max_length=30)
    maison = models.CharField(null=True, blank=True, max_length=80, verbose_name="libellé maison")

    famille = models.CharField(
        null=True, blank=True, max_length=80, verbose_name="IMD avec F 1ère position"
    )
    unit_weight = models.CharField(null=True, blank=True, max_length=20)
    packaging_qty = models.DecimalField(
        null=True, decimal_places=5, default=1, max_digits=20, verbose_name="QTY avec 52"
    )

    vat_rate = models.DecimalField(
        null=True,
        max_digits=20,
        decimal_places=5,
        default=0,
        verbose_name="taux de tva TAX avec 7 quand ALC avec Y",
    )
    packaging_amount = models.DecimalField(
        null=True,
        max_digits=20,
        decimal_places=5,
        default=0,
        verbose_name="prix emballage MOA avec 8 quand ALC avec M et PC",
    )
    transport_amount = models.DecimalField(
        null=True,
        max_digits=20,
        decimal_places=5,
        default=0,
        verbose_name="prix transport MOA avec 8 quand ALC avec M et FC",
    )
    insurance_amount = models.DecimalField(
        null=True,
        max_digits=20,
        decimal_places=5,
        default=0,
        verbose_name="prix assurance",
    )
    fob_amount = models.DecimalField(
        null=True,
        max_digits=20,
        decimal_places=5,
        default=0,
        verbose_name="prix transport MOA avec 8 quand ALC avec M et FC",
    )
    fees_amount = models.DecimalField(
        null=True,
        max_digits=20,
        decimal_places=5,
        default=0,
        verbose_name="prix assurance",
    )
    active = models.BooleanField(null=True, default=False)
    to_delete = models.BooleanField(null=True, default=False)
    to_export = models.BooleanField(null=True, default=False)
    valid = models.BooleanField(null=True, default=False)
    vat_rate_exists = models.BooleanField(null=True, default=False)
    supplier_exists = models.BooleanField(null=True, default=False)
    maison_exists = models.BooleanField(null=True, default=False)
    article_exists = models.BooleanField(null=True, default=False)
    axe_pro_supplier_exists = models.BooleanField(null=True, default=False)
    axe_pro_supplier = models.CharField(null=True, blank=True, max_length=10)
    # regex stats edi : ^(?P<tp>[\d]).{2}(?P<stat>.{2})

    big_category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        to_field="uuid_identification",
        related_name="big_category_edi_import",
        db_column="uuid_big_category",
    )

    uuid_control = models.ForeignKey(
        EdiImportControl,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        to_field="uuid_identification",
        related_name="edi_import_control",
        db_column="uuid_validation",
    )


class SupplierDefinition(DatesTable):
    """Table de définition des entêtes des fichiers fournisseurs"""

    flow_name = models.CharField(unique=True, max_length=80)
    supplier = models.CharField(null=True, blank=True, max_length=35)
    supplier_ident = models.CharField(null=True, blank=True, max_length=20)
    first_line = models.IntegerField(default=1)
    encoding = models.CharField(null=True, blank=True, max_length=20)
    delimiter = models.CharField(null=True, blank=True, max_length=10, default=";")
    lineterminator = models.CharField(null=True, blank=True, max_length=10, default=r"\n")
    quotechar = models.CharField(null=True, blank=True, max_length=10, default='"')
    escapechar = models.CharField(null=True, blank=True, max_length=10, default='"')
    directory = models.CharField(unique=True, max_length=80)


class ColumnDefinition(models.Model):
    """Table de définition des entêtes de l'ordre et du formatage"""

    flow_name = models.ForeignKey(
        SupplierDefinition,
        on_delete=models.PROTECT,
        to_field="flow_name",
        related_name="columns_suppliers",
        db_column="flow_name",
    )
    ranking = models.IntegerField(null=True)
    attr_name = models.CharField(max_length=120)
    file_column = models.CharField(null=True, blank=True, max_length=120)
    input_format = models.CharField(null=True, blank=True, max_length=120)
    function = models.CharField(null=True, blank=True, max_length=50)
    exclude_rows_dict = models.CharField(null=True, blank=True, max_length=120)
    unique = models.BooleanField(null=True)

    class Meta:
        """class Meta"""

        ordering = ["ranking"]
        unique_together = (("flow_name", "ranking"),)
