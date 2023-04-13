import re
from decimal import Decimal

import pendulum
import lxml.html as html
from lxml.etree import ParserError

from django import template
from django.template.defaultfilters import stringfilter

from apps.core.bin.encoders import set_base_64_list, set_base_64_str
from apps.accountancy.bin.utils import get_str_echeances

register = template.Library()


@register.filter(name="point")
@stringfilter
def point(value):
    return value.replace(",", ".")


@register.filter(name="left_trunc")
@stringfilter
def left_trunc(value, num):
    return value[int(num):]


@register.filter(name="right_align")
def right_align(value, num):
    to_split = value.split("-")

    if len(to_split) == 1:
        return value.rjust(num)

    return to_split[0].rjust(num) + " - " + " - ".join(row for row in to_split[1:])


def right_align_(value, num):
    to_split = value.split("-")

    if len(to_split) == 1:
        return value.rjust(num)

    return (
        to_split[0].rjust(num).replace(" ", "&nbsp;")
        + " - "
        + " - ".join(row for row in to_split[1:])
    )


@register.filter(name="right_trunc")
@stringfilter
def right_trunc(value, num):
    return value[: int(num)]


@register.filter(name="bool_and")
def bool_and(fisrt_bool, second_bool):
    return all([fisrt_bool, second_bool])


@register.filter(name="bool_in")
def bool_in(part, value):
    return part in value


@register.filter(name="get_bool_value")
def bool_in(part, value):
    test_part = None if part == "None" else part
    return test_part or value


@register.filter(name="get_background_date_lt")
def bool_date_lt(date_value):
    return (
        ""
        if date_value is None or date_value > pendulum.today().date()
        else "background-color: lightgray;"
    )


@register.filter(name="replace_space_splash")
def space_splash(value):
    return str(value).replace(" ", "_")


@register.filter(name="is_str")
def get_is_str(value):
    return isinstance(value, (str,))


@register.filter(name="html_to_text")
def html_to_text(value):
    try:
        if value is None or value == "None":
            return ""

        return html.fromstring(value).text_content().strip()

    except (ParserError, TypeError):
        return value or ""


@register.filter(name="strip_value")
def strip_value(value):
    return str(value).strip()


@register.filter(name="get_dict_keys")
def get_dict_keys(value):
    if isinstance(value, (dict,)):
        return list(value.keys())


@register.filter(name="get_dict_values")
def get_dict_values(value):
    if isinstance(value, (dict,)):
        return list(value.values())


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter(name="date_from_str_4")
def date_from_str_4(value):
    if value:
        day, month, year = value.split("/")
        if len(year) == 2:
            year = f"20{year}"

        try:
            return pendulum.date(int(year), int(month), int(day)).isoformat()
        except (TypeError, ValueError):
            pass

    return ""


@register.filter(name="numbers")
def numbers(value, num):
    if not value:
        return "0"
    list_values = str(value).split(".")

    if len(list_values) == 0:
        nombre = "0"
        centimes = ""

    elif len(list_values) == 1:
        nombre = str(value)
        centimes = ""

    else:
        nombre, centimes, *_ = list_values

    centimes += "0" * 99
    return_value = ""

    for i, value in enumerate(nombre[::-1], 1):
        return_value += value

    if num:
        centimes_part = "." + centimes[:num]
    else:
        centimes_part = ""

    return (return_value[::-1] + centimes_part).strip()


@register.filter(name="default_if_zero")
def default_if_zero(value):
    if str(value) == "0":
        return ""

    return value


@register.filter(name="numbers_format")
def numbers_format(value, num):
    if not value:
        return "0"

    nombre, centimes, *_ = str(value).split(".")
    centimes += "0" * 99
    return_value = ""

    for i, value in enumerate(nombre[::-1], 1):
        return_value += value
        if i % 3 == 0:
            return_value += " "

    return (return_value[::-1] + ("," if num else "") + centimes[:num]).strip()


