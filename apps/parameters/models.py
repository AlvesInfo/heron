# pylint: disable=E0401,R0903
"""
FR : Module des modèles des paramètres
EN : Parameters Models Module

Commentaire:

created at: 2021-11-07
created by: Paulo ALVES

modified at: 2021-11-07
modified by: Paulo ALVES
"""
import uuid

from django.conf import settings
from django.db import models
from django.shortcuts import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify

from heron.models import DatesTable, FlagsTable
from apps.accountancy.models import VatSage, VatRegimeSage, CctSage, SectionSage
from apps.countries.models import Country


class Parameters(FlagsTable):
    """
    Table des Parametrages généraux de l'application
    FR : Paramétrages
    EN : Settings
    """

    name = models.CharField(unique=True, max_length=80)
    short_name = models.CharField(null=True, blank=True, max_length=20)
    text = models.TextField(null=True, blank=True)
    value = models.DecimalField(null=True, max_digits=20, decimal_places=5, default=0)
    unit = models.CharField(null=True, blank=True, max_length=20)
    validator = models.CharField(null=True, blank=True, max_length=50)
    operation = models.CharField(null=True, blank=True, max_length=200)
    module = models.CharField(null=True, blank=True, max_length=50)
    func = models.CharField(null=True, blank=True, max_length=50)
    rate = models.DecimalField(null=True, max_digits=20, decimal_places=5, default=0)
    base = models.CharField(null=True, blank=True, max_length=50)
    char_01 = models.CharField(null=True, blank=True, max_length=50)
    char_02 = models.CharField(null=True, blank=True, max_length=50)
    char_03 = models.CharField(null=True, blank=True, max_length=50)
    char_04 = models.CharField(null=True, blank=True, max_length=50)
    char_05 = models.CharField(null=True, blank=True, max_length=50)
    check_01 = models.BooleanField(null=True, default=False)
    check_02 = models.BooleanField(null=True, default=False)
    check_03 = models.BooleanField(null=True, default=False)
    check_04 = models.BooleanField(null=True, default=False)
    check_05 = models.BooleanField(null=True, default=False)
    num_01 = models.DecimalField(null=True, max_digits=20, decimal_places=5, default=0)
    num_02 = models.DecimalField(null=True, max_digits=20, decimal_places=5, default=0)
    num_03 = models.DecimalField(null=True, max_digits=20, decimal_places=5, default=0)
    num_04 = models.DecimalField(null=True, max_digits=20, decimal_places=5, default=0)
    num_05 = models.DecimalField(null=True, max_digits=20, decimal_places=5, default=0)

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return self.name

    class Meta:
        """class Meta du modèle django"""

        ordering = ["name"]


class Counter(FlagsTable):
    """
    Table des compteurs de l'application
    FR : Compteur
    EN : Counter
    """

    class DateType(models.TextChoices):
        """DateType choices"""

        FDM = 1, _("Fin de mois")
        DDM = 2, _("Début de mois")
        QDM = 3, _("Quinzaine")
        TDM = 4, _("Trimestriel")
        SDM = 5, _("Semestriel")
        ADA = 6, _("Début d'année")
        AFA = 7, _("Fin d'année")

    name = models.CharField(unique=True, max_length=80, verbose_name="Type de numérotation")
    prefix = models.CharField(max_length=5, verbose_name="préfix")
    iso_date = models.CharField(null=True, blank=True, max_length=10)
    date_type = models.CharField(
        null=True, blank=True, max_length=20, choices=DateType.choices, default=DateType.FDM
    )
    num = models.IntegerField(default=1)
    suffix = models.CharField(max_length=35, verbose_name="suffix")

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return self.name

    class Meta:
        """class Meta du modèle django"""

        ordering = ["name"]


