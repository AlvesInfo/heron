import uuid

from django.db import models

# Create your models here.


class EssaisCopyPostgresql(models.Model):
    l_00 = models.CharField(unique=True, max_length=20)
    l_01 = models.CharField(null=True, blank=True, max_length=20)
    l_02 = models.CharField(null=True, blank=True, max_length=20)
    l_03 = models.CharField(null=True, blank=True, max_length=20)
    l_04 = models.CharField(null=True, blank=True, max_length=20)
    l_05 = models.CharField(null=True, blank=True, max_length=20)
    l_06 = models.CharField(null=True, blank=True, max_length=20)
    l_07 = models.CharField(null=True, blank=True, max_length=20)
    l_08 = models.CharField(null=True, blank=True, max_length=20)
    l_09 = models.CharField(null=True, blank=True, max_length=20)
    l_10 = models.CharField(null=True, blank=True, max_length=20)
    l_11 = models.CharField(null=True, blank=True, max_length=20)
    l_12 = models.CharField(null=True, blank=True, max_length=20)
    l_13 = models.CharField(null=True, blank=True, max_length=20)
    l_14 = models.CharField(null=True, blank=True, max_length=20)
    l_15 = models.CharField(null=True, blank=True, max_length=20)
    l_16 = models.CharField(null=True, blank=True, max_length=20)
    l_17 = models.CharField(null=True, blank=True, max_length=20)
    l_18 = models.CharField(null=True, blank=True, max_length=20)
    l_19 = models.CharField(null=True, blank=True, max_length=20)
    l_20 = models.CharField(null=True, blank=True, max_length=20)
    l_21 = models.CharField(null=True, blank=True, max_length=20)
    l_22 = models.CharField(null=True, blank=True, max_length=20)
    l_23 = models.CharField(null=True, blank=True, max_length=20)
    l_24 = models.CharField(null=True, blank=True, max_length=20)
    l_25 = models.CharField(null=True, blank=True, max_length=20)
    l_26 = models.CharField(null=True, blank=True, max_length=20)
    l_27 = models.CharField(null=True, blank=True, max_length=20)
    l_28 = models.CharField(null=True, blank=True, max_length=20)
    l_29 = models.CharField(null=True, blank=True, max_length=20)
    l_30 = models.CharField(null=True, blank=True, max_length=20)


class PicklerFiles(models.Model):
    """Modèle servant à stocker les fichier ou objets pickler"""
    uuid_identification = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pickle_file = models.FileField()
