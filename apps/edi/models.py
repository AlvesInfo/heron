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


class EdiImport(models.Model):
    """
    Table de préparation à l'import des factures fournisseurs edi et spécifique
    FR : Table Import EDI
    EN : Edi Import table
    """

    uuid_identification = models.UUIDField(default=uuid.uuid4, editable=False)
    third_party_num = models.CharField(null=True, max_length=15, verbose_name="tiers X3")
    flow_name = models.CharField(max_length=80)
    supplier = models.CharField(null=True, blank=True, max_length=35)
    supplier_ident = models.CharField(null=True, blank=True, max_length=20)
    siret_payeur = models.CharField(null=True, blank=True, max_length=20)
    code_fournisseur = models.CharField(null=True, blank=True, max_length=30)
    code_maison = models.CharField(null=True, blank=True, max_length=30)
    maison = models.CharField(null=True, blank=True, max_length=80, verbose_name="libellé maison")
    acuitis_order_number = models.CharField(
        null=True, blank=True, max_length=80, verbose_name="RFF avec ON"
    )
    acuitis_order_date = models.DateField(null=True, verbose_name="DTM avec 4 quand RFF avec ON")
    delivery_number = models.CharField(
        null=True, blank=True, max_length=80, verbose_name="RFF avec AAK"
    )
    delivery_date = models.DateField(null=True, verbose_name="DTM avec 35 quand RFF avec AAK")
    invoice_number = models.CharField(max_length=35)
    invoice_date = models.DateField(verbose_name="DTM avec 3")
    invoice_type = models.CharField(
        null=True, blank=True, max_length=3, verbose_name="BGM Facture=380 Avoir=381"
    )
    devise = models.CharField(null=True, blank=True, max_length=3, default="EUR")
    reference_article = models.CharField(
        null=True, blank=True, max_length=35, verbose_name="LIN avec 21 et autre chose que EN"
    )
    ean_code = models.CharField(
        null=True, blank=True, max_length=35, verbose_name="LIN avec 21 et EN"
    )
    libelle = models.CharField(
        null=True, blank=True, max_length=150, verbose_name="IMD avec F dernière position"
    )
    famille = models.CharField(
        null=True, blank=True, max_length=80, verbose_name="IMD avec F 1ère position"
    )
    qty = models.DecimalField(
        null=True, decimal_places=5, default=1, max_digits=20, verbose_name="QTY avec 47"
    )
    unit_weight = models.CharField(null=True, blank=True, max_length=20)
    packaging_qty = models.DecimalField(
        null=True, decimal_places=5, default=1, max_digits=20, verbose_name="QTY avec 52"
    )
    gross_unit_price = models.DecimalField(
        null=True,
        max_digits=20,
        decimal_places=5,
        default=0,
        verbose_name="Prix unitaire brut PRI avec AAB et GRP",
    )
    net_unit_price = models.DecimalField(
        null=True,
        max_digits=20,
        decimal_places=5,
        default=0,
        verbose_name="prix unitaire net PRI avec AAA et NTP",
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
    gross_amount = models.DecimalField(
        null=True,
        max_digits=20,
        decimal_places=5,
        default=0,
        verbose_name="montant brut MOA avec 8 quand ALC avec H",
    )
    discount_price_01 = models.DecimalField(
        null=True,
        max_digits=20,
        decimal_places=5,
        default=0,
        verbose_name="remise 1 MOA avec 8 quand ALC avec H",
    )
    discount_price_02 = models.DecimalField(
        null=True,
        max_digits=20,
        decimal_places=5,
        default=0,
        verbose_name="remise 2 MOA avec 8 quand ALC avec H",
    )
    discount_price_03 = models.DecimalField(
        null=True, max_digits=20, decimal_places=5, default=0, verbose_name="remise 3 MOA avec 98"
    )
    net_amount = models.DecimalField(
        null=True,
        max_digits=20,
        decimal_places=5,
        default=0,
        verbose_name="montant net MOA avec 125",
    )
    vat_rate = models.DecimalField(
        null=True,
        max_digits=20,
        decimal_places=5,
        default=0,
        verbose_name="taux de tva TAX avec 7 quand ALC avec Y",
    )
    vat_amount = models.DecimalField(
        null=True,
        max_digits=20,
        decimal_places=5,
        default=0,
        verbose_name="montant de tva montant tva calculé",
    )
    amount_with_vat = models.DecimalField(
        null=True, max_digits=20, decimal_places=5, default=0, verbose_name="montant ttc calculé"
    )
    client_name = models.CharField(null=True, blank=True, max_length=80)
    serial_number = models.TextField(null=True, blank=True, max_length=1000)
    comment = models.CharField(null=True, blank=True, max_length=120)
    montant_facture_HT = models.DecimalField(
        null=True, max_digits=20, decimal_places=5, default=0, verbose_name="MOA avec 125"
    )
    montant_facture_TVA = models.DecimalField(
        null=True, max_digits=20, decimal_places=5, default=0, verbose_name="MOA avec 150"
    )
    montant_facture_TTC = models.DecimalField(
        null=True, max_digits=20, decimal_places=5, default=0, verbose_name="MOA avec 128"
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
    # regex stats edi : ^(?P<tp>[\d]).{2}(?P<stat>.{2})


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


class SupplierTiers(FlagsTable):
    """
    Table de liaison entre fournisseurs edi et tiers sage X3
    FR : Table Suppliers/Tiers
    EN : Suppliers/Tiers table
    """
    tiers = models.ForeignKey(
        Society,
        on_delete=models.CASCADE,
        to_field="third_party_num",
        related_name="supplier_tiers_edi",
        verbose_name="tiers X3",
        db_column="tiers",
    )
    supplier_identifiant = models.CharField(unique=True, max_length=35)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{self.tiers} - {self.supplier_identifiant}"

    class Meta:
        """class Meta Django"""
        unique_together = (("tiers", "supplier_identifiant"),)
