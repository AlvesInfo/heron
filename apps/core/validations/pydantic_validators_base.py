"""FR : Module de class de validation.

EN : Sage X3 import validation forms module.

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

# VALIDATEUR GENERIQUE REPRENANT ===================================================================
# TruncateStrFieldsBase
# NullZeroDecimalFieldBase
# DecimalFieldBase
# ==================================================================================================


# Formats de dates acceptés en entrée par les validateurs, essayés dans cet ordre
DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%d.%m.%Y", "%Y.%m.%d", "%d-%m-%Y", "%Y%m%d", "%d/%m/%y")


def _truncated(value, max_length: int):
    """Texte tronqué à max_length, sans la partie après « ~~ » ; None si la valeur est vide."""
    if not value:
        return None

    return str(value).split("~~", maxsplit=1)[0].strip()[:max_length]


class ValidateFieldsBase(BaseModel):
    """Validation de base des champs.

    Pré tronque le texte à la valeur du max_length
    pré valide les Decimal python, pour avoir zéro, par defaut
    pré valide les Decimal python
    pré valide les dates python.
    """

    @validator("*", pre=True, always=True)
    def truncate(cls, value, field):
        """Tronque les chaînes à la longueur maximale du champ."""
        if hasattr(field.type_, "max_length"):
            value = _truncated(value, field.type_.max_length)

        return value

    @validator("*", pre=True, always=True)
    def fiels_decimal(cls, value, field):
        """Convertit les champs décimaux, zéro si vide."""
        if str(field.type_) == "<class 'decimal.Decimal'>":
            return get_decimal(get_zero_decimal(value))

        return value

    """
    @validator('acuitis_order_date', pre=True)
    def check_acuitis_order_date(cls, value):

        if not value or value == "None":
            return datetime.datetime(1900, 1, 1)

        return value

    @validator('delivery_date', pre=True)
    def check_delivery_date(cls, value):

        if not value or value == "None":
            return datetime.datetime(1900, 1, 1)

        return value
    """

    @validator("*", pre=True, always=True)
    def input_format_date(cls, value, field):
        """Convertit un texte en datetime pour les champs date, au premier format qui convient.

        La valeur est rendue telle quelle si aucun format ne correspond.
        """
        if not hasattr(field.type_, "day") or not isinstance(value, (str,)):
            return value

        value = str(value).strip()

        for date_format in DATE_FORMATS:
            try:
                return datetime.datetime.strptime(value, date_format)  # noqa: DTZ007 (date sans heure)
            except ValueError:
                continue

        return value


# GESTION DE TEXTE =================================================================================


class TruncateStrFieldsBase(BaseModel):
    """Validation qui pré tronque le texte à la valeur du max_length."""

    @validator("*", pre=True, always=True)
    def truncate_str(cls, value, field):
        """Tronque les chaînes à la longueur maximale du champ."""
        if hasattr(field.type_, "max_length"):
            value = _truncated(value, field.type_.max_length)

        return value


class SageTruncateStrFieldsBase(BaseModel):
    """Validation qui pré supprime les imports Sage avec des tildes "~".

    et tronque le texte à la valeur du max_length.
    """

    @validator("*", pre=True, always=True)
    def sage_truncate_str(cls, value, field):
        """Tronque les chaînes Sage à la longueur maximale du champ."""
        if hasattr(field.type_, "max_length"):
            value = _truncated(value, field.type_.max_length)

        return value


# GESTION DE BOOLEEN ===============================================================================


class SageNullBooleanFieldsBase(BaseModel):
    """Validation qui pré valide les booléens Sage et qui peuvent être null=True Dajngo."""

    @validator("*", pre=True, always=True)
    def sage_null_boolean(cls, value, field):
        """Convertit les booléens Sage, None si la valeur est indéterminée."""
        if str(field.type_) == "<class 'bool'>":
            str_value = str(value).lower()

            if str_value in {"2.0", "2", "on", "t", "true", "y", "o", "yes", "oui", "vrai"}:
                return True

            if str_value in {"1.0", "1", "off", "f", "false", "n", "no", "", "non", "faux"}:
                return False

            return None

        return value


class SageNullFalseBooleanFieldsBase(BaseModel):
    """Validation qui pré valide les booléens Sage et qui peuvent être null=True Dajngo."""

    @validator("*", pre=True, always=True)
    def sage_null_false_boolean(cls, value, field):
        """Convertit les booléens Sage, False si la valeur est indéterminée."""
        if str(field.type_) == "<class 'bool'>":
            str_value = str(value).lower()

            return str_value in {"2.0", "2", "on", "t", "true", "y", "o", "yes", "oui", "vrai"}

        return value


# GESTION DE CHIFFRE ===============================================================================


class DecimalFieldBase(BaseModel):
    """Validation qui pré valide les Decimal python."""

    @validator("*", pre=True, always=True)
    def fiels_decimal_base(cls, value, field):
        """Convertit les champs décimaux sans valeur par défaut."""
        if str(field.type_) == "<class 'decimal.Decimal'>":
            return get_decimal(value)

        return value


class NullZeroDecimalFieldBase(BaseModel):
    """Validation qui pré valide les Decimal python, pour avoir zéro, par defaut."""

    @validator("*", pre=True, always=True)
    def null_zero_decimal(cls, value, field):
        """Convertit les champs décimaux, zéro si vide."""
        if str(field.type_) == "<class 'decimal.Decimal'>":
            return get_zero_decimal(value)

        return value


# GESTION DE DATE ==================================================================================


class SageDateFieldsBase(BaseModel):
    """Validation qui pré valide les DateField Django, et qui arrive au format sage ddmmyy."""

    @validator("*", pre=True, always=True)
    def sage_date(cls, value, field):
        """Convertit les dates Sage, None si vide."""
        if hasattr(field.type_, "day") and isinstance(value, (str,)):
            value = str(value).strip()

            if not value:
                return None

            value = datetime.datetime.strptime(value, "%d%m%y")  # noqa: DTZ007 (date sans heure)

        return value


class ExcelDateFieldsBase(BaseModel):
    """Validation qui pré valide les DateField Django, et qui arrive au format sage ddmmyyyy."""

    @validator("*", pre=True, always=True)
    def sage_date(cls, value, field):
        """Convertit les dates Excel, None si vide."""
        if hasattr(field.type_, "day") and isinstance(value, (str,)):
            value = str(value).strip()

            if not value:
                return None

            value = datetime.datetime.strptime(value, "%d/%m/%Y")  # noqa: DTZ007 (date sans heure)

        return value


class SageDefaultDateFieldsBase(BaseModel):
    """Validation qui pré valide les DateField Django, et qui arrive au format sage ddmmyy."""

    @validator("*", pre=True, always=True)
    def sage_date(cls, value, field):
        """Convertit les dates Sage, 1900-01-01 si vide."""
        if hasattr(field.type_, "day") and isinstance(value, (str,)):
            value = str(value).strip()

            if not value or value == "None":
                return datetime.datetime.strptime("1900-01-01", "%Y-%m-%d")  # noqa: DTZ007 (date sans heure)

            value = datetime.datetime.strptime(value, "%d%m%y")  # noqa: DTZ007 (date sans heure)

        return value


# GESTION DE TVA ===================================================================================


class TvaEyeConfor(BaseModel):
    """Validation du taux de tva pour EyeConfort."""

    @validator("vat_rate", pre=True, check_fields=False)
    def tva_eye_confort(cls, value):
        """Convertit le taux de TVA Eye Confort exprimé en pourcentage."""
        if "%" in value:
            value = Decimal(f"{value.replace('%', '.')}") / Decimal(100)

        return value


class TvaGenerique(BaseModel):
    """Validation du taux de tva pour GENERIQUE."""

    @validator("vat_rate", pre=True, check_fields=False)
    def tva_generique(cls, value):
        """Convertit les codes de TVA génériques en taux."""
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
            value = Decimal(value) / Decimal(10000)

        if not value:
            value = Decimal(0)

        return value


class TvaInterson(BaseModel):
    """Validation du taux de tva pour INTERSON."""

    @validator("vat_rate", pre=True, check_fields=False)
    def tva_interson(cls, value):
        """Convertit les codes de TVA Interson en taux."""
        if value in {"", None, False}:
            value = Decimal(0)

        elif value in {"1.0", "1", 1}:
            value = Decimal("0.2")

        elif value in {"2.0", "2", 2}:
            value = Decimal(".055")

        return value


class TvaWidex(BaseModel):
    """Validation du taux de tva pour Widex."""

    @validator("vat_rate", pre=True, check_fields=False)
    def tva_widex(cls, value):
        # les zéros en tête sont retirés : "06" -> "6", "020.0" -> "20.0", "0" -> ""
        """Convertit les codes de TVA Widex en taux."""
        value = str(value).replace(",", ".").lstrip("0")

        if value in {"6.0", "6", "5.5", "5.50", "20.0", "20", "20.00"}:
            value = Decimal("0.2") if Decimal(value) == Decimal(20) else Decimal(".055")

        if not value:
            value = Decimal(0)

        return value


class TvaNewson(BaseModel):
    """Validation du taux de tva pour Nexson."""

    @validator("vat_rate", pre=True, check_fields=False)
    def tva_newson(cls, value):
        """Convertit les codes de TVA Newson en taux."""
        if value in {"C0", "C1", "C2", "E7"}:
            value = Decimal(0)

        elif value == "C3":
            value = Decimal(".055")

        elif value == "C4":
            value = Decimal(".2")

        return value
