# pylint: disable=E0401,R0903
"""
FR : Module des modèles de comptabilité sage pour forms_validation et vérifications
     des élements à importer de Sage X3
EN : Sage accounting models module for forms_validation and verifications
     elements to import of Sage X3

Commentaire:

created at: 2021-09-09
created by: Paulo ALVES

modified at: 2021-09-09
modified by: Paulo ALVES
"""

import uuid
from django.db import models

from heron.models import FlagsTable


class AccountingTypeSage:
    """
    FR :
    EN :
    """


class AccountSage(FlagsTable):
    """
    Table des comptes Sage X3 - GACCOUNT
    FR : Comptes au sens comptable de Sage X3
    EN : Accounts in the accounting sense of Sage X3
    """

    code_plan_sage = models.CharField(max_length=10)  # COA
    account = models.CharField(max_length=35)  # ACC
    name = models.CharField(null=True, max_length=30, verbose_name="intitulé")  # DES
    short_name = models.CharField(null=True, max_length=20, verbose_name="intitulé court")  # DESSHO
    collective = models.BooleanField(null=True)  # SAC
    call_code = models.CharField(
        null=True, blank=True, max_length=15, verbose_name="code d'appel"
    )  # ACCSHO
    analytic = models.BooleanField(null=True, default=False)  # AUZBPR
    nb_axes = models.IntegerField(default=0)  # DACDIENBR
    axe_00 = models.CharField(null=True, blank=True, max_length=10)  # DIE
    section_00 = models.CharField(null=True, blank=True, max_length=15)  # CCEDEF
    axe_01 = models.CharField(null=True, blank=True, max_length=10)  # DIE(1)
    section_01 = models.CharField(null=True, blank=True, max_length=15)  # CCEDEF(1)
    axe_02 = models.CharField(null=True, blank=True, max_length=10)  # DIE(2)
    section_02 = models.CharField(null=True, blank=True, max_length=15)  # CCEDEF(2)
    axe_03 = models.CharField(null=True, blank=True, max_length=10)  # DIE(3)
    section_03 = models.CharField(null=True, blank=True, max_length=15)  # CCEDEF(3)
    axe_04 = models.CharField(null=True, blank=True, max_length=10)  # DIE(4)
    section_04 = models.CharField(null=True, blank=True, max_length=15)  # CCEDEF(4)
    axe_05 = models.CharField(null=True, blank=True, max_length=10)  # DIE(5)
    section_05 = models.CharField(null=True, blank=True, max_length=15)  # CCEDEF(5)
    axe_06 = models.CharField(null=True, blank=True, max_length=10)  # DIE(6)
    section_06 = models.CharField(null=True, blank=True, max_length=15)  # CCEDEF(6)
    axe_07 = models.CharField(null=True, blank=True, max_length=10)  # DIE(7)
    section_07 = models.CharField(null=True, blank=True, max_length=15)  # CCEDEF(7)
    axe_08 = models.CharField(null=True, blank=True, max_length=10)  # DIE(8)
    section_08 = models.CharField(null=True, blank=True, max_length=15)  # CCEDEF(8)
    axe_09 = models.CharField(null=True, blank=True, max_length=10)  # DIE(9)
    section_09 = models.CharField(null=True, blank=True, max_length=15)  # CCEDEF(9)
    vat_default = models.CharField(null=True, blank=True, max_length=15)  # VAT
    chargeback_x3 = models.BooleanField(default=False, verbose_name="refacturable X3")  # XFLGREFAC
    bu_suc = models.CharField(null=True, blank=True, max_length=20)  # ZBUSUC

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    @staticmethod
    def file_import_sage():
        """
        FR : Retourne le nom du fichier dans le répertoire du serveur Sage X3
        EN : Returns the name of the file in the  directory of the Sage X3 server
        """
        return "ZBIACCOUNT_journalier.heron"

    @staticmethod
    def get_columns_import():
        """
        FR : Retourne la position des colonnes
        EN : Returns the position of the columns
        """
        return {
            "code_plan_sage": 0,
            "account": 1,
            "name": 2,
            "short_name": 3,
            "collective": 4,
            "call_code": 5,
            "analytic": 6,
            "nb_axes": 7,
            "axe_00": 8,
            "section_00": 9,
            "axe_01": 10,
            "section_01": 11,
            "axe_02": 12,
            "section_02": 13,
            "axe_03": 14,
            "section_03": 15,
            "axe_04": 16,
            "section_04": 17,
            "axe_05": 18,
            "section_05": 19,
            "axe_06": 20,
            "section_06": 21,
            "axe_07": 22,
            "section_07": 23,
            "axe_08": 24,
            "section_08": 25,
            "axe_09": 26,
            "section_09": 27,
            "vat_default": 28,
            "chargeback_x3": 29,
            "bu_suc": 30,
        }

    @staticmethod
    def get_import():
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
    Table des axes GDIE Sage X3
    FR : Axes au sens Sage X3
    EN : Axes in the sense of Sage X3
    ======================================================
    champ          | model attr. | table SAGE | Champ Sage
    ======================================================
    Axe            | axe         | GDIE       | DIE
    Intitulé       | name        | GDIE       | DES
    Intitulécourt  | short_name  | GDIE       | DESSHO
    ======================================================
    """

    axe = models.CharField(unique=True, max_length=10)
    name = models.CharField(null=True, blank=True, max_length=30, verbose_name="intitulé")
    short_name = models.CharField(
        null=True, blank=True, max_length=20, verbose_name="intitulé court"
    )

    @staticmethod
    def file_import_sage():
        """
        FR : Retourne le nom du fichier dans le répertoire du serveur Sage X3
        EN : Returns the name of the file in the  directory of the Sage X3 server
        """
        return "ZBIAXES_journalier.heron"

    @staticmethod
    def get_columns_import():
        """
        FR : Retourne la position des colonnes
        EN : Returns the position of the columns
        """
        return {
            "axe": 0,
            "name": 1,
            "short_name": 2,
        }

    @staticmethod
    def get_import():
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
    Table des sections CACCE Sage X3
    FR : Section au sens Sage X3
    EN : Sections in the sense of Sage X3
    ========================================================
    champ           | model attr. | table SAGE  | Champ Sage
    ========================================================
    Axe             | axe         | CACCE       | DIE
    Section         | section     | CACCE       | CCE
    Intitulé        | name        | CACCE        | DES
    Intitulé court  | short_name  | CACCE        | DESSHO
    Refacturable    | chargeable  | CACCE       | XFLREFAC
    Regroupement    | regroup_01  | CACCE       | ZREG1
    Regroupement    | regroup_02  | CACCE       | ZREG2
    ========================================================
    """

    axe = models.ForeignKey(
        AxeSage, on_delete=models.CASCADE, to_field="axe", related_name="axe_axe"
    )
    section = models.CharField(max_length=15)
    name = models.CharField(null=True, blank=True, max_length=30, verbose_name="intitulé")
    short_name = models.CharField(
        null=True, blank=True, max_length=20, verbose_name="intitulé court"
    )
    chargeable = models.BooleanField(null=True, default=True)
    regroup_01 = models.CharField(null=True, blank=True, max_length=15)
    regroup_02 = models.CharField(null=True, blank=True, max_length=15)

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    axes = models.Manager()
    objects = SectionSageQuerySet.as_manager()

    @staticmethod
    def file_import_sage():
        """
        FR : Retourne le nom du fichier dans le répertoire du serveur Sage X3
        EN : Returns the name of the file in the  directory of the Sage X3 server
        """
        return "ZBICCE_journalier.heron"

    @staticmethod
    def get_columns_import():
        """
        FR : Retourne la position des colonnes
        EN : Returns the position of the columns
        """
        return {
            "axe": 0,
            "section": 1,
            "name": 2,
            "short_name": 3,
            "chargeable": 4,
            "regroup_01": 5,
            "regroup_02": 6,
        }

    @staticmethod
    def get_import():
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
    ======================================================================
    champ          | model attr.              | table SAGE    | Champ Sage
    ======================================================================
    Régime         | vat_regime               | TABVACBPR     | VACBPR
    Actif          | flag_active (FlagsTable) | TABVACBPR     | ENAFLG
    Intitulé       | name                     | TABVACBPR     | DESAXX
    Intitulé court | short_name               | TABVACBPR     | SHOAXX
    Code taxe      | vat_code                 | TABVACBPR     | VAT
    Classe vente   | sale_class               | TABVACBPR     | SALCLA
    Type de régime | regime_type              | TABVACBPR     | REGVAC
    ======================================================================
    """

    vat_regime = models.CharField(null=True, blank=True, max_length=5)
    name = models.CharField(null=True, max_length=30, verbose_name="intitulé")
    short_name = models.CharField(null=True, max_length=20, verbose_name="intitulé court")
    vat_code = models.CharField(null=True, max_length=5, verbose_name="code taxe")
    sale_class = models.CharField(null=True, max_length=10, verbose_name="classe vente")
    regime_type = models.CharField(null=True, max_length=20, verbose_name="type de régime")

    @staticmethod
    def file_import_sage():
        """
        FR : Retourne le nom du fichier dans le répertoire du serveur Sage X3
        EN : Returns the name of the file in the  directory of the Sage X3 server
        """
        return "ZBIREG_journalier.heron"

    @staticmethod
    def get_columns_import():
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

    @staticmethod
    def get_import():
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
    Régime       | vat_regime  | TABVAT     | VATVAC
    ====================================================
    """

    vat = models.CharField(unique=True, max_length=5)
    name = models.CharField(null=True, blank=True, max_length=30)
    vat_regime = models.CharField(null=True, blank=True, max_length=5)

    @staticmethod
    def file_import_sage():
        """
        FR : Retourne le nom du fichier dans le répertoire du serveur Sage X3
        EN : Returns the name of the file in the  directory of the Sage X3 server
        """
        return "ZBIVAT_journalier.heron"

    @staticmethod
    def get_columns_import():
        """
        FR : Retourne la position des colonnes
        EN : Returns the position of the columns
        """
        return {
            "vat": 0,
            "name": 1,
            "vat_regime": 2,
        }

    @staticmethod
    def get_import():
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


