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
from django.utils.translation import gettext_lazy as _

from heron.models import FlagsTable

from apps.accountancy.models import (
    AccountSage,
    PaymentCondition,
    TabDivSage,
    CategorySage,
    # CurrencySage,
)
from apps.centers_purchasing.models import Signboard
from apps.parameters.models import SalePriceCategory
from apps.countries.models import Country

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
    correspondant à la table BPARTNER, BPSUPPLIER et BPCUSTOMER des tiers Sage X3
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

    third_party_num = models.CharField(
        unique=True, max_length=15, verbose_name="tiers X3"
    )  # BPRNUM

    nature = models.ForeignKey(
        Nature,
        on_delete=models.PROTECT,
        to_field="name",
        related_name="society_nature",
        null=True,
        db_column="nature",
    )
    name = models.CharField(null=True, blank=True, max_length=80)  # BPRNAM_0
    short_name = models.CharField(
        null=True, blank=True, max_length=20, verbose_name="intitulé Court"
    )  # BPRSHO
    corporate_name = models.CharField(
        null=True, blank=True, max_length=80, verbose_name="raison sociale"
    )  # BPRNAM_1
    code_plan_sage = models.CharField(max_length=10, verbose_name="code plan X3")
    siren_number = models.CharField(
        null=True, blank=True, max_length=20, verbose_name="n° siren"
    )  # ?
    siret_number = models.CharField(
        null=True, blank=True, max_length=20, verbose_name="n° siret"
    )  # CRN
    vat_cee_number = models.CharField(
        null=True, blank=True, max_length=20, verbose_name="n° tva intracommunataire"
    )  # EECNUM
    vat_number = models.CharField(null=True, blank=True, max_length=20)  # VATNUM
    client_category = models.ForeignKey(
        CategorySage,
        on_delete=models.PROTECT,
        null=True,
        related_name="client_category",
        verbose_name="catégorie",
        limit_choices_to={"initial": "C"},
        db_column="client_category",
    )  # BCGCOD
    supplier_category = models.ForeignKey(
        CategorySage,
        on_delete=models.PROTECT,
        null=True,
        related_name="supplier_category",
        verbose_name="catégorie",
        limit_choices_to={"initial": "S"},
        db_column="supplier_category",
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
    country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        to_field="country_iso",
        related_name="society_country_country",
        null=True,
        verbose_name="pays",
        db_column="country",
    )  # CRY
    language = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        to_field="country_iso",
        related_name="society_language_country",
        null=True,
        db_column="language",
    )  # LAN
    budget_code = models.ForeignKey(
        TabDivSage,
        null=True,
        on_delete=models.PROTECT,
        limit_choices_to={"num_table": "6100"},
        verbose_name="code budget",
        db_column="budget_code",
    )  # Z_CODBUD
    reviser = models.CharField(null=True, blank=True, max_length=5)  # Z_REVUSR
    comment = models.TextField(null=True, blank=True)

    # Supplier type
    is_client = models.BooleanField(null=True, default=False)  # BPCFLG
    is_agent = models.BooleanField(null=True, default=False)  # REPFLG
    is_prospect = models.BooleanField(null=True, default=False)  # PPTFLG
    is_supplier = models.BooleanField(null=True, default=False)  # BPSFLG
    is_various = models.BooleanField(null=True, default=False)  # BPRACC
    is_service_provider = models.BooleanField(null=True, default=False)  # PRVFLG
    is_transporter = models.BooleanField(null=True, default=False)  # BPTFLG
    is_contractor = models.BooleanField(null=True, default=False)  # DOOFLG

    # Paiements
    payment_condition_supplier = models.ForeignKey(
        PaymentCondition,
        null=True,
        on_delete=models.PROTECT,
        to_field="code",
        related_name="society_supplier_payment",
        verbose_name="conditions de paiement fournisseur",
        db_column="payment_condition_supplier",
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
        db_column="payment_condition_client",
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
        Signboard,
        on_delete=models.PROTECT,
        null=True,
        to_field="name",
        verbose_name="enseigne",
        db_column="sign_board",
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
        SalePriceCategory,
        on_delete=models.PROTECT,
        to_field="name",
        verbose_name="categorie de prix",
        db_column="sale_price_category",
    )
    generic_coefficient = models.DecimalField(
        max_digits=20, decimal_places=5, default=1, verbose_name="coefiscient de vente générique"
    )
    credit_account = models.ForeignKey(
        AccountSage,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        related_name="credit_account",
        verbose_name="compte X3 au crédit",
        db_column="credit_account",
    )
    debit_account = models.ForeignKey(
        AccountSage,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        related_name="debit_account",
        verbose_name="compte X3 au débit",
        db_column="debit_account",
    )
    prov_account = models.ForeignKey(
        AccountSage,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        related_name="prov_account",
        verbose_name="compte X3 de provision",
        db_column="prov_account",
    )
    sage_vat_by_default = models.CharField(
        null=True, blank=True, max_length=5, verbose_name="tva X3 par défaut"
    )
    sage_pan_code = models.CharField(null=True, blank=True, max_length=10)

    # RFA
    rfa_frequence = models.IntegerField(choices=Frequence.choices, default=Frequence.MENSUEL)
    rfa_remise = models.IntegerField(choices=Remise.choices, default=Remise.TOTAL)

    def __str__(self):
        return f"{self.nature}{' - ' if self.nature else ''}{self.name}"

    class Meta:
        """class Meta du modèle django"""

        ordering = ["name"]


