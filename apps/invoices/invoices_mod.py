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
from django.core.exceptions import ValidationError

from heron.models import FlagsTable
from apps.parameters.models import BaseAdressesTable, BaseInvoiceTable, BaseInvoiceDetailsTable
from apps.accountancy.models import CctSage
from apps.book.models import Society
from apps.edi.models import EdiImportControl


class CentersInvoices(models.Model):
    """Table pour stocker l'historique des éléments enseigne et centrale pour les factures"""

    created_at = models.DateTimeField(auto_now_add=True)

    # Elements Centrale fille
    code_center = models.CharField(max_length=15)
    comment_center = models.TextField(null=True, blank=True)
    legal_notice_center = models.TextField(null=True, blank=True)
    bank_center = models.CharField(null=True, blank=True, max_length=50)
    iban_center = models.CharField(null=True, blank=True, max_length=50)
    code_swift_center = models.CharField(null=True, blank=True, max_length=27)

    # Elements Enseigne
    code_signboard = models.CharField(max_length=15)
    logo_signboard = models.ImageField(null=True, blank=True, upload_to="logos/")
    message = models.TextField(null=True, blank=True)

    # uuid_identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    class Meta:
        """class Meta du modèle django"""

        constraints = [
            models.UniqueConstraint(
                fields=["client_billing", "code_center", "code_signboard"],
                name="centers_invoices_billing",
            ),
            models.UniqueConstraint(
                fields=[
                    "code_center",
                    "comment_center",
                    "legal_notice_center",
                    "bank_center",
                    "iban_center",
                    "code_swift_center",
                    "code_signboard",
                    "logo_signboard",
                    "message",
                ],
                name="centers_invoices_billing",
            ),
        ]


class PartiesInvoices(BaseAdressesTable):
    """Table fixe des adresses du facturé CCT et Tiers"""

    created_at = models.DateTimeField(auto_now_add=True)

    # Client CCT
    cct = models.ForeignKey(
        CctSage,
        on_delete=models.PROTECT,
        to_field="cct",
        related_name="cct_parties",
        verbose_name="cct x3",
        db_column="cct",
    )
    name_cct = models.CharField(null=True, blank=True, max_length=80)
    immeuble_cct = models.CharField(null=True, blank=True, max_length=200)
    adresse_cct = models.CharField(max_length=200)
    code_postal_cct = models.CharField(max_length=15)
    ville_cct = models.CharField(max_length=50)
    pays_cct = models.CharField(max_length=80)

    # Tiers facturé à qui appartient le CCT
    third_party_num = models.ForeignKey(
        Society,
        on_delete=models.PROTECT,
        to_field="third_party_num",
        related_name="society_parties",
        db_column="third_party_num",
    )
    name_third_party = models.CharField(null=True, blank=True, max_length=80)
    immeuble_third_party = models.CharField(null=True, blank=True, max_length=200)
    adresse_third_party = models.CharField(max_length=200)
    code_postal_third_party = models.CharField(max_length=15)
    ville_third_party = models.CharField(max_length=50)
    pays_third_party = models.CharField(max_length=80)

    # uuid_identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{self.created_at} - {self.cct} - {self.third_party_num}"

    class Meta:
        """class Meta du modèle django"""

        constraints = [
            models.UniqueConstraint(
                fields=["created_at", "cct", "third_party"],
                name="parties_adresses_billing",
            ),
            models.UniqueConstraint(
                fields=[
                    "cct",
                    "name_cct",
                    "immeuble_cct",
                    "adresse_cct",
                    "code_postal_cct",
                    "ville_cct",
                    "pays_cct",
                    "third_party_num",
                    "name_third_party",
                    "immeuble_third_party",
                    "adresse_third_party",
                    "code_postal_third_party",
                    "ville_third_party",
                    "pays_third_party",
                ],
                name="parties_adresses_billing",
            ),
        ]


