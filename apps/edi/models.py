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

import pendulum
from django.db import models

from heron.models import DatesTable, FlagsTable
from apps.accountancy.models import VatSage, VatRegimeSage, CctSage
from apps.book.models import Society
from apps.centers_clients.models import Maison
from apps.parameters.models import BaseInvoiceTable, BaseInvoiceDetailsTable, Category, SubCategory


class EdiImportControl(FlagsTable):
    """Table de saisie de relevé des fournisseurs, pour contrôle des intégrations"""

    statement_without_tax = models.DecimalField(
        null=True, max_digits=20, decimal_places=5, default=0, verbose_name="Montant HT"
    )
    statement_with_tax = models.DecimalField(
        null=True, max_digits=20, decimal_places=5, default=0, verbose_name="Montant TTC"
    )
    comment = models.TextField(blank=True, null=True)
    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)


class EdiImport(FlagsTable, BaseInvoiceTable, BaseInvoiceDetailsTable):
    """
    Table de préparation à l'import des factures fournisseurs edi et spécifique
    FR : Table Import EDI
    EN : Edi Import table
    """

    uuid_identification = models.UUIDField(default=uuid.uuid4, editable=False)
    third_party_num = models.CharField(null=True, max_length=15, verbose_name="tiers X3")
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
    serial_number = models.TextField(null=True, blank=True)
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
        to_field="uuid_identification",
        related_name="big_category_edi_import",
        db_column="uuid_big_category",
    )
    sub_category = models.ForeignKey(
        SubCategory,
        on_delete=models.PROTECT,
        null=True,
        to_field="uuid_identification",
        related_name="sub_category_edi_import",
        db_column="uuid_sub_big_category",
    )
    uuid_control = models.ForeignKey(
        EdiImportControl,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        to_field="uuid_identification",
        related_name="edi_import_control",
        db_column="uuid_control",
    )
    vat = models.ForeignKey(
        VatSage,
        null=True,
        on_delete=models.PROTECT,
        to_field="vat",
        db_column="vat",
    )
    vat_regime = models.CharField(null=True, max_length=5, verbose_name="régime de taxe")
    cct_uuid_identification = models.ForeignKey(
        Maison,
        null=True,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        related_name="edi_maison",
        verbose_name="CCT x3",
        db_column="cct_uuid_identification",
    )

    # pour vérifier si les factures sont multi magasins
    is_multi_store = models.BooleanField(null=True)

    def save(self, *args, **kwargs):
        """
        FR : Avant la sauvegarde on clean les données
        EN : Before the backup we clean the data
        """
        if not self.invoice_month:
            self.invoice_month = pendulum.parse(self.invoice_date.isoformat()).start_of("month")

        if not self.invoice_year:
            self.invoice_year = self.invoice_date.year

        super().save(*args, **kwargs)

    class Meta:
        """Class Meta Django"""

        indexes = [
            models.Index(fields=["cct_uuid_identification"]),
            models.Index(fields=["valid"]),
            models.Index(fields=["third_party_num"]),
            models.Index(fields=["supplier_ident"]),
            models.Index(fields=["uuid_identification"]),
            models.Index(fields=["invoice_number"]),
            models.Index(fields=["id"]),
            models.Index(fields=["is_multi_store"]),
            models.Index(fields=["third_party_num", "supplier_ident", "valid"]),
            models.Index(fields=["uuid_identification", "invoice_number"]),
            models.Index(fields=["id", "valid"]),
            models.Index(
                fields=[
                    "third_party_num",
                    "uuid_identification",
                    "invoice_number",
                    "is_multi_store",
                    "valid",
                ]
            ),
        ]


class StarkeyDepot(FlagsTable, BaseInvoiceTable, BaseInvoiceDetailsTable):
    """
    Table de dépôts STARKEY
    FR : Table Import EDI
    EN : Edi Import table
    """

    uuid_identification = models.UUIDField(default=uuid.uuid4, editable=False)
    third_party_num = models.CharField(null=True, max_length=15, verbose_name="tiers X3")
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
    serial_number = models.TextField(null=True, blank=True)
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
        to_field="uuid_identification",
        related_name="+",
        db_column="uuid_big_category",
    )
    sub_category = models.ForeignKey(
        SubCategory,
        on_delete=models.PROTECT,
        null=True,
        to_field="uuid_identification",
        related_name="+",
        db_column="uuid_sub_big_category",
    )
    uuid_control = models.ForeignKey(
        EdiImportControl,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        to_field="uuid_identification",
        related_name="+",
        db_column="uuid_control",
    )
    vat = models.ForeignKey(
        VatSage,
        null=True,
        on_delete=models.PROTECT,
        to_field="vat",
        db_column="vat",
    )
    vat_regime = models.CharField(null=True, max_length=5, verbose_name="régime de taxe")
    cct_uuid_identification = models.ForeignKey(
        Maison,
        null=True,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        related_name="+",
        verbose_name="CCT x3",
        db_column="cct_uuid_identification",
    )

    # pour vérifier si les factures sont multi magasins
    is_multi_store = models.BooleanField(null=True)

    def save(self, *args, **kwargs):
        """
        FR : Avant la sauvegarde on clean les données
        EN : Before the backup we clean the data
        """
        if not self.invoice_month:
            self.invoice_month = pendulum.parse(self.invoice_date.isoformat()).start_of("month")

        if not self.invoice_year:
            self.invoice_year = self.invoice_date.year

        super().save(*args, **kwargs)

    class Meta:
        """Class Meta Django"""

        indexes = [
            models.Index(fields=["cct_uuid_identification"]),
            models.Index(fields=["valid"]),
            models.Index(fields=["third_party_num"]),
            models.Index(fields=["supplier_ident"]),
            models.Index(fields=["uuid_identification"]),
            models.Index(fields=["invoice_number"]),
            models.Index(fields=["id"]),
            models.Index(fields=["is_multi_store"]),
            models.Index(fields=["third_party_num", "supplier_ident", "valid"]),
            models.Index(fields=["uuid_identification", "invoice_number"]),
            models.Index(fields=["id", "valid"]),
            models.Index(
                fields=[
                    "third_party_num",
                    "uuid_identification",
                    "invoice_number",
                    "is_multi_store",
                    "valid",
                ]
            ),
        ]


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
    """Table de définition des entêtes de l'ordre et du formatage,
    dans les fichiers fournissuers à importer
    """

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