class SendFiles(FlagsTable):
    """
    Table de paramétrage de l'envoi de fichier
    FR : Envoi de fichiers
    EN : SendFiles
    """

    name = models.CharField(unique=True, max_length=80, verbose_name="type d'envoi")
    file = models.CharField(max_length=35)
    description = models.CharField(null=True, blank=True, max_length=100)
    periodicity = models.CharField(null=True, blank=True, max_length=20)

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return self.name

    class Meta:
        """class Meta du modèle django"""

        ordering = ["name"]


class SendFilesMail(FlagsTable):
    """
    Table de paramétrage de l'envoi de fichier
    FR : Envoi de fichiers
    EN : SendFiles
    """

    file = models.ForeignKey(
        SendFiles,
        on_delete=models.CASCADE,
        to_field="name",
        related_name="file_send_file",
        db_column="file",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        to_field="uuid_identification",
        related_name="user_send_file",
        null=True,
        blank=True,
        db_column="user",
    )
    email = models.EmailField(null=True, blank=True)

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{self.file} - {self.user} - {self.email}"

    class Meta:
        """class Meta du modèle django"""

        ordering = ["file", "email", "user"]
        unique_together = (("file", "user", "email"),)


class AddressCode(DatesTable):
    """En attente"""

    ...


class SubFamilly(FlagsTable):
    """
    Sous Familles
    FR : Sous Familles
    EN : Sub Famillies
    """

    name = models.CharField(unique=True, max_length=80)

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return self.name

    class Meta:
        """class Meta du modèle django"""

        ordering = ["name"]


class Category(FlagsTable):
    """
    Grandes Catégories
    FR : Grandes Catégories
    EN : Categories
    """
    code = models.CharField(unique=True, max_length=15)
    name = models.CharField(unique=True, max_length=80)
    ranking = models.IntegerField(unique=True)
    slug_name = models.CharField(unique=True, max_length=120)

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{self.ranking:02d} - {self.name}"

    @staticmethod
    def get_absolute_url():
        """get absolute url in succes case"""
        return reverse("parameters:categories_list")

    def save(self, *args, **kwargs):
        """
        FR : Avant la sauvegarde on ajoute slug_name
        EN : Before the backup we add slug_name
        """
        if not self.slug_name:
            self.slug_name = slugify(self.name)

        super().save(*args, **kwargs)

    class Meta:
        """class Meta du modèle django"""

        ordering = ["ranking"]


class CategoryModelInvoice(FlagsTable):
    """
    Modèle de refacturation des Grandes Catégories
    FR : Grandes Catégories
    EN : Categories
    """

    function = models.CharField(unique=True, max_length=255)
    big_category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        null=True,
        to_field="uuid_identification",
        related_name="model_function_big_category",
        db_column="uuid_big_category",
    )

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{self.function}"

    @staticmethod
    def get_absolute_url():
        """get absolute url in succes case"""
        return reverse("parameters:categories_list")

    class Meta:
        """class Meta du modèle django"""

        ordering = ["big_category"]


class SubCategory(FlagsTable):
    """
    Sous Grandes Catégories - Rubriques Presta
    FR : Sous Grandes Catégories
    EN : Sub-Categories
    """
    code = models.CharField(unique=True, max_length=15)
    name = models.CharField(unique=True, max_length=80)
    ranking = models.IntegerField(unique=True)
    big_category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        null=True,
        to_field="uuid_identification",
        related_name="big_sub_category",
        db_column="uuid_big_category",
    )

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{self.big_category.name} - {self.ranking} - {self.name}"

    @staticmethod
    def get_absolute_url():
        """get absolute url in succes case"""
        return reverse("parameters:sub_categories_list")

    class Meta:
        """class Meta du modèle django"""

        ordering = ["ranking"]


# class UnionCategories(FlagsTable):
#     """Many to Many pour unir les Catégories aux Sous-Catégories"""
#     big_category = models.ForeignKey(
#         Category,
#         on_delete=models.PROTECT,
#         null=True,
#         to_field="uuid_identification",
#         related_name="big_sub_category",
#         db_column="uuid_big_category",
#     )
#     sub_category = models.ForeignKey(
#         SubCategory,
#         on_delete=models.PROTECT,
#         null=True,
#         to_field="uuid_identification",
#         related_name="sub_sub_category",
#         db_column="uuid_sub_big_category",
#     )
#
#     def __str__(self):
#         """Texte renvoyé dans les selects et à l'affichage de l'objet"""
#         return f"{self.big_category.name} - {self.sub_category.name}"


