# pylint: disable=E0401,R0903
"""
FR : Module du modèle de répertoire, des fournisseurs et clients. Les modèles peuvent être liés
     aux modèles Sage de l'application Accountancy, et mis à jours depuis Sage X3
EN : Directory model module, suppliers and customers. Models can be linked
     to the Sage models of the Accountancy application, and updated from Sage X3

Commentaire:

created at: 2021-11-07
created by: Paulo ALVES

modified at: 2021-11-07
modified by: Paulo ALVES
"""
import uuid

from django.db import models
from django.utils.translation import ugettext_lazy as _

from heron.models import FlagsTable

from apps.accountancy.models import AccountSage, PaymentCondition, TabDivSage, CategorySage
from apps.centers_purchasing.models import Signboard
from apps.countries.models import Country
from apps.parameters.models import SalePriceCategory

# Validation xml tva intra : https://ec.europa.eu/taxation_customs/vies/faq.html#item_18
#                            https://ec.europa.eu/taxation_customs/vies/technicalInformation.html


class Nature(FlagsTable):
    """
    Table des natures. Ex. : Mr, Mme, SARL, ...
    FR : Table des natures
    EN : Nature table
    """

    name = models.CharField(unique=True, blank=True, max_length=35)
    to_display = models.CharField(null=True, blank=True, max_length=35)
    for_contact = models.BooleanField(null=True, default=None)

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
        return self.to_display

    class Meta:
        """class Meta du modèle django"""

        ordering = ["name"]


