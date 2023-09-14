# pylint: disable=E0401,R0903
"""
FR : Module des modèles de comptabilité sage pour validation et vérifications
     des élements à importer de Sage X3
EN : Sage accounting models module for validation and verifications
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
    def get_uniques():
        """
        FR : Retourne les champs uniques de la table
        EN: Returns the unique fields of the table
        """
        return {"axe"}

    @property
    def get_import(self):
        """
        FR : Retourne la methode à appeler pour importer à partir d'un fichier de type csv
        EN : Returns the method to call to import from a csv file type
        """
        return "methode d'import à retourner"

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{str(self.axe)} - {self.name}"

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
    Intitulé        | name        | CACCE       | DES
    Intitulé court  | short_name  | CACCE       | DESSHO
    Refacturable    | chargeable  | CACCE       | XFLREFAC
    Regroupement    | regroup_01  | CACCE       | ZREG1
    Regroupement    | regroup_02  | CACCE       | ZREG2
    actif           | active      | CACCE       | ENAFLG
    ========================================================
    """

    axe = models.ForeignKey(
        AxeSage,
        on_delete=models.CASCADE,
        to_field="axe",
        related_name="axe_axe",
        db_column="axe",
    )
    section = models.CharField(max_length=15)
    name = models.CharField(null=True, blank=True, max_length=30, verbose_name="intitulé")
    short_name = models.CharField(
        null=True, blank=True, max_length=20, verbose_name="intitulé court"
    )
    chargeable = models.BooleanField(null=True, default=True)
    regroup_01 = models.CharField(null=True, blank=True, max_length=15)
    regroup_02 = models.CharField(null=True, blank=True, max_length=15)
    active = models.BooleanField(null=True, default=True)

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    axes = models.Manager()
    objects = SectionSageQuerySet.as_manager()

    @classmethod
    def axe_bu(cls):
        """
        FR : Retourne les sections pour l'axe BU de Sage X3
        EN : Returns the sections for the BU axis of Sage X3
        """
        return [(row.section, row.section) for row in cls.objects.bu_section()]

    @classmethod
    def axe_cct(cls):
        """
        FR : Retourne les sections pour l'axe CCT de Sage X3
        EN : Returns the sections for the CCT axis of Sage X3
        """
        return [(row.section, row.section) for row in cls.objects.cct_section()]

    @classmethod
    def axe_prj(cls):
        """
        FR : Retourne les sections pour l'axe PRJ de Sage X3
        EN : Returns the sections for the PRJ axis of Sage X3
        """
        return [(row.section, row.section) for row in cls.objects.prj_section()]

    @classmethod
    def axe_pro(cls):
        """
        FR : Retourne les sections pour l'axe PRO de Sage X3
        EN : Returns the sections for the PRO axis of Sage X3
        """
        return [(row.section, row.section) for row in cls.objects.pro_section()]

    @classmethod
    def axe_pys(cls):
        """
        FR : Retourne les sections pour l'axe PYS de Sage X3
        EN : Returns the sections for the PYS axis of Sage X3
        """
        return [(row.section, row.section) for row in cls.objects.pys_section()]

    @classmethod
    def axe_rfa(cls):
        """
        FR : Retourne les sections pour l'axe RFA de Sage X3
        EN : Returns the sections for the RFA axis of Sage X3
        """
        return [(row.section, row.section) for row in cls.objects.rfa_section()]

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
            "active": 7,
        }

    @staticmethod
    def get_uniques():
        """
        FR : Retourne les champs uniques de la table
        EN: Returns the unique fields of the table
        """
        return {"axe", "section"}

    @property
    def get_import(self):
        """
        FR : Retourne la methode à appeler pour importer à partir d'un fichier de type csv
        EN : Returns the method to call to import from a csv file type
        """
        return "methode d'import à retourner"

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{str(self.section)} - {self.name}"

    class Meta:
        """class Meta du modèle django"""

        ordering = ["section"]
        unique_together = (("axe", "section"),)
        index_together = [
            ["axe", "section"],
        ]