class Invoice(FlagsTable, BaseInvoiceTable):
    """
    FR : Factures
    EN : Invoices
    """

    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    sale_invoice_number = models.CharField(max_length=20)
    sale_invoice_date = models.DateField()
    sale_invoice_month = models.DateField()
    sale_invoice_year = models.IntegerField()
    sale_invoice_periode = models.IntegerField()

    # Tiers X3 qui a facturé
    third_party_num = models.ForeignKey(
        Society,
        on_delete=models.PROTECT,
        to_field="third_party_num",
        related_name="society_invoice",
        db_column="third_party_num",
    )
    # cct X3 facturé
    cct = models.ForeignKey(
        CctSage,
        on_delete=models.PROTECT,
        to_field="cct",
        related_name="cct_invoice",
        verbose_name="cct x3",
        db_column="cct",
    )

    # Centrale / Enseigne
    centers = models.ForeignKey(
        CentersInvoices,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        related_name="centers_invoice",
        verbose_name="facturation",
        db_column="centers",
        null=True,
    )

    # Parties
    parties = models.ForeignKey(
        PartiesInvoices,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        related_name="parties_invoice",
        verbose_name="facturation",
        db_column="parties",
        null=True,
    )

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

    big_category = models.CharField(max_length=120)

    def clean(self):
        """
        FR : Nettoyage de la donnée pour les formulaires
        EN : Data cleansing for forms
        """

        if self.sale_invoice and not self.centers:
            raise ValidationError(
                "Vous devez sélectionner au moins un Centre si c'est une facture Client"
            )

        if self.sale_invoice and not self.parties:
            raise ValidationError(
                "Vous devez sélectionner au moins une partie prenante si c'est une facture Client"
            )

        if self.sale_invoice and not self.sale_invoice_number:
            raise ValidationError(
                "Vous devez avoir le N° de Facture Client si c'est une facture Client"
            )

        if not self.sale_devise:
            self.sale_devise = self.devise

        if not self.sale_invoice_type:
            self.sale_invoice_type = self.invoice_type

        if not self.sale_invoice_month:
            self.sale_invoice_month = pendulum.parse(self.sale_invoice_date.isoformat()).start_of(
                "month"
            )

        if not self.sale_invoice_year:
            self.sale_invoice_year = self.sale_invoice_date.year

        if not self.sale_invoice_periode:
            self.sale_invoice_periode = self.invoice_date.month

    def save(self, *args, **kwargs):
        """
        FR : On met l'année par défaut suivant la date de la facture
        EN : We set the year by default according to the date of the invoice
        """

        if not self.sale_devise:
            self.sale_devise = self.devise

        if not self.sale_invoice_type:
            self.sale_invoice_type = self.invoice_type

        if not self.sale_invoice_month:
            self.sale_invoice_month = pendulum.parse(self.sale_invoice_date.isoformat()).start_of(
                "month"
            )

        if not self.sale_invoice_year:
            self.sale_invoice_year = self.sale_invoice_date.year

        if not self.sale_invoice_periode:
            self.sale_invoice_periode = self.invoice_date.month

        super().save(*args, **kwargs)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return (
            f"{self.third_party_num} - {self.cct} - "
            f"{self.invoice_number} - {self.sale_invoice_number} - {self.invoice_date}"
        )

    class Meta:
        """class Meta du modèle django"""

        constraints = [
            models.UniqueConstraint(
                fields=["third_party_num", "invoice_number", "invoice_year", "cct"],
                name="unique_invoice_purchase",
            ),
            models.UniqueConstraint(
                fields=["third_party_num", "sale_invoice_number", "invoice_year"],
                name="unique_invoice_sale",
            ),
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
    # Axes
    axe_bu = models.CharField(max_length=15)
    axe_prj = models.CharField(max_length=15)
    axe_rfa = models.CharField(max_length=15)

    # Regroupement de facturation
    axe_pro = models.CharField(max_length=15)
    base = models.CharField(max_length=35)
    grouping_goods = models.CharField(null=True, max_length=35)
    personnel_type = models.CharField(null=True, max_length=35)

    # Achats
    axe_pys = models.CharField(max_length=15)
    vat = models.CharField(max_length=5)
    vat_rate = models.DecimalField(max_digits=20, decimal_places=5)
    vat_regime = models.CharField(max_length=5)

    # Ventes
    sale_axe_pys = models.CharField(max_length=15)
    sale_vat = models.CharField(max_length=5)
    sale_vat_rate = models.DecimalField(max_digits=20, decimal_places=5)
    sale_vat_regime = models.CharField(max_length=5)
    sale_sub_category = models.CharField(null=True, max_length=80)

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    class Meta:
        """class Meta du modèle django"""

        indexes = [
            models.Index(fields=["invoice"], name="invoice_idx"),
            models.Index(fields=["invoice", "article"], name="invoice_article_idx"),
            models.Index(fields=["axe_bu"], name="invoice_axe_bu"),
            models.Index(fields=["axe_prj"], name="invoice_axe_prj"),
            models.Index(fields=["axe_rfa"], name="invoice_axe_rfa"),
            models.Index(fields=["axe_pro"], name="invoice_axe_pro"),
            models.Index(fields=["axe_pys"], name="invoice_axe_pys"),
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
