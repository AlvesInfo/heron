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
from django.utils.translation import gettext_lazy as _

from heron.models import DatesTable, FlagsTable


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
    unit = models.CharField(blank=True, null=True, max_length=20)
    validator = models.CharField(blank=True, null=True, max_length=50)
    operation = models.CharField(blank=True, null=True, max_length=200)
    func = models.CharField(blank=True, null=True, max_length=50)
    rate = models.DecimalField(null=True, max_digits=20, decimal_places=5, default=0)
    base = models.CharField(blank=True, null=True, max_length=50)
    char_01 = models.CharField(blank=True, null=True, max_length=50)
    char_02 = models.CharField(blank=True, null=True, max_length=50)
    char_03 = models.CharField(blank=True, null=True, max_length=50)
    char_04 = models.CharField(blank=True, null=True, max_length=50)
    char_05 = models.CharField(blank=True, null=True, max_length=50)
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
        return self.name

    class Meta:
        """class Meta du modèle django"""

        ordering = ["name"]


class Counter(FlagsTable):
    """
    Table des compteurs de l'application
    FR : Compteur
    EN : Counter
    """

    class DateType(models.TextChoices):
        """DateType choices"""

        FDM = 1, _("Fin de mois")
        DDM = 2, _("Début de mois")
        QDM = 3, _("Quinzaine")
        TDM = 4, _("Trimestriel")
        SDM = 5, _("Semestriel")
        ADA = 6, _("Début d'année")
        AFA = 7, _("Fin d'année")

    name = models.CharField(max_length=35, verbose_name="Type de numérotation")
    prefix = models.CharField(max_length=5, verbose_name="préfix")
    iso_date = models.CharField(null=True, blank=True, max_length=10)
    date_type = models.CharField(
        null=True, blank=True, max_length=20, choices=DateType.choices, default=DateType.FDM
    )
    num = models.IntegerField(default=1)
    suffix = models.CharField(max_length=35, verbose_name="suffix")

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        return self.name

    class Meta:
        """class Meta du modèle django"""

        ordering = ["name"]


class SendFiles(FlagsTable):
    """
    Table de paramétrage de l'envoi de fichier
    FR : Envoi de fichiers
    EN : SendFiles
    """

    name = models.CharField(unique=True, max_length=35, verbose_name="type d'envoi")
    file = models.CharField(unique=True, max_length=35)
    description = models.CharField(null=True, blank=True, max_length=100)
    periodicity = models.CharField(null=True, blank=True, max_length=20)

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        return self.name

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
        to_field="uuid_identification",
        related_name="file_send_file",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        to_field="uuid_identification",
        related_name="user_send_file",
        null=True,
    )
    email = models.EmailField(null=True, blank=True)

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        return f"{self.file} - {self.user} - {self.email}"

    class Meta:
        """class Meta du modèle django"""

        ordering = ["file", "email", "user"]
        unique_together = (("file", "user", "email"),)


class AddressCode(DatesTable):
    """En attente"""

    ...


class SubFamilly(FlagsTable):
    """
    Sous Familles
    FR : Sous Familles
    EN : Sub Famillies
    """

    name = models.CharField(unique=True, max_length=35)

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        return self.name

    class Meta:
        """class Meta du modèle django"""

        ordering = ["name"]


class Category(FlagsTable):
    """
    Grandes Catégories
    FR : Grande Catégories
    EN : Categories
    """

    name = models.CharField(unique=True, max_length=35)
    ranking = models.IntegerField(unique=True)

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        return f"{self.ranking} - {self.name}"

    class Meta:
        """class Meta du modèle django"""

        ordering = ["ranking"]


class Periodicity(FlagsTable):
    """
    Périodicité
    FR : Périodicité
    EN : Periodicity
    """

    name = models.CharField(unique=True, max_length=35)

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        return self.name

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

    name = models.CharField(max_length=80)
    coefficient = models.DecimalField(max_digits=20, decimal_places=5, default=1)
    comment = models.TextField(null=True, blank=True)

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        return self.name

    class Meta:
        """class Meta du modèle django"""

        ordering = ["name"]


class ActionPermission(FlagsTable):
    """
    Action et Permissions
    FR : Action / Permissions
    EN : Action / Permission
    """

    name = models.CharField(unique=True, max_length=35)

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    class Meta:
        """class Meta du modèle django"""

        ordering = ["name"]
