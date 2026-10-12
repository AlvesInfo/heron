"""Filtres de templates du projet heron."""

import re

import pendulum
from django import template
from django.template.defaultfilters import stringfilter
from django.utils.html import format_html, format_html_join

from apps.core.bin.encoders import set_base_64_str

register = template.Library()

# Balises conservées par les filtres keep_br et trace_comment : texte source -> html sûr
BR_TAGS = {"<br>": format_html("<{}>", "br")}
TRACE_TAGS = {
    **BR_TAGS,
    "<div style='padding-left: 20px;'>": format_html('<div style="{}">', "padding-left: 20px;"),
    "</div>": format_html("</{}>", "div"),
}


def escape_except(value, tags):
    """Échappe le texte en ne laissant passer que les balises attendues.

    :param value: texte à afficher, None est affiché vide
    :param tags: dictionnaire des balises conservées (texte exact dans la valeur -> html sûr)
    :return: html sûr, à afficher sans le filtre safe.
    """
    if value is None:
        return ""

    pattern = "(" + "|".join(re.escape(tag) for tag in tags) + ")"

    return format_html_join(
        "", "{}", ((tags.get(part, part),) for part in re.split(pattern, str(value)))
    )


@register.filter(name="keep_br")
def keep_br(value):
    """Échappe la valeur en conservant ses sauts de ligne <br>."""
    return escape_except(value, BR_TAGS)


@register.filter(name="trace_comment")
def trace_comment(value):
    """Échappe le commentaire d'une trace en conservant la mise en forme écrite par les imports.

    (sauts de ligne <br> et bloc indenté), les données venues des fichiers sont échappées.
    """
    return escape_except(value, TRACE_TAGS)


@register.filter(name="point")
@stringfilter
def point(value):
    """Remplace la virgule décimale par un point."""
    return value.replace(",", ".")


@register.filter(name="is_str")
def get_is_str(value):
    """Indique si la valeur est une chaîne."""
    return isinstance(value, (str,))


@register.filter(name="get_dict_values")
def get_dict_values(value):
    """Liste des valeurs d'un dictionnaire."""
    if isinstance(value, (dict,)):
        return list(value.values())
    return None


@register.filter
def get_item(dictionary, key):
    """Valeur d'un dictionnaire pour une clé."""
    return dictionary.get(key)


@register.filter(name="date_from_str_4")
def date_from_str_4(value):
    """Convertit une date jj/mm/aa ou jj/mm/aaaa en date."""
    if value:
        day, month, year = value.split("/")
        if len(year) == 2:
            year = f"20{year}"

        try:
            return pendulum.date(int(year), int(month), int(day)).isoformat()
        except (TypeError, ValueError):
            pass

    return ""


def _split_number(value):
    """Sépare la partie entière et les centimes d'un nombre (texte, int ou Decimal).

    Les centimes sont complétés de zéros pour être tronqués à la précision demandée.
    """
    nombre, _, centimes = str(value).partition(".")
    return nombre, centimes + "0" * 99


def _group_thousands(nombre):
    """Insère une espace tous les trois chiffres en partant de la droite."""
    grouped = ""

    for i, digit in enumerate(nombre[::-1], 1):
        grouped += digit

        if i % 3 == 0:
            grouped += " "

    return grouped[::-1].strip()


@register.filter(name="numbers")
def numbers(value, num):
    """Nombre avec num décimales (séparateur point), sans séparateur de milliers."""
    if not value:
        return "0"

    nombre, centimes = _split_number(value)
    return nombre + (f".{centimes[:num]}" if num else "")


@register.filter(name="numbersp")
def numbersp(valueh, num):
    """Pourcentage : valeur multipliée par 100, avec num décimales."""
    if not valueh:
        return "0"

    return numbers(valueh * 100, num)


@register.filter(name="default_if_zero")
def default_if_zero(value):
    """Chaîne vide si la valeur est zéro."""
    if str(value) == "0":
        return ""

    return value


@register.filter(name="numbers_format")
def numbers_format(value, num):
    """Nombre avec séparateur de milliers (espace) et num décimales (séparateur virgule).

    Accepte aussi un entier ou un texte sans partie décimale.
    """
    if not value:
        return "0"

    nombre, centimes = _split_number(value)
    return _group_thousands(nombre) + (f",{centimes[:num]}" if num else "")


@register.filter(name="int_formats")
def int_formats(value):
    """Partie entière avec séparateur de milliers."""
    if not value:
        return "0"

    return _group_thousands(str(value).split(".")[0])


@register.filter(name="encode_b64_str")
def encode_b64_str(value):
    """Renvoi un string en base 64 decodée."""
    return set_base_64_str(value)


@register.simple_tag
def regroup_list_pipe(*args):
    """Retourne un str avec separateur '||'."""
    return "||".join(args)


@register.simple_tag
def get_address(adresse):
    """Compose une adresse avec un str comme séparateur ||,.

    avec obligatoirement le code postal et la ville en dernière position.
    """
    values_list = adresse.split("||")
    intitule_list = [value for value in values_list[:-2] if value]
    lieux_liste = [value for value in values_list[-2:] if value]
    intitule = ", ".join(intitule_list) if intitule_list else ""
    lieux = (" - " + " ".join(lieux_liste)) if lieux_liste else ""
    return f"{intitule}{lieux}"


@register.filter
def percentage(value):
    """Formate un ratio en pourcentage à une décimale."""
    return "" if value is None else f"{value:.1%}"


@register.filter(name="regroup_sum")
def regroup_sum(values_list, field):
    """Somme d'un champ sur une liste d'objets."""
    total = 0

    for invoice in values_list:
        try:
            total += invoice.__dict__.get(field, 0)
        except AttributeError:
            total += invoice.get(field, 0)

    return total


@register.filter(name="siret_number")
def siret_number(value):
    """Embelli les N° de Siret.

    :param value: valeur venue du queryset
    :return:
    """
    siret = ""
    value_to_siret = str(value).strip().replace("_", "").replace(" ", "").replace("-", "")

    for i, letter in enumerate(value_to_siret, 1):
        siret += letter
        if i % 3 == 0 and i < 10:
            siret += " "

    return siret
