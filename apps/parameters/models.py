"""
Modèles pour les paramétrages
"""
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.db import models

from heron.models import DatesTable, FlagsTable


class StockageJson(DatesTable):
    storage = models.CharField(unique=True, max_length=50)
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
    num_01 = models.DecimalField(null=True, max_digits=20, decimal_places=5, default=0)
    num_02 = models.DecimalField(null=True, max_digits=20, decimal_places=5, default=0)
    num_03 = models.DecimalField(null=True, max_digits=20, decimal_places=5, default=0)
    num_04 = models.DecimalField(null=True, max_digits=20, decimal_places=5, default=0)
    num_05 = models.DecimalField(null=True, max_digits=20, decimal_places=5, default=0)


class Parametrages(FlagsTable):
    parameter_name = models.CharField(unique=True, max_length=50)
    text = models.TextField(null=True, blank=True)
    value = models.DecimalField(null=True, max_digits=20, decimal_places=5, default=0)
    unit = models.CharField(blank=True, null=True, max_length=20)
    validator = models.CharField(blank=True, null=True, max_length=50)
    operation = models.CharField(blank=True, null=True, max_length=200)
    func = models.CharField(blank=True, null=True, max_length=50)
    rate = models.DecimalField(null=True, max_digits=20, decimal_places=5, default=0)
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
    num_01 = models.DecimalField(null=True, max_digits=20, decimal_places=5, default=0)
    num_02 = models.DecimalField(null=True, max_digits=20, decimal_places=5, default=0)
    num_03 = models.DecimalField(null=True, max_digits=20, decimal_places=5, default=0)
    num_04 = models.DecimalField(null=True, max_digits=20, decimal_places=5, default=0)
    num_05 = models.DecimalField(null=True, max_digits=20, decimal_places=5, default=0)


class Numerotation(DatesTable):
    num = models.IntegerField(default=1)
    type_num = models.CharField(max_length=35, verbose_name="Type de numérotation")


class UserParametrage(FlagsTable):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    parameter = models.ForeignKey(Parametrages, on_delete=models.CASCADE)


class SendFiles(FlagsTable):
    file = models.CharField(max_length=35, unique=True)
    description = models.CharField(blank=True, null=True, max_length=100)

    def __str__(self):
        return f"{self.file}"


class SendFilesMail(FlagsTable):
    file = models.ForeignKey(SendFiles, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    email = models.EmailField(null=True, blank=True, max_length=85)

    def __str__(self):
        return f"{self.file} - {self.email}"

    class Meta:
        unique_together = (("file", "email"),)


class AddressesCode(DatesTable):
    ...


class PaymentCondition(FlagsTable):
    name = models.CharField(unique=True, max_length=35)

    def __str__(self):
        return self.name


class BudgetCode(FlagsTable):
    ranking = models.IntegerField(unique=True)
    name = models.CharField(unique=True, max_length=35)

    def __str__(self):
        return f"{self.ranking} - {self.name}"


class AxeSage(FlagsTable):
    class Axe(models.TextChoices):
        BU = "BU", _("BU")
        CCT = "CCT", _("CCT")
        PRJ = "PRJ", _("PRJ")
        PRO = "PRO", _("PRO")
        PYS = "PYS", _("PYS")
        RFA = "RFA", _("RFA")

    axe = models.CharField(choices=Axe.choices, max_length=10)

    def __str__(self):
        return self.axe


class SectionSage(FlagsTable):
    axe = models.ForeignKey(AxeSage, on_delete=models.PROTECT)
    section = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.axe} - {self.section}"


class SubFamilly(FlagsTable):
    name = models.CharField(unique=True, max_length=35)

    def __str__(self):
        return self.name


class Category(FlagsTable):
    ranking = models.IntegerField(unique=True)
    name = models.CharField(unique=True, max_length=35)

    def __str__(self):
        return f"{self.ranking} - {self.name}"


class Periodicity(FlagsTable):
    name = models.CharField(unique=True, max_length=35)

    def __str__(self):
        return self.name


class SageAccount(FlagsTable):
    code_plan_sage = models.CharField(max_length=10)
    account = models.CharField(max_length=35)
    collective = models.CharField(null=True, blank=True, max_length=15)
    auxiliary = models.BooleanField()
    analytical_obligatory = models.BooleanField()
    nb_axes = models.IntegerField(default=0)
    vat_default = models.CharField(null=True, blank=True, max_length=15)

    def __str__(self):
        return f"{self.code_plan_sage} - {self.account}"

    class Meta:
        ordering = ["account"]
        index_together = [
            ["code_plan_sage", "account"],
        ]
        unique_together = ("code_plan_sage", "account")


class SalePriceCategory(FlagsTable):
    name = models.CharField(max_length=80)
    coefficient = models.DecimalField(max_digits=20, decimal_places=5, default=1)
    comment = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


class ActionPermission(FlagsTable):
    name = models.CharField(unique=True, max_length=35)
