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
    Table Abstraite des dates, création et modification
    FR : Table des Dates
    EN : Dates Table
    """

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("created at"))
    modified_at = models.DateTimeField(auto_now=True, verbose_name=_("modified at"))

    class Meta:
        """class Meta du modèle django"""

        abstract = True


class FlagsTable(models.Model):
    """
    Table Abstraite des dates, création et modification, flags et users
    FR : Table des Flags
    EN : Flags Table
    """

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("created at"))
    modified_at = models.DateTimeField(auto_now=True, verbose_name=_("modified at"))
    active = models.BooleanField(default=False)
    to_delete = models.BooleanField(default=False)
    visible = models.BooleanField(default=True)
    flag_delete = models.BooleanField(null=True)
    flag_to_delete = models.BooleanField(null=True)
    flag_active = models.BooleanField(null=True)
    flag_export = models.BooleanField(null=True)
    flag_to_validated = models.BooleanField(null=True)
    flag_valide = models.BooleanField(null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, related_name="+"
    )
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, related_name="+"
    )
    delete_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, related_name="+"
    )

    class Meta:
        """class Meta du modèle django"""

        abstract = True