class Address(FlagsTable):
    """
    Adresses liées aux sociétés, table BPADDRESS de Sage X3
    FR : Table des adresses
    EN : Addresses table
    """

    society = models.ForeignKey(
        Society,
        on_delete=models.CASCADE,
        to_field="third_party_num",
        related_name="society_society",
        db_column="society",
    )  # BPANUM
    default_adress = models.BooleanField(null=True, default=False)  # BPAADDFLG
    address_code = models.CharField(null=True, blank=True, max_length=20)  # BPAADD
    address_type = models.CharField(null=True, blank=True, max_length=20)  # BPATYP
    address_number = models.CharField(null=True, blank=True, max_length=20)
    road_type = models.CharField(null=True, blank=True, max_length=35)
    line_01 = models.CharField(max_length=80)  # BPAADDLIG(0)
    line_02 = models.CharField(null=True, blank=True, max_length=80)  # BPAADDLIG(1)
    line_03 = models.CharField(null=True, blank=True, max_length=80)  # BPAADDLIG(2)
    state = models.CharField(null=True, blank=True, max_length=80)  # SAT
    region = models.CharField(null=True, blank=True, max_length=80)
    postal_code = models.CharField(null=True, blank=True, max_length=35)  # POSCOD
    city = models.CharField(null=True, blank=True, max_length=80)  # CTY
    country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        to_field="country_iso",
        related_name="adresse_country",
        null=True,
        db_column="country",
    )  # CRY
    building = models.CharField(null=True, blank=True, max_length=80)
    floor = models.CharField(null=True, blank=True, max_length=80)
    phone_number_01 = models.CharField(null=True, blank=True, max_length=35)  # TEL(0)
    phone_number_02 = models.CharField(null=True, blank=True, max_length=35)  # TEL(1)
    phone_number_03 = models.CharField(null=True, blank=True, max_length=35)  # TEL(2)
    phone_number_04 = models.CharField(null=True, blank=True, max_length=35)  # TEL(3)
    phone_number_05 = models.CharField(null=True, blank=True, max_length=35)  # TEL(4)
    mobile_number = models.CharField(null=True, blank=True, max_length=35)  # MOB
    email_01 = models.EmailField(null=True, blank=True)  # WEB(0)
    email_02 = models.EmailField(null=True, blank=True)  # WEB(1)
    email_03 = models.EmailField(null=True, blank=True)  # WEB(2)
    email_04 = models.EmailField(null=True, blank=True)  # WEB(3)
    email_05 = models.EmailField(null=True, blank=True)  # WEB(4)
    web_site = models.CharField(null=True, blank=True, max_length=250)  # FCYWEB

    def save(self, *args, **kwargs):
        """
        FR : Avant la sauvegarde on clean les données
        EN : Before the backup we clean the data
        """
        # Avant la sauvegarde on vérifie si dans l'instance à sauvegarder le champ default_adress
        # est à True et si c'est le cas alors on update d'abord les autres à False pour la même
        # société

        if self.default_adress:
            Address.objects.filter(society=self.society, default_adress=True).update(
                default_adress=False
            )

        super().save(*args, **kwargs)

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

    def __str__(self):
        return self.name

    class Meta:
        """class Meta du modèle django"""

        ordering = ["name"]


