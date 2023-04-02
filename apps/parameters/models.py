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
from django.db.models import Q
from django.shortcuts import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from heron.models import DatesTable, FlagsTable
from apps.accountancy.models import SectionSage
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
        return f"{self.name}"

    class Meta:
        """class Meta du modèle django"""

        ordering = ["name"]


class UnitChoices(FlagsTable):
    """
    Table de paramétrage des unités
    FR : Unités
    EN : Unities
    """

    num = models.IntegerField(unique=True)
    unity = models.CharField(unique=True, max_length=80, verbose_name="unité")
    to_display = models.CharField(null=True, max_length=5)

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{self.unity}"

    class Meta:
        """class Meta du modèle django"""

        ordering = ["num"]


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
        return f"{self.name}"

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
        return f"{self.name}"

    class Meta:
        """class Meta du modèle django"""

        ordering = ["name"]


class InvoiceFunctions(FlagsTable):
    """Table des fonctions qui génèrent les factures"""

    function_name = models.CharField(unique=True, max_length=255, verbose_name="nom")
    function = models.TextField(verbose_name="fonction")
    absolute_path_windows = models.TextField(null=True, blank=True, verbose_name="dir windows")
    absolute_path_linux = models.TextField(null=True, blank=True, verbose_name="dir linux")
    description = models.CharField(null=True, blank=True, max_length=255)

    def __str__(self):
        """Texte renvoyé dans les appels à la class"""
        return f"{self.function_name}"

    @staticmethod
    def get_success_url():
        """Return the URL to redirect to after processing a valid form."""
        return reverse("parameters:functions_list")

    @staticmethod
    def get_absolute_url():
        """Return the URL to redirect to after processing a valid form."""
        return reverse("parameters:functions_list")

    class Meta:
        """class Meta du modèle django"""

        ordering = ["function_name"]
        indexes = [
            models.Index(fields=["function_name"]),
        ]


class Counter(FlagsTable):
    """
    Table des compteurs de l'application
    FR : Compteur
    EN : Counter
    """

    name = models.CharField(unique=True, max_length=80, verbose_name="Type de numérotation")
    prefix = models.CharField(null=True, max_length=35, verbose_name="préfix")
    suffix = models.CharField(null=True, max_length=35, verbose_name="suffix")
    function = models.ForeignKey(
        InvoiceFunctions,
        on_delete=models.PROTECT,
        to_field="function_name",
        related_name="counter_invoice_functions",
        db_column="function",
        null=True,
    )
    lpad_num = models.IntegerField(null=True, default=0)
    description = models.CharField(null=True, max_length=255, verbose_name="description")
    separateur = models.CharField(null=True, max_length=1, verbose_name="séparateur")

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{self.name}"

    @staticmethod
    def get_absolute_url():
        """Url de retour après create ou Update"""
        return reverse("parameters:numberings_list")

    class Meta:
        """class Meta du modèle django"""

        ordering = ["name"]
        constraints = [
            # Ensures constraint on DB level, raises IntegrityError (500 on debug=False)
            models.CheckConstraint(check=models.Q(lpad_num__gte=0), name="lpad_num_gte_0"),
        ]

    @staticmethod
    def bool_function(function):
        """Si la fonction est None en paramètre, on renvoie False"""
        if function is None:
            return False

        counters = set(
            Counter.objects.exclude(Q(function="") | Q(function__isnull=True)).values_list(
                "function", flat=True
            )
        )
        return function.function_name in counters

    def clean(self):
        """Clean method django"""
        # Ensures constraint on model level, raises ValidationError
        if self.lpad_num < 0:
            # raise error for field
            raise ValidationError({"lpad_num": _("LPAD doit être > 0.")})

        if self.pk is None and self.bool_function(self.function):
            # Controle des doublonction sur les fonctions
            raise ValidationError(
                {"function": _(f"La fonction {self.function} a déjà été utilisée")}
            )


class CounterNums(models.Model):
    """
    Table de la numérotation des compteurs
    """

    counter = models.OneToOneField(
        Counter,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        related_name="counter",
        db_column="uuid_counter",
        unique=True,
    )
    num = models.IntegerField(default=1)


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
    function = models.ForeignKey(
        InvoiceFunctions,
        on_delete=models.PROTECT,
        null=True,
        to_field="function_name",
        related_name="invoice_function",
        db_column="function_name",
    )

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


