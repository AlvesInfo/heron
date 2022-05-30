"""
Modèles de base de données générales pour l'ensemble de l'application
"""
import uuid
import json

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.bin.encoders import PersonalizedDjangoJSONEncoder


class PicklerFiles(models.Model):
    """Modèle servant à stocker les fichier ou objets pickler"""

    uuid_identification = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pickle_file = models.FileField(upload_to="pickler/")


class ChangesTrace(models.Model):
    """Table de stockage de toutes les modifications en json"""

    DELETE = 0
    CREATE = 1
    UPDATE = 2
    UNDIFINED = 9

    ACTION_CHOICES = [
        (DELETE, "Supression"),
        (CREATE, "Création"),
        (UPDATE, "Mofification"),
        (UNDIFINED, "Inconnu"),
    ]

    action_datetime = models.DateTimeField(auto_now_add=True, verbose_name=_("action date"))
    action_type = models.IntegerField(choices=ACTION_CHOICES)
    function_name = models.CharField(null=True, blank=True, max_length=255)
    action_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="action_by",
        db_column="action_by",
    )
    before = models.JSONField(
        null=True,
        blank=True,
        encoder=PersonalizedDjangoJSONEncoder,
        decoder=json.JSONDecoder,
        verbose_name="avant modification/suppression",
    )
    after = models.JSONField(
        encoder=PersonalizedDjangoJSONEncoder,
        decoder=json.JSONDecoder,
        verbose_name="après création/modification/suppression",
    )
    model_name = models.CharField(null=True, blank=True, max_length=255)
    model = models.CharField(null=True, blank=True, max_length=255)
    db_table = models.CharField(null=True, blank=True, max_length=255)
