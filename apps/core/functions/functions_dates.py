"""Module d'itilisation des dates."""

import calendar
import datetime
from typing import Any

from django.utils import timezone

MONTHS = [
    "",
    "janvier",
    "février",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "août",
    "septembre",
    "octobre",
    "novembre",
    "décembre",
]
TRUNC_MONTHS = [
    "",
    "janv.",
    "févr.",
    "mars",
    "avr.",
    "mai",
    "juin",
    "juil.",
    "août",
    "sept.",
    "oct.",
    "nov.",
    "déc.",
]
WEEK_DAYS_FR = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
WEEK_DAYS_SHORT_FR = ["lun.", "mar.", "mer.", "jeu.", "ven.", "sam.", "dim."]


def get_date_apostrophe(dte: Any):
    """Renvoi "de" où "d'" en fonction du mois reçu."""
    if isinstance(dte, (str,)):
        if not dte:
            return "de "

        return "d'" if str(dte).lower()[0] in {"a", "o"} else "de "

    return "d'" if dte.month in {4, 8, 10} else "de "


def last_day_month(dte):
    """Fonction qui retourne le dernier jour du mois.

    :param dte: 17/01/2017
    :return: '2017-01-01' au format datetime.date(2017, 1, 31).
    """
    return datetime.date(dte.year, dte.month, days_of_month(dte))


def date_string_series(dte=None):
    """Fonction qui renvoie une date sous forme de string.

    :param dte: de type date
    :return: de type string ex.: 2017_02_01.
    """
    if dte is None:
        dte = timezone.localdate()

    y = str(dte.year)
    if len(y) == 2:
        y = "20" + y

    m = str(dte.month)
    if len(m) == 1:
        m = "0" + m

    d = str(dte.day)
    if len(d) == 1:
        d = "0" + d

    return f"{y}_{m}_{d}"


def time_string_series():
    """Fonction qui renvoie le nombre de secondes entre maintenant et le 01/01/2000 - 00:00 UTC.

        exemple résultat -> 1497797172
    :return: de type string.
    """
    past = datetime.datetime(2000, 1, 1, tzinfo=datetime.UTC)
    now = timezone.now()
    delta = now - past

    return str(abs(delta.days * 24 * 3600 + delta.seconds))


def long_date_string(dte):
    """Fonction qui renvoie le nom du mois (avec accents), avec l'année.

    :param dte: 17/01/2017
    :return: Janvier 2017.
    """
    return f"{MONTHS[dte.month].capitalize()} {dte.year}"


def days_of_month(dte):
    """Fonction qui retourne le nombre de jours dans le mois.

    :param dte: 17/01/2017
    :return: 31.
    """
    return calendar.monthrange(dte.year, dte.month)[1]


# Générateur de jours ouvrés français en python
# Fin du générateur des jours fériés en français
DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%d.%m.%Y", "%d-%m-%Y", "%Y%m%d", "%d/%m/%y")


def validate_date(value: str):
    """Fonction de validation et renvoie de la date au format datetime, en essayant les formats.

    de DATE_FORMATS dans l'ordre
    :param value: valeur à transformer
    :return: datetime.datetime.
    """
    value = str(value).strip()

    for date_format in DATE_FORMATS:
        try:
            return datetime.datetime.strptime(value, date_format)  # noqa: DTZ007 (date sans heure)
        except ValueError:
            continue

    raise ValueError(
        f"Erreur de date : core.functions.functions_dates.validate_date, "
        f"value passée à la fonction : {value!r}"
    )
