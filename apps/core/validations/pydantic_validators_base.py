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
from decimal import Decimal

from pydantic import BaseModel, validator

from apps.core.functions.functions_utilitaires import get_decimal, get_zero_decimal

# print(field.name, field.type_, type(field), dir(field.type_))


# GESTION DE TEXTE =================================================================================


class TruncateStrFieldsBase(BaseModel):
    """Validation qui pré tronque le texte à la valeur du max_length"""

    @validator("*", pre=True, always=True)
    def truncate_str(cls, value, field):

        if hasattr(field.type_, "max_length"):
            value = (
                None
                if not value
                else str("" if value is None else str(value).split("~~", maxsplit=1)[0]).strip()[
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
                else str("" if value is None else str(value).split("~~", maxsplit=1)[0]).strip()[
                    : field.type_.max_length
                ]
            )

        return value


# GESTION DE BOOLEEN ===============================================================================


class FrenchBooleanFieldsBase(BaseModel):
    """Validation qui pré valide les booléens Français"""

    @validator("*", pre=True, always=True)
    def french_boolean(cls, value, field):

        if str(field.type_) == "<class 'bool'>":
            str_value = str(value).lower()

            if str_value in {"1.0", "1", "on", "t", "true", "y", "o", "yes", "oui", "vrai"}:
                return True

            if str_value in {"0.0", "0", "off", "f", "false", "n", "no", "", "non", "faux"}:
                return False

        return value


class FrenchNullBooleanFieldsBase(BaseModel):
    """Validation qui pré valide les booléens Français et qui peuvent être null=True Dajngo"""

    @validator("*", pre=True, always=True)
    def french_null_boolean(cls, value, field):

        if str(field.type_) == "<class 'bool'>":
            str_value = str(value).lower()

            if str_value in {"1.0", "1", "on", "t", "true", "y", "o", "yes", "oui", "vrai"}:
                return True

            if str_value in {"0.0", "0", "off", "f", "false", "n", "no", "non", "faux"}:
                return False

            return None

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
    def sage_null_false_boolean(cls, value, field):

        if str(field.type_) == "<class 'bool'>":
            str_value = str(value).lower()

            if str_value in {"2.0", "2", "on", "t", "true", "y", "o", "yes", "oui", "vrai"}:
                return True

            return False

        return value


# GESTION DE CHIFFRE ===============================================================================


class DecimalFieldBase(BaseModel):
    """Validation qui pré valide les Decimal python"""

    @validator("*", pre=True, always=True)
    def fiels_decimal_base(cls, value, field):
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


# GESTION DE DATE ==================================================================================


class SageDateFieldsBase(BaseModel):
    """Validation qui pré valide les DateField Django, et qui arrive au format sage ddmmyy"""

    @validator("*", pre=True, always=True)
    def sage_date(cls, value, field):

        if hasattr(field.type_, "day") and isinstance(value, (str,)):
            if not value:
                return None

            value = datetime.datetime.strptime(value, "%d%m%y")

        return value


class GenericDateFieldsBase(BaseModel):
    """Validation qui pré valide les DateField Django, et qui arrive au format import Générique"""

    @validator("*", pre=True, always=True)
    def generic_date(cls, value, field):

        if hasattr(field.type_, "day") and isinstance(value, (str,)):
            if not value:
                return None

            value = datetime.datetime.strptime(value, "%Y%m%d")

        return value


class DdMmYyyyyDateFieldsBase(BaseModel):
    """Validation qui pré valide les DateField Django, et qui arrive au format import Générique"""

    @validator("*", pre=True, always=True)
    def yyyy_date(cls, value, field):

        if hasattr(field.type_, "day") and isinstance(value, (str,)):
            if not value:
                return None

            value = datetime.datetime.strptime(value, "%d/%m/%Y")

        return value


class IsoDateFieldsBase(BaseModel):
    """Validation qui pré valide les DateField Django, et qui arrive au format import Générique"""

    @validator("*", pre=True, always=True)
    def iso_date(cls, value, field):

        if hasattr(field.type_, "day") and isinstance(value, (str,)):
            if not value:
                return None

            value = datetime.datetime.strptime(value, "%Y-%m-%d")

        return value


class IsoInverseDateFieldsBase(BaseModel):
    """Validation qui pré valide les DateField Django, et qui arrive au format import Générique"""

    @validator("*", pre=True, always=True)
    def iso_inv_date(cls, value, field):

        if hasattr(field.type_, "day") and isinstance(value, (str,)):
            if not value:
                return None

            value = datetime.datetime.strptime(value, "%d-%m-%Y")

        return value


class PointDateFieldsBase(BaseModel):
    """Validation qui pré valide les DateField Django, et qui arrive au format import Générique"""

    @validator("*", pre=True, always=True)
    def point_date(cls, value, field):

        if hasattr(field.type_, "day") and isinstance(value, (str,)):
            if not value:
                return None

            value = datetime.datetime.strptime(value, "%d.%m.%Y")

        return value


# GESTION DE TVA ===================================================================================


class TvaEyeConfor(BaseModel):
    """Validation du taux de tva pour EyeConfort"""

    @validator("vat_rate", pre=True, check_fields=False)
    def tva_eye_confort(cls, value):

        if "%" in value:
            value = Decimal(f"{value.replace('%', '.')}") / Decimal("100")

        return value


class TvaGenerique(BaseModel):
    """Validation du taux de tva pour GENERIQUE"""

    @validator("vat_rate", pre=True, check_fields=False)
    def tva_generique(cls, value):

        if value in {
            "0",
            "0000",
            "0.0",
            "0000.0",
            "550",
            "0550",
            "550.0",
            "0550.0",
            "2000",
            "2000.0",
        }:
            value = Decimal(value) / Decimal("10000")

        return value


class TvaInterson(BaseModel):
    """Validation du taux de tva pour INTERSON"""

    @validator("vat_rate", pre=True, check_fields=False)
    def tva_interson(cls, value):

        if value in {"1.0", "1", 1, "2.0", "2", 2, "", None, False}:
            if not value:
                value = Decimal("0")

            elif value in {"1.0", "1", 1}:
                value = Decimal("0.2")

            elif value in {"2.0", "2", 2}:
                value = Decimal(".055")

        return value


class TvaWidex(BaseModel):
    """Validation du taux de tva pour Widex"""

    @validator("vat_rate", pre=True, check_fields=False)
    def tva_widex(cls, value):
        value = str(value).replace(",", ".")
        if value in {
            "0.0",
            "00.0",
            "00",
            "6.0",
            "06.0",
            "06",
            "5.5",
            "05.5",
            "20.0",
            "020.0",
            "20",
            "20.00",
            "05.50",
            "5.50",
        }:
            if Decimal(value) == Decimal("0"):
                value = Decimal("0")

            elif Decimal(value) == Decimal("20"):
                value = Decimal("0.2")

            elif Decimal(value) == Decimal("6") or Decimal(value) == Decimal("5.5"):
                value = Decimal(".055")

        return value


class TvaNewson(BaseModel):
    """Validation du taux de tva pour Nexson"""

    @validator("vat_rate", pre=True, check_fields=False)
    def tva_newson(cls, value):

        if value == "C3":
            value = Decimal(".055")

        elif value == "C4":
            value = Decimal(".2")

        return value