class VatRatSage(FlagsTable):
    """
    Table des taux et nom de TVA Sage X3
    FR : TVA au sens de Sage X3
    EN : VAT as defined by Sage X3
    ==========================================================
    champ        | model attr.    | table SAGE    | Champ Sage
    ==========================================================
    Tva          | vat            | TABRATVAT     | VAT
    Date début   | vat_start_date | TABRATVAT     | STRDAT
    Taux         | rate           | TABRATVAT     | VATRAT
    Régime       | vat_regime     | TABRATVAT     | VATEXEFLG
    ==========================================================
    """

    vat = models.ForeignKey(VatSage, on_delete=models.CASCADE, to_field="vat")
    vat_start_date = models.CharField(blank=True, max_length=30)
    rate = models.DecimalField(max_digits=20, decimal_places=5, default=0)
    exoneration = models.BooleanField(null=True)

    @staticmethod
    def file_import_sage():
        """
        FR : Retourne le nom du fichier dans le répertoire du serveur Sage X3
        EN : Returns the name of the file in the  directory of the Sage X3 server
        """
        return "ZBIRATVAT_journalier.heron"

    @staticmethod
    def get_columns_import():
        """
        FR : Retourne la position des colonnes
        EN : Returns the position of the columns
        """
        return {
            "vat": 0,
            "vat_start_date": 1,
            "rate": 2,
            "exoneration": 3,
        }

    @staticmethod
    def get_import():
        """
        FR : Retourne la methode à appeler pour importer les fixtures du modèle
        EN : Returns the method to call to import the fixtures from the model
        """
        return "methode d'import à retourner"

    def __str__(self):
        return f"{self.vat} - {self.vat_start_date} - {self.rate}"

    class Meta:
        """class Meta du modèle django"""

        ordering = ["vat", "-vat_start_date"]


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

    @staticmethod
    def file_import_sage():
        """
        FR : Retourne le nom du fichier dans le répertoire du serveur Sage X3
        EN : Returns the name of the file in the  directory of the Sage X3 server
        """
        return "ZBIPTE_journalier.heron"

    @staticmethod
    def get_columns_import():
        """
        FR : Retourne la position des colonnes
        EN : Returns the position of the columns
        """
        return {
            "code": 0,
            "name": 1,
            "short_name": 2,
        }

    @staticmethod
    def get_import():
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

    @staticmethod
    def file_import_sage():
        """
        FR : Retourne le nom du fichier dans le répertoire du serveur Sage X3
        EN : Returns the name of the file in the  directory of the Sage X3 server
        """
        return "ZBIDIV_journalier.heron"

    @staticmethod
    def get_columns_import():
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

    @staticmethod
    def get_import():
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

    @staticmethod
    def file_import_sage():
        """
        FR : Retourne le nom du fichier dans le répertoire du serveur Sage X3
        EN : Returns the name of the file in the  directory of the Sage X3 server
        """
        return "ZBICATC_journalier.heron", "ZBICATS_journalier.heron"

    @staticmethod
    def get_columns_import():
        """
        FR : Retourne la position des colonnes
        EN : Returns the position of the columns
        """
        return {
            "initial": 0,
            "code": 1,
            "name": 2,
            "short_name": 3,
            "cur": 4,
        }

    @staticmethod
    def get_import():
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