@register.filter(name="numbers_point")
def numbers_point(value, num):
    if not value or value == "0":
        return "0"

    if "." in str(value):
        nombre, centimes, *_ = str(value).split(".")
    else:
        nombre = str(value)
        centimes = ""

    centimes += "0" * 99
    return_value = ""

    for i, value in enumerate(nombre[::-1], 1):
        return_value += value
        if i % 3 == 0:
            return_value += " "

    return (return_value[::-1] + "." + centimes[:num]).strip()


@register.filter(name="rangex")
def rangex(value, num):
    return range(value, num)


@register.filter(name="int_formats")
def int_formats(value):
    # print("int_formats : ", value)
    if not value:
        return "0"

    str_value = str(value).split(".")[0]
    return_value = ""

    for i, value in enumerate(str_value[::-1], 1):
        return_value += value
        if i % 3 == 0:
            return_value += " "

    return str(return_value[::-1]).strip()


@register.filter(name="format")
def int_formats(value, fmt):
    return fmt.format(value)


@register.filter(name="encode_b64_str")
def encode_b64_str(value):
    """Renvoi un string en base 64 decodée"""
    return set_base_64_str(value)


@register.filter(name="encode_b64_list")
def encode_b64_list(values_list):
    """Renvoi une liste en base 64 decodée"""
    return set_base_64_list(values_list)


@register.simple_tag
def regroup_list_pipe(*args):
    """Retourne un str avec separateur '||'"""
    return "||".join(args)


@register.simple_tag
def get_address(adresse):
    """Compose une adresse avec un str comme séparateur ||,
    avec obligatoirement le code postal et la ville en dernière position
    """
    values_list = adresse.split("||")
    intitule_list = [value for value in values_list[:-2] if value]
    lieux_liste = [value for value in values_list[-2:] if value]
    intitule = ", ".join(intitule_list) if intitule_list else ""
    lieux = (" - " + " ".join(lieux_liste)) if lieux_liste else ""
    return f"{intitule}{lieux}"


@register.filter
def percentage(value):
    return f"{value:.1%}"


@register.filter(name="due_dates")
def due_dates(date_value, paiement_condition):
    """Renvoie les dates d'échéance en fonction de la date de facture
    et le nom de la condition de paiement
    """
    if not paiement_condition:
        return ""

    return get_str_echeances(date_value, paiement_condition)


@register.filter(name="string_agg")
def string_agg(value_list, deliminter=","):
    """Renvoie du texte séparé par une virgule, à partir d'une liste, tuple, ... génératoeur,
    comme un string_agg postgresql"""
    return f"{deliminter} ".join([str(value) for value in value_list])


@register.filter(name="string_agg_uniques")
def string_agg_uniques(value_list, delimiter=","):
    """Renvoie du texte séparé par une virgule, à partir d'une liste, tuple, ... génératoeur,
    comme un string_agg postgresql"""
    # Pour en limiter le nombre en fin de texte du delimiter on peut mettre un chiffre
    digits_list = list(re.finditer(r"\d*$", delimiter))
    digits = digits_list[0].group() if digits_list else ""
    values = sorted(set(value_list))

    if digits:
        delimiter = delimiter.replace(digits, "")
        string_return = f"{delimiter} ".join([str(value) for value in values[: int(digits)]])
        values_nb = len(values)

        if string_return and values_nb > 1 and values_nb > int(digits):
            return string_return + f"{delimiter} ..."
        else:
            return string_return

    return f"{delimiter} ".join([str(value) for value in values])


@register.filter(name="addition")
def addition(value, other):
    """
    Adittione deux nombres
    :param value:
    :param other:
    :return:
    """
    print(value, other)
    print(Decimal(value), " - ", Decimal(other))
    return Decimal(value) + Decimal(other)


@register.filter(name="regroup_sum")
def regroup_sum(values_list, field):
    total = 0

    for invoice in values_list:
        try:
            total += invoice.__dict__.get(field, 0)
        except AttributeError:
            total += invoice.get(field, 0)

    return total
