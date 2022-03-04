from django.db import models


class Periode(models.Model):

    annee = models.IntegerField(default=0, verbose_name="année")
    type_periode = models.CharField(
        blank=True, null=True, max_length=35, verbose_name="type de période"
    )
    libelle = models.CharField(
        blank=True, null=True, max_length=35, verbose_name="libellé"
    )
    date_debut = models.DateField()
    date_fin = models.DateField()

    def __str__(self):
        return "{0} - {1} - {2}".format(self.annee, self.type_periode, self.libelle)

    class Meta:
        unique_together = (
            ("annee", "type_periode", "libelle", "date_debut", "date_fin"),
        )
