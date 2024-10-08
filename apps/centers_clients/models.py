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
from django.core.exceptions import ValidationError

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
from apps.parameters.models import SalePriceCategory, Nature, InvoiceFunctions, UnitChoices
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


class TypeVente(models.Model):
    """
    Table des types de vente
        0: BLOCAGE
        1: VENTE
        2: OD ANA
    """
    num = models.IntegerField(unique=True)
    name = models.CharField(max_length=20)

    class Meta:
        """class Meta du modèle django"""
        ordering = ["num"]

    def __str__(self):
        """Retourne le str de la class"""
        return f"{self.name}"


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
        limit_choices_to={"is_client": True},
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
    invoice_entete = models.CharField(null=True, blank=True, max_length=50)
    client_familly = models.ForeignKey(
        ClientFamilly,
        on_delete=models.PROTECT,
        to_field="name",
        related_name="maison_client_familly",
        verbose_name="catégorie client",
        db_column="client_familly",
    )

    code_maison = models.CharField(null=True, blank=True, max_length=30, verbose_name="code maison")
    code_cosium = models.CharField(null=True, blank=True, max_length=30, verbose_name="code cosium")
    reference_cosium = models.CharField(
        null=True, blank=True, max_length=35, verbose_name="référence cosium"
    )
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
        limit_choices_to={"collective": True},
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
        limit_choices_to={"collective": True},
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
    axe_bu = models.ForeignKey(
        SectionSage,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        limit_choices_to={"axe": "BU"},
        related_name="cct_bu",
        db_column="axe_bu",
    )
    axe_pys = models.ForeignKey(
        SectionSage,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        limit_choices_to={"axe": "PYS"},
        related_name="cct_pys",
        db_column="axe_pys",
    )
    axe_prj = models.ForeignKey(
        SectionSage,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        limit_choices_to={"axe": "PRJ"},
        related_name="cct_prj",
        db_column="axe_prj",
    )
    axe_rfa = models.ForeignKey(
        SectionSage,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        limit_choices_to={"axe": "RFA"},
        related_name="cct_rfa",
        db_column="axe_rfa",
    )

    # Identifiants magasin
    siren_number = models.CharField(null=True, blank=True, max_length=20, verbose_name="siren")
    siret_number = models.CharField(null=True, blank=True, max_length=20, verbose_name="siret")
    vat_cee_number = models.CharField(
        null=True, blank=True, max_length=20, verbose_name="tva intracommunataire"
    )

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    # type de vente X3 (BLOCAGE - aucune vente, VENTE - BICPA, OD SUCC - GASPA OD ANA)
    type_x3 = models.ForeignKey(
        TypeVente,
        on_delete=models.PROTECT,
        to_field="num",
        related_name="cct_type_vente",
        db_column="type_x3",
        default=0
    )

    def clean(self):
        # Ensures constraint on model level, raises ValidationError
        if self.type_x3 == 2 and not self.axe_bu:
            # raise error for field
            raise ValidationError(
                {
                    "axe_bu": _(
                        "Si vous avez sélectionné OD-ANA dans type Vente, "
                        "Alors l'axe BU est obligatoire!"
                    )
                }
            )

        # Si le type n'est pas OD-ANA alors il ne faut pas d'axe BU
        if self.type_x3 != 2:
            self.axe_bu = None

        # Vérifiaction de l'unicité sur la référence Cosium
        if self.reference_cosium:
            exist_list = Maison.objects.filter(reference_cosium=self.reference_cosium).values_list(
                "cct", flat=True
            )
            if exist_list and self.cct.cct not in set(exist_list):
                raise ValidationError(
                    {
                        "reference_cosium": _(
                            f"La référence Cosium existe déjà {exist_list[0]}"
                        )
                    }
                )

        # On vérifie que le compte au crédit soit bien un compte collectif
        if self.credit_account and not self.credit_account.collective:
            raise ValidationError(
                    {
                        "credit_account": _(
                            "Le compte au crédit choisi, doit être un compte collectif !"
                        )
                    }
            )

        # On vérifie que le compte au débit soit bien un compte collectif
        if self.debit_account and not self.debit_account.collective:
            raise ValidationError(
                    {
                        "debit_account": _(
                            "Le compte au débit choisi, doit être un compte collectif !"
                        )
                    }
            )

        # On s'assure que le Tiers X3 client est bien un client
        if self.third_party_num and not self.third_party_num.is_client:
            raise ValidationError(
                    {
                        "third_party_num": _(
                            "Le Tiers Client X3 doît être un client dans Sage X3 !"
                        )
                    }
            )

    def save(self, *args, **kwargs):
        """
        FR : Avant la sauvegarde on clean les données
        EN : Before the backup we clean the data
        """

        if not self.code_maison:
            self.code_maison = self.cct.cct
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
    code_maison = models.CharField(primary_key=True, max_length=30, verbose_name="code maison")
    intitule = models.CharField(null=True, blank=True, max_length=50)
    intitule_court = models.CharField(null=True, blank=True, max_length=20)
    code_cosium = models.CharField(null=True, blank=True, max_length=30, verbose_name="code cosium")
    reference_cosium = models.CharField(
        null=True, blank=True, max_length=30, verbose_name="code cosium"
    )
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
    cct_uuid_identification = models.ForeignKey(
        Maison,
        on_delete=models.CASCADE,
        to_field="uuid_identification",
        related_name="cct_to_discard",
        verbose_name="CCT x3",
        db_column="cct_uuid_identification",
    )

    def __str__(self):
        return f"{self.third_party_num} - {self.cct_uuid_identification.cct.cct}"

    @staticmethod
    def get_success_url():
        """Surcharge de l'url en case de succes pour revenir à l'écran d'accueil'"""
        return reverse("home")

    class Meta:
        """class Meta du modèle django"""

        ordering = ["third_party_num", "cct_uuid_identification"]
        unique_together = (("third_party_num", "cct_uuid_identification"),)
        indexes = [
            models.Index(fields=["third_party_num"]),
            models.Index(fields=["cct_uuid_identification"]),
            models.Index(
                fields=[
                    "third_party_num",
                    "cct_uuid_identification",
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
    pays = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        to_field="country",
        related_name="country_tiers",
        verbose_name="pays",
        db_column="pays",
    )

    def __str__(self):
        return f"{self.third_party_num} - {self.pays}"

    @staticmethod
    def get_success_url():
        """Surcharge de l'url en case de succes pour revenir à l'écran d'accueil'"""
        return reverse("home")

    class Meta:
        """class Meta du modèle django"""

        ordering = ["third_party_num", "pays"]
        unique_together = (("third_party_num", "pays"),)
        indexes = [
            models.Index(fields=["third_party_num"]),
            models.Index(fields=["pays"]),
            models.Index(
                fields=[
                    "third_party_num",
                    "pays",
                ]
            ),
        ]


class MaisonSubcription(FlagsTable):
    """Table des souscriptions des abonnnements par maisons
    FR : Table des souscriptions des abonnnements par maisonss
    EN : Flags Abstract Table for Invoices details
    """

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
    unit_weight = models.ForeignKey(
        UnitChoices,
        on_delete=models.PROTECT,
        to_field="num",
        related_name="unity_subscription",
        db_column="unit_weight",
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
        default="ACF",
    )

    @staticmethod
    def get_columns_import():
        """
        FR : Retourne la position des colonnes
        EN : Returns the position of the columns
        """
        return {
            "maison": 0,
            "article": 1,
            "qty": 2,
            "unit_weight": 3,
            "net_unit_price": 4,
            "function": 5,
            "for_signboard": 6,
        }

    @staticmethod
    def get_uniques():
        """
        FR : Retourne les champs uniques de la table
        EN: Returns the unique fields of the table
        """
        return {"maison", "article", "function", "for_signboard"}

    @staticmethod
    def get_absolute_url():
        """get absolute url in succes case"""
        return reverse("centers_clients:subscriptions_list")

    @staticmethod
    def get_success_url():
        """Return the URL to redirect to after processing a valid form."""
        return reverse("centers_clients:subscriptions_list")

    class Meta:
        """class Meta du modèle django"""

        ordering = ["maison", "function", "article"]
        unique_together = (
            (
                "maison",
                "function",
                "article",
                "for_signboard",
            ),
        )
        indexes = [
            models.Index(fields=["maison"]),
            models.Index(fields=["function"]),
            models.Index(fields=["article"]),
            models.Index(fields=["for_signboard"]),
            models.Index(
                fields=[
                    "maison",
                    "function",
                ]
            ),
            models.Index(
                fields=[
                    "maison",
                    "function",
                    "article",
                    "for_signboard",
                ]
            ),
        ]
