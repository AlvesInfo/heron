# pylint: disable=E0401,R0903
"""
FR : Module de validation par djantic
EN : Sage X3 import validation forms module

Commentaire:

created at: 2022-02-17
created by: Paulo ALVES

modified at: 2022-02-17
modified by: Paulo ALVES
"""
import datetime
import uuid

from pydantic import ValidationError
from apps.core.validation.pydantic_validators_base import (
    NullZeroDecimalFieldBase,
    SageTruncateStrFieldsBase,
    SageDateFieldsBase,
    SageNullBooleanFieldsBase,
)
from django.utils import timezone
from djantic import ModelSchema
from apps.core.functions.functions_setups import settings
from apps.accountancy.models import (
    AccountSage,
    AxeSage,
    SectionSage,
    VatRegimeSage,
    VatSage,
    VatRatSage,
    PaymentCondition,
    TabDivSage,
    CategorySage,
    CurrencySage,
)


class AccountSageSchema(ModelSchema, SageTruncateStrFieldsBase, SageNullBooleanFieldsBase):
    now = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now
    uuid_identification: uuid.UUID = uuid.uuid4()

    class Config:
        model = AccountSage
        include = [key for key in model.get_columns_import().keys()] + [
            "uuid_identification",
            "created_at",
            "modified_at",
        ]


class AxeSageSchema(ModelSchema, SageTruncateStrFieldsBase):
    now = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now

    class Config:
        model = AxeSage
        include = [key for key in model.get_columns_import().keys()] + [
            "created_at",
            "modified_at",
        ]


class SectionSagechema(ModelSchema, SageTruncateStrFieldsBase, SageNullBooleanFieldsBase):
    now = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now
    axe: str
    chargeable: bool = None
    uuid_identification: uuid.UUID = uuid.uuid4()

    class Config:
        model = SectionSage
        include = [key for key in model.get_columns_import().keys()] + [
            "uuid_identification",
            "created_at",
            "modified_at",
        ]


class VatRegimeSagechema(ModelSchema, SageTruncateStrFieldsBase):
    now = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now

    class Config:
        model = VatRegimeSage
        include = [key for key in model.get_columns_import().keys()] + [
            "created_at",
            "modified_at",
        ]


class VatSagechema(ModelSchema, SageTruncateStrFieldsBase):
    now = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now

    class Config:
        model = VatSage
        include = [key for key in model.get_columns_import().keys()] + [
            "created_at",
            "modified_at",
        ]


class VatRatSageSchema(
    ModelSchema,
    SageTruncateStrFieldsBase,
    SageDateFieldsBase,
    SageNullBooleanFieldsBase,
    NullZeroDecimalFieldBase,
):
    now = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now
    vat: str
    exoneration: bool = None

    class Config:
        model = VatRatSage
        include = [key for key in model.get_columns_import().keys()] + [
            "created_at",
            "modified_at",
        ]


class PaymentConditionSchema(ModelSchema, SageTruncateStrFieldsBase):
    now = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now

    class Config:
        model = PaymentCondition
        include = [key for key in model.get_columns_import().keys()] + [
            "created_at",
            "modified_at",
        ]


class TabDivSageSchema(
    ModelSchema,
    SageTruncateStrFieldsBase,
    SageNullBooleanFieldsBase,
    NullZeroDecimalFieldBase,
):
    now = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now

    class Config:
        model = TabDivSage
        include = [key for key in model.get_columns_import().keys()] + [
            "created_at",
            "modified_at",
        ]


class CategorySageSchema(ModelSchema, SageTruncateStrFieldsBase):
    now = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now

    class Config:
        model = CategorySage
        include = [key for key in model.get_columns_import().keys()] + [
            "created_at",
            "modified_at",
        ]


class CurrencySageSchema(
    ModelSchema,
    SageTruncateStrFieldsBase,
    SageDateFieldsBase,
    SageNullBooleanFieldsBase,
    NullZeroDecimalFieldBase,
):
    now = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now
    uuid_identification: uuid.UUID = uuid.uuid4()

    class Config:
        model = CurrencySage
        include = [key for key in model.get_columns_import().keys()] + [
            "uuid_identification",
            "created_at",
            "modified_at",
        ]


def main():
    import time

    data_dict = {
        "code_plan_sage": 0,
        "account": "    zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz             ",
        "name": "zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz",
        "short_name": "zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz",
    }
    start = time.time()
    t = None
    for i in range(1):
        try:
            t = AccountSageSchema(**data_dict)
            # AccountSage.objects.update_or_create(**t.dict())
        except ValidationError as errors:
            print(i + 1, errors.errors())
            # raise Exception from errors
        else:...
            # print(i + 1, t.dict())
    print(f"validation par djantic en {time.time() - start} s")
    import djantic

    if isinstance(AccountSageSchema, (djantic.main.ModelSchemaMetaclass, )):
        print(type(AccountSageSchema))
    # start = time.time()
    # f = None
    # for i in range(1_000_000):
    #     print(i + 1)
    #     f = AccountSageForm(data=data_dict)
    #     f.is_valid()
    # print(f"validation par djantic en {time.time() - start} s")
    # print(f.cleandata, "\n")

    # data_dict = {
    #     "vat": "001",
    #     "vat_start_date": "010123",
    #     "rate": "",
    #     "exoneration": "0",
    # }
    # start = time.time()
    # t = None
    # for i in range(1):
    #     try:
    #         t = VatRatSageSchema(**data_dict)
    #     except ValidationError as errors:
    #         print(i + 1, errors.errors())
    #         # raise Exception from errors
    #     else:
    #         ...
    #         print(i + 1, t.dict())
    #
    # print(f"validation par djantic en {time.time() - start} s")
    # start = time.time()
    # f = None
    # for i in range(1_000_000):
    #     print(i + 1)
    #     f = VatRatSageForm(data=data_dict)
    #     f.is_valid()
    # print(f"validation par djantic en {time.time() - start} s")
    # print(f.cleandata, "\n")

    data_dict = {
        "num_table": 6100,
        "code": "010123",
        "rate": "",
        "exoneration": "0",
    }
    start = time.time()
    t = None
    for i in range(1):
        try:
            t = TabDivSageSchema(**data_dict)
        except ValidationError as errors:
            print(i + 1, errors.errors())
            # raise Exception from errors
        else:
            ...
            print(i + 1, t.dict())

    print(f"validation par djantic en {time.time() - start} s")


if __name__ == "__main__":
    main()
