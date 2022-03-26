# pylint: disable=E0401,R0903
"""
FR : Module des modèles des pays
EN : Country Models Module

Commentaire:

created at: 2021-11-07
created by: Paulo ALVES

modified at: 2021-11-07
modified by: Paulo ALVES
"""
import uuid
from django.db import models


class Country(models.Model):
    """
    Table des Pays
    FR : Pays
    EN : Countries
    """

    country_iso = models.CharField(primary_key=True, max_length=3, verbose_name="code pays iso 2")
    country_iso_3 = models.CharField(
        null=True, blank=True, max_length=3, verbose_name="code pays iso 3"
    )
    country_insee = models.IntegerField(null=True, verbose_name="code pays insee")
    country_iso_num = models.IntegerField(null=True, verbose_name="code pays iso num")
    country_deb = models.CharField(
        null=True, blank=True, max_length=3, verbose_name="code pays deb"
    )
    country = models.CharField(max_length=80)
    currency_sigle = models.CharField(blank=True, null=True, max_length=3)
    currency_name = models.CharField(blank=True, null=True, max_length=35)
    currency_iso = models.CharField(blank=True, null=True, max_length=3)
    phone_indicatif = models.CharField(blank=True, null=True, max_length=15)
    lang_iso = models.CharField(blank=True, null=True, max_length=3)
    language = models.CharField(null=True, blank=True, max_length=35)
    cee = models.BooleanField(default=False)
    country_vat_num = models.CharField(
        null=True, blank=True, max_length=3, verbose_name="code pays tva"
    )

    def __str__(self):
        return f"{self.country} - {self.currency_iso}"

    class Meta:
        """class Meta du modèle django"""

        ordering = ["country"]


class ExchangeRate(models.Model):
    """
    Table des Taux de change
    FR : Taux de change
    EN : Change rate
    """

    currency_iso_current = models.CharField(blank=True, null=True, max_length=3)
    currency_iso_change = models.CharField(blank=True, null=True, max_length=3)
    exchange_date = models.DateField(auto_now_add=True, verbose_name="créé le")
    average_exchange_rate = models.DecimalField(max_digits=20, decimal_places=5, default=0)
    purchase_exchange_rate = models.DecimalField(null=True, max_digits=20, decimal_places=5)
    sale_exchange_rate = models.DecimalField(null=True, max_digits=20, decimal_places=5)
    cee = models.BooleanField(default=False)

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        return f"{self.currency_iso_current} - {self.currency_iso_change}"

    class Meta:
        """class Meta du modèle django"""

        ordering = ["currency_iso_current", "currency_iso_change", "exchange_date"]
        unique_together = (("currency_iso_current", "currency_iso_change", "exchange_date"),)


class ValidationPostalCode(models.Model):
    """
    Table por la Validation Codes Postaux
    FR : Table contenant les élements pour la validation des codes postaux
    EN : Table containing the elements for validating postals codes
    """

    country = models.OneToOneField(
        Country,
        on_delete=models.CASCADE,
        to_field="country_iso",
        related_name="post_code_country",
    )
    number_char = models.IntegerField(default=0, verbose_name="nombre de caractères")
    rule_number = models.IntegerField(default=0, verbose_name="n° de règle")
    exemple = models.CharField(blank=True, null=True, max_length=35)

    def __str__(self):
        return f"{self.country} - {self.number_char} - {self.exemple}"

    class Meta:
        """class Meta du modèle django"""

        ordering = ["country"]


class ValidationIntraVies(models.Model):
    """
    Table por la Validation N° de TVA Intracommunataire
    FR : Table contenant les élements pour la validation des N° de TVA Intracommunataire
    EN : Table containing the elements for the validation of intra-community VAT numbers
    """

    country = models.OneToOneField(
        Country,
        on_delete=models.CASCADE,
        to_field="country_iso",
        related_name="vies_country",
    )
    prefix = models.CharField(blank=True, null=True, max_length=2)
    func_verif = models.CharField(blank=True, null=True, max_length=35)
    lng_min = models.IntegerField(default=0, verbose_name="longeur minimun")
    lng_max = models.IntegerField(default=0, verbose_name="longeur maxi")

    def __str__(self):
        return f"{self.country} - {self.func_verif}"

    class Meta:
        """class Meta du modèle django"""

        ordering = ["country"]
