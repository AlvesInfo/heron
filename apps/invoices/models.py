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

import pendulum
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
from apps.edi.models import EdiImportControl


class CentersInvoices(models.Model):
    """Table pour stocker les éléments enseigne et centrale de la facture"""
    # Elements Centrale fille
    code_center = models.CharField(unique=True, max_length=15)
    comment_center = models.TextField(null=True, blank=True)
    legal_notice_center = models.TextField(null=True, blank=True)
    bank_center = models.CharField(null=True, blank=True, max_length=50)
    iban_center = models.CharField(null=True, blank=True, max_length=50)
    code_swift_center = models.CharField(null=True, blank=True, max_length=27)

    # Elements Enseigne
    code_signboard = models.CharField(unique=True, max_length=15)
    logo_signboard = models.ImageField(null=True, blank=True, upload_to="logos/")
    message = models.TextField(null=True, blank=True)

    # uuid_identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)


class ThirdPartyAdress(BaseAdressesTable):
    """Table fixe des adresses du facturé"""

    third_party_num = models.ForeignKey(
        Society,
        on_delete=models.PROTECT,
        to_field="third_party_num",
        related_name="detail_society",
        db_column="third_party_num",
    )
    flow_name = models.CharField(max_length=80)
    supplier_name = models.CharField(null=True, blank=True, max_length=80)
    supplier = models.CharField(null=True, blank=True, max_length=35)

    # uuid_identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{self.third_party_num} - {self.supplier_name}"


class CctAdress(BaseAdressesTable):
    """Table fixe des adresses de la maison facturée"""

    client_cct = models.ForeignKey(
        Maison,
        null=True,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        related_name="+",
        verbose_name="CCT x3",
        db_column="cct_uuid_identification",
    )
    intitule = models.CharField(max_length=50)
    # uuid_identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{self.intitule}"


class Invoice(FlagsTable, BaseInvoiceTable):
    """
    FR : Factures fournisseurs
    EN : Suppliers Invoices
    """

    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    sales_invoice_number = models.CharField(null=True, blank=True, max_length=20)
    flow_name = models.CharField(max_length=80, default="Saisie")

    # Centrale/Enseigne
    center_signboard = models.ForeignKey(
        CentersInvoices,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        related_name="invoice_center_signboard",
        verbose_name="Centrale / Enseigne",
        db_column="center_signboard",
    )

    # Magasin Facturé
    client_adress = models.ForeignKey(
        CctAdress,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        related_name="cct_client_adress",
        verbose_name="CCT x3",
        db_column="cct_adress",
    )

    # Tiers Client Facturé
    third_party_num = models.ForeignKey(
        Society,
        on_delete=models.PROTECT,
        to_field="third_party_num",
        related_name="dinvoice_third_party_num",
        db_column="third_party_num",
    )
    third_party_adress = models.ForeignKey(
        ThirdPartyAdress,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        related_name="client_third_party_adress",
        verbose_name="Tiers x3",
        db_column="third_party_adress",
    )
    periode = models.IntegerField()
    flag_sage_purchases = models.BooleanField(null=True, default=False)
    flag_sage_sales = models.BooleanField(null=True, default=False)

    vat_regime = models.CharField(null=True, max_length=5, verbose_name="régime de taxe")
    uuid_control = models.ForeignKey(
        EdiImportControl,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        to_field="uuid_identification",
        related_name="invoices_edi_import_control",
        db_column="uuid_control",
    )

    def save(self, *args, **kwargs):
        """
        FR : On met l'année par défaut suivant la date de la facture
        EN : We set the year by default according to the date of the invoice
        """
        self.invoice_year = self.invoice_date.year
        self.periode = self.invoice_date.month
        self.invoice_month = pendulum.date(self.invoice_year, self.periode, 1)
        super().save(*args, **kwargs)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{self.third_party_adress} - {self.invoice_number} - {self.invoice_date}"

    @staticmethod
    def set_export():
        """
        FR : Retourne la methode pour exporter le fichier destiné à l'intégration dans Sage X3
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
        on_delete=models.PROTECT,
        to_field="vat",
        db_column="vat",
    )
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
    serial = models.CharField(max_length=50)
