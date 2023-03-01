# pylint: disable=
# E0401,R0903
"""
FR : Module du modèle des maisons
EN : Houses model module

Commentaire:

created at: 2022-04-07
created by: Paulo ALVES

modified at: 2022-04-07
modified by: Paulo ALVES
"""
import uuid

from django.db import models
from django.shortcuts import reverse
from django.utils.translation import gettext_lazy as _

from heron.models import FlagsTable

from apps.accountancy.models import (
    AccountSage,
    CctSage,
    CodePlanSage,
    VatSage,
    TabDivSage,
    SectionSage,
)
from apps.book.models import Society
from apps.centers_purchasing.models import ChildCenterPurchase, Signboard
from apps.parameters.models import SalePriceCategory, Nature, InvoiceFunctions
from apps.countries.models import Country, Language, Currency
from apps.articles.models import Article

CHOICES_LANGUE = (
    ("FRA", "Français"),
    ("ANG", "Anglais"),
    ("ALL", "Allemand"),
    ("ESP", "Espagnol"),
    ("POR", "Portugais"),
)


class ClientFamilly(FlagsTable):
    """
    Table des familles des maisons
    FR : Table des Familles
    EN : Families table
    """

    name = models.CharField(unique=True, max_length=80)
    comment = models.CharField(null=True, blank=True, max_length=255)

    def save(self, *args, **kwargs):
        """
        FR : Avant la sauvegarde on clean les données
        EN : Before the backup we clean the data
        """
        self.name = self.name.capitalize()

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        """class Meta du modèle django"""

        ordering = ["name"]


