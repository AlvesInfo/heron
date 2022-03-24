# pylint: disable=E0401,R0903
"""
FR : Module de validation par djantic
EN : Sage X3 import validation forms module

Commentaire:

created at: 2021-11-07
created by: Paulo ALVES

modified at: 2021-11-07
modified by: Paulo ALVES
"""
import datetime
from django.utils import timezone
from djantic import ModelSchema
from apps.core.functions.functions_setups import settings
from apps.accountancy.models import AccountSage


class AccountSageSchema(ModelSchema):
    created_at: datetime.datetime = datetime.datetime.now()
    modified_at: datetime.datetime = datetime.datetime.now()

    class Config:
        model = AccountSage
        include = [key for key in AccountSage.get_columns_import().keys()] + [
            "created_at",
            "modified_at",
        ]


def main():
    t = AccountSageSchema(
        **{
            "code_plan_sage": 0,
            "account": 1,
            "name": 2,
        }
    )
    print(t.dict())


if __name__ == "__main__":
    main()
