# pylint: disable=E0401
"""Module du modèle de données pour la gestion d'erreurs et de lecture trace

Commentaire:

created at: 2022-03-22
created by: Paulo ALVES

modified at:
modified by:
"""
import uuid

from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.db import models


class BaseFlux(models.Model):
    """
    Table Abstraite de base pour les tables
    FR : Table Abstraite de Base
    EN : Flags Abstract Table
    """

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("created at"))
    to_active = models.BooleanField(null=True, default=False)
    to_delete = models.BooleanField(null=True, default=False)
    delete = models.BooleanField(null=True)
    active = models.BooleanField(null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        related_name="+",
        db_column="created_by",
    )

    class Meta:
        """class Meta du modèle django"""

        abstract = True


class Trace(BaseFlux):
    """
    Table pour les traces apllicatives ou des actions utilisateurs
    FR : Table Traces Apllicatives
    EN : Applications Traces Table
    """

    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    application_name = models.CharField(max_length=35)
    flow_name = models.CharField(max_length=80)
    errors = models.BooleanField(default=False)
    comment = models.TextField(null=True, blank=True)


class Line(models.Model):
    class Insertion(models.TextChoices):
        """Insertion choices"""

        IN = "Create", _("Create")
        UP = "Update", _("Update")
        ER = "Error", _("Error")
        PA = "Passed", _("Passed")

    trace = models.ForeignKey(
        Trace,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        related_name="line_trace",
        db_column="trace",
    )
    insertion = models.CharField(
        null=True, blank=True, max_length=20, choices=Insertion.choices
    )
    line = models.IntegerField()
    designation = models.TextField()