class Maison(FlagsTable):
    """
    Table des Maisons
    FR : Table des Maisons
    EN : Shop table
    """

    class Frequence(models.IntegerChoices):
        """Frequence choices"""

        AUCUNE = 0, _("---------")
        MENSUEL = 1, _("Mensuel")
        TRIMESTRIEL = 2, _("Trimestriel")
        SEMESTRIEL = 3, _("Semestriel")
        ANNUEL = 4, _("Annuel")

    class Remise(models.IntegerChoices):
        """Remise choices"""

        AUCUNE = 0, _("---------")
        TOTAL = 1, _("Fournisseur Total")
        FAMILLE = 2, _("Famille Article")
        ARTICLE = 3, _("Article")

    cct = models.OneToOneField(
        CctSage,
        unique=True,
        on_delete=models.PROTECT,
        to_field="cct",
        related_name="maison_cct",
        verbose_name="cct x3",
        db_column="cct",
    )
    third_party_num = models.ForeignKey(
        Society,
        on_delete=models.CASCADE,
        to_field="third_party_num",
        related_name="tiers_maison",
        verbose_name="tiers X3",
        db_column="third_party_num",
    )
    center_purchase = models.ForeignKey(
        ChildCenterPurchase,
        on_delete=models.PROTECT,
        to_field="code",
        related_name="maison_center_purchase",
        verbose_name="Centrale Fille",
        db_column="center_purchase",
    )
    sign_board = models.ForeignKey(
        Signboard,
        on_delete=models.PROTECT,
        to_field="code",
        related_name="maison_sign_board",
        verbose_name="Enseigne",
        db_column="sign_board",
    )
    intitule = models.CharField(max_length=50)
    intitule_court = models.CharField(max_length=20)
    client_familly = models.ForeignKey(
        ClientFamilly,
        on_delete=models.PROTECT,
        to_field="name",
        related_name="maison_client_familly",
        verbose_name="catégorie client",
        db_column="client_familly",
    )

    code_maison = models.CharField(null=True, blank=True, max_length=15, verbose_name="code maison")
    code_cosium = models.CharField(null=True, blank=True, max_length=15, verbose_name="code cosium")
    code_bbgr = models.CharField(null=True, blank=True, max_length=15, verbose_name="code BBGR")
    opening_date = models.DateField(verbose_name="date d'ouveture")
    closing_date = models.DateField(null=True, blank=True, verbose_name="date de fermeture")
    signature_franchise_date = models.DateField(null=True, verbose_name="date de signature contrat")
    agreement_franchise_end_date = models.DateField(
        null=True, blank=True, verbose_name="date de signature de fin de contrat"
    )
    agreement_renew_date = models.DateField(
        null=True, blank=True, verbose_name="date de renouvellement contrat"
    )
    entry_fee_amount = models.DecimalField(
        max_digits=20,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name="montant de droit d'entrée",
    )
    renew_fee_amoount = models.DecimalField(
        max_digits=20,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name="montant de droit de renouvellement",
    )
    sale_price_category = models.ForeignKey(
        SalePriceCategory,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        to_field="uuid_identification",
        related_name="maison_sale_price_category",
        verbose_name="categorie de prix",
        db_column="uuid_sale_price_category",
    )
    generic_coefficient = models.DecimalField(
        null=True,
        max_digits=20,
        decimal_places=5,
        default=1,
        verbose_name="coeficient de vente générique",
    )
    credit_account = models.ForeignKey(
        AccountSage,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        to_field="uuid_identification",
        related_name="credit_account",
        verbose_name="compte X3 par défaut au crédit",
        db_column="credit_account",
    )
    debit_account = models.ForeignKey(
        AccountSage,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        to_field="uuid_identification",
        related_name="debit_account",
        verbose_name="compte X3 par défaut au débit",
        db_column="debit_account",
    )
    prov_account = models.ForeignKey(
        AccountSage,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        to_field="uuid_identification",
        related_name="prov_account",
        verbose_name="compte X3 par défaut sur provision",
        db_column="prov_account",
    )
    extourne_account = models.ForeignKey(
        AccountSage,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        to_field="uuid_identification",
        related_name="extourne_account",
        verbose_name="compte X3 par défaut sur extourne",
        db_column="extourne_account",
    )
    budget_code = models.ForeignKey(
        TabDivSage,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        limit_choices_to={"num_table": "6100"},
        related_name="budget_code_client_tab_div",
        verbose_name="code budget",
        db_column="budget_code",
    )
    sage_vat_by_default = models.ForeignKey(
        VatSage,
        on_delete=models.PROTECT,
        to_field="vat",
        related_name="vat_sage_maison",
        verbose_name="tva X3 par défaut",
        db_column="sage_vat_by_default",
    )
    sage_plan_code = models.ForeignKey(
        CodePlanSage,
        on_delete=models.PROTECT,
        to_field="code_plan_sage",
        related_name="code_plan_sage_maison",
        verbose_name="Plan Sage par défaut",
        db_column="sage_plan_code",
    )

    # RFA
    rfa_frequence = models.IntegerField(
        choices=Frequence.choices,
        default=Frequence.MENSUEL,
        verbose_name="fréquence des rfa",
    )
    rfa_remise = models.IntegerField(
        choices=Remise.choices,
        default=Remise.TOTAL,
        verbose_name="taux de remboursement rfa",
    )

    invoice_client_name = models.CharField(
        null=True, blank=True, max_length=80, verbose_name="Nom pour l'identifiant Client"
    )
    currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        to_field="code",
        related_name="currency_maison",
        verbose_name="Devise",
        db_column="currency",
        default="EUR",
    )
    language = models.ForeignKey(
        Language,
        on_delete=models.PROTECT,
        to_field="code",
        related_name="language_maison",
        verbose_name="Langue",
        db_column="language",
        default="FRA",
    )

    # Adresse Maison
    immeuble = models.CharField(null=True, blank=True, max_length=200, verbose_name="immeuble")
    adresse = models.CharField(max_length=200, verbose_name="adresse")
    code_postal = models.CharField(max_length=15, verbose_name="code postal")
    ville = models.CharField(max_length=50, verbose_name="ville")
    pays = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        to_field="country",
        related_name="country_maison_country",
        verbose_name="pays",
        db_column="pays",
    )
    telephone = models.CharField(null=True, blank=True, max_length=25, verbose_name="téléphone")
    mobile = models.CharField(null=True, blank=True, max_length=25, verbose_name="mobile")
    email = models.EmailField(null=True, blank=True, max_length=85, verbose_name="email")

    # Système pour les fichiers d'export vers Sage X3
    integrable = models.BooleanField(null=True, default=True, verbose_name="à intégrer X3")
    chargeable = models.BooleanField(null=True, default=True, verbose_name="à refacturer")
    od_ana = models.BooleanField(null=True, default=False, verbose_name="OD Analytique")

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def save(self, *args, **kwargs):
        """
        FR : Avant la sauvegarde on clean les données
        EN : Before the backup we clean the data
        """

        if not self.code_maison:
            self.code_maison = self.cct
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.cct} - {self.intitule}"

    @property
    def get_address(self):
        """Renvoie le nom à afficher"""
        values_list = [self.intitule, self.immeuble, self.adresse, self.code_postal, self.ville]
        intitule_list = [value for value in values_list[:-2] if value]
        lieux_liste = [value for value in values_list[-2:] if value]
        intitule = ", ".join(intitule_list) if intitule_list else ""
        lieux = (" - " + " ".join(lieux_liste)) if lieux_liste else ""
        return f"{intitule}{lieux}"

    @staticmethod
    def get_absolute_url():
        return reverse("centers_clients:maisons_list")

    class Meta:
        """class Meta du modèle django"""

        ordering = ["cct"]
        indexes = [
            models.Index(fields=["cct"]),
            models.Index(fields=["third_party_num"]),
            models.Index(fields=["center_purchase"]),
            models.Index(fields=["sign_board"]),
            models.Index(fields=["intitule"]),
            models.Index(fields=["currency"]),
            models.Index(fields=["language"]),
            models.Index(fields=["pays"]),
            models.Index(
                fields=[
                    "cct",
                    "third_party_num",
                    "center_purchase",
                    "sign_board",
                    "intitule",
                    "currency",
                    "language",
                    "pays",
                ]
            ),
        ]


