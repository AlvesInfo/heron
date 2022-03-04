from django.db import models


class Pays(models.Model):

    iso_pays = models.CharField(primary_key=True, max_length=3, verbose_name="code pays iso")
    pays = models.CharField(max_length=80)
    sigle_monaie = models.CharField(blank=True, null=True, max_length=3)
    nom_monaie = models.CharField(blank=True, null=True, max_length=35)
    iso_monaie = models.CharField(blank=True, null=True, max_length=3)
    ind_tel = models.CharField(blank=True, null=True, max_length=15, verbose_name="indicatif")
    cee = models.BooleanField(default=False)

    def __str__(self):
        return "{0} - {1}".format(self.pays, self.iso_monaie)


class TauxChange(models.Model):
    iso_monaie_principale = models.CharField(blank=True, null=True, max_length=3)
    iso_monaie_change = models.CharField(blank=True, null=True, max_length=3)
    date_change = models.DateField(auto_now_add=True, verbose_name="créé le")
    taux_change_moyen = models.DecimalField(default=0, max_digits=20, decimal_places=5)
    taux_change_achat = models.DecimalField(null=True, max_digits=20, decimal_places=5)
    taux_change_vente = models.DecimalField(null=True, max_digits=20, decimal_places=5)

    class Meta:
        unique_together = (("iso_monaie_principale", "iso_monaie_change", "date_change"),)


class VerificationCodePostaux(models.Model):

    pays = models.OneToOneField(Pays, on_delete=models.CASCADE)
    nbre_car = models.IntegerField(default=0, verbose_name="nombre de caractères")
    num_regle = models.IntegerField(default=0, verbose_name="n° de règle")
    exemple = models.CharField(blank=True, null=True, max_length=35)

    def __str__(self):
        return "{0} - {1} - {2}".format(self.pays, self.nbre_car, self.exemple)


class VerificationNumIntra(models.Model):

    pays = models.OneToOneField(Pays, on_delete=models.CASCADE)
    l = models.CharField(blank=True, null=True, max_length=35)
    func_verif = models.CharField(blank=True, null=True, max_length=35)
    n = models.CharField(blank=True, null=True, max_length=3)
    lng_mini = models.IntegerField(default=0, verbose_name="longeur minimun")
    lng_maxi = models.IntegerField(default=0, verbose_name="longeur maxi")

    def __str__(self):
        return "{0} - {1}".format(self.pays, self.func_verif)
