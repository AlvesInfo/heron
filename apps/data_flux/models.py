# pylint: disable=E0401,R0903
"""Module du modèle de données pour la gestion d'erreurs et de lecture trace

Commentaire:

created at: 2022-03-22
created by: Paulo ALVES

modified at:
modified by:
"""
import uuid

from django.utils.translation import gettext_lazy as _
from django.db import models

from heron.models import FlagsTable


class Trace(FlagsTable):
    """
    Table pour les traces apllicatives ou des actions utilisateurs
    FR : Table Traces Apllicatives
    EN : Applications Traces Table
    """

    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    trace_name = models.CharField(max_length=160)
    file_name = models.CharField(null=True, blank=True, max_length=255)
    application_name = models.CharField(null=True, blank=True, max_length=80)
    flow_name = models.CharField(null=True, blank=True, max_length=80)
    errors = models.BooleanField(default=False)
    comment = models.TextField(null=True, blank=True)
    created_numbers_records = models.IntegerField(null=True)
    updated_numbers_records = models.IntegerField(null=True)
    errors_numbers_records = models.IntegerField(null=True)
    unknown_numbers_records = models.IntegerField(null=True)
    time_to_process = models.DecimalField(
        null=True, max_digits=20, decimal_places=2, verbose_name="temps de traitement", default=0
    )

    class Meta:
        """class Meta du modèle django"""

        ordering = ["-created_at", "trace_name", "file_name"]


class Line(models.Model):
    """
    Table pour les lignes des traces
    FR : Table Lignes Traces Apllicatives
    EN : Applications Traces Lines Table
    """

    class Insertiontype(models.TextChoices):
        """Insertion choices"""

        IN = "Create", _("Create")
        UP = "Update", _("Update")
        ER = "Errors", _("Errors")
        PA = "Passed", _("Passed")

    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    trace = models.ForeignKey(
        Trace,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        related_name="line_trace",
        db_column="trace",
    )
    insertion_type = models.CharField(
        null=True, blank=True, max_length=20, choices=Insertiontype.choices
    )
    num_line = models.IntegerField(null=True)
    designation = models.TextField(null=True)


class Error(models.Model):
    """
    Table pour les lignes d'erreurs des traces
    FR : Table Lignes Erreurs Traces Apllicatives
    EN : Applications Traces Lines Errors Table
    """

    line = models.ForeignKey(
        Line,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
        related_name="error_line",
        db_column="line",
    )
    attr_name = models.CharField(null=True, blank=True, max_length=80)
    file_column = models.CharField(null=True, blank=True, max_length=80)
    message = models.CharField(null=True, blank=True, max_length=255)
    data_expected = models.TextField(null=True, blank=True)
    data_received = models.TextField(null=True, blank=True)


class Essais(models.Model):
    """EssaiS"""

    col_texte = models.CharField(max_length=12)
    col_2 = models.CharField(null=True, blank=True, max_length=10)
    col_3 = models.CharField(null=True, blank=True, max_length=100)
    col_int = models.IntegerField(null=True)


class EssaisZ(models.Model):
    """EssaiSZ"""

    trace = models.ForeignKey(
        Trace,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        to_field="uuid_identification",
    )
    col_texte = models.CharField(max_length=12)
    col_2 = models.CharField(null=True, blank=True, max_length=10)
    col_3 = models.CharField(null=True, blank=True, max_length=100)
    col_int = models.IntegerField(unique=True)

    class Meta:
        """class Meta du modèle django"""

        constraints = [
            models.UniqueConstraint(fields=["col_texte", "col_2", "col_3"], name="unique_essaisz")
        ]