class Contact(FlagsTable):
    """
    Contact des Sociétés, tables CONTACT et CONTACTCRM de Sage X3
    FR : Table des Contacts
    EN : Table of Contacts
    """

    society = models.ForeignKey(
        Society,
        on_delete=models.CASCADE,
        to_field="third_party_num",
        related_name="contact_society",
        db_column="society",
    )  # BPANUM
    code = models.CharField(unique=True, max_length=15)  # CCNCRM
    service = models.CharField(null=True, blank=True, max_length=30)  # CNTSRV
    role = models.CharField(null=True, blank=True, max_length=15)  # CNTMSS
    nature = models.ForeignKey(
        Nature,
        on_delete=models.PROTECT,
        to_field="name",
        related_name="contact_nature_country",
        null=True,
        limit_choices_to={"for_contact": True},
        db_column="nature",
    )
    civility = models.CharField(null=True, blank=True, max_length=20)  # CNTTTL
    first_name = models.CharField(null=True, blank=True, max_length=80)  # CNTFNA
    last_name = models.CharField(null=True, blank=True, max_length=80)  # CNTLNA
    language = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        to_field="country_iso",
        related_name="contact_language_country",
        null=True,
        db_column="language",
    )  # CNTLAN
    category = models.CharField(null=True, blank=True, max_length=20)  # CNTCSP
    address_number = models.CharField(null=True, blank=True, max_length=20)
    road_type = models.CharField(null=True, blank=True, max_length=35)
    line_01 = models.CharField(max_length=80)  # ADD(0)
    line_02 = models.CharField(null=True, blank=True, max_length=80)  # ADD(1)
    line_03 = models.CharField(null=True, blank=True, max_length=80)  # ADD(2)
    state = models.CharField(null=True, blank=True, max_length=80)  # SAT
    region = models.CharField(null=True, blank=True, max_length=80)
    postal_code = models.CharField(null=True, blank=True, max_length=35)  # ZIP
    city = models.CharField(null=True, blank=True, max_length=80)  # CTY
    country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        to_field="country_iso",
        related_name="contact_country_country",
        null=True,
        verbose_name="pays",
        db_column="country",
    )  # CRY
    building = models.CharField(null=True, blank=True, max_length=80)
    floor = models.CharField(null=True, blank=True, max_length=80)
    phone_number = models.CharField(null=True, blank=True, max_length=35)  # CNTETS
    mobile_number = models.CharField(null=True, blank=True, max_length=35)  # CNTMOB
    email = models.EmailField(null=True, blank=True)  # CNTEMA

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        return f"{self.first_name}{' - ' if self.first_name else ''}{self.last_name}"

    class Meta:
        """class Meta du modèle django"""

        ordering = ["last_name", "first_name"]
        unique_together = (("society", "code"),)


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
        to_field="third_party_num",
        related_name="bank_society",
        db_column="society",
    )  # BPANUM
    account_number = models.CharField(null=True, blank=True, max_length=50)  # BIDNUM
    address = models.CharField(null=True, blank=True, max_length=50)  # BPAADD
    payee = models.CharField(
        null=True, blank=True, max_length=50, verbose_name="bénéficiaire"
    )  # BNF
    domiciliation_01 = models.CharField(null=True, blank=True, max_length=50)  # PAB1
    domiciliation_02 = models.CharField(null=True, blank=True, max_length=50)  # PAB2
    domiciliation_03 = models.CharField(null=True, blank=True, max_length=50)  # PAB3
    domiciliation_04 = models.CharField(null=True, blank=True, max_length=50)  # PAB4
    iban_prefix = models.CharField(null=True, blank=True, max_length=10)  # IBAN
    bic_code = models.CharField(null=True, blank=True, max_length=20)  # BICCOD
    country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        to_field="country_iso",
        related_name="bank_country",
        null=True,
        db_column="country",
    )  # CRY
    currency = models.CharField(blank=True, null=True, max_length=3)  # CUR
    is_default = models.BooleanField(null=True, default=False)  # BIDNUMFLG

    # bank_name = models.CharField(max_length=35)
    # bank_code = models.CharField(unique=True, max_length=5)
    # counter_code = models.CharField(null=True, blank=True, max_length=5)
    # account_key = models.CharField(null=True, blank=True, max_length=2)
    # iban = models.CharField(null=True, blank=True, max_length=50)
    # code_swift = models.CharField(null=True, blank=True, max_length=27)

    def __str__(self):
        return f"{self.society} - {self.account_number}"

    class Meta:
        """class Meta du modèle django"""

        ordering = ["society", "-is_default", "account_number"]


