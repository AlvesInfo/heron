"""
Modèles pour les paramétrages
"""
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.db import models


class DatesTable(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("created at"))
    modified_at = models.DateTimeField(auto_now=True, verbose_name=_("modified at"))
    active = models.BooleanField(default=False)
    to_delete = models.BooleanField(default=False)
    visible = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, related_name="+"
    )
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, related_name="+"
    )

    class Meta:
        abstract = True


class StockageJson(DatesTable):
    stockage = models.CharField(unique=True, max_length=50)
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
    num_01 = models.DecimalField(blank=True, null=True, default=0, decimal_places=5, max_digits=20)
    num_02 = models.DecimalField(blank=True, null=True, default=0, decimal_places=5, max_digits=20)
    num_03 = models.DecimalField(blank=True, null=True, default=0, decimal_places=5, max_digits=20)
    num_04 = models.DecimalField(blank=True, null=True, default=0, decimal_places=5, max_digits=20)
    num_05 = models.DecimalField(blank=True, null=True, default=0, decimal_places=5, max_digits=20)


class Parametrages(DatesTable):
    nom_parametrage = models.CharField(unique=True, max_length=50)
    texte = models.TextField(null=True, blank=True)
    valeur = models.DecimalField(null=True, blank=True, default=0, decimal_places=2, max_digits=20)
    unite = models.CharField(blank=True, null=True, max_length=20)
    validateur = models.CharField(blank=True, null=True, max_length=50)
    operation = models.CharField(blank=True, null=True, max_length=200)
    fonction = models.CharField(blank=True, null=True, max_length=50)
    taux = models.DecimalField(max_digits=20, decimal_places=5, blank=True, null=True)
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
    num_01 = models.DecimalField(blank=True, null=True, default=0, decimal_places=5, max_digits=20)
    num_02 = models.DecimalField(blank=True, null=True, default=0, decimal_places=5, max_digits=20)
    num_03 = models.DecimalField(blank=True, null=True, default=0, decimal_places=5, max_digits=20)
    num_04 = models.DecimalField(blank=True, null=True, default=0, decimal_places=5, max_digits=20)
    num_05 = models.DecimalField(blank=True, null=True, default=0, decimal_places=5, max_digits=20)


class Numerotation(DatesTable):
    num = models.IntegerField(default=1)
    type_num = models.CharField(max_length=35, verbose_name="Type de numérotation")


class UserParametrage(DatesTable):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    parametrage = models.ForeignKey(Parametrages, on_delete=models.CASCADE)


class SendFiles(models.Model):

    fichier = models.CharField(max_length=35, unique=True)
    description = models.CharField(blank=True, null=True, max_length=100)

    def __str__(self):
        return "{0}".format(self.fichier)


class SendFilesMail(models.Model):

    fichier = models.ForeignKey(SendFiles, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    email = models.EmailField(null=True, blank=True, max_length=85)

    def __str__(self):
        return "{0} - {1}".format(self.fichier, self.email)

    class Meta:
        unique_together = (("fichier", "email"),)
