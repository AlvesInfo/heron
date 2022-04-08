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
import io
import uuid
import time

import pydantic
from pydantic import BaseModel, ValidationError
from django.utils import timezone
from djantic import ModelSchema
import djantic
from apps.core.functions.functions_setups import settings
from apps.core.validations.pydantic_validators_base import (
    NullZeroDecimalFieldBase,
    SageTruncateStrFieldsBase,
    SageDateFieldsBase,
    SageNullFalseBooleanFieldsBase,
    SageNullBooleanFieldsBase,
)
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


class AccountSageSchema(ModelSchema, SageTruncateStrFieldsBase, SageNullFalseBooleanFieldsBase):
    """Schema Djantic pour validation du modèle AccountSage"""

    now = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now
    uuid_identification: uuid.UUID = uuid.uuid4()

    class Config:
        model = AccountSage
        include = list(model.get_columns_import()) + [
            "created_at",
            "modified_at",
            "uuid_identification",
        ]


class AxeSageSchema(ModelSchema, SageTruncateStrFieldsBase):
    now = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now

    class Config:
        model = AxeSage
        include = list(model.get_columns_import())


class SectionSageSchema(ModelSchema, SageTruncateStrFieldsBase, SageNullBooleanFieldsBase):
    now = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now
    axe: str
    chargeable: bool = None
    uuid_identification: uuid.UUID = uuid.uuid4()

    class Config:
        model = SectionSage
        include = list(model.get_columns_import())


class VatRegimeSagechema(ModelSchema, SageTruncateStrFieldsBase):
    now = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now

    class Config:
        model = VatRegimeSage
        include = list(model.get_columns_import())


class VatSagechema(ModelSchema, SageTruncateStrFieldsBase):
    now = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now

    class Config:
        model = VatSage
        include = list(model.get_columns_import())


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
        include = list(model.get_columns_import())


class PaymentConditionSchema(ModelSchema, SageTruncateStrFieldsBase):
    now = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now

    class Config:
        model = PaymentCondition
        include = list(model.get_columns_import())


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
        include = list(model.get_columns_import())


class CategorySageSchema(ModelSchema, SageTruncateStrFieldsBase):
    now = timezone.now()
    created_at: datetime.datetime = now
    modified_at: datetime.datetime = now

    class Config:
        model = CategorySage
        include = list(model.get_columns_import())


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
        include = list(model.get_columns_import())


def main():

    # data_dict = {
    #     "code_plan_sage": "zzzzzzzzzzzzzzzzzzzzzzzzz",
    #     "account": "    zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz             ",
    #     "name": "zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz",
    #     "short_name": "zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz",
    # }
    # start = time.time()
    # t = None
    # for i in range(1):
    #     try:
    #         t = AccountSageSchema(**data_dict)
    #         # AccountSage.objects.update_or_create(**t.dict())
    #     except ValidationError as except_error:
    #         print(i + 1, except_error.errors())
    #         # raise Exception from errors
    #     else:...
    #         # print(i + 1, t.dict())
    # print(f"validation par djantic en {time.time() - start} s")
    # import djantic
    #
    # if isinstance(AccountSageSchema, (djantic.main.ModelSchemaMetaclass, )):
    #     print(type(AccountSageSchema))
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
    #     except ValidationError as except_error:
    #         print(i + 1, except_error.errors())
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

    for i in range(10_000):
        try:
            t = TabDivSageSchema(**data_dict)
        except ValidationError as except_error:
            print(i + 1, except_error.errors())
            # raise Exception from errors
        else:
            ...
            print(i + 1, t.dict())

    print(f"validation par djantic en {time.time() - start} s")


class SectionSagePydanticSchema(BaseModel):
    axe: str
    section: str
    name: str
    short_name: str
    chargeable: str


class SectionSageDjanticSchema(ModelSchema):
    test: str

    class Config:
        model = SectionSage
        include = list(model.get_columns_import())