class Society(FlagsTable):
    """
    Répertoire des sociétés Fournisseurs / CLients,
    correspondant à la table BPSUPPLIER, BPCUSTOMER des tiers Sage X3
    FR : Table des sociétés
    EN : Societies table
    """

    class Frequence(models.TextChoices):
        """Frequence choices"""

        MENSUEL = 1, _("Mensuel")
        TRIMESTRIEL = 2, _("Trimestriel")
        SEMESTRIEL = 3, _("Semestriel")
        ANNUEL = 4, _("Annuel")

    class Remise(models.TextChoices):
        """Remise choices"""

        TOTAL = 1, _("Fournisseur Total")
        FAMILLE = 2, _("Famille Article")
        ARTICLE = 3, _("Article")

    nature = models.ForeignKey(
        Nature,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        related_name="society_nature",
        null=True,
    )
    short_name = models.CharField(
        null=True, blank=True, max_length=20, verbose_name="intitulé Court"
    )  # BPRSHO
    name = models.CharField(max_length=80)  # BPRNAM_0
    corporate_name = models.CharField(
        null=True, blank=True, max_length=80, verbose_name="raison sociale"
    )  # BPRNAM_1
    code_tiers_x3 = models.CharField(
        null=True, blank=True, max_length=15, verbose_name="tiers X3"
    )  # BPRNUM
    code_plan_sage = models.CharField(max_length=10, verbose_name="code plan X3")
    siren_number = models.CharField(
        null=True, blank=True, max_length=20, verbose_name="n° siren"
    )  # CRN
    siret_number = models.CharField(
        null=True, blank=True, max_length=20, verbose_name="n° siret"
    )  # CRN
    vat_cee_number = models.CharField(
        null=True, blank=True, max_length=20, verbose_name="n° tva intracommunataire"
    )  # EECNUM
    vat_number = models.CharField(null=True, blank=True, max_length=20, verbose_name="n° tva")
    third_party_vat_regime = 1
    client_category = models.ForeignKey(
        CategorySage,
        on_delete=models.PROTECT,
        null=True,
        to_field="code",
        related_name="client_category",
        verbose_name="catégorie",
    )  # BCGCOD
    supplier_category = models.ForeignKey(
        CategorySage,
        on_delete=models.PROTECT,
        null=True,
        to_field="code",
        related_name="supplier_category",
        verbose_name="catégorie",
    )  # BSGCOD
    supplier_identifier = models.CharField(
        null=True, blank=True, max_length=70, verbose_name="identifiant fournisseur"
    )
    client_identifier = models.CharField(
        null=True, blank=True, max_length=70, verbose_name="identifiant client"
    )
    naf_code = models.CharField(
        null=True, blank=True, max_length=10, verbose_name="code naf"
    )  # NAF
    currency = models.CharField(default="EUR", max_length=3, verbose_name="monaie")  # CUR
    cry = models.CharField(null=True, blank=True, max_length=3, verbose_name="pays")  # CRY
    language = models.CharField(null=True, blank=True, max_length=3, verbose_name="pays")  # LAN
    budget_code = models.ForeignKey(
        TabDivSage,
        null=True,
        on_delete=models.PROTECT,
        to_field="code",
        limit_choices_to={"num_table": "6100"},
        verbose_name="code budget",
    )  # Z_CODBUD
    reviser = models.CharField(null=True, blank=True, max_length=5)  # Z_REVUSR
    comment = models.TextField(null=True, blank=True)

    # Supplier type
    is_client = models.BooleanField(default=False)  # BPCFLG
    is_agent = models.BooleanField(default=False)  # REPFLG
    is_prospect = models.BooleanField(default=False)  # PPTFLG
    is_supplier = models.BooleanField(default=False)  # BPSFLG
    is_various = models.BooleanField(default=False)  # BPRACC
    is_service_provider = models.BooleanField(default=False)  # PRVFLG
    is_transporter = models.BooleanField(default=False)  # BPTFLG
    is_contractor = models.BooleanField(default=False)  # DOOFLG

    # Paiements
    payment_condition_supplier = models.ForeignKey(
        PaymentCondition,
        null=True,
        on_delete=models.PROTECT,
        to_field="code",
        related_name="society_supplier_payment",
        verbose_name="conditions de paiement fournisseur",
    )  # PTE - BPSUPPLIER (Table TABPAYTERM)
    vat_sheme_supplier = models.CharField(
        null=True, blank=True, max_length=5, verbose_name="régime de taxe"
    )  # VACBPR - BPSUPPLIER (Table TABVACBPR)
    account_supplier_code = models.CharField(
        null=True, blank=True, max_length=10
    )  # ACCCOD - BPSUPPLIER (Table GACCCODE)
    payment_condition_client = models.ForeignKey(
        PaymentCondition,
        null=True,
        on_delete=models.PROTECT,
        to_field="code",
        related_name="society_client_payment",
        verbose_name="conditions de paiement client",
    )  # PTE - BPCUSTOMER (Table TABPAYTERM)
    vat_sheme_client = models.CharField(
        null=True, blank=True, max_length=5, verbose_name="régime de taxe"
    )  # VACBPR - BPCUSTOMER (Table TABVACBPR)
    account_client_code = models.CharField(
        null=True, blank=True, max_length=10
    )  # ACCCOD - BPCUSTOMER (Table GACCCODE)

    # Maisons part
    code_cct_x3 = models.CharField(null=True, blank=True, max_length=15, verbose_name="cct X3")
    code_cosium = models.CharField(null=True, blank=True, max_length=15, verbose_name="code cosium")
    sign_board = models.ForeignKey(
        Signboard, on_delete=models.PROTECT, null=True, verbose_name="ensigne"
    )
    opening_date = models.DateField(null=True, verbose_name="date d'ouveture")
    closing_date = models.DateField(null=True, verbose_name="date de fermeture")
    signature_franchise_date = models.DateField(null=True, verbose_name="date de signature contrat")
    agreement_franchise_end_date = models.DateField(
        null=True, verbose_name="date de signature de fin de contrat"
    )
    agreement_renew_date = models.DateField(null=True, verbose_name="date de renouvelement contrat")
    entry_fee_amount = models.DecimalField(
        max_digits=20, decimal_places=5, null=True, verbose_name="montant de droit d'entrée"
    )
    renew_fee_amoount = models.DecimalField(
        max_digits=20,
        decimal_places=5,
        null=True,
        verbose_name="montant de droit de renouvellement",
    )
    sale_price_category = models.ForeignKey(
        SalePriceCategory, on_delete=models.PROTECT, verbose_name="categorie de prix"
    )
    generic_coefficient = models.DecimalField(
        max_digits=20, decimal_places=5, default=1, verbose_name="coefiscient de vente générique"
    )
    credit_account = models.ForeignKey(
        AccountSage,
        on_delete=models.PROTECT,
        related_name="credit_account",
        verbose_name="compte X3 au crédit",
    )
    debit_account = models.ForeignKey(
        AccountSage,
        on_delete=models.PROTECT,
        related_name="debit_account",
        verbose_name="compte X3 au débit",
    )
    prov_account = models.ForeignKey(
        AccountSage,
        on_delete=models.PROTECT,
        related_name="prov_account",
        verbose_name="compte X3 de provision",
    )
    sage_vat_by_default = models.CharField(
        null=True, blank=True, max_length=5, verbose_name="tva X3 par défaut"
    )
    sage_pan_code = models.CharField(null=True, blank=True, max_length=10)

    # RFA
    rfa_frequence = models.IntegerField(choices=Frequence.choices, default=Frequence.MENSUEL)
    rfa_remise = models.IntegerField(choices=Remise.choices, default=Remise.TOTAL)

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        return f"{self.nature}{' - ' if self.nature else ''}{self.name}"

    class Meta:
        """class Meta du modèle django"""

        ordering = ["name"]