class SubCategory(FlagsTable):
    """
    Sous Grandes Catégories - Rubriques Presta
    FR : Sous Grandes Catégories
    EN : Sub-Categories
    """

    code = models.CharField(unique=True, max_length=15)
    name = models.CharField(unique=True, max_length=80)
    ranking = models.IntegerField()
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
        return f"{self.big_category.name} - {self.ranking} - {self.code} - {self.name}"

    @staticmethod
    def get_absolute_url():
        """get absolute url in succes case"""
        return reverse("parameters:categories_list")

    class Meta:
        """class Meta du modèle django"""

        unique_together = (("big_category", "ranking"),)
        ordering = ["ranking"]


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
        return f"{self.name}"

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
        return f"{self.name}"

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


class Nature(FlagsTable):
    """
    Table des natures. Ex. : Mr, Mme, SARL, ...
    FR : Table des natures
    EN : Nature table
    """

    name = models.CharField(unique=True, blank=True, max_length=80)
    to_display = models.CharField(null=True, blank=True, max_length=35)
    for_contact = models.BooleanField(default=False)
    for_personnel = models.BooleanField(default=False)
    for_formation = models.BooleanField(default=False)

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def save(self, *args, **kwargs):
        """
        FR : Avant la sauvegarde on clean les données
        EN : Before the backup we clean the data
        """
        self.name = self.name.capitalize()

        if not self.to_display:
            self.to_display = self.name

        super().save(*args, **kwargs)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return self.to_display

    @staticmethod
    def get_absolute_url():
        """Return the URL to redirect to after processing a valid form."""
        return reverse("parameters:natures_list")

    class Meta:
        """class Meta du modèle django"""

        ordering = ["name"]


class IconOriginChoice(models.Model):
    """Table des icônes pour la représentation des Origines des invoices"""

    origin = models.IntegerField(unique=True)
    origin_name = models.CharField(max_length=35)
    icon = models.CharField(max_length=50)


class BaseInvoiceTable(models.Model):
    """
    Table Abstraite de base pour les Factures
    FR : Table Abstraite de Base Flags
    EN : Flags Abstract Table Flags
    """

    uuid_file = models.UUIDField(null=True)

    invoice_type = models.CharField(
        null=True,
        blank=True,
        max_length=10,
        verbose_name="FA:380, AV:381",
    )
    invoice_number = models.CharField(max_length=35)
    invoice_date = models.DateField(verbose_name="DTM avec 3")
    invoice_month = models.DateField(null=True, blank=True)
    invoice_year = models.IntegerField(null=True, blank=True)
    devise = models.CharField(null=True, blank=True, max_length=3, default="EUR")

    # Achats
    invoice_amount_without_tax = models.DecimalField(
        null=True, max_digits=20, decimal_places=5, default=0
    )
    invoice_amount_tax = models.DecimalField(null=True, max_digits=20, decimal_places=5, default=0)
    invoice_amount_with_tax = models.DecimalField(
        null=True, max_digits=20, decimal_places=5, default=0
    )
    purchase_invoice = models.BooleanField(null=True, default=False)
    sale_invoice = models.BooleanField(null=True, default=False)
    manual_entry = models.BooleanField(null=True, default=False)
    code_center = models.CharField(null=True, max_length=15, verbose_name="code centrale fille")
    code_signboard = models.CharField(null=True, max_length=15, verbose_name="code enseigne")

    class Meta:
        """class Meta du modèle django"""

        abstract = True


class BaseInvoiceDetailsTable(models.Model):
    """
    Table Abstraite de base pour les Détails de Factures
    FR : Table Abstraite de Base pour les Détails de Factures
    EN : Flags Abstract Table for Invoices details
    """

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
    base_discount_01 = models.DecimalField(null=True, max_digits=20, decimal_places=5, default=0)
    discount_price_01 = models.DecimalField(
        null=True,
        max_digits=20,
        decimal_places=5,
        default=0,
        verbose_name="remise 1 MOA avec 8 quand ALC avec H",
    )
    base_discount_02 = models.DecimalField(null=True, max_digits=20, decimal_places=5, default=0)
    discount_price_02 = models.DecimalField(
        null=True,
        max_digits=20,
        decimal_places=5,
        default=0,
        verbose_name="remise 2 MOA avec 8 quand ALC avec H",
    )
    base_discount_03 = models.DecimalField(null=True, max_digits=20, decimal_places=5, default=0)
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
    unit_weight = models.ForeignKey(
        UnitChoices,
        on_delete=models.PROTECT,
        to_field="num",
        related_name="+",
        db_column="unit_weight",
        null=True,
    )

    class Meta:
        """class Meta du modèle django"""

        abstract = True


