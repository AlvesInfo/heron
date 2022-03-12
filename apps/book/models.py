import uuid

from django.db import models
from django.utils.translation import ugettext_lazy as _

from heron.models import DatesTable, FlagsTable

from apps.centers_purchasing.models import Signboard
from apps.countries.models import Country
from apps.parameters.models import PaymentCondition, BudgetCode, SageAccount, SalePriceCategory

# Validation xml tva intra : https://ec.europa.eu/taxation_customs/vies/faq.html#item_18
#                            https://ec.europa.eu/taxation_customs/vies/technicalInformation.html


class Nature(FlagsTable):
    category = models.CharField(unique=True, blank=True, max_length=35)
    to_display = models.CharField(null=True, blank=True, max_length=35)
    for_contact = models.BooleanField(null=True, default=None)

    def save(self, *args, **kwargs):
        self.category = self.category.capitalize()

        if not self.to_display:
            self.to_display = self.category

        super().save(*args, **kwargs)

    def __str__(self):
        return self.to_display

    class Meta:
        ordering = ["category"]


class CLientCategory(FlagsTable):
    name = models.CharField(max_length=80)


class Society(FlagsTable):
    class Frequence(models.TextChoices):
        MENSUEL = 1, _("Mensuel")
        TRIMESTRIEL = 2, _("Trimestriel")
        SEMESTRIEL = 3, _("Semestriel")
        ANNUEL = 4, _("Annuel")

    class Remise(models.TextChoices):
        TOTAL = 1, _("Fournisseur Total")
        FAMILLE = 2, _("Famille Article")
        ARTICLE = 3, _("Article")

    nature = models.ForeignKey(Nature, on_delete=models.PROTECT, related_name="society_nature")
    name = models.CharField(max_length=80)
    corporate_name = models.CharField(null=True, blank=True, max_length=80)
    code_tiers_x3 = models.CharField(null=True, blank=True, max_length=15)
    code_plan_sage = models.CharField(max_length=10)
    siren_number = models.CharField(null=True, blank=True, max_length=70)
    siret_number = models.CharField(null=True, blank=True, max_length=70)
    vat_cee_number = models.CharField(null=True, blank=True, max_length=70)
    vat_number = models.CharField(null=True, blank=True, max_length=70)
    supplier_identifier = models.CharField(null=True, blank=True, max_length=70)
    client_identifier = models.CharField(null=True, blank=True, max_length=70)
    naf_code = models.CharField(null=True, blank=True, max_length=70)
    currency = models.CharField(default="EUR", max_length=3)
    comment = models.TextField(null=True, blank=True)

    # Supplier type
    is_supplier = models.BooleanField(default=False)
    is_client = models.BooleanField(default=False)
    is_particular = models.BooleanField(default=False)
    is_service_provider = models.BooleanField(default=False)
    is_prospect = models.BooleanField(default=False)
    is_transporter = models.BooleanField(default=False)
    is_contractor = models.BooleanField(default=False)
    is_agent = models.BooleanField(default=False)

    # Maisons part
    code_cct_x3 = models.CharField(null=True, blank=True, max_length=15)
    code_cosium = models.CharField(null=True, blank=True, max_length=15)
    client_category = models.ForeignKey(CLientCategory, on_delete=models.PROTECT, null=True)
    sign_board = models.ForeignKey(Signboard, on_delete=models.PROTECT, null=True)
    payment_condition = models.ForeignKey(PaymentCondition, null=True, on_delete=models.PROTECT)
    budget_code = models.ForeignKey(BudgetCode, null=True, on_delete=models.PROTECT)
    opening_date = models.DateField(null=True)
    closing_date = models.DateField(null=True)
    signature_franchise_date = models.DateField(null=True)
    agreement_franchise_end_date = models.DateField(null=True)
    agreement_renew_date = models.DateField(null=True)
    entry_fee_amount = models.DecimalField(max_digits=20, decimal_places=5, null=True)
    renew_fee_amoount = models.DecimalField(max_digits=20, decimal_places=5, null=True)
    sale_price_category = models.ForeignKey(SalePriceCategory, on_delete=models.PROTECT)
    generic_coefficient = models.DecimalField(max_digits=20, decimal_places=5, default=1)
    credit_account = models.ForeignKey(SageAccount, on_delete=models.PROTECT, related_name="cr_soc")
    debit_account = models.ForeignKey(SageAccount, on_delete=models.PROTECT, related_name="cd_soc")
    prov_account = models.ForeignKey(SageAccount, on_delete=models.PROTECT, related_name="prov_soc")

    # RFA
    rfa_frequence = models.IntegerField(choices=Frequence.choices, default=Frequence.MENSUEL)
    rfa_remise = models.IntegerField(choices=Remise.choices, default=Remise.TOTAL)

    # Identification
    uuid_identification = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    def __str__(self):
        return f"{self.nature}{' - ' if self.nature else ''}{self.name}"

    class Meta:
        ordering = ["name"]


