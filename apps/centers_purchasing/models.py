import uuid

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

    # Identification
    uuid_identification = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)


class ChildCenterPurchase(FlagsTable):
    principal_center = models.ForeignKey(PrincipalCenterPurchase, on_delete=models.PROTECT)
    name = models.CharField(max_length=80)
    code_name = models.CharField(max_length=35)
    coefficient = models.DecimalField(max_digits=20, decimal_places=5, default=1)
    comment = models.TextField(null=True, blank=True)

    # Identification
    uuid_identification = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)


class Signboard(FlagsTable):
    center_purchase = models.ForeignKey(ChildCenterPurchase, on_delete=models.PROTECT)
    sale_price_category = models.ForeignKey(SalePriceCategory, on_delete=models.PROTECT)
    name = models.CharField(max_length=80)
    code_name = models.CharField(max_length=35)
    logo = models.ImageField(null=True, upload_to="logos")
    generic_coefficient = models.DecimalField(max_digits=20, decimal_places=5, default=1)
    language = models.ForeignKey(Country, on_delete=models.PROTECT)
    comment = models.TextField(null=True, blank=True)

    # Identification
    uuid_identification = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)


class SignboardModel(FlagsTable):
    sign_board = models.ForeignKey(Signboard, on_delete=models.PROTECT)
    name = models.CharField(max_length=80)
    code_name = models.CharField(max_length=35)
    action = models.CharField(null=True, blank=True, max_length=80)
    comment = models.TextField(null=True, blank=True)

    # Identification
    uuid_identification = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)


class Translation(FlagsTable):
    name = models.CharField(max_length=80)
    code_name = models.CharField(max_length=35)
    french_text = models.TextField()
    german_text = models.TextField(null=True, blank=True)
    italian_text = models.TextField(null=True, blank=True)
    spanih_text = models.TextField(null=True, blank=True)
    polish_text = models.TextField(null=True, blank=True)
    romanian_text = models.TextField(null=True, blank=True)
    dutch_text = models.TextField(null=True, blank=True)
    flemish_text = models.TextField(null=True, blank=True)
    greek_text = models.TextField(null=True, blank=True)
    hungarian_text = models.TextField(null=True, blank=True)
    portuguese_text = models.TextField(null=True, blank=True)
    czech_text = models.TextField(null=True, blank=True)
    swedish_text = models.TextField(null=True, blank=True)
    bulgarian_text = models.TextField(null=True, blank=True)
    english_text = models.TextField(null=True, blank=True)
    slovak_text = models.TextField(null=True, blank=True)
    danish_text = models.TextField(null=True, blank=True)
    norwegian_text = models.TextField(null=True, blank=True)
    finnish_text = models.TextField(null=True, blank=True)
    lithuanian_text = models.TextField(null=True, blank=True)
    croatian_text = models.TextField(null=True, blank=True)
    slovene_text = models.TextField(null=True, blank=True)
    estonian_text = models.TextField(null=True, blank=True)
    irish_text = models.TextField(null=True, blank=True)
    latvian_text = models.TextField(null=True, blank=True)
    maltese_text = models.TextField(null=True, blank=True)

    # Identification
    uuid_identification = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)


class SignboardModelTranslate(FlagsTable):
    sign_board_model = models.ForeignKey(SignboardModel, on_delete=models.PROTECT)
    translation = models.ForeignKey(SignboardModel, on_delete=models.PROTECT)

    # Identification
    uuid_identification = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)


class TranslationParamaters(FlagsTable):
    translation = models.ForeignKey(
        Translation, on_delete=models.PROTECT, related_name="paramter_translation"
    )
    prefix_suffix = models.CharField(max_length=1, default="$")
    model = models.CharField(max_length=80)
    field = models.CharField(max_length=80)