class BaseCommonDetailsTable(models.Model):
    """
    Table Abstraite de base pour lignes communes entre aachats et ventes
    FR : Table Abstraite de base pour des artilces facturés
    EN : Basic Abstract Table for Invoiced Items
    """
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

    # Livraison
    acuitis_order_number = models.CharField(
        null=True, blank=True, max_length=80, verbose_name="RFF avec ON"
    )
    acuitis_order_date = models.DateField(null=True, verbose_name="DTM avec 4 quand RFF avec ON")
    delivery_number = models.CharField(
        null=True, blank=True, max_length=80, verbose_name="RFF avec AAK"
    )
    delivery_date = models.DateField(null=True, verbose_name="DTM avec 35 quand RFF avec AAK")
    client_name = models.CharField(null=True, blank=True, max_length=80)
    comment = models.CharField(null=True, blank=True, max_length=120)
    command_reference = models.CharField(null=True, blank=True, max_length=120)

    # Qty / Montants
    qty = models.DecimalField(
        null=True, decimal_places=5, default=1, max_digits=20, verbose_name="QTY avec 47"
    )
    item_weight = models.DecimalField(null=True, max_digits=20, decimal_places=5, default=0)
    origin = models.ForeignKey(
        IconOriginChoice,
        null=True,
        on_delete=models.PROTECT,
        to_field="origin",
        related_name="+",
        db_column="origin",
    )
    saisie = models.BooleanField(null=True)
    saisie_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        to_field="uuid_identification",
        db_column="saisie_by",
    )
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        to_field="uuid_identification",
        db_column="modified_by",
    )
    bi_id = models.BigIntegerField(null=True, verbose_name="ID BI ACUITIS")
    flow_name = models.CharField(max_length=80, default="Saisie")
    customs_code = models.CharField(null=True, blank=True, max_length=35)
    supplier = models.CharField(null=True, blank=True, max_length=35)

    # Formation
    initial_home = models.CharField(null=True, blank=True, max_length=15)
    initial_date = models.DateField(null=True, verbose_name="date initiale")
    final_date = models.DateField(null=True, verbose_name="date finale")
    first_name = models.CharField(null=True, blank=True, max_length=80, verbose_name="prenom")
    last_name = models.CharField(null=True, blank=True, max_length=80, verbose_name="nom")
    heures_formation = models.DecimalField(
        null=True,
        max_digits=20,
        decimal_places=5,
        default=0,
        verbose_name="nombre heures formation",
    )
    formation_month = models.DateField(null=True, verbose_name="Mois concerné")

    # Personnel
    personnel_type = models.CharField(null=True, max_length=80)

    # N° de serie
    serial_number = models.TextField(null=True, blank=True)

    class Meta:
        """class Meta du modèle django"""

        abstract = True


class BaseAdressesTable(models.Model):
    """
    Table Abstraite de base pour les Adresses
    FR : Table Abstraite de Base pour les Adresses
    EN : Flags Abstract Table for Adresses
    """

    name = models.CharField(null=True, blank=True, max_length=80)
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


class DefaultAxeArticle(FlagsTable):
    """Table des axes par défaut du catalogue article à part sur l'axe Pro et les categories"""

    slug_name = models.CharField(unique=True, max_length=15)
    big_category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        null=True,
        to_field="uuid_identification",
        related_name="default_big_category",
        db_column="uuid_big_category",
    )
    sub_category = models.ForeignKey(
        SubCategory,
        on_delete=models.PROTECT,
        null=True,
        to_field="uuid_identification",
        related_name="default_sub_category",
        db_column="uuid_sub_big_category",
    )
    axe_bu = models.ForeignKey(
        SectionSage,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        limit_choices_to={"axe": "BU"},
        related_name="default_bu_section",
        db_column="axe_bu",
    )
    axe_prj = models.ForeignKey(
        SectionSage,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        limit_choices_to={"axe": "PRJ"},
        related_name="default_prj_section",
        db_column="axe_prj",
    )
    axe_pys = models.ForeignKey(
        SectionSage,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        limit_choices_to={"axe": "PYS"},
        related_name="default_pys_section",
        db_column="axe_pys",
    )
    axe_rfa = models.ForeignKey(
        SectionSage,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        limit_choices_to={"axe": "RFA"},
        related_name="default_rfa_section",
        db_column="axe_rfa",
    )

    @staticmethod
    def get_absolute_url():
        """Url de retour après create ou Update"""
        return reverse("parameters:axes_articles_defaut", kwargs={"slug_name": "axes_articles"})

    class Meta:
        """class Meta du modèle django"""

        ordering = ["id"]
