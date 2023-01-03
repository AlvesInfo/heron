# pylint: disable=E0401,R0903
"""
FR : Module des modèles de factures founisseurs
EN : supplier invoice templates module

Commentaire:

created at: 2021-11-07
created by: Paulo ALVES

modified at: 2021-11-07
modified by: Paulo ALVES
"""
import uuid

from django.db import models

from heron.models import FlagsTable
from apps.parameters.models import BaseAdressesTable, BaseInvoiceTable, BaseInvoiceDetailsTable
from apps.accountancy.models import VatSage, VatRegimeSage
from apps.centers_clients.models import Maison
from apps.articles.models import (
    Article,
    Category,
    SubFamilly,
    TabDivSage,
)
from apps.book.models import Society
from apps.centers_clients.models import Maison


class Invoice(FlagsTable, BaseInvoiceTable, BaseAdressesTable):
    """
    FR : Factures fournisseurs
    EN : Suppliers Invoices
    """

    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    third_party_num = models.ForeignKey(
        Society,
        on_delete=models.PROTECT,
        to_field="third_party_num",
        related_name="detail_society",
        db_column="third_party_num",
    )
    # Fournisseur
    flow_name = models.CharField(max_length=80)
    supplier_name = models.CharField(null=True, blank=True, max_length=80)
    supplier = models.CharField(null=True, blank=True, max_length=35)

    # Magasin Facturé
    cct_uuid_identification = models.ForeignKey(
        Maison,
        null=True,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        related_name="+",
        verbose_name="CCT x3",
        db_column="cct_uuid_identification",
    )
    periode = models.IntegerField()
    flag_sage = models.BooleanField(null=True, default=False)
    big_category = models.CharField(unique=True, max_length=80)
    big_category_uuid = models.UUIDField(unique=True, default=uuid.uuid4)
    sub_category = models.CharField(unique=True, max_length=80)
    sub_category_uuid = models.UUIDField(unique=True, default=uuid.uuid4)
    function = models.CharField(unique=True, max_length=255)
    function_uuid = models.UUIDField(unique=True, default=uuid.uuid4)
    function_created_at = models.DateTimeField()
    vat_regime = models.CharField(null=True, max_length=5, verbose_name="régime de taxe")

    def save(self, *args, **kwargs):
        """
        FR : On met l'année par défaut suivant la date de la facture
        EN : We set the year by default according to the date of the invoice
        """
        self.invoice_year = self.invoice_date.year

        super().save(*args, **kwargs)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{self.third_party_num} - {self.invoice_number} - {self.invoice_date}"

    @staticmethod
    def set_export():
        """
        FR : Retourne la methode pour exporter le fihier destiné à l'intégration dans Sage X3
        EN : Returns the method to export the file intended for integration in Sage X3
        """
        return "methode d'export à retourner"

    class Meta:
        """class Meta du modèle django"""

        constraints = [
            models.UniqueConstraint(
                fields=["third_party_num", "invoice_number", "invoice_year"],
                name="unique_invoice",
            )
        ]


class InvoiceTax(FlagsTable):

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    uuid_edi_import = models.UUIDField()
    third_party_num = models.CharField(max_length=15)
    invoice_number = models.CharField(max_length=35)
    total_without_tax = models.DecimalField(max_digits=20, decimal_places=5)
    vat_rate = models.DecimalField(max_digits=20, decimal_places=5)
    total_tax = models.DecimalField(max_digits=20, decimal_places=5)
    total_with_tax = models.DecimalField(max_digits=20, decimal_places=5)
    vat_rank = models.IntegerField()
    vat = models.ForeignKey(
        VatSage,
        on_delete=models.CASCADE,
        to_field="vat",
        db_column="vat",
    )
    vat_regime = models.CharField(null=True, max_length=5, verbose_name="régime de taxe")


class InvoiceDetail(FlagsTable, BaseInvoiceDetailsTable):
    """
    FR : Detail des factures fournisseurs
    EN : Suppliers Invoices detail
    """

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        to_field="uuid_identification",
        related_name="detail_invoice",
        db_column="uuid_invoice",
    )

    # Article
    article = models.ForeignKey(
        Article,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        related_name="invoices_detail_article",
        db_column="uuid_article",
    )

    # Maison
    cct = models.ForeignKey(
        Maison,
        null=True,
        on_delete=models.PROTECT,
        to_field="cct",
        related_name="invoices_details_cct",
        db_column="cct",
    )

    vat = models.ForeignKey(
        VatSage,
        on_delete=models.CASCADE,
        to_field="vat",
        db_column="vat",
    )
    vat_regime = models.CharField(null=True, max_length=5, verbose_name="régime de taxe")
    vat_start_date = models.DateField()

    brand = models.CharField(null=True, blank=True, max_length=80)
    manufacturer = models.CharField(null=True, blank=True, max_length=80)

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    class Meta:
        """class Meta du modèle django"""

        indexes = [
            models.Index(fields=["invoice"], name="invoice_idx"),
            models.Index(fields=["invoice", "article"], name="invoice_article_idx"),
        ]


class InvoiceSerials(models.Model):
    """
    FR : Detail des n° de série
    EN : Serial numbers detail
    """

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        to_field="uuid_identification",
        related_name="serial_invoice",
        db_column="uuid_invoice",
    )
    serial = models.CharField(max_length=255)