class Periodicity(FlagsTable):
    """
    Périodicité
    FR : Périodicité
    EN : Periodicity
    """

    name = models.CharField(unique=True, max_length=80)

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return self.name

    class Meta:
        """class Meta du modèle django"""

        ordering = ["name"]


class SalePriceCategory(FlagsTable):
    """
    Catégorie des prix de ventes. Si l'on met un coéficient alors à l'arrivée d'une nouvelle ligne
    de facture par défaut, il ira mettre le prix d'achat de la facture avec le coéficient prédéfini.
    FR : Catégorie des prix de ventes
    EN : Sale Price Category
    """

    name = models.CharField(unique=True, max_length=80)
    coefficient = models.DecimalField(max_digits=20, decimal_places=5, default=1)
    comment = models.TextField(null=True, blank=True)

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return self.name

    class Meta:
        """class Meta du modèle django"""

        ordering = ["name"]


class ActionPermission(FlagsTable):
    """
    Action et Permissions
    FR : Action / Permissions
    EN : Action / Permission
    """

    name = models.CharField(unique=True, max_length=80)

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    class Meta:
        """class Meta du modèle django"""

        ordering = ["name"]


class BaseInvoiceTable(models.Model):
    """
    Table Abstraite de base pour les Factures
    FR : Table Abstraite de Base Flags
    EN : Flags Abstract Table Flags
    """

    class ForChoices(models.IntegerChoices):
        """Frequence choices"""

        FOUR = 0, "Fournisseur"
        CLI = 1, "Client"

    uuid_file = models.UUIDField(null=True)

    invoice_number = models.CharField(max_length=35)
    invoice_date = models.DateField(verbose_name="DTM avec 3")
    invoice_month = models.DateField(null=True, blank=True)
    invoice_year = models.IntegerField(null=True, blank=True)
    invoice_type = models.CharField(
        null=True, blank=True, max_length=3, verbose_name="BGM FA:380, AV:381"
    )
    devise = models.CharField(null=True, blank=True, max_length=3, default="EUR")

    invoice_amount_without_tax = models.DecimalField(
        null=True, max_digits=20, decimal_places=5, default=0, verbose_name="MOA avec 125"
    )
    invoice_amount_tax = models.DecimalField(
        null=True, max_digits=20, decimal_places=5, default=0, verbose_name="MOA avec 150"
    )
    invoice_amount_with_tax = models.DecimalField(
        null=True, max_digits=20, decimal_places=5, default=0, verbose_name="MOA avec 128"
    )
    purchase_invoice = models.BooleanField(null=True, default=False)
    sale_invoice = models.BooleanField(null=True, default=False)
    manual_entry = models.BooleanField(null=True, default=False)

    class Meta:
        """class Meta du modèle django"""

        abstract = True