class Addresses(FlagsTable):
    society = models.ForeignKey(Society, on_delete=models.CASCADE, related_name="adresses_society")
    address_name = models.CharField(default="Principale", unique=True, max_length=35)
    address_code = models.CharField(null=True, blank=True, max_length=10)
    address_number = models.CharField(null=True, blank=True, max_length=10)
    road_type = models.CharField(null=True, blank=True, max_length=35)
    line_01 = models.CharField(max_length=80)
    line_02 = models.CharField(null=True, blank=True, max_length=80)
    line_03 = models.CharField(null=True, blank=True, max_length=80)
    state = models.CharField(null=True, blank=True, max_length=80)
    region = models.CharField(null=True, blank=True, max_length=80)
    postal_code = models.CharField(null=True, blank=True, max_length=35)
    city = models.CharField(null=True, blank=True, max_length=80)
    country = models.ForeignKey(Country, on_delete=models.PROTECT, related_name="adresses_country")
    building = models.CharField(null=True, blank=True, max_length=80)
    floor = models.CharField(null=True, blank=True, max_length=80)
    phone_number = models.CharField(null=True, blank=True, max_length=35)

    def __str__(self):
        return f"{self.city}"

    class Meta:
        ordering = ["country"]


class ExchangePermision(FlagsTable):
    name = models.CharField(unique=True, max_length=35)
    comment = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class Contact(FlagsTable):
    society = models.ForeignKey(Society, on_delete=models.CASCADE, related_name="contact_society")
    nature = models.ForeignKey(Nature, on_delete=models.PROTECT, related_name="contact_nature")
    first_name = models.CharField(null=True, blank=True, max_length=80)
    last_name = models.CharField(null=True, blank=True, max_length=80)
    phone_number = models.CharField(null=True, blank=True, max_length=35)
    mobile_number = models.CharField(null=True, blank=True, max_length=35)
    email = models.EmailField(null=True, blank=True)

    def __str__(self):
        return f"{self.first_name}{' - ' if self.first_name else ''}{self.last_name}"

    class Meta:
        ordering = ["last_name", "first_name"]


class ContactExchange(models.Model):
    contact = models.ForeignKey(Contact, on_delete=models.PROTECT)
    exchange_permission = models.ForeignKey(ExchangePermision, on_delete=models.PROTECT)


class SocietyBank(FlagsTable):
    society = models.ForeignKey(Society, on_delete=models.CASCADE, related_name="bank_society")
    payee = models.CharField(null=True, blank=True, max_length=80)
    uuid_identification = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    bank_name = models.CharField(max_length=35)
    bank_code = models.CharField(unique=True, max_length=5)
    counter_code = models.CharField(null=True, blank=True, max_length=5)
    account_number = models.CharField(unique=True, max_length=11)
    account_key = models.CharField(null=True, blank=True, max_length=2)
    iban = models.CharField(null=True, blank=True, max_length=50)
    code_swift = models.CharField(null=True, blank=True, max_length=27)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.society} - {self.bank_name}"

    class Meta:
        ordering = ["bank_name"]
