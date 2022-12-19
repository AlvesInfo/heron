import pendulum
import lxml.html as html
from lxml.etree import ParserError

from django import template
from django.template.defaultfilters import stringfilter

from apps.core.bin.encoders import set_base_64_list, set_base_64_str

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

    nombre, centimes, *_ = str(value).split(".")
    centimes += "0" * 99
    return_value = ""

    for i, value in enumerate(nombre[::-1], 1):
        return_value += value

    if num:
        centimes_part = "." + centimes[:num]
    else:
        centimes_part = ""

    return (return_value[::-1] + centimes_part).strip()


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

    return (return_value[::-1] + "," + centimes[:num]).strip()


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
