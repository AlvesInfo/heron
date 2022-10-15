from django.db import models


class PocBalance(models.Model):
    societe = models.CharField(max_length=150)
    annee = models.CharField(max_length=10)
    compte = models.CharField(max_length=10)
    libelle = models.CharField(max_length=255)
    debit = models.DecimalField(null=True, max_digits=20, decimal_places=5, default=0)
    credit = models.DecimalField(null=True, max_digits=20, decimal_places=5, default=0)
    solde = models.DecimalField(null=True, max_digits=20, decimal_places=5, default=0)
