# pylint: disable=E0401,R0903
"""
FR : Module des models des périodes
EN : Periods models module

Commentaire:

created at: 2021-11-07
created by: Paulo ALVES

modified at: 2021-11-07
modified by: Paulo ALVES
"""
from django.db import models


class Periode(models.Model):
    """
    Table des Peridoe, sert à selectionner des dates périodes et between
    FR : Périodes
    EN : Periods
    """

    year = models.IntegerField(default=0, verbose_name="année")
    period_type = models.CharField(
        blank=True, null=True, max_length=35, verbose_name="type de période"
    )
    wording = models.CharField(blank=True, null=True, max_length=35, verbose_name="libellé")
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return f"{self.year} - {self.period_type} - {self.wording}"

    class Meta:
        """class Meta du modèle django"""

        ordering = [
            "period_type",
            "start_date",
        ]
        unique_together = (("year", "period_type", "wording", "start_date", "end_date"),)