class DocumentsSubscription(FlagsTable):
    """
    Abonnements des envois de documents aux contacts
    FR : Table des abonnements aux envois de documents
    EN : Table of subscriptions to sending documents
    """

    name = models.CharField(unique=True, max_length=80)
    comment = models.TextField(null=True, blank=True)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return self.name

    class Meta:
        """class Meta du modèle django"""

        ordering = ["name"]


class Contact(FlagsTable):
    """
    Contact des Maisons
    FR : Table des Maisons
    EN : Table of Shops
    """

    maison = models.ForeignKey(
        Maison,
        on_delete=models.CASCADE,
        to_field="cct",
        related_name="contact_cct",
        db_column="cct",
        verbose_name="maison",
    )
    nature = models.ForeignKey(
        Nature,
        on_delete=models.PROTECT,
        to_field="name",
        related_name="contact_nature_cct",
        null=True,
        limit_choices_to={"for_contact": True},
        db_column="nature",
        verbose_name="Nature",
    )
    first_name = models.CharField(null=True, blank=True, max_length=80, verbose_name="Prénom")
    last_name = models.CharField(null=True, blank=True, max_length=80, verbose_name="Nom")
    language = models.ForeignKey(
        Language,
        on_delete=models.PROTECT,
        to_field="code",
        related_name="language_contact_cct",
        verbose_name="Langue",
        db_column="language",
        default="FRA",
    )

    phone_number = models.CharField(null=True, blank=True, max_length=35, verbose_name="N° Tél.")
    mobile_number = models.CharField(null=True, blank=True, max_length=35, verbose_name="N° Mobile")
    email = models.EmailField(null=True, blank=True, verbose_name="e-mail")

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{self.first_name}{' - ' if self.first_name else ''}{self.last_name}"

    class Meta:
        """class Meta du modèle django"""

        ordering = ["last_name", "first_name"]


