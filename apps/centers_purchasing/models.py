from django.db import models

from heron.models import DatesTable, FlagsTable
from apps.countries.models import Country
from apps.parameters.models import SalePriceCategory


class Action(FlagsTable):
    ...


class PrincipalCenterPurchase(FlagsTable):
    name = models.CharField(max_length=80)
    code_name = models.CharField(max_length=35)
    coefficient = models.DecimalField(max_digits=20, decimal_places=5, default=1)
    comment = models.TextField(null=True, blank=True)


class ChildCenterPurchase(FlagsTable):
    principal_center = models.ForeignKey(PrincipalCenterPurchase, on_delete=models.PROTECT)
    name = models.CharField(max_length=80)
    code_name = models.CharField(max_length=35)
    coefficient = models.DecimalField(max_digits=20, decimal_places=5, default=1)
    comment = models.TextField(null=True, blank=True)


class Signboard(FlagsTable):
    center_purchase = models.ForeignKey(ChildCenterPurchase, on_delete=models.PROTECT)
    sale_price_category = models.ForeignKey(SalePriceCategory, on_delete=models.PROTECT)
    name = models.CharField(max_length=80)
    code_name = models.CharField(max_length=35)
    logo = models.ImageField(null=True, upload_to='logos')
    generic_coefficient = models.DecimalField(max_digits=20, decimal_places=5, default=1)
    language = models.ForeignKey(Country, on_delete=models.PROTECT)
    comment = models.TextField(null=True, blank=True)
