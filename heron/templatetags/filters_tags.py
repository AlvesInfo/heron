import pendulum
import lxml.html as html
from lxml.etree import ParserError

from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter(name="point")
@stringfilter
def point(value):
    return value.replace(",", ".")


@register.filter(name="left_trunc")
@stringfilter
def left_trunc(value, num):
    return value[int(num) :]


@register.filter(name="right_align")
def right_align(value, num):
    to_split = value.split("-")

    if len(to_split) == 1:
        return value.rjust(num)

    return (
        to_split[0].rjust(num)
        + " - "
        + " - ".join(row for row in to_split[1:])
    )


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