class ContactExchange(models.Model):
    """
    Relation many to Many entre les contacts et les documents auxquels ils ont le droit
    FR : Table des Contact / Documents
    EN : Table of Contacts / Documents
    """

    contact = models.ForeignKey(
        Contact,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        related_name="exchange_contact",
        db_column="contact",
    )
    document = models.ForeignKey(
        DocumentsSubscription,
        on_delete=models.PROTECT,
        to_field="name",
        related_name="document_contact",
        db_column="document",
    )

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{self.contact} - {self.document}"

    class Meta:
        """class Meta du modèle django"""

        ordering = ["contact", "document"]


class MaisonBi(models.Model):
    """
    Table des Maisons issue de la B.I
    FR : Table des Maisons
    EN : Shop table
    """

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("created at"))
    code_maison = models.CharField(primary_key=True, max_length=15, verbose_name="code maison")
    intitule = models.CharField(null=True, blank=True, max_length=50)
    intitule_court = models.CharField(null=True, blank=True, max_length=20)
    code_cosium = models.CharField(null=True, blank=True, max_length=15, verbose_name="code cosium")
    code_bbgr = models.CharField(null=True, blank=True, max_length=15, verbose_name="code BBGR")
    opening_date = models.DateField(null=True, verbose_name="date d'ouveture")
    closing_date = models.DateField(null=True, verbose_name="date de fermeture")
    immeuble = models.CharField(null=True, blank=True, max_length=200, verbose_name="immeuble")
    adresse = models.CharField(null=True, blank=True, max_length=200, verbose_name="adresse")
    code_postal = models.CharField(null=True, blank=True, max_length=15, verbose_name="code postal")
    ville = models.CharField(null=True, blank=True, max_length=50, verbose_name="ville")
    pays = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        to_field="country",
        related_name="coutry_maison_bi_country",
        null=True,
        verbose_name="pays",
        db_column="pays",
    )
    telephone = models.CharField(null=True, blank=True, max_length=25, verbose_name="téléphone")
    email = models.EmailField(null=True, blank=True, max_length=85, verbose_name="email")
    is_new = models.BooleanField(default=True)
    is_modify = models.BooleanField(default=False)


class MaisonSupllierExclusion(FlagsTable):
    """
    Table des identifiants des Maisons/Tiers X3 ne devant pas donner lieu à facturation
    FR : Table Identifiants Maisons/Tiers
    EN : Shop/Suppliers Identifiers Table
    """

    third_party_num = models.ForeignKey(
        Society,
        on_delete=models.PROTECT,
        to_field="third_party_num",
        related_name="supplier_to_discard",
        db_column="third_party_num",
    )
    maison = models.ForeignKey(
        Maison,
        on_delete=models.CASCADE,
        to_field="cct",
        related_name="cct_to_discard",
        db_column="maison",
        verbose_name="maison",
    )

    def __str__(self):
        return f"{self.third_party_num} - {self.maison}"

    @staticmethod
    def get_success_url():
        """Surcharge de l'url en case de succes pour revenir à l'écran d'accueil'"""
        return reverse("home")

    class Meta:
        """class Meta du modèle django"""

        ordering = ["third_party_num", "maison"]
        unique_together = (("third_party_num", "maison"),)
        indexes = [
            models.Index(fields=["third_party_num"]),
            models.Index(fields=["maison"]),
            models.Index(
                fields=[
                    "third_party_num",
                    "maison",
                ]
            ),
        ]