class BaseInvoiceDetailsTable(models.Model):
    """
    Table Abstraite de base pour les Détails de Factures
    FR : Table Abstraite de Base pour les Détails de Factures
    EN : Flags Abstract Table for Invoices details
    """

    class DateType(models.TextChoices):
        """DateType choices"""

        UNI = 1, _("U")
        GRA = 2, _("Grammes")
        KIL = 3, _("Kilos")
        PIE = 4, _("Pièce")
        BOI = 5, _("Boite")
        CAR = 6, _("Carton")
        JRS = 7, _("Jrs")
        MOI = 8, _("Mois")
        FOR = 9, _("Forfait")
        HEU = 10, _("Heures")
        ENS = 11, _("Ens")

    # Livraison
    acuitis_order_number = models.CharField(
        null=True, blank=True, max_length=80, verbose_name="RFF avec ON"
    )
    acuitis_order_date = models.DateField(null=True, verbose_name="DTM avec 4 quand RFF avec ON")
    delivery_number = models.CharField(
        null=True, blank=True, max_length=80, verbose_name="RFF avec AAK"
    )
    delivery_date = models.DateField(null=True, verbose_name="DTM avec 35 quand RFF avec AAK")

    # Formation
    final_date = models.DateField(null=True, verbose_name="date finale")
    first_name = models.CharField(null=True, max_length=80, verbose_name="prenom")
    last_name = models.CharField(null=True, max_length=80, verbose_name="nom")
    heures_formation = models.DecimalField(
        null=True,
        max_digits=20,
        decimal_places=5,
        default=0,
        verbose_name="nombre heures formation",
    )

    # Article
    reference_article = models.CharField(
        null=True, blank=True, max_length=150, verbose_name="LIN avec 21 et autre chose que EN"
    )
    ean_code = models.CharField(
        null=True, blank=True, max_length=35, verbose_name="LIN avec 21 et EN"
    )
    libelle = models.CharField(
        null=True, blank=True, max_length=150, verbose_name="IMD avec F dernière position"
    )
    client_name = models.CharField(null=True, blank=True, max_length=80)
    serial_number = models.TextField(null=True, blank=True, max_length=1000)
    comment = models.CharField(null=True, blank=True, max_length=120)
    command_reference = models.CharField(null=True, blank=True, max_length=120)

    # Qty / Montants
    qty = models.DecimalField(
        null=True, decimal_places=5, default=1, max_digits=20, verbose_name="QTY avec 47"
    )
    unity = models.IntegerField(
        null=True, blank=True, choices=DateType.choices, default=DateType.UNI
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

    # Sage
    axe_bu = models.ForeignKey(
        SectionSage,
        null=True,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        limit_choices_to={"axe": "BU"},
        related_name="+",
        db_column="axe_bu_uuid",
    )
    axe_prj = models.ForeignKey(
        SectionSage,
        null=True,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        limit_choices_to={"axe": "PRJ"},
        related_name="+",
        db_column="axe_prj_uuid",
    )
    axe_pro = models.ForeignKey(
        SectionSage,
        null=True,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        limit_choices_to={"axe": "PRO"},
        related_name="+",
        db_column="axe_pro_uuid",
    )
    axe_pys = models.ForeignKey(
        SectionSage,
        null=True,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        limit_choices_to={"axe": "PYS"},
        related_name="+",
        db_column="axe_pys_uuid",
    )
    axe_rfa = models.ForeignKey(
        SectionSage,
        null=True,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        limit_choices_to={"axe": "RFA"},
        related_name="+",
        db_column="axe_rfa_uuid",
    )
    bi_id = models.BigIntegerField(null=True, verbose_name="ID BI ACUITIS")

    class Meta:
        """class Meta du modèle django"""

        abstract = True


class BaseAdressesTable(models.Model):
    """
    Table Abstraite de base pour les Adresses
    FR : Table Abstraite de Base pour les Adresses
    EN : Flags Abstract Table for Adresses
    """

    immeuble = models.CharField(null=True, blank=True, max_length=200, verbose_name="immeuble")
    adresse = models.CharField(max_length=200, verbose_name="adresse")
    code_postal = models.CharField(max_length=15, verbose_name="code postal")
    ville = models.CharField(max_length=50, verbose_name="ville")
    pays = models.ForeignKey(
        Country,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        to_field="country",
        related_name="+",
        verbose_name="pays",
        db_column="pays",
    )

    class Meta:
        """class Meta du modèle django"""

        abstract = True


class ActionInProgress(FlagsTable):
    """
    Table des Actions en cours
    FR : Table des Actions en cours
    EN : Current Actions Table
    """

    action = models.CharField(unique=True, max_length=80)
    in_progress = models.BooleanField(default=False)
    comment = models.CharField(blank=True, null=True, max_length=255)

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    class Meta:
        """class Meta du modèle django"""

        ordering = ["action"]