class CurrencySage(FlagsTable):
    """
    Table des devises TABCHANGE de Sage X3
    FR : Table des devises définie par Sage X3
    EN : Currency table as defined by Sage X3
    =================================================================
    champ          | model attr.            | table SAGE | Champ Sage
    =================================================================
    Devise         | currency_current       | TABCHANGE  | CUR
    Devise dest.   | currency_change        | TABCHANGE  | CURDEN
    Date cours     | exchange_date          | TABCHANGE  | CHGSTRDAT
    Type de cours  | exchange_type          | TABCHANGE  | CHGTYP
    Cours achat    | exchange_rate          | TABCHANGE  | CHGRAT
    Cours inverse  | exchange_inverse       | TABCHANGE  | REVCOURS
    Diviseur       | divider                | TABCHANGE  | CHGDIV
    Date modif     | modification_date      | TABCHANGE  | UPDDAT
    Cours vente    | purchase_exchange_rate |            |
    =================================================================
    """

    currency_current = models.CharField(blank=True, null=True, max_length=3)
    currency_change = models.CharField(blank=True, null=True, max_length=3)
    exchange_date = models.DateField(verbose_name="créé le")
    exchange_type = models.IntegerField(default=1)
    exchange_rate = models.DecimalField(max_digits=20, decimal_places=5, default=0)
    exchange_inverse = models.DecimalField(max_digits=20, decimal_places=5, default=0)
    divider = models.DecimalField(max_digits=20, decimal_places=5, default=1)
    modification_date = models.DateField(verbose_name="modifié le")
    sale_exchange_rate = models.DecimalField(null=True, max_digits=20, decimal_places=5)

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    @staticmethod
    def file_import_sage():
        """
        FR : Retourne le nom du fichier dans le répertoire du serveur Sage X3
        EN : Returns the name of the file in the  directory of the Sage X3 server
        """
        return "ZBICUR_journalier.heron"

    @staticmethod
    def get_columns_import():
        """
        FR : Retourne la position des colonnes
        EN : Returns the position of the columns
        """
        return {
            "currency_current": 0,
            "currency_change": 1,
            "exchange_date": 2,
            "exchange_type": 3,
            "exchange_rate": 4,
            "exchange_inverse": 5,
            "divider": 6,
            "modification_date": 7,
        }

    @staticmethod
    def get_import():
        """
        FR : Retourne la methode à appeler pour importer les fixtures du modèle
        EN : Returns the method to call to import the fixtures from the model
        """
        return "methode d'import à retourner"

    def __str__(self):
        return f"{self.currency_change} - {self.currency_change}"

    class Meta:
        """class Meta du modèle django"""

        ordering = ["currency_current", "currency_change", "exchange_date"]
        unique_together = (("currency_current", "currency_change", "exchange_date"),)