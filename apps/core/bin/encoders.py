"""Encodeur JSON personnalisé et utilitaires base64."""

import base64
import datetime
import decimal
import json
import uuid

from django.db.models.fields.files import ImageFieldFile
from django.utils.duration import duration_iso_string
from django.utils.functional import Promise
from django.utils.timezone import is_aware


def _datetime_to_json(value: datetime.datetime) -> str:
    """Datetime au format ECMA-262 : millisecondes et suffixe Z pour UTC."""
    text = value.isoformat()
    if value.microsecond:
        text = text[:23] + text[26:]
    if text.endswith("+00:00"):
        text = text[:-6] + "Z"
    return text


def _time_to_json(value: datetime.time) -> str:
    """Heure naïve au format ECMA-262 (millisecondes) ; les heures conscientes sont refusées."""
    if is_aware(value):
        raise ValueError("JSON can't represent timezone-aware times.")
    text = value.isoformat()
    if value.microsecond:
        text = text[:12]
    return text


class PersonalizedDjangoJSONEncoder(json.JSONEncoder):
    """JSONEncoder subclass that knows how to encode date/time, decimal types, and.

    UUIDs.
    """

    def default(self, o):
        # See "Date Time String Format" in the ECMA-262 specification.
        """Sérialise les dates, heures, décimaux, UUID et promesses au format ECMA-262."""
        if isinstance(o, datetime.datetime):
            return _datetime_to_json(o)
        if isinstance(o, datetime.date):
            return o.isoformat()
        if isinstance(o, datetime.time):
            return _time_to_json(o)
        if isinstance(o, datetime.timedelta):
            return duration_iso_string(o)
        if isinstance(o, (decimal.Decimal, uuid.UUID, Promise, ImageFieldFile)):
            return str(o)
        return super().default(o)


def set_base_64_list(values_list: list) -> str:
    """Set en base64 une liste sous forme de chaine à spliter lors du décodage.

    :param values_list: liste de valeur
    :return: chaîne encodée en base64.
    """
    value = "||".join(values_list)
    return base64.b64encode(value.encode(encoding="utf8")).decode(encoding="utf8")


def set_base_64_str(value: str) -> str:
    """Set en base64 une liste sous forme de chaine à spliter lors du décodage.

    :param value: string déjà formaté avec || en séparateur
    :return: chaîne encodée en base64.
    """
    b_value = b"" if value is None else value.encode(encoding="utf8")
    return base64.b64encode(b_value).decode(encoding="utf8")


def get_base_64(value_base64: str | None) -> list:
    """Décode de base64 une chaine à spliter lors du décodage en liste.

    :param value_base64: chaîne en base64 à décoder puis spliter
    :return: list des éléments décodés.
    """
    b_value = b"" if value_base64 is None else value_base64.encode(encoding="utf8")
    value = base64.b64decode(b_value + b"=" * (-len(b_value) % 4)).decode(encoding="utf8")
    return value.split("||")
