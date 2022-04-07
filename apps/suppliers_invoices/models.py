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
from apps.articles.models import Article
from apps.book.models import Society


class Invoice(FlagsTable):
    """
    FR : Factures fournisseurs
    EN : Suppliers Invoices
    """

    supplier = models.ForeignKey(
        Society,
        on_delete=models.PROTECT,
        to_field="third_party_num",
        related_name="detail_society",
        db_column="supplier",
    )
    invoice_number = models.CharField(max_length=35)
    invoice_date = models.DateField()
    invoice_year = models.IntegerField()
    devise = models.CharField(null=True, blank=True, max_length=3, default="EUR")
    invoice_type = models.CharField(max_length=3)
    flag_sage = models.BooleanField(null=True, default=False)

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def save(self, *args, **kwargs):
        """
        FR : On met l'année par défaut suivant la date de la facture
        EN : We set the year by default according to the date of the invoice
        """
        self.invoice_year = self.invoice_date.year

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.supplier} - {self.invoice_number} - {self.invoice_date}"

    @property
    def set_import(self):
        """
        FR : Retourne la methode à appeler pour importer à partir d'un fichier de type csv
        EN : Returns the method to call to import from a csv file type
        """
        return "methode d'import à retourner"

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
                fields=["supplier", "invoice_number", "invoice_year"], name="unique_invoice"
            )
        ]


class InvoiceDetail(FlagsTable):
    """
    FR : Detail des factures fournisseurs
    EN : Suppliers Invoices detail
    """

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        to_field="uuid_identification",
        related_name="detail_invoice",
        db_column="invoice",
    )

    # Article
    article = models.ForeignKey(
        Article,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        related_name="detail_article",
        db_column="article",
    )

    # Sage
    axe_bu = models.CharField(null=True, blank=True, max_length=10)
    axe_cct = models.CharField(null=True, blank=True, max_length=10)
    axe_prj = models.CharField(null=True, blank=True, max_length=10)
    axe_pro = models.CharField(null=True, blank=True, max_length=10)
    axe_pys = models.CharField(null=True, blank=True, max_length=10)
    axe_rfa = models.CharField(null=True, blank=True, max_length=10)

    # Maison
    maison = models.ForeignKey(
        Society,
        on_delete=models.PROTECT,
        to_field="third_party_num",
        related_name="maison_society",
        db_column="maison",
    )

    # Commande / BL
    acuitis_order_number = models.CharField(null=True, blank=True, max_length=80)
    acuitis_order_date = models.DateField(null=True)
    delivery_number = models.CharField(null=True, blank=True, max_length=80)
    delivery_date = models.DateField(null=True)

    # Prices
    qty = models.DecimalField(decimal_places=5, default=1, max_digits=20, verbose_name="quantité")
    gross_unit_price = models.DecimalField(
        max_digits=20, decimal_places=5, default=0, verbose_name="prix unitaire brut"
    )
    net_unit_price = models.DecimalField(
        max_digits=20, decimal_places=5, default=0, verbose_name="prix unitaire net"
    )
    gross_price = models.DecimalField(
        max_digits=20, decimal_places=5, default=0, verbose_name="montant brut"
    )
    discount_price_01 = models.DecimalField(
        max_digits=20, decimal_places=5, default=0, verbose_name="remise 1"
    )
    discount_price_02 = models.DecimalField(
        max_digits=20, decimal_places=5, default=0, verbose_name="remise 2"
    )
    discount_price_03 = models.DecimalField(
        max_digits=20, decimal_places=5, default=0, verbose_name="remise 3"
    )
    net_amount = models.DecimalField(
        max_digits=20, decimal_places=5, default=0, verbose_name="montant net"
    )
    vat = models.CharField(max_length=5, verbose_name="taux de tva sage")
    vat_amount = models.DecimalField(
        max_digits=20, decimal_places=5, default=0, verbose_name="montant tva calculé"
    )
    amount_with_vat = models.DecimalField(
        max_digits=20, decimal_places=5, default=0, verbose_name="montant ttc calculé"
    )

    # Other descriptions
    client_name = models.CharField(null=True, blank=True, max_length=80)
    serial_number = models.TextField(null=True, blank=True, max_length=1000)
    comment = models.CharField(null=True, blank=True, max_length=120)
