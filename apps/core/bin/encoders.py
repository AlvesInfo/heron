import datetime
import decimal
import json
import uuid
import base64

from django.db.models.fields.files import ImageFieldFile
from django.utils.duration import duration_iso_string
from django.utils.functional import Promise
from django.utils.timezone import is_aware


class PersonalizedDjangoJSONEncoder(json.JSONEncoder):
    """
    JSONEncoder subclass that knows how to encode date/time, decimal types, and
    UUIDs.
    """

    def default(self, o):
        # See "Date Time String Format" in the ECMA-262 specification.
        if isinstance(o, datetime.datetime):
            r = o.isoformat()
            if o.microsecond:
                r = r[:23] + r[26:]
            if r.endswith("+00:00"):
                r = r[:-6] + "Z"
            return r
        elif isinstance(o, datetime.date):
            return o.isoformat()
        elif isinstance(o, datetime.time):
            if is_aware(o):
                raise ValueError("JSON can't represent timezone-aware times.")
            r = o.isoformat()
            if o.microsecond:
                r = r[:12]
            return r
        elif isinstance(o, datetime.timedelta):
            return duration_iso_string(o)
        elif isinstance(o, (decimal.Decimal, uuid.UUID, Promise, ImageFieldFile)):
            return str(o)
        else:
            return super().default(o)


def set_base_64_list(values_list: list) -> base64:
    """
    Set en base64 une liste sous forme de chaine à spliter lors du décodage
    :param values_list: liste de valeur
    :return: base64
    """
    value = "||".join(values_list)
    return base64.b64encode(value.encode(encoding="utf8")).decode(encoding="utf8")


def set_base_64_str(value: str) -> base64:
    """
    Set en base64 une liste sous forme de chaine à spliter lors du décodage
    :param value: string déjà formaté avec || en séparateur
    :return: base64
    """
    return base64.b64encode(value.encode(encoding="utf8")).decode(encoding="utf8")


def get_base_64(value_base64: base64) -> list:
    """
    Décode de base64 une chaine à spliter lors du décodage en liste
    :param value_base64: valeur en base64 à spliter
    :return: list des éléments décodés
    """
    b_value = value_base64.encode(encoding="utf8")
    value = base64.b64decode(b_value + b'=' * (-len(b_value) % 4)).decode(encoding="utf8")
    return value.split("||")