class BprBookSage:
    """
    Table des tiers Sage X3
    pour imports, cela sera importé directement dans l'applicaton BOOK
    ici on ne fait que commenter la structure et préciser la méthode d'import
    FR : Tiers au sens de Sage X3
    EN : Third party as defined by Sage X3
    """

    model = Society

    @staticmethod
    def file_import_sage():
        """
        FR : Retourne le nom du fichier dans le répertoire du serveur Sage X3
        EN : Returns the name of the file in the  directory of the Sage X3 server
        """
        return "ZBIBPR_journalier.heron"

    @staticmethod
    def get_columns_import():
        """
        FR : Retourne la position des colonnes
        EN : Returns the position of the columns
        """
        return {
            "third_party_num": 0,
            "name": 1,
            "short_name": 2,
            "corporate_name": 3,
            "siret_number": 4,
            "vat_cee_number": 5,
            "vat_number": 6,
            "naf_code": 7,
            "currency": 8,
            "country": 9,
            "language": 10,
            "budget_code": 11,
            "reviser": 12,
            "is_client": 13,
            "is_agent": 14,
            "is_prospect": 15,
            "is_supplier": 16,
            "is_various": 17,
            "is_service_provider": 18,
            "is_transporter": 19,
            "is_contractor": 20,
            # Issu de l'héritage de FlagsTable
            # From the legacy of FlagsTable
            "created_at": 21,
            "modified_at": 22,
        }

    @property
    def get_import(self):
        """
        FR : Retourne la methode à appeler pour importer à partir d'un fichier de type csv
        EN : Returns the method to call to import from a csv file type
        """
        return "methode d'import à retourner"


class BpsBookSage:
    """
    Table des tiers Fournisseurs Sage X3
    pour cette table et imports, cela sera importé directement dans l'applicaton BOOK
    ici on ne fait que commenter la structure et préciser la méthode d'import
    FR : Tiers au sens de Sage X3
    EN : Third party as defined by Sage X3
    """

    model = Society

    @staticmethod
    def file_import_sage():
        """
        FR : Retourne le nom du fichier dans le répertoire du serveur Sage X3
        EN : Returns the name of the file in the  directory of the Sage X3 server
        """
        return "ZBIBPS_journalier.heron"

    @staticmethod
    def get_columns_import():
        """
        FR : Retourne la position des colonnes
        EN : Returns the position of the columns
        """
        return {
            "third_party_num": 0,
            "payment_condition_supplier": 1,
            "vat_sheme_supplier": 2,
            "account_supplier_code": 3,
            # Issu de l'héritage de FlagsTable
            # From the legacy of FlagsTable
            "created_at": 4,
            "modified_at": 5,
        }

    @property
    def get_import(self):
        """
        FR : Retourne la methode à appeler pour importer à partir d'un fichier de type csv
        EN : Returns the method to call to import from a csv file type
        """
        return "methode d'import à retourner"


class BpcBookSage:
    """
    Table des tiers Clients Sage X3
    pour cette table et imports, cela sera importé directement dans l'applicaton BOOK
    ici on ne fait que commenter la structure et préciser la méthode d'import
    FR : Tiers au sens de Sage X3
    EN : Third party as defined by Sage X3
    """

    model = Society

    @staticmethod
    def file_import_sage():
        """
        FR : Retourne le nom du fichier dans le répertoire du serveur Sage X3
        EN : Returns the name of the file in the  directory of the Sage X3 server
        """
        return "ZBIBPC_journalier.heron"

    @staticmethod
    def get_columns_import():
        """
        FR : Retourne la position des colonnes
        EN : Returns the position of the columns
        """
        return {
            "third_party_num": 0,
            "payment_condition_client": 1,
            "vat_sheme_client": 2,
            "account_client_code": 3,
            # Issu de l'héritage de FlagsTable
            # From the legacy of FlagsTable
            "created_at": 4,
            "modified_at": 5,
        }

    @property
    def get_import(self):
        """
        FR : Retourne la methode à appeler pour importer à partir d'un fichier de type csv
        EN : Returns the method to call to import from a csv file type
        """
        return "methode d'import à retourner"


class BookAdressesSage:
    """
    Table des adresses des tiers Sage X3
    pour cette table et imports, cela sera importé directement dans l'applicaton BOOK
    ici on ne fait que commenter la structure et préciser la méthode d'import
    FR : Adresses des Tiers au sens de Sage X3
    EN : Adresses Third party as defined by Sage X3
    """

    model = Address

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
            "society": 0,
            "default_adress": 1,
            "address_code": 2,
            "address_type": 3,
            "line_01": 4,
            "line_02": 5,
            "line_03": 6,
            "state": 7,
            "postal_code": 8,
            "city": 9,
            "country": 10,
            "phone_number_01": 11,
            "phone_number_02": 12,
            "phone_number_03": 13,
            "phone_number_04": 14,
            "phone_number_05": 15,
            "mobile": 16,
            "email_01": 17,
            "email_02": 18,
            "email_03": 19,
            "email_04": 20,
            "email_05": 21,
            "web_site": 22,
            # Issu de l'héritage de FlagsTable
            # From the legacy of FlagsTable
            "created_at": 23,
            "modified_at": 24,
        }

    @property
    def get_import(self):
        """
        FR : Retourne la methode à appeler pour importer à partir d'un fichier de type csv
        EN : Returns the method to call to import from a csv file type
        """
        return "methode d'import à retourner"


