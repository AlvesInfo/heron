# pylint: disable=E0401,R0903
"""
FR : Module de l'application Héron, des tables Abstraites
EN : Héron application module, Abstract tables

Commentaire:

created at: 2021-11-07
created by: Paulo ALVES

modified at: 2021-11-07
modified by: Paulo ALVES
"""
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.db import models


class DatesTable(models.Model):
    """
    Table Abstraite de base pour les tables
    FR : Table Abstraite de Base Dates
    EN : Flags Abstract Table Dates
    """

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("created at"))
    modified_at = models.DateTimeField(auto_now=True, verbose_name=_("modified at"))

    class Meta:
        """class Meta du modèle django"""

        abstract = True


class FlagsTable(models.Model):
    """
    Table Abstraite de base pour les tables
    FR : Table Abstraite de Base Flags
    EN : Flags Abstract Table Flags
    """

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("created at"))
    modified_at = models.DateTimeField(auto_now=True, verbose_name=_("modified at"))
    active = models.BooleanField(null=True, default=False)
    delete = models.BooleanField(null=True, default=False)
    export = models.BooleanField(null=True, default=False)
    valid = models.BooleanField(null=True, default=False)
    flag_to_active = models.BooleanField(null=True, default=False)
    flag_to_delete = models.BooleanField(null=True, default=False)
    flag_to_export = models.BooleanField(null=True, default=False)
    flag_to_valid = models.BooleanField(null=True, default=False)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        db_column="created_by",
    )
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        db_column="modified_by",
    )
    delete_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        db_column="delete_by",
    )

    class Meta:
        """class Meta du modèle django"""

        abstract = True


class DbTableAuthorisation(models.Model):
    """
    Table pour savoir si un utlisateur peux visualiser ou modifier un champ
    FR : Table pour les Flags d'authorisation
    EN : Flags Table authorisation
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    model_to_consult = models.CharField(max_length=255, verbose_name="model django")
    all_table = models.BooleanField(default=False)

    to_display = models.BooleanField(default=True)
    to_edit = models.BooleanField(default=True)
