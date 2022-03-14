# pylint: disable=E0401,R0903
"""
FR : Module des modèles de comptabilité sage pour validations et vérifications
     des élements à importer de Sage X3
EN : Sage accounting models module for validations and verifications
     elements to import of Sage X3

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


class AccountingTypeSage:
    """
    FR :
    EN :
    """


class AccountSage(FlagsTable):
    """
    Table des comptes Sage X3
    FR : Comptes au sens comptable de Sage X3
    EN : Accounts in the accounting sense of Sage X3
    """

    # TODO : à reprendre en vérifiant par rapport aux reprises déjà faites
    code_plan_sage = models.CharField(max_length=10)
    account = models.CharField(max_length=35)
    collective = models.CharField(null=True, blank=True, max_length=15)
    auxiliary = models.BooleanField()
    analytical_obligatory = models.BooleanField()
    nb_axes = models.IntegerField(default=0)
    vat_default = models.CharField(null=True, blank=True, max_length=15)

    @property
    def file_import_sage(self):
        """
        FR : Retourne le nom du fichier dans le répertoire du serveur Sage X3
        EN : Returns the name of the file in the  directory of the Sage X3 server
        """
        return "ZBIACCOUNT_journalier.heron"

    @property
    def get_columns_import(self):
        """
        FR : Retourne la position des colonnes
        EN : Returns the position of the columns
        """
        return {
            "code_plan_sage": 0,
            "account": 1,
            "collective": 2,
            "auxiliary": 3,
            "analytical_obligatory": 4,
            "nb_axes": 5,
            "vat_default": 6,
        }

    @property
    def set_import(self):
        """
        FR : Retourne la methode à appeler pour importer les fixtures du modèle
        EN : Returns the method to call to import the fixtures from the model
        """
        return "methode d'import à retourner"

    def __str__(self):
        return f"{self.code_plan_sage} - {self.account}"

    class Meta:
        """class Meta du modèle django"""

        ordering = ["account"]
        index_together = [
            ["code_plan_sage", "account"],
        ]
        unique_together = (("code_plan_sage", "account"),)


class AxeSage(FlagsTable):
    """
    Table des axes Sage X3
    FR : Axes au sens Sage X3
    EN : Axes in the sense of Sage X3
    ================================================
    champ    | model attr. | table SAGE | Champ Sage
    ================================================
    Axe      | axe         | GDIE       | DIE
    Intitulé | name        | GDIE       | DES
    ================================================
    """

    class Axe(models.TextChoices):
        """
        Axes Choices
        """

        BU = "BU", _("BU")
        CCT = "CCT", _("CCT")
        PRJ = "PRJ", _("PRJ")
        PRO = "PRO", _("PRO")
        PYS = "PYS", _("PYS")
        RFA = "RFA", _("RFA")

    axe = models.CharField(unique=True, choices=Axe.choices, max_length=10)
    name = models.CharField(null=True, blank=True, max_length=30)

    @property
    def file_import_sage(self):
        """
        FR : Retourne le nom du fichier dans le répertoire du serveur Sage X3
        EN : Returns the name of the file in the  directory of the Sage X3 server
        """
        return "ZBIAXES_journalier.heron"

    @property
    def get_columns_import(self):
        """
        FR : Retourne la position des colonnes
        EN : Returns the position of the columns
        """
        return {
            "axe": 0,
            "name": 1,
        }

    @property
    def set_import(self):
        """
        FR : Retourne la methode à appeler pour importer les fixtures du modèle
        EN : Returns the method to call to import the fixtures from the model
        """
        return "methode d'import à retourner"

    def __str__(self):
        return self.axe

    class Meta:
        """class Meta du modèle django"""

        ordering = ["axe"]


class SectionSageQuerySet(models.QuerySet):
    """
    FR : Retourne le Queryset managé
    EN : Returns the Managed Queryset
    """

    def bu_section(self):
        """
        FR : Retourne les sections pour l'axe BU de Sage X3
        EN : Returns the sections for the BU axis of Sage X3
        """
        return self.filter(axe="BU")

    def cct_section(self):
        """
        FR : Retourne les sections pour l'axe CCT de Sage X3
        EN : Returns the sections for the CCT axis of Sage X3
        """
        return self.filter(axe="CCT")

    def prj_section(self):
        """
        FR : Retourne les sections pour l'axe PRJ de Sage X3
        EN : Returns the sections for the PRJ axis of Sage X3
        """
        return self.filter(axe="PRJ")

    def pro_section(self):
        """
        FR : Retourne les sections pour l'axe PRO de Sage X3
        EN : Returns the sections for the PRO axis of Sage X3
        """
        return self.filter(axe="PRO")

    def pys_section(self):
        """
        FR : Retourne les sections pour l'axe PYS de Sage X3
        EN : Returns the sections for the PYS axis of Sage X3
        """
        return self.filter(axe="PYS")

    def rfa_section(self):
        """
        FR : Retourne les sections pour l'axe RFA de Sage X3
        EN : Returns the sections for the RFA axis of Sage X3
        """
        return self.filter(axe="RFA")


class SectionSage(FlagsTable):
    """
    Table des sections Sage X3
    FR : Section au sens Sage X3
    EN : Sections in the sense of Sage X3
    =====================================================
    champ        | model attr. | table SAGE  | Champ Sage
    =====================================================
    Axe          | axe         | CACCE       | DIE
    Section      | section     | CACCE       | CCE
    Refacturable | chargeable  | CACCE       | XFLREFAC
    Regroupement | regroup_01  | CACCE       | ZREG1
    Regroupement | regroup_02  | CACCE       | ZREG2
    =====================================================
    """

    axe = models.ForeignKey(
        AxeSage, on_delete=models.PROTECT, to_field="axe", related_name="axe_axe"
    )
    section = models.CharField(unique=True, max_length=15)
    chargeable = models.BooleanField(default=True)
    regroup_01 = models.CharField(null=True, blank=True, max_length=15)
    regroup_02 = models.CharField(null=True, blank=True, max_length=15)

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    axes = models.Manager()
    objects = SectionSageQuerySet.as_manager()

    @property
    def file_import_sage(self):
        """
        FR : Retourne le nom du fichier dans le répertoire du serveur Sage X3
        EN : Returns the name of the file in the  directory of the Sage X3 server
        """
        return "ZBICCE_journalier.heron"

    @property
    def get_columns_import(self):
        """
        FR : Retourne la position des colonnes
        EN : Returns the position of the columns
        """
        return {
            "axe": 0,
            "section": 1,
            "chargeable": 2,
            "regroup_01": 3,
            "regroup_02": 4,
        }

    @property
    def set_import(self):
        """
        FR : Retourne la methode à appeler pour importer les fixtures du modèle
        EN : Returns the method to call to import the fixtures from the model
        """
        return "methode d'import à retourner"

    def __str__(self):
        return f"{self.axe} - {self.section}"

    class Meta:
        """class Meta du modèle django"""

        ordering = ["section"]
        unique_together = (("axe", "section"),)
        index_together = [
            ["axe", "section"],
        ]


class VatRegimeSage(FlagsTable):
    """
    Table des régimes de TVA Sage X3
    FR : TVA au sens de Sage X3
    EN : VAT as defined by Sage X3
    =========================================================
    champ          | model attr. | table SAGE    | Champ Sage
    =========================================================
    Régime         | vat_regime  | TABVACBPR     | VACBPR
    Actif          | flag_active | TABVACBPR     | ENAFLG
    Intitulé       | name        | TABVACBPR     | DESAXX
    Intitulé court | short_name  | TABVACBPR     | SHOAXX
    Code taxe      | vat_code    | TABVACBPR     | VAT
    Classe vente   | sale_class  | TABVACBPR     | SALCLA
    Type de régime | regime_type | TABVACBPR     | REGVAC
    =========================================================
    """

    vat_regime = models.CharField(null=True, blank=True, max_length=5)
    name = models.CharField(null=True, max_length=30, verbose_name="intitulé")
    short_name = models.CharField(null=True, max_length=20, verbose_name="intitulé court")
    vat_code = models.CharField(null=True, max_length=5, verbose_name="code taxe")
    sale_class = models.CharField(null=True, max_length=10, verbose_name="classe vente")
    regime_type = models.CharField(null=True, max_length=20, verbose_name="type de régime")

    @property
    def file_import_sage(self):
        """
        FR : Retourne le nom du fichier dans le répertoire du serveur Sage X3
        EN : Returns the name of the file in the  directory of the Sage X3 server
        """
        return "ZBIREG_journalier.heron"

    @property
    def get_columns_import(self):
        """
        FR : Retourne la position des colonnes
        EN : Returns the position of the columns
        """
        return {
            "vat_regime": 0,
            "flag_active": 1,
            "name": 2,
            "short_name": 3,
            "vat_code": 4,
            "sale_class": 5,
            "regime_type": 6,
        }

    @property
    def set_import(self):
        """
        FR : Retourne la methode à appeler pour importer les fixtures du modèle
        EN : Returns the method to call to import the fixtures from the model
        """
        return "methode d'import à retourner"

    def __str__(self):
        return f"{self.vat_regime} - {self.name}"

    class Meta:
        """class Meta du modèle django"""

        ordering = ["vat_regime", "name"]


class VatSage(FlagsTable):
    """
    Table des taux et nom de TVA Sage X3
    FR : TVA au sens de Sage X3
    EN : VAT as defined by Sage X3
    ====================================================
    champ        | model attr. | table SAGE | Champ Sage
    ====================================================
    Tva          | vat         | TABVAT     | VAT
    Intitulé     | name        | TABVAT     | VATDES
    Taux         | rate        | TABVAT     | VATRAT
    Régime       | vat_regime  | TABVAT     | VATVAC
    ====================================================
    """

    vat = models.CharField(null=True, blank=True, max_length=5)
    name = models.CharField(null=True, blank=True, max_length=30)
    rate = models.DecimalField(max_digits=20, decimal_places=5, default=0)
    vat_regime = models.CharField(null=True, blank=True, max_length=5)

    @property
    def file_import_sage(self):
        """
        FR : Retourne le nom du fichier dans le répertoire du serveur Sage X3
        EN : Returns the name of the file in the  directory of the Sage X3 server
        """
        return "ZBIVAT_journalier.heron"

    @property
    def get_columns_import(self):
        """
        FR : Retourne la position des colonnes
        EN : Returns the position of the columns
        """
        return {
            "vat": 0,
            "name": 1,
            "rate": 2,
            "vat_regime": 3,
        }

    @property
    def set_import(self):
        """
        FR : Retourne la methode à appeler pour importer les fixtures du modèle
        EN : Returns the method to call to import the fixtures from the model
        """
        return "methode d'import à retourner"

    def __str__(self):
        return f"{self.vat} - {self.name}"

    class Meta:
        """class Meta du modèle django"""

        ordering = ["vat"]


class ThirdPartySageVatSage:
    """
    Table des tiers Sage X3
    pour cette table et imports, cela sera importé directement dans l'applicaton BOOK
    ici on ne fait que commenter la structure et préciser la méthode d'import
    FR : Tiers au sens de Sage X3
    EN : Third party as defined by Sage X3
    """

    @property
    def file_import_sage(self):
        """
        FR : Retourne le nom du fichier dans le répertoire du serveur Sage X3
        EN : Returns the name of the file in the  directory of the Sage X3 server
        """
        return "ZBIBPS_journalier.heron", "ZBIBPC_journalier.heron"

    @property
    def get_columns_import(self):
        """
        FR : Retourne la position des colonnes
        EN : Returns the position of the columns
        """
        # TODO : mapping à faire pour les champs du modèle Book lignes par ligne
        return {
            "A": {},
            "B": {},
        }

    @property
    def set_import(self):
        """
        FR : Retourne la methode à appeler pour importer les fixtures du modèle
        EN : Returns the method to call to import the fixtures from the model
        """
        return "methode d'import à retourner"


class PaymentCondition(FlagsTable):
    """
    Table des conditions de Paiement Sage X3
    FR : Conditions de Paiement au sens de Sage X3
    EN : Payment Terms as defined by Sage X3
    =========================================================
    champ          | model attr. | table SAGE    | Champ Sage
    =========================================================
    Condition      | code        | TABPAYTERM    | PTE
    Intitulé       | name        | TABPAYTERM    | DESAXX
    Intitulé court | short_name  | TABPAYTERM    | SHOAXX
    =========================================================
    """

    code = models.CharField(unique=True, max_length=35)
    name = models.CharField(null=True, max_length=30, verbose_name="intitulé")
    short_name = models.CharField(null=True, max_length=20, verbose_name="intitulé court")

    @property
    def file_import_sage(self):
        """
        FR : Retourne le nom du fichier dans le répertoire du serveur Sage X3
        EN : Returns the name of the file in the  directory of the Sage X3 server
        """
        return "ZBIPTE_journalier.heron"

    @property
    def get_columns_import(self):
        """
        FR : Retourne la position des colonnes
        EN : Returns the position of the columns
        """
        return {
            "code": 0,
            "name": 1,
            "short_name": 2,
        }

    @property
    def set_import(self):
        """
        FR : Retourne la methode à appeler pour importer les fixtures du modèle
        EN : Returns the method to call to import the fixtures from the model
        """
        return "methode d'import à retourner"

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        """class Meta du modèle django"""

        ordering = ["code"]


class TabDivQuerySet(models.QuerySet):
    """
    FR : Retourne le Queryset managé
    EN : Returns the Managed Queryset
    """

    def budget(self):
        """
        FR : Retourne les sections pour l'axe RFA de Sage X3
        EN : Returns the sections for the RFA axis of Sage X3
        """
        return self.filter(num_table="6100")


class TabDivSage(FlagsTable):
    """
    Table divers de Sage X3
    pour les budgets la table est la 6100
    FR : Table divers au sens de Sage X3
    EN : Miscellaneous table as defined by Sage X3
    ===========================================================
    champ          | model attr.   | table SAGE    | Champ Sage
    ===========================================================
    N° Table       | num_table     | ATABDIV       | NUMTAB
    Budget         | code          | ATABDIV       | CODE
    alpha 1..15    | a_01 .. a_015 | ATABDIV       | A1 .. A15
    number 1..15   | n_01 .. n_015 | ATABDIV       | N1 .. N15
    Intitulé       | name          | ATABDIV       | LNGDES
    Intitulé court | short_name    | ATABDIV       | SHODES
    default        | short_name    | ATABDIV       | DEFVAL
    ===========================================================
    """

    num_table = models.IntegerField(verbose_name="n° table divers Sage X3")
    code = models.CharField(unique=True, max_length=35)
    a_01 = models.CharField(null=True, max_length=40)
    a_02 = models.CharField(null=True, max_length=40)
    a_03 = models.CharField(null=True, max_length=40)
    a_04 = models.CharField(null=True, max_length=40)
    a_05 = models.CharField(null=True, max_length=40)
    a_06 = models.CharField(null=True, max_length=40)
    a_07 = models.CharField(null=True, max_length=40)
    a_08 = models.CharField(null=True, max_length=40)
    a_09 = models.CharField(null=True, max_length=40)
    a_10 = models.CharField(null=True, max_length=40)
    a_11 = models.CharField(null=True, max_length=40)
    a_12 = models.CharField(null=True, max_length=40)
    a_13 = models.CharField(null=True, max_length=40)
    a_14 = models.CharField(null=True, max_length=40)
    a_15 = models.CharField(null=True, max_length=40)
    n_01 = models.DecimalField(null=True, max_digits=20, decimal_places=6, default=0)
    n_02 = models.DecimalField(null=True, max_digits=20, decimal_places=6, default=0)
    n_03 = models.DecimalField(null=True, max_digits=20, decimal_places=6, default=0)
    n_04 = models.DecimalField(null=True, max_digits=20, decimal_places=6, default=0)
    n_05 = models.DecimalField(null=True, max_digits=20, decimal_places=6, default=0)
    n_06 = models.DecimalField(null=True, max_digits=20, decimal_places=6, default=0)
    n_07 = models.DecimalField(null=True, max_digits=20, decimal_places=6, default=0)
    n_08 = models.DecimalField(null=True, max_digits=20, decimal_places=6, default=0)
    n_09 = models.DecimalField(null=True, max_digits=20, decimal_places=6, default=0)
    n_10 = models.DecimalField(null=True, max_digits=20, decimal_places=6, default=0)
    n_11 = models.DecimalField(null=True, max_digits=20, decimal_places=6, default=0)
    n_12 = models.DecimalField(null=True, max_digits=20, decimal_places=6, default=0)
    n_13 = models.DecimalField(null=True, max_digits=20, decimal_places=6, default=0)
    n_14 = models.DecimalField(null=True, max_digits=20, decimal_places=6, default=0)
    n_15 = models.DecimalField(null=True, max_digits=20, decimal_places=6, default=0)
    name = models.CharField(null=True, max_length=30, verbose_name="intitulé")
    short_name = models.CharField(null=True, max_length=20, verbose_name="intitulé court")
    def_val = models.BooleanField(null=True, verbose_name="valeur par défaut")

    tab_div = models.Manager()
    objects = TabDivQuerySet.as_manager()

    @property
    def file_import_sage(self):
        """
        FR : Retourne le nom du fichier dans le répertoire du serveur Sage X3
        EN : Returns the name of the file in the  directory of the Sage X3 server
        """
        return "ZBIDIV_journalier.heron"

    @property
    def get_columns_import(self):
        """
        FR : Retourne la position des colonnes
        EN : Returns the position of the columns
        """
        return {
            "num_table": 0,
            "code": 1,
            "a_01": 2,
            "a_02": 3,
            "a_03": 4,
            "a_04": 5,
            "a_05": 6,
            "a_06": 7,
            "a_07": 8,
            "a_08": 9,
            "a_09": 10,
            "a_10": 11,
            "a_11": 12,
            "a_12": 13,
            "a_13": 14,
            "a_14": 15,
            "a_15": 16,
            "n_01": 17,
            "n_02": 18,
            "n_03": 19,
            "n_04": 20,
            "n_05": 21,
            "n_06": 22,
            "n_07": 23,
            "n_08": 24,
            "n_09": 25,
            "n_10": 26,
            "n_11": 27,
            "n_12": 28,
            "n_13": 29,
            "n_14": 30,
            "n_15": 31,
            "name": 32,
            "short_name": 33,
            # Issu de l'héritage de FlagsTable
            # From the legacy of FlagsTable
            "flag_active": 34,
        }

    @property
    def set_import(self):
        """
        FR : Retourne la methode à appeler pour importer les fixtures du modèle
        EN : Returns the method to call to import the fixtures from the model
        """
        return "methode d'import à retourner"

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        """class Meta du modèle django"""

        ordering = ["code"]
        index_together = [
            ["num_table", "code"],
        ]
        unique_together = (("num_table", "code"),)


class CategorySage(FlagsTable):
    """
    Table des catégories Clients et Fournisseurs de Sage X3
    FR : Table Catégorie définie par Sage X3
    EN : Categories table as defined by Sage X3
    =================================================================
    champ          | model attr.   | table SAGE    | Champ Sage
    =================================================================
    Initiale       | initial       |                | C ou S
    Catégorie      | code          | BPCCATEG       | BCGCOD - BSGCOD
    Intitulé       | name          | BPCCATEG       | DESAXX
    Intitulé court | short_name    | BPCCATEG       | SHOAXX
    Devise         | cur           | BPCCATEG       | CUR
    =================================================================
    """

    initial = models.CharField(max_length=1)
    code = models.CharField(unique=True, max_length=5)
    name = models.CharField(null=True, max_length=30, verbose_name="intitulé")
    short_name = models.CharField(null=True, max_length=20, verbose_name="intitulé court")
    cur = models.CharField(null=True, max_length=3, verbose_name="devise")

    @property
    def file_import_sage(self):
        """
        FR : Retourne le nom du fichier dans le répertoire du serveur Sage X3
        EN : Returns the name of the file in the  directory of the Sage X3 server
        """
        return "ZBICATC_journalier.heron", "ZBICATS_journalier.heron"

    @property
    def get_columns_import(self):
        """
        FR : Retourne la position des colonnes
        EN : Returns the position of the columns
        """
        return {
            "initials": 0,
            "code": 1,
            "name": 2,
            "short_name": 3,
            "cur": 4,
        }

    @property
    def set_import(self):
        """
        FR : Retourne la methode à appeler pour importer les fixtures du modèle
        EN : Returns the method to call to import the fixtures from the model
        """
        return "methode d'import à retourner"

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        """class Meta du modèle django"""

        ordering = ["code"]