class CodeContactsSage:
    """
    Table des Codes Contacts des tiers Sage X3
    pour cette table et imports, cela sera importé directement dans l'applicaton BOOK
    ici on ne fait que commenter la structure et préciser la méthode d'import
    FR : Code Contacts des Tiers au sens de Sage X3
    EN : Contacts Code Third party as defined by Sage X3
    """

    model = Contact

    @staticmethod
    def file_import_sage():
        """
        FR : Retourne le nom du fichier dans le répertoire du serveur Sage X3
        EN : Returns the name of the file in the  directory of the Sage X3 server
        """
        return "ZBICONTACT_journalier.heron"

    @staticmethod
    def get_columns_import():
        """
        FR : Retourne la position des colonnes
        EN : Returns the position of the columns
        """
        return {
            "society": 0,
            "code": 1,
            "service": 2,
            "role": 3,
            # Issu de l'héritage de FlagsTable
            # From the legacy of FlagsTable
            "uuid_identification": 4,
            "created_at": 5,
            "modified_at": 6,
        }

    @property
    def get_import(self):
        """
        FR : Retourne la methode à appeler pour importer à partir d'un fichier de type csv
        EN : Returns the method to call to import from a csv file type
        """
        return "methode d'import à retourner"


class BookContactsSage:
    """
    Table des Contacts des tiers Sage X3
    pour cette table et imports, cela sera importé directement dans l'applicaton BOOK
    ici on ne fait que commenter la structure et préciser la méthode d'import
    FR : Contacts des Tiers au sens de Sage X3
    EN : Contacts Third party as defined by Sage X3
    """

    model = Contact

    @staticmethod
    def file_import_sage():
        """
        FR : Retourne le nom du fichier dans le répertoire du serveur Sage X3
        EN : Returns the name of the file in the  directory of the Sage X3 server
        """
        return "ZBICONTCRM_journalier.heron"

    @staticmethod
    def get_columns_import():
        """
        FR : Retourne la position des colonnes
        EN : Returns the position of the columns
        """
        return {
            "society": 0,
            "civility": 1,
            "first_name": 2,
            "last_name": 3,
            "language": 4,
            "category": 5,
            "line_01": 6,
            "line_02": 7,
            "line_03": 8,
            "state": 9,
            "postal_code": 10,
            "city": 11,
            "country": 12,
            "phone_number": 13,
            "mobile_number": 14,
            "email": 15,
            # Issu de l'héritage de FlagsTable
            # From the legacy of FlagsTable
            "uuid_identification": 16,
            "created_at": 17,
            "modified_at": 18,
        }

    @property
    def get_import(self):
        """
        FR : Retourne la methode à appeler pour importer à partir d'un fichier de type csv
        EN : Returns the method to call to import from a csv file type
        """
        return "methode d'import à retourner"


class BookBanksSage:
    """
    Table des Banques des tiers Sage X3
    pour cette table et imports, cela sera importé directement dans l'applicaton BOOK
    ici on ne fait que commenter la structure et préciser la méthode d'import
    FR : Banques des Tiers au sens de Sage X3
    EN : Banks Third party as defined by Sage X3
    """

    model = SocietyBank

    @staticmethod
    def file_import_sage():
        """
        FR : Retourne le nom du fichier dans le répertoire du serveur Sage X3
        EN : Returns the name of the file in the  directory of the Sage X3 server
        """
        return "ZBIBANK_journalier.heron"

    @staticmethod
    def get_columns_import():
        """
        FR : Retourne la position des colonnes
        EN : Returns the position of the columns
        """
        return {
            "society": 0,
            "account_number": 1,
            "address": 2,
            "payee": 3,
            "domiciliation_01": 4,
            "domiciliation_02": 5,
            "domiciliation_03": 6,
            "domiciliation_04": 7,
            "iban_prefix": 8,
            "bic_code": 9,
            "country": 10,
            "currency": 11,
            "is_default": 12,
            # Issu de l'héritage de FlagsTable
            # From the legacy of FlagsTable
            "created_at": 13,
            "modified_at": 14,
        }

    @property
    def get_import(self):
        """
        FR : Retourne la methode à appeler pour importer à partir d'un fichier de type csv
        EN : Returns the method to call to import from a csv file type
        """
        return "methode d'import à retourner"
