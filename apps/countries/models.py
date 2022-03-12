from django.db import models


class Country(models.Model):
    iso_pays = models.CharField(primary_key=True, max_length=3, verbose_name="code pays iso")
    country = models.CharField(max_length=80)
    currency_sigle = models.CharField(blank=True, null=True, max_length=3)
    currency_name = models.CharField(blank=True, null=True, max_length=35)
    currency_iso = models.CharField(blank=True, null=True, max_length=3)
    phone_indicatif = models.CharField(blank=True, null=True, max_length=15)
    cee = models.BooleanField(default=False)

    def __str__(self):
        return "{0} - {1}".format(self.country, self.currency_iso)


class ExchangeRate(models.Model):
    currency_iso_current = models.CharField(blank=True, null=True, max_length=3)
    currency_iso_change = models.CharField(blank=True, null=True, max_length=3)
    exchange_date = models.DateField(auto_now_add=True, verbose_name="créé le")
    average_exchange_rate = models.DecimalField(max_digits=20, decimal_places=5, default=0)
    purchase_exchange_rate = models.DecimalField(null=True, max_digits=20, decimal_places=5)
    sale_exchange_rate = models.DecimalField(null=True, max_digits=20, decimal_places=5)

    class Meta:
        unique_together = (("currency_iso_current", "currency_iso_change", "exchange_date"),)


class ValidationPostalCode(models.Model):
    country = models.OneToOneField(Country, on_delete=models.CASCADE)
    number_char = models.IntegerField(default=0, verbose_name="nombre de caractères")
    rule_number = models.IntegerField(default=0, verbose_name="n° de règle")
    exemple = models.CharField(blank=True, null=True, max_length=35)

    def __str__(self):
        return "{0} - {1} - {2}".format(self.country, self.number_char, self.exemple)


class ValidationIntraVies(models.Model):
    country = models.OneToOneField(Country, on_delete=models.CASCADE)
    prefix = models.CharField(blank=True, null=True, max_length=2)
    func_verif = models.CharField(blank=True, null=True, max_length=35)
    lng_min = models.IntegerField(default=0, verbose_name="longeur minimun")
    lng_max = models.IntegerField(default=0, verbose_name="longeur maxi")

    def __str__(self):
        return "{0} - {1}".format(self.country, self.func_verif)
