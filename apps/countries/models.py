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
from django.db import models


class Country(models.Model):
    """
    Table des Pays
    FR : Pays
    EN : Countries
    """

    country = models.CharField(
        primary_key=True, max_length=3, verbose_name="code pays iso 2"
    )  # CRY
    country_name = models.CharField(max_length=80)  # CRYDES
    country_deb = models.CharField(
        null=True, blank=True, max_length=3, verbose_name="code pays deb"
    )  # EECCOD
    country_insee = models.CharField(
        null=True, blank=True, max_length=80, verbose_name="code pays insee"
    )  # CINSEE
    country_iso = models.CharField(
        null=True, blank=True, max_length=3, verbose_name="code pays iso 2"
    )  # ISO
    country_iso_3 = models.CharField(
        null=True, blank=True, max_length=3, verbose_name="code pays iso 3"
    )  # ISOA3
    country_iso_num = models.IntegerField(null=True, verbose_name="code pays iso num")  # ISONUM
    lang_iso = models.CharField(null=True, blank=True, max_length=3)  # LAN
    cee = models.BooleanField(default=False)  # EECFLG
    cee_date = models.DateField(null=True)  # EECDAT
    cee_date_quit = models.DateField(null=True)  # EECDATOUT
    script_control = models.CharField(null=True, blank=True, max_length=255)  # CTLPRG
    currency_iso = models.CharField(null=True, blank=True, max_length=3)  # CUR
    format_naf = models.CharField(null=True, blank=True, max_length=255)  # NAFFMT
    format_tel = models.CharField(null=True, blank=True, max_length=255)  # TELFMT
    format_imp = models.CharField(null=True, blank=True, max_length=255)  # POSCODCRY
    format_ville = models.CharField(null=True, blank=True, max_length=255)  # CTYCODFMT
    currency_sigle = models.CharField(null=True, blank=True, max_length=3)
    currency_name = models.CharField(null=True, blank=True, max_length=35)
    phone_indicatif = models.CharField(null=True, blank=True, max_length=15)
    language = models.CharField(null=True, blank=True, max_length=35)
    country_vat_num = models.CharField(
        null=True, blank=True, max_length=3, verbose_name="code pays tva"
    )

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{self.country_name}"

    @staticmethod
    def file_import_sage():
        """
        FR : Retourne le nom du fichier dans le répertoire du serveur Sage X3
        EN : Returns the name of the file in the  directory of the Sage X3 server
        """
        return "ZBIADDR_journalier.heron"

    @staticmethod
    def get_columns_import():
        """
        FR : Retourne la position des colonnes
        EN : Returns the position of the columns
        """
        return {
            "country": 0,
            "country_name": 1,
            "country_deb": 2,
            "country_insee": 3,
            "country_iso": 4,
            "country_iso_3": 5,
            "country_iso_num": 6,
            "lang_iso": 7,
            "cee": 8,
            "cee_date": 9,
            "cee_date_quit": 10,
            "script_control": 11,
            "currency_iso": 12,
            "format_naf": 13,
            "format_tel": 14,
            "format_imp": 15,
            "format_ville": 16,
        }

    @staticmethod
    def get_uniques():
        """
        FR : Retourne les champs uniques de la table
        EN: Returns the unique fields of the table
        """
        return {"country"}

    @property
    def get_import(self):
        """
        FR : Retourne la methode à appeler pour importer à partir d'un fichier de type csv
        EN : Returns the method to call to import from a csv file type
        """
        return "methode d'import à retourner"

    class Meta:
        """class Meta du modèle django"""

        ordering = ["country_name"]


class Language(models.Model):
    """
    Table des Langues
    FR : Langues
    EN : language
    """
    code = models.CharField(primary_key=True, max_length=3)
    name = models.CharField(max_length=35)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return self.name


class Currency(models.Model):
    """
    Table des Langues
    FR : Langues
    EN : language
    """
    code = models.CharField(primary_key=True, max_length=3)
    name = models.CharField(max_length=35)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return self.name


class ExchangeRate(models.Model):
    """
    Table des Taux de change
    FR : Taux de change
    EN : Change rate
    """

    currency_iso_current = models.CharField(null=True, blank=True, max_length=3)
    currency_iso_change = models.CharField(null=True, blank=True, max_length=3)
    exchange_date = models.DateField(auto_now_add=True, verbose_name="créé le")
    average_exchange_rate = models.DecimalField(max_digits=20, decimal_places=5, default=0)
    purchase_exchange_rate = models.DecimalField(null=True, max_digits=20, decimal_places=5)
    sale_exchange_rate = models.DecimalField(null=True, max_digits=20, decimal_places=5)
    cee = models.BooleanField(default=False)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
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
        to_field="country",
        related_name="post_code_country",
    )
    number_char = models.IntegerField(default=0, verbose_name="nombre de caractères")
    rule_number = models.IntegerField(default=0, verbose_name="n° de règle")
    exemple = models.CharField(null=True, blank=True, max_length=35)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
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
        to_field="country",
        related_name="vies_country",
    )
    prefix = models.CharField(null=True, blank=True, max_length=2)
    func_verif = models.CharField(null=True, blank=True, max_length=35)
    lng_min = models.IntegerField(default=0, verbose_name="longeur minimun")
    lng_max = models.IntegerField(default=0, verbose_name="longeur maxi")

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{self.country} - {self.func_verif}"

    class Meta:
        """class Meta du modèle django"""

        ordering = ["country"]
