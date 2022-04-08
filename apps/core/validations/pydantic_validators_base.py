# pylint: disable=E0213,E0401,C0116,R0201,R0903
"""
FR : Module de class de validation
EN : Sage X3 import validation forms module

Commentaire:

created at: 2021-11-07
created by: Paulo ALVES

modified at: 2021-11-07
modified by: Paulo ALVES
"""
import datetime

from pydantic import BaseModel, validator

from apps.core.functions.functions_utilitaires import get_decimal, get_zero_decimal

# print(field.name, field.type_, type(field), dir(field.type_))


class TruncateStrFieldsBase(BaseModel):
    """Validation qui pré tronque le texte à la valeur du max_length"""

    @validator("*", pre=True, always=True)
    def truncate_str(cls, value, field):

        if hasattr(field.type_, "max_length"):
            value = (
                None
                if not value
                else str("" if value is None else str(value).split("~~")[0]).strip()[
                    : field.type_.max_length
                ]
            )

        return value


class SageTruncateStrFieldsBase(BaseModel):
    """
    Validation qui pré supprime les imports Sage avec des tildes "~"
    et tronque le texte à la valeur du max_length
    """

    @validator("*", pre=True, always=True)
    def sage_truncate_str(cls, value, field):

        if hasattr(field.type_, "max_length"):
            value = (
                None
                if not value
                else str("" if value is None else str(value).split("~~")[0]).strip()[
                    : field.type_.max_length
                ]
            )

        return value


class FrenchBooleanFieldsBase(BaseModel):
    """Validation qui pré valide les booléens Français"""

    @validator("*", pre=True, always=True)
    def french_boolean(cls, value, field):

        if str(field.type_) == "<class 'bool'>":
            str_value = str(value).lower()

            if str_value in {"1", "on", "t", "true", "y", "o", "yes", "oui", "vrai"}:
                return True

            if str_value in {"0", "off", "f", "false", "n", "no", "", "non", "faux"}:
                return False

        return value


class FrenchNullBooleanFieldsBase(BaseModel):
    """Validation qui pré valide les booléens Français et qui peuvent être null=True Dajngo"""

    @validator("*", pre=True, always=True)
    def french_null_boolean(cls, value, field):

        if str(field.type_) == "<class 'bool'>":
            str_value = str(value).lower()

            if str_value in {"1", "on", "t", "true", "y", "o", "yes", "oui", "vrai"}:
                return True

            if str_value in {"0", "off", "f", "false", "n", "no", "non", "faux"}:
                return False

            return None

        return value


class DecimalFieldBase(BaseModel):
    """Validation qui pré valide les Decimal python"""

    @validator("*", pre=True, always=True)
    def null_zero_decimal(cls, value, field):

        if str(field.type_) == "<class 'decimal.Decimal'>":
            return get_decimal(value)

        return value


class NullZeroDecimalFieldBase(BaseModel):
    """Validation qui pré valide les Decimal python, pour avoir zéro, par defaut"""

    @validator("*", pre=True, always=True)
    def null_zero_decimal(cls, value, field):

        if str(field.type_) == "<class 'decimal.Decimal'>":
            return get_zero_decimal(value)

        return value


class SageDateFieldsBase(BaseModel):
    """Validation qui pré valide les DateField Django, et qui arrive au format sage ddmmyy"""

    @validator("*", pre=True, always=True)
    def sage_date(cls, value, field):

        if hasattr(field.type_, "day") and isinstance(value, (str,)):
            value = datetime.datetime.strptime(value, "%d%m%y")

        return value


class SageBooleanFieldsBase(BaseModel):
    """Validation qui pré valide les booléens Sage"""

    @validator("*", pre=True, always=True)
    def sage_boolean(cls, value, field):

        if str(field.type_) == "<class 'bool'>":
            str_value = str(value).lower()

            if str_value in {"2.0", "2", "on", "t", "true", "y", "o", "yes", "oui", "vrai"}:
                return True

            if str_value in {"1.0", "1", "off", "f", "false", "n", "no", "", "non", "faux"}:
                return False

        return value


class SageNullBooleanFieldsBase(BaseModel):
    """Validation qui pré valide les booléens Sage et qui peuvent être null=True Dajngo"""

    @validator("*", pre=True, always=True)
    def sage_null_boolean(cls, value, field):

        if str(field.type_) == "<class 'bool'>":
            str_value = str(value).lower()

            if str_value in {"2.0", "2", "on", "t", "true", "y", "o", "yes", "oui", "vrai"}:
                return True

            if str_value in {"1.0", "1", "off", "f", "false", "n", "no", "", "non", "faux"}:
                return False

            return None

        return value


class SageNullFalseBooleanFieldsBase(BaseModel):
    """Validation qui pré valide les booléens Sage et qui peuvent être null=True Dajngo"""

    @validator("*", pre=True, always=True)
    def sage_null_boolean(cls, value, field):

        if str(field.type_) == "<class 'bool'>":
            str_value = str(value).lower()

            if str_value in {"2.0", "2", "on", "t", "true", "y", "o", "yes", "oui", "vrai"}:
                return True

            return False

        return value
