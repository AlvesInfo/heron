# pylint: disable=E0401,R0903
"""
FR : Module des éléments de comptabilité sage pour validations et vérifications
     des élements à exporter dans Sage X3
EN : Sage accounting elements module for validations and verifications
     elements to export in Sage X3

Commentaire:

created at: 2021-11-07
created by: Paulo ALVES

modified at: 2021-11-07
modified by: Paulo ALVES
"""

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
    FR : Comptes au sens comptable de Sage
    EN : Accounts in the accounting sense of Sage
    """

    code_plan_sage = models.CharField(max_length=10)
    account = models.CharField(max_length=35)
    collective = models.CharField(null=True, blank=True, max_length=15)
    auxiliary = models.BooleanField()
    analytical_obligatory = models.BooleanField()
    nb_axes = models.IntegerField(default=0)
    vat_default = models.CharField(null=True, blank=True, max_length=15)

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
    FR : Axes au sens Sage
    EN : Axes in the sense of Sage
    ================================================
    champ    | model attr. | table SAGE | Champ Sage
    ================================================
    Axe      | axe         | GDIE       | DIE
    Intitulé | title       | GDIE       | DES
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
    title = models.CharField(null=True, blank=True, max_length=30)

    @staticmethod
    def file_import_sage():
        """
        FR : Retourne le nom du fichier dans le répertoire ARCHIVE du serveur SAGE
        EN : Returns the name of the file in the ARCHIVE directory of the SAGE server
        """
        return "ZBIAXES_journalier.heron"

    @staticmethod
    def set_import():
        """
        FR : Retourne la methode à appeler pour importer les fixtures du modèle
        EN : RReturns the method to call to import the fixtures from the model
        """
        return "methode d'import à retourner"

    def __str__(self):
        return self.axe


class SectionSage(FlagsTable):
    """
    FR : Section au sens Sage
    EN : Sections in the sense of Sage
    ====================================================
    champ        | model attr. | table SAGE | Champ Sage
    ====================================================
    Axe          | axe         | CACCE       | DIE
    Section      | section     | CACCE       | CCE
    Refacturable | chargeable  | CACCE       | XFLREFAC
    ====================================================
    """

    axe = models.ForeignKey(AxeSage, on_delete=models.PROTECT)
    section = models.CharField(max_length=15)
    chargeable = models.BooleanField(default=True)
    regroup_01 = models.CharField(null=True, blank=True, max_length=15)
    regroup_02 = models.CharField(null=True, blank=True, max_length=15)

    @staticmethod
    def file_import_sage():
        """
        FR : Retourne le nom du fichier dans le répertoire ARCHIVE du serveur SAGE
        EN :: Returns the name of the file in the ARCHIVE directory of the SAGE server
        """
        return "ZBICCE_journalier.heron"

    @staticmethod
    def set_import():
        """
        FR : Retourne la methode à appeler pour importer les fixtures du modèle
        EN : RReturns the method to call to import the fixtures from the model
        """
        return "methode d'import à retourner"

    def __str__(self):
        return f"{self.axe} - {self.section}"

    class Meta:
        """class Meta du modèle django"""

        unique_together = (("axe", "section"),)
        index_together = [
            ["axe", "section"],
        ]


class VatSage(FlagsTable):
    """
    FR : TVA au sens de Sage
    EN : VAT as defined by Sage
    ====================================================
    champ        | model attr. | table SAGE | Champ Sage
    ====================================================
    Tva          | vat         | TABVAT     | VAT
    Intitulé     | title       | TABVAT     | VATDES
    Taux         | rate        | TABVAT     | VATRAT
    Régime       | vat_regime  | TABVAT     | VATVAC
    ====================================================
    """

    vat = models.CharField(null=True, blank=True, max_length=5)
    title = models.CharField(null=True, blank=True, max_length=30)
    rate = models.DecimalField(max_digits=20, decimal_places=5, default=0)
    vat_regime = models.CharField(null=True, blank=True, max_length=5)

    @staticmethod
    def file_import_sage():
        """
        FR : Retourne le nom du fichier dans le répertoire ARCHIVE du serveur SAGE
        EN :: Returns the name of the file in the ARCHIVE directory of the SAGE server
        """
        return "ZBIVAT_journalier.heron"

    @staticmethod
    def set_import():
        """
        FR : Retourne la methode à appeler pour importer les fixtures du modèle
        EN : RReturns the method to call to import the fixtures from the model
        """
        return "methode d'import à retourner"

    def __str__(self):
        return f"{self.vat} - {self.title}"