class MaisonSupplierIdentifier(FlagsTable):
    """
    Table des identifiants des Tiers X3 pour les Maisons (pour les fournisseurs edi)
    FR : Table Identifiants Maisons/Tiers
    EN : Shop/Suppliers Identifiers Table
    """

    third_party_num = models.ForeignKey(
        Society,
        on_delete=models.CASCADE,
        to_field="third_party_num",
        related_name="third_party_identifier",
        verbose_name="tiers X3",
        db_column="third_party_num",
    )
    maison = models.ForeignKey(
        Maison,
        on_delete=models.CASCADE,
        to_field="cct",
        related_name="cct_identifier",
        db_column="maison",
        verbose_name="maison",
    )
    identifiant = models.CharField(max_length=35, verbose_name="Identifiant Maison")

    def __str__(self):
        return f"{self.third_party_num} - {self.maison}"

    class Meta:
        """class Meta Django"""

        unique_together = (("third_party_num", "maison"),)

        indexes = [
            models.Index(fields=["third_party_num"]),
            models.Index(fields=["maison"]),
            models.Index(fields=["identifiant"]),
            models.Index(
                fields=[
                    "third_party_num",
                    "maison",
                ]
            ),
            models.Index(
                fields=[
                    "third_party_num",
                    "maison",
                    "identifiant",
                ]
            ),
        ]


class SupllierCountryExclusion(FlagsTable):
    """
    Table des identifiants des Tiers X3/Pays ne devant pas donner lieu à facturation
    FR : Table Identifiants Tiers X3/Pays
    EN : Suppliers/Countries Identifiers Table
    """

    third_party_num = models.ForeignKey(
        Society,
        on_delete=models.PROTECT,
        to_field="third_party_num",
        related_name="supplier_exclusion",
        db_column="third_party_num",
    )
    country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        to_field="country",
        related_name="pys_exclusion",
        db_column="country",
        verbose_name="Pays",
    )

    def __str__(self):
        return f"{self.third_party_num} - {self.country}"

    @staticmethod
    def get_success_url():
        """Surcharge de l'url en case de succes pour revenir à l'écran d'accueil'"""
        return reverse("home")

    class Meta:
        """class Meta du modèle django"""

        ordering = ["third_party_num", "country"]
        unique_together = (("third_party_num", "country"),)
        indexes = [
            models.Index(fields=["third_party_num"]),
            models.Index(fields=["country"]),
            models.Index(
                fields=[
                    "third_party_num",
                    "country",
                ]
            ),
        ]


class MaisonSubcription(FlagsTable):
    """Table des souscriptions des abonnnements par maisons
    FR : Table des souscriptions des abonnnements par maisonss
    EN : Flags Abstract Table for Invoices details
    """

    class UnitChoice(models.IntegerChoices):
        """DateType choices"""

        UNI = 1, _("U")
        GRA = 2, _("Grammes")
        KIL = 3, _("Kg")
        PIE = 4, _("Pièce")
        BOI = 5, _("Boite")
        CAR = 6, _("Carton")
        JRS = 7, _("Jrs")
        MOI = 8, _("Mois")
        FOR = 9, _("Forfait")
        HEU = 10, _("Heures")
        ENS = 11, _("Ens")
        POU = 12, _("%")

    maison = models.ForeignKey(
        Maison,
        on_delete=models.CASCADE,
        to_field="cct",
        related_name="cct_subscription",
        db_column="cct",
        verbose_name="maison",
    )
    article = models.ForeignKey(
        Article,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        related_name="article_subscription",
        db_column="article",
    )
    qty = models.DecimalField(
        null=True, decimal_places=5, default=1, max_digits=20, verbose_name="quantity"
    )
    unity = models.IntegerField(
        choices=UnitChoice.choices, default=UnitChoice.UNI
    )
    net_unit_price = models.DecimalField(
        null=True,
        max_digits=20,
        decimal_places=5,
        default=0,
        verbose_name="prix unitaire",
    )
    function = models.ForeignKey(
        InvoiceFunctions,
        on_delete=models.PROTECT,
        to_field="function_name",
        related_name="function_subscription",
        db_column="function",
    )
    for_signboard = models.ForeignKey(
        Signboard,
        null=True,
        on_delete=models.PROTECT,
        to_field="code",
        related_name="signborad_subscription",
        db_column="for_signboard",
    )
