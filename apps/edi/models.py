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
from heron.models import FlagsTable


class EdiImport(FlagsTable):
    """
    Table de préparation à l'import des factures fournisseurs edi et spécifique
    FR : Table Import EDI
    EN : Edi Import table
    """

    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    fournisseur = models.CharField(null=True, blank=True, max_length=35)
    siret_fournisseur = models.CharField(null=True, blank=True, max_length=20)
    siret_payeur = models.CharField(null=True, blank=True, max_length=20)
    code_fournisseur = models.CharField(null=True, blank=True, max_length=30)
    code_maison = models.CharField(null=True, blank=True, max_length=30, default="AF000")
    maison = models.CharField(null=True, blank=True, max_length=80, verbose_name="libellé maison")
    acuitis_order_number = models.CharField(
        null=True, blank=True, max_length=80, verbose_name="RFF avec ON"
    )
    acuitis_order_date = models.DateField(null=True, verbose_name="DTM avec 4 quand RFF avec ON")
    delivery_number = models.CharField(
        null=True, blank=True, max_length=80, verbose_name="RFF avec AAK"
    )
    delivery_date = models.DateField(null=True, verbose_name="DTM avec 35 quand RFF avec AAK")
    invoice_number = models.CharField(null=True, blank=True, max_length=35)
    invoice_date = models.DateField(null=True, verbose_name="DTM avec 3")
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
        null=True, blank=True, max_length=80, verbose_name="IMD avec F dernière position"
    )
    famille = models.CharField(
        null=True, blank=True, max_length=80, verbose_name="IMD avec F 1ère position"
    )
    qty = models.DecimalField(
        decimal_places=5, default=1, max_digits=20, verbose_name="QTY avec 47"
    )
    packaging_qty = models.DecimalField(
        decimal_places=5, default=1, max_digits=20, verbose_name="QTY avec 52"
    )
    gross_unit_price = models.DecimalField(
        max_digits=20,
        decimal_places=5,
        default=0,
        verbose_name="Prix unitaire brut PRI avec AAB et GRP",
    )
    net_unit_price = models.DecimalField(
        max_digits=20,
        decimal_places=5,
        default=0,
        verbose_name="prix unitaire net PRI avec AAA et NTP",
    )
    packaging_price = models.DecimalField(
        max_digits=20,
        decimal_places=5,
        default=0,
        verbose_name="prix emballage MOA avec 8 quand ALC avec M et PC",
    )
    transport_price = models.DecimalField(
        max_digits=20,
        decimal_places=5,
        default=0,
        verbose_name="prix transport MOA avec 8 quand ALC avec M et FC",
    )
    gross_price = models.DecimalField(
        max_digits=20,
        decimal_places=5,
        default=0,
        verbose_name="montant brut MOA avec 8 quand ALC avec H",
    )
    discount_price_01 = models.DecimalField(
        max_digits=20,
        decimal_places=5,
        default=0,
        verbose_name="remise 1 MOA avec 8 quand ALC avec H",
    )
    discount_price_02 = models.DecimalField(
        max_digits=20,
        decimal_places=5,
        default=0,
        verbose_name="remise 2 MOA avec 8 quand ALC avec H",
    )
    discount_price_03 = models.DecimalField(
        max_digits=20, decimal_places=5, default=0, verbose_name="remise 3 MOA avec 98"
    )
    net_amount = models.DecimalField(
        max_digits=20, decimal_places=5, default=0, verbose_name="montant net MOA avec 125"
    )
    vat_rate = models.DecimalField(
        max_digits=20,
        decimal_places=5,
        default=0,
        verbose_name="taux de tva TAX avec 7 quand ALC avec Y",
    )
    vat_amount = models.DecimalField(
        max_digits=20,
        decimal_places=5,
        default=0,
        verbose_name="montant de tva montant tva calculé",
    )
    amount_with_vat = models.DecimalField(
        max_digits=20, decimal_places=5, default=0, verbose_name="montant ttc calculé"
    )
    client_name = models.CharField(null=True, blank=True, max_length=80)
    serial_number = models.TextField(null=True, blank=True, max_length=1000)
    comment = models.CharField(null=True, blank=True, max_length=120)
    montant_facture_HT = models.DecimalField(
        max_digits=20, decimal_places=5, default=0, verbose_name="MOA avec 125"
    )
    montant_facture_TVA = models.DecimalField(
        max_digits=20, decimal_places=5, default=0, verbose_name="MOA avec 150"
    )
    montant_facture_TTC = models.DecimalField(
        max_digits=20, decimal_places=5, default=0, verbose_name="MOA avec 128"
    )