class Address(FlagsTable):
    """
    Adresses liées aux sociétés
    FR : Table des adresses
    EN : Addresses table
    """

    # TODO : Faire la validation de l'adresse par défaut une seule par société
    society = models.ForeignKey(
        Society,
        on_delete=models.CASCADE,
        to_field="uuid_identification",
        related_name="adresse_society",
    )
    default_adress = models.BooleanField(default=True)
    address_code = models.CharField(null=True, blank=True, max_length=10)
    address_number = models.CharField(null=True, blank=True, max_length=10)
    road_type = models.CharField(null=True, blank=True, max_length=35)
    line_01 = models.CharField(max_length=80)
    line_02 = models.CharField(null=True, blank=True, max_length=80)
    line_03 = models.CharField(null=True, blank=True, max_length=80)
    state = models.CharField(null=True, blank=True, max_length=80)
    region = models.CharField(null=True, blank=True, max_length=80)
    postal_code = models.CharField(null=True, blank=True, max_length=35)
    city = models.CharField(null=True, blank=True, max_length=80)
    country = models.ForeignKey(Country, on_delete=models.PROTECT, related_name="adresse_country")
    building = models.CharField(null=True, blank=True, max_length=80)
    floor = models.CharField(null=True, blank=True, max_length=80)
    phone_number = models.CharField(null=True, blank=True, max_length=35)

    def __str__(self):
        return f"{self.city}"

    class Meta:
        """class Meta du modèle django"""

        ordering = ["country"]


class DocumentsSubscription(FlagsTable):
    """
    Abonnements des envois de documents aux contacts
    FR : Table des abonnements aux envois de documents
    EN : Table of subscriptions to sending documents
    """

    name = models.CharField(unique=True, max_length=35)
    comment = models.TextField(null=True, blank=True)

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        return self.name

    class Meta:
        """class Meta du modèle django"""

        ordering = ["name"]


class Contact(FlagsTable):
    """
    Contact des Sociétés
    FR : Table des Contacts
    EN : Table of Contacts
    """

    society = models.ForeignKey(
        Society,
        on_delete=models.CASCADE,
        to_field="uuid_identification",
        related_name="contact_society",
    )
    nature = models.ForeignKey(
        Nature,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        null=True,
        related_name="contact_nature",
    )
    default_contact = models.BooleanField(default=True)
    first_name = models.CharField(null=True, blank=True, max_length=80)
    last_name = models.CharField(null=True, blank=True, max_length=80)
    phone_number = models.CharField(null=True, blank=True, max_length=35)
    mobile_number = models.CharField(null=True, blank=True, max_length=35)
    email = models.EmailField(null=True, blank=True)

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def __str__(self):
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
    )
    document = models.ForeignKey(
        DocumentsSubscription,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        related_name="document_contact",
    )

    def __str__(self):
        return f"{self.contact} - {self.document}"

    class Meta:
        """class Meta du modèle django"""

        ordering = ["contact", "document"]


class SocietyBank(FlagsTable):
    """
    Banques des Sociétés
    FR : Table des Banques
    EN : Table of Banks
    """

    society = models.ForeignKey(
        Society,
        on_delete=models.CASCADE,
        to_field="uuid_identification",
        related_name="bank_society",
    )
    payee = models.CharField(null=True, blank=True, max_length=80)
    bank_name = models.CharField(max_length=35)
    bank_code = models.CharField(unique=True, max_length=5)
    counter_code = models.CharField(null=True, blank=True, max_length=5)
    account_number = models.CharField(unique=True, max_length=11)
    account_key = models.CharField(null=True, blank=True, max_length=2)
    iban = models.CharField(null=True, blank=True, max_length=50)
    code_swift = models.CharField(null=True, blank=True, max_length=27)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.society} - {self.bank_name}"

    class Meta:
        """class Meta du modèle django"""

        ordering = ["bank_name"]