def essai_SectionSagechema():

    errors_dict = {}

    data_dict = {
        "axe": "001",
        "section": "NAF",
        "name": "Prèmière section",
        "short_name": "first section",
        "chargeable": "zzzzzzzzzzzz",
    }
    start = time.time()

    for i in range(1):
        try:
            t = ""
            print(
                " isinstance : ",
                isinstance(SectionSagePydanticSchema, (type(BaseModel), type(ModelSchema))),
            )
            print(
                " isinstance : ",
                isinstance(SectionSageDjanticSchema, (type(BaseModel), type(ModelSchema))),
            )
            SectionSageDjanticSchema(**data_dict)
        except ValidationError as except_error:

            errors_dict[i] = except_error.errors()
            print(i + 1, except_error.errors())
            print(str(except_error.args[1].dict))
            error_dict = {
                ", ".join(dict_row.get("loc")): [
                    {
                        "message": dict_row.get("msg"),
                        "data_received": "aucune valeur reçue"
                        if not data_dict.get(", ".join(dict_row.get("loc")))
                        else data_dict.get(", ".join(dict_row.get("loc"))),
                    }
                ]
                for dict_row in except_error.errors()
            }
            print(error_dict)
            # raise Exception from except_error
        else:
            ...

    # print(errors_dict)
    print(f"validation par djantic en {time.time() - start} s")
    print(TabDivSage.get_columns_import())


from pathlib import Path
from uuid import uuid4
from datetime import datetime

from django.db import connection
from apps.core.functions.functions_setups import settings
from apps.data_flux.models import Trace
from apps.data_flux.loader import (
    GetAddDictError,
    IterFileToInsertError,
    ExcelToCsvError,
    FileToCsvError,
    FileLoader,
)
from apps.data_flux.validation import Validation, PydanticValidation, PydanticTrace
from apps.data_flux.postgres_save import PostgresKeyError, PostgresTypeError, PostgresDjangoUpsert


if __name__ == "__main__":
    # main()
    # essai_SectionSagechema()
    source = Path(r"C:\Users\33680\Downloads\ZBIACCOUNT_journalier.heron")
    now = datetime.now().isoformat()
    uuid_identification = uuid4()
    trace = Trace.objects.create(
        created_at=timezone.now(),
        uuid_identification=uuid4(),
        trace_name="Mise à jour Comptes Sage",
        file_name=source.name,
        application_name="Import Sage",
        flow_name="AccountSage",
        comment="import journalier des comptes comptables Sage",
        created_numbers_records=0,
        updated_numbers_records=0,
        errors_numbers_records=0,
        unknown_numbers_records=0,
    )
    params_dict_loader = {
        "add_fields_dict": {
            "created_at": now,
            "modified_at": now,
            "uuid_identification": (uuid4, {}),
        }
    }
    file_io = io.StringIO()
    params_dict_validation = {
        "trace": trace,
        "insert_method": "upsert",
        "validation": (PydanticValidation, PydanticTrace),
        "file_io": file_io,
    }
    fields_dict = {
        key: True if key in AccountSage.get_uniques() else False
        for key in {**AccountSage.get_columns_import(), **params_dict_loader.get("add_fields_dict")}
    }
    try:
        with FileLoader(
            source=source,
            columns_dict=AccountSage.get_columns_import(),
            params_dict=params_dict_loader,
        ) as file_load:

            validation = Validation(
                dict_flow=file_load.read_dict(),
                model=AccountSage,
                validator=AccountSageSchema,
                params_dict=params_dict_validation,
            )
            error_lines = validation.validate()

            postgres_upsert = PostgresDjangoUpsert(
                model=AccountSage,
                fields_dict=fields_dict,
                cnx=connection,
                exclude_update_fields={"created_at", "modified_at", "uuid_identification"}
            )
            file_io.seek(0)

            postgres_upsert.insertion(
                file=file_io,
                insert_mode="upsert",
                delimiter=";",
                quote_character='"',
            )

    # Exceptions FileLoader ========================================================================
    except GetAddDictError as except_error:
        print("GetAddDictError : ", except_error)

    except IterFileToInsertError as except_error:
        print("IterFileToInsertError : ", except_error)

    except ExcelToCsvError as except_error:
        print("ExcelToCsvError : ", except_error)

    except FileToCsvError as except_error:
        print("FileToCsvError : ", except_error)

    # Exceptions PostgresDjangoUpsert ==============================================================
    except PostgresKeyError as except_error:
        print("PostgresKeyError : ", except_error)

    # except PostgresTypeError as except_error:
    #     print("PostgresTypeError : ", except_error)

    finally:
        trace.time_to_process = (timezone.now() - trace.created_at).total_seconds()
        trace.save()
        print(trace.time_to_process)
