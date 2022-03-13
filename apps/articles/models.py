import uuid

from django.db import models
from django.utils.translation import ugettext_lazy as _

from heron.models import DatesTable, FlagsTable
from apps.countries.models import Country
from apps.parameters.models import SubFamilly, Category, BudgetCode, SalePriceCategory
from apps.book.models import Society


class Article(FlagsTable):
    class Unit(models.TextChoices):
        GR = "Grammes", _("Grammes")
        KG = "Kilo", _("Kilo")
        U = "Unité", _("Unité")
        BOITE = "Boite", _("Boite")

    supplier = models.ForeignKey(Society, on_delete=models.PROTECT)
    reference = models.CharField(max_length=35)
    ean_code = models.CharField(null=True, blank=True, max_length=35)
    libelle = models.CharField(null=True, blank=True, max_length=80)
    libelle_heron = models.CharField(null=True, blank=True, max_length=80)
    big_category = models.ForeignKey(Category, on_delete=models.PROTECT, null=True)
    sub_familly = models.ForeignKey(SubFamilly, on_delete=models.PROTECT, null=True)
    budget_code = models.ForeignKey(BudgetCode, on_delete=models.PROTECT, null=True)
    axe_pro_supplier = models.CharField(null=True, blank=True, max_length=10)
    axe_bu = models.CharField(null=True, blank=True, max_length=10)
    axe_cct = models.CharField(null=True, blank=True, max_length=10)
    axe_prj = models.CharField(null=True, blank=True, max_length=10)
    axe_pro = models.CharField(null=True, blank=True, max_length=10)
    axe_pys = models.CharField(null=True, blank=True, max_length=10)
    axe_rfa = models.CharField(null=True, blank=True, max_length=10)
    made_in = models.ForeignKey(
        Country, on_delete=models.PROTECT, related_name="article_country", null=True
    )
    item_weight = models.DecimalField(max_digits=20, decimal_places=5, default=0)
    unit_weight = models.CharField(
        null=True, blank=True, max_length=20, choices=Unit.choices, default=Unit.GR
    )
    packaging_qty = models.DecimalField(max_digits=20, decimal_places=5, default=1)
    customs_code = models.CharField(null=True, blank=True, max_length=35)
    catalog_price = models.CharField(null=True, blank=True, max_length=35)
    uuid_identification = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    comment = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.supplier} - {self.reference} - {self.libelle_heron}"


class SellingPrice(FlagsTable):
    sale_price_category = models.ForeignKey(SalePriceCategory, on_delete=models.PROTECT)
    article = models.ForeignKey(Article, on_delete=models.PROTECT)
    currency = models.CharField(max_length=3, default="EUR")
    sale_price = models.DecimalField(max_digits=20, decimal_places=5)
    comment = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.sale_price_category} - {self.article}"


class SalePriceHistory(DatesTable):
    sale_price_category = models.ForeignKey(SalePriceCategory, on_delete=models.PROTECT)
    article = models.ForeignKey(Article, on_delete=models.PROTECT)
    currency = models.CharField(max_length=3, default="EUR")
    sale_price = models.DecimalField(max_digits=20, decimal_places=5)
    start_date = models.DecimalField(max_digits=20, decimal_places=5)
    end_date = models.DecimalField(max_digits=20, decimal_places=5)

    def __str__(self):
        return f"{self.sale_price_category} - {self.article}"


class Subscription(FlagsTable):
    name = models.CharField(max_length=80)

    def __str__(self):
        return self.name
