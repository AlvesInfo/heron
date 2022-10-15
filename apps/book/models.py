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
from django.shortcuts import reverse
from django.utils.translation import gettext_lazy as _

from heron.models import FlagsTable
from apps.accountancy.models import CategorySage, PaymentCondition
from apps.countries.models import Country

# Validation xml tva intra : https://ec.europa.eu/taxation_customs/vies/faq.html#item_18
#                            https://ec.europa.eu/taxation_customs/vies/technicalInformation.html


class Nature(FlagsTable):
    """
    Table des natures. Ex. : Mr, Mme, SARL, ...
    FR : Table des natures
    EN : Nature table
    """

    name = models.CharField(unique=True, blank=True, max_length=80)
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
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return self.to_display

    class Meta:
        """class Meta du modèle django"""
        ordering = ["name"]


class Society(FlagsTable):
    """
    Répertoire des sociétés Fournisseurs / Clients,
    correspondant à la table BPARTNER, BPSUPPLIER et BPCUSTOMER des tiers Sage X3
    FR : Table des sociétés
    EN : Societies table
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

    third_party_num = models.CharField(
        unique=True, max_length=15, verbose_name="N° de tiers X3"
    )  # BPRNUM

    nature = models.ForeignKey(
        Nature,
        on_delete=models.PROTECT,
        to_field="name",
        related_name="society_nature",
        null=True,
        blank=True,
        db_column="nature",
    )
    name = models.CharField(null=True, blank=True, max_length=80)  # BPRNAM_0
    short_name = models.CharField(
        null=True, blank=True, max_length=20, verbose_name="intitulé Court"
    )  # BPRSHO
    corporate_name = models.CharField(
        null=True, blank=True, max_length=80, verbose_name="raison sociale"
    )  # BPRNAM_1
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
        blank=True,
        related_name="client_category",
        verbose_name="catégorie client",
        limit_choices_to={"initial": "C"},
        db_column="client_category",
    )  # BCGCOD
    supplier_category = models.ForeignKey(
        CategorySage,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="supplier_category",
        verbose_name="catégorie fournisseur",
        limit_choices_to={"initial": "S"},
        db_column="supplier_category",
    )  # BSGCOD
    naf_code = models.CharField(
        null=True, blank=True, max_length=10, verbose_name="code naf"
    )  # NAF
    currency = models.CharField(
        null=True, blank=True, default="EUR", max_length=3, verbose_name="monaie"
    )  # CUR
    country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        to_field="country",
        related_name="society_country_country",
        null=True,
        blank=True,
        verbose_name="pays",
        db_column="country",
    )  # CRY models Country
    language = models.CharField(
        null=True, blank=True, max_length=80, verbose_name="langue"
    )  # LAN models Country
    budget_code = models.CharField(
        null=True, blank=True, max_length=80, verbose_name="code budget"
    )  # Z_CODBUD models TabDivSage limit_choices_to={"num_table": "6100"}
    reviser = models.CharField(
        null=True, blank=True, max_length=5, verbose_name="réviseur"
    )  # Z_REVUSR
    comment = models.TextField(null=True, blank=True, verbose_name="commentaire")

    # Supplier type
    is_client = models.BooleanField(default=False, verbose_name="Client")  # BPCFLG
    is_agent = models.BooleanField(default=False, verbose_name="Représentant")  # REPFLG
    is_prospect = models.BooleanField(default=False, verbose_name="Prospect")  # PPTFLG
    is_supplier = models.BooleanField(default=False, verbose_name="Fournisseur")  # BPSFLG
    is_various = models.BooleanField(default=False, verbose_name="Tiers Divers")  # BPRACC
    is_service_provider = models.BooleanField(default=False, verbose_name="Prestataire")  # PRVFLG
    is_transporter = models.BooleanField(default=False, verbose_name="Transporteur")  # BPTFLG
    is_contractor = models.BooleanField(default=False, verbose_name="Donneur d'ordre")  # DOOFLG
    is_physical_person = models.BooleanField(
        default=False, verbose_name="Personne physique"
    )  # LEGETT

    payment_condition_supplier = models.ForeignKey(
        PaymentCondition,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        to_field="auuid",
        related_name="supplier_paiement_condition",
        verbose_name="Condition de paiement",
        db_column="payment_condition_supplier",
    )  # PTE - BPSUPPLIER (Table TABPAYTERM)

    vat_sheme_supplier = models.CharField(
        null=True, blank=True, max_length=5, verbose_name="régime de taxe"
    )  # VACBPR - BPSUPPLIER (Table TABVACBPR)
    account_supplier_code = models.CharField(
        null=True, blank=True, max_length=10, verbose_name="code comptable fournisseur"
    )  # ACCCOD - BPSUPPLIER (Table GACCCODE)

    payment_condition_client = models.ForeignKey(
        PaymentCondition,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        to_field="auuid",
        related_name="client_paiement_condition",
        verbose_name="Condition de paiement",
        db_column="payment_condition_client",
    )  # PTE - BPCUSTOMER (Table TABPAYTERM)

    vat_sheme_client = models.CharField(
        null=True, blank=True, max_length=5, verbose_name="régime de taxe"
    )  # VACBPR - BPCUSTOMER (Table TABVACBPR)
    account_client_code = models.CharField(
        null=True, blank=True, max_length=10, verbose_name="code comptable client"
    )  # ACCCOD - BPCUSTOMER (Table GACCCODE)

    # Identifian Fournisseur pour la centrale d'achat
    centers_suppliers_indentifier = models.CharField(
        null=True, blank=True, max_length=80, verbose_name="identifiant fournisseur"
    )
    integrable = models.BooleanField(null=True, default=True, verbose_name="à intégrer X3")
    chargeable = models.BooleanField(null=True, default=True, verbose_name="à refacturer")

    # Adresse pour la centrale d'achat
    immeuble = models.CharField(null=True, blank=True, max_length=200, verbose_name="immeuble")
    adresse = models.CharField(null=True, blank=True, max_length=200, verbose_name="adresse")
    code_postal = models.CharField(null=True, blank=True, max_length=15, verbose_name="code postal")
    ville = models.CharField(null=True, blank=True, max_length=50, verbose_name="ville")
    pays = models.ForeignKey(
        Country,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        to_field="country",
        related_name="supplier_address_country",
        verbose_name="pays",
        db_column="pays",
    )
    telephone = models.CharField(null=True, blank=True, max_length=25, verbose_name="téléphone")
    mobile = models.CharField(null=True, blank=True, max_length=25, verbose_name="mobile")
    email = models.EmailField(null=True, blank=True, max_length=85, verbose_name="email")

    # RFA
    rfa_frequence = models.IntegerField(
        null=True,
        blank=True,
        choices=Frequence.choices,
        default=Frequence.AUCUNE,
        verbose_name="fréquence des rfa",
    )
    rfa_remise = models.IntegerField(
        null=True,
        blank=True,
        choices=Remise.choices,
        default=Remise.AUCUNE,
        verbose_name="taux de remboursement rfa",
    )

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{self.third_party_num} - {self.name}"

    @staticmethod
    def get_absolute_url():
        """Retourne l'url en cas de success create, update ou delete"""
        return reverse("book:societies_list")

    class Meta:
        """class Meta du modèle django"""

        ordering = ["third_party_num"]


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
        verbose_name="Tiers",
    )  # BPANUM
    default_adress = models.BooleanField(
        null=True, default=False, verbose_name="Adresse Par Défaut"
    )  # BPAADDFLG
    address_code = models.CharField(
        null=True, blank=True, max_length=20, verbose_name="Code adresse"
    )  # BPAADD
    address_type = models.CharField(
        null=True, blank=True, max_length=20, verbose_name="Type Adresse"
    )  # BPATYP
    address_number = models.CharField(
        null=True, blank=True, max_length=20, verbose_name="N° adresse"
    )
    road_type = models.CharField(null=True, blank=True, max_length=35, verbose_name="Type de voie")
    line_01 = models.CharField(
        null=True, blank=True, max_length=80, verbose_name="Ligne adresse 01"
    )  # BPAADDLIG(0)
    line_02 = models.CharField(
        null=True, blank=True, max_length=80, verbose_name="Ligne adresse 02"
    )  # BPAADDLIG(1)
    line_03 = models.CharField(
        null=True, blank=True, max_length=80, verbose_name="Ligne adresse 03"
    )  # BPAADDLIG(2)
    state = models.CharField(null=True, blank=True, max_length=80, verbose_name="Etat")  # SAT
    region = models.CharField(null=True, blank=True, max_length=80, verbose_name="Région")
    postal_code = models.CharField(
        null=True, blank=True, max_length=35, verbose_name="Code_postal"
    )  # POSCOD
    city = models.CharField(null=True, blank=True, max_length=80, verbose_name="Ville")  # CTY
    country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        to_field="country",
        related_name="adresse_country",
        null=True,
        db_column="country",
        verbose_name="Pays",
    )  # CRY
    building = models.CharField(null=True, blank=True, max_length=80, verbose_name="Immeuble")
    floor = models.CharField(null=True, blank=True, max_length=80, verbose_name="Etage")
    phone_number_01 = models.CharField(
        null=True, blank=True, max_length=35, verbose_name="N° téléphone 01"
    )  # TEL(0)
    phone_number_02 = models.CharField(
        null=True, blank=True, max_length=35, verbose_name="N° téléphone 02"
    )  # TEL(1)
    phone_number_03 = models.CharField(
        null=True, blank=True, max_length=35, verbose_name="N° téléphone 03"
    )  # TEL(2)
    phone_number_04 = models.CharField(
        null=True, blank=True, max_length=35, verbose_name="N° téléphone 04"
    )  # TEL(3)
    phone_number_05 = models.CharField(
        null=True, blank=True, max_length=35, verbose_name="N° téléphone 05"
    )  # TEL(4)
    email_01 = models.EmailField(null=True, blank=True, verbose_name="e-mail_01")  # WEB(0)
    email_02 = models.EmailField(null=True, blank=True, verbose_name="e-mail_02")  # WEB(1)
    email_03 = models.EmailField(null=True, blank=True, verbose_name="e-mail_03")  # WEB(2)
    email_04 = models.EmailField(null=True, blank=True, verbose_name="e-mail_04")  # WEB(3)
    email_05 = models.EmailField(null=True, blank=True, verbose_name="e-mail_05")  # WEB(4)
    web_site = models.CharField(
        null=True, blank=True, max_length=250, verbose_name="site web"
    )  # FCYWEB
    mobile_number = models.CharField(
        null=True, blank=True, max_length=35, verbose_name="N° mobile"
    )  # MOB

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
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{self.society} - {self.address_code}"

    class Meta:
        """class Meta du modèle django"""

        ordering = ["country"]
        unique_together = (("society", "address_code"),)


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
        verbose_name="Tiers",
    )  # BPANUM
    code = models.CharField(max_length=15, verbose_name="Code Adresse")  # CCNCRM
    service = models.CharField(
        null=True, blank=True, max_length=30, verbose_name="Service"
    )  # CNTSRV
    role = models.CharField(null=True, blank=True, max_length=15, verbose_name="Role")  # CNTMSS
    nature = models.ForeignKey(
        Nature,
        on_delete=models.PROTECT,
        to_field="name",
        related_name="contact_nature_country",
        null=True,
        limit_choices_to={"for_contact": True},
        db_column="nature",
        verbose_name="Nature",
    )
    civility = models.CharField(
        null=True, blank=True, max_length=20, verbose_name="Civilité"
    )  # CNTTTL
    first_name = models.CharField(
        null=True, blank=True, max_length=80, verbose_name="Prénom"
    )  # CNTFNA
    last_name = models.CharField(null=True, blank=True, max_length=80, verbose_name="Nom")  # CNTLNA
    language = models.CharField(
        null=True, blank=True, max_length=20, verbose_name="Langue"
    )  # CNTLAN models Country
    category = models.CharField(
        null=True, blank=True, max_length=20, verbose_name="Catégorie"
    )  # CNTCSP
    address_number = models.CharField(
        null=True, blank=True, max_length=20, verbose_name="N° Adresse"
    )
    road_type = models.CharField(null=True, blank=True, max_length=35, verbose_name="Type de voie")
    line_01 = models.CharField(null=True, max_length=80, verbose_name="Ligne Adresse 01")  # ADD(0)
    line_02 = models.CharField(
        null=True, blank=True, max_length=80, verbose_name="Ligne Adresse 02"
    )  # ADD(1)
    line_03 = models.CharField(
        null=True, blank=True, max_length=80, verbose_name="Ligne Adresse 03"
    )  # ADD(2)
    state = models.CharField(null=True, blank=True, max_length=80, verbose_name="Etat")  # SAT
    region = models.CharField(null=True, blank=True, max_length=80, verbose_name="Région")
    postal_code = models.CharField(
        null=True, blank=True, max_length=35, verbose_name="Code_postal"
    )  # ZIP
    city = models.CharField(null=True, blank=True, max_length=80, verbose_name="Ville")  # CTY
    country = models.CharField(
        null=True, blank=True, max_length=20, verbose_name="Pays"
    )  # CRY models Country
    building = models.CharField(null=True, blank=True, max_length=80, verbose_name="Immeuble")
    floor = models.CharField(null=True, blank=True, max_length=80, verbose_name="Etage")
    phone_number = models.CharField(
        null=True, blank=True, max_length=35, verbose_name="N° Téléphone"
    )  # CNTETS
    mobile_number = models.CharField(
        null=True, blank=True, max_length=35, verbose_name="N° Mobile"
    )  # CNTMOB
    email = models.EmailField(null=True, blank=True, verbose_name="e-mail")  # CNTEMA

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{self.first_name}{' - ' if self.first_name else ''}{self.last_name}"

    class Meta:
        """class Meta du modèle django"""

        ordering = ["last_name", "first_name"]
        unique_together = (("society", "code"),)


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
        to_field="country",
        related_name="bank_country",
        null=True,
        db_column="country",
    )  # CRY
    currency = models.CharField(null=True, blank=True, max_length=3)  # CUR
    is_default = models.BooleanField(null=True, default=False)  # BIDNUMFLG

    # bank_name = models.CharField(max_length=35)
    # bank_code = models.CharField(unique=True, max_length=5)
    # counter_code = models.CharField(null=True, blank=True, max_length=5)
    # account_key = models.CharField(null=True, blank=True, max_length=2)
    # iban = models.CharField(null=True, blank=True, max_length=50)
    # code_swift = models.CharField(null=True, blank=True, max_length=27)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{self.society} - {self.account_number}"

    class Meta:
        """class Meta du modèle django"""

        ordering = ["society", "-is_default", "account_number"]
        unique_together = (("society", "account_number"),)


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
            "is_client": 11,
            "is_agent": 12,
            "is_prospect": 13,
            "is_supplier": 14,
            "is_various": 15,
            "is_service_provider": 16,
            "is_transporter": 17,
            "is_contractor": 18,
            "budget_code": 19,
            "reviser": 20,
            "is_physical_person": 21,
        }

    @staticmethod
    def get_uniques():
        """
        FR : Retourne les champs uniques de la table
        EN: Returns the unique fields of the table
        """
        return {"third_party_num"}

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
            "is_client": 4,
            "is_agent": 5,
            "is_prospect": 6,
            "is_supplier": 7,
            "is_various": 8,
            "is_service_provider": 9,
            "is_transporter": 10,
            "is_contractor": 11,
            "is_physical_person": 12,
        }

    @staticmethod
    def get_uniques():
        """
        FR : Retourne les champs uniques de la table
        EN: Returns the unique fields of the table
        """
        return {"third_party_num"}

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
            "is_client": 4,
            "is_agent": 5,
            "is_prospect": 6,
            "is_supplier": 7,
            "is_various": 8,
            "is_service_provider": 9,
            "is_transporter": 10,
            "is_contractor": 11,
            "is_physical_person": 12,
        }

    @staticmethod
    def get_uniques():
        """
        FR : Retourne les champs uniques de la table
        EN: Returns the unique fields of the table
        """
        return {"third_party_num"}

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
            "line_01": 5,
            "line_02": 6,
            "line_03": 7,
            "state": 8,
            "postal_code": 9,
            "city": 10,
            "country": 11,
            "phone_number_01": 12,
            "phone_number_02": 13,
            "phone_number_03": 14,
            "phone_number_04": 15,
            "phone_number_05": 16,
            "email_01": 17,
            "email_02": 18,
            "email_03": 19,
            "email_04": 20,
            "email_05": 20,
            "web_site": 21,
        }

    @staticmethod
    def get_uniques():
        """
        FR : Retourne les champs uniques de la table
        EN: Returns the unique fields of the table
        """
        return {"society", "address_code"}

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
        }

    @staticmethod
    def get_uniques():
        """
        FR : Retourne les champs uniques de la table
        EN: Returns the unique fields of the table
        """
        return {"society", "code"}

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
        }

    @staticmethod
    def get_uniques():
        """
        FR : Retourne les champs uniques de la table
        EN: Returns the unique fields of the table
        """
        return {}

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
        }

    @staticmethod
    def get_uniques():
        """
        FR : Retourne les champs uniques de la table
        EN: Returns the unique fields of the table
        """
        return {"society", "account_number"}

    @property
    def get_import(self):
        """
        FR : Retourne la methode à appeler pour importer à partir d'un fichier de type csv
        EN : Returns the method to call to import from a csv file type
        """
        return "methode d'import à retourner"
