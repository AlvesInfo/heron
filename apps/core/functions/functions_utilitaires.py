"""
Module Utilitaires
"""
import os
from itertools import chain, islice, accumulate
import time
from decimal import Decimal
import datetime
from operator import itemgetter
from chardet.universaldetector import UniversalDetector
from typing import AnyStr
import importlib

from heron.loggers import LOGGER_DJANGO


class EncodingError(Exception):
    """Exception sniff encodig"""


def overlaps(
    iterable_1: [int, float, Decimal, type(datetime)],
    iterable_2: [int, float, Decimal, type(datetime)],
):
    """
    :param iterable_1: iterable de int, float, Decimal ou de datetime
    :param iterable_2: iterable de int, float, Decimal ou de datetime
    :return: Renvoie True si iterable_1 overlap iterable_2 sinon False
    >>> overlaps([0, 3], [3, 4])
    True
    >>> overlaps([3, 4], [0, 3])
    True
    >>> overlaps([-1, 0], [0, 3])
    True
    >>> overlaps([0, 3], [-1, 0])
    True
    >>> overlaps([0, 3], [4, 6])
    False
    >>> overlaps([0, 3], [-4, -6])
    False
    >>> from datetime import date
    >>> overlaps([date(2022, 1, 1), date(2022, 1,3)], [date(2022, 1, 3), date(2022, 1,6)])
    True
    >>> overlaps([date(2022, 1, 1), date(2022, 1,3)], [date(2021, 12, 20), date(2022, 1, 1)])
    True
    >>> overlaps([date(2022, 1, 1), date(2022, 1,3)], [date(2021, 12, 20), date(2021, 12, 31)])
    False
    >>> overlaps([date(2022, 1, 1), date(2022, 1,3)], [date(2022, 1, 2), date(2022, 1,2)])
    True
    >>> overlaps([date(2022, 1, 1), date(2022, 1,3)], [date(2022, 1, 6), date(2022, 1,8)])
    False
    """
    return max(iterable_1) >= min(iterable_2) >= min(iterable_1) or max(iterable_2) >= min(
        iterable_1
    ) >= min(iterable_2)


N_DIC = {
    "A": {
        "Ȁ",
        "ȃ",
        "À",
        "Ǻ",
        "Ȃ",
        "ą",
        "ȁ",
        "Á",
        "ä",
        "ǻ",
        "Ã",
        "à",
        "Ȧ",
        "Ǎ",
        "ă",
        "ȧ",
        "Ǟ",
        "Å",
        "Ą",
        "ã",
        "Ă",
        "â",
        "Ǡ",
        "Â",
        "á",
        "å",
        "Ä",
        "Ⱥ",
        "ǡ",
        "ā",
        "ǎ",
        "Ā",
        "ǟ",
    },
    "AE": {"ǣ", "æ", "Æ", "Ǣ", "Ǽ", "ǽ"},
    "B": {"Ƅ", "Ƀ", "Ƃ", "Ɓ", "ƃ", "þ", "ß", "ƅ", "Þ", "ƀ"},
    "C": {"Ċ", "ĉ", "Ć", "č", "ƈ", "Ƈ", "Č", "ç", "ȼ", "Ç", "Ȼ", "ċ", "ć", "Ĉ"},
    "D": {"Ɗ", "ƌ", "ƍ", "ď", "Ď", "Đ", "Ƌ", "Ð", "đ", "Ɖ"},
    "DZ": {"ǲ", "Ǆ", "ǆ", "ȡ", "ǅ", "ǳ", "Ǳ"},
    "E": {
        "ę",
        "Ȅ",
        "É",
        "ë",
        "Ê",
        "Ė",
        "Ǝ",
        "ê",
        "ǝ",
        "Ȩ",
        "é",
        "Ē",
        "Ě",
        "Ȇ",
        "ĕ",
        "È",
        "è",
        "Ę",
        "ȩ",
        "Ə",
        "Ĕ",
        "ȅ",
        "Ɛ",
        "Ɇ",
        "ė",
        "ě",
        "ȇ",
        "Ë",
        "ɇ",
        "ē",
    },
    "F": {"ƒ", "Ƒ"},
    "G": {"ģ", "Ġ", "ğ", "Ǵ", "ǧ", "Ɣ", "ġ", "ǵ", "Ǥ", "Ǧ", "ǥ", "ĝ", "Ĝ", "Ɠ", "Ģ", "Ğ"},
    "H": {"Ħ", "Ĥ", "Ƕ", "Ȟ", "ʱ", "ʰ", "ħ", "ĥ", "ȟ"},
    "I": {
        "ı",
        "Ĩ",
        "Ɨ",
        "Ȋ",
        "ȋ",
        "Ɩ",
        "ì",
        "Į",
        "Ĭ",
        "î",
        "ĳ",
        "İ",
        "ȉ",
        "ǐ",
        "ï",
        "Ĳ",
        "ĭ",
        "Ì",
        "ī",
        "į",
        "ĩ",
        "Ȉ",
        "Ǐ",
        "í",
        "Ī",
        "Í",
        "Ï",
        "Î",
    },
    "J": {"ʲ", "Ɉ", "ɉ", "ĵ", "Ĵ", "ȷ"},
    "K": {"Ķ", "ƙ", "ķ", "ĸ", "Ǩ", "ǩ", "Ƙ"},
    "L": {"Ĺ", "Ƚ", "ĺ", "ŀ", "Ļ", "Ŀ", "Ł", "Ľ", "ł", "ľ", "ȴ", "ļ", "ƛ", "ƚ"},
    "LJ": {"ǉ", "ǈ", "Ǉ"},
    "M": {"Ɯ"},
    "N": {"Ñ", "ņ", "ñ", "Ǹ", "Ň", "Ņ", "ŉ", "Ŋ", "Ń", "Ƞ", "ń", "ǹ", "ȵ", "ň", "ŋ", "Ɲ", "ƞ"},
    "NJ": {"Ǌ", "ǌ", "ǋ"},
    "O": {
        "Ō",
        "ȫ",
        "Ŏ",
        "ǒ",
        "Ȭ",
        "Ɵ",
        "ȭ",
        "Ɔ",
        "ȱ",
        "Ő",
        "Ô",
        "Ȫ",
        "ō",
        "ȯ",
        "ó",
        "ø",
        "ő",
        "Ơ",
        "Ȯ",
        "ŏ",
        "Ø",
        "Ȍ",
        "ò",
        "Ò",
        "ǿ",
        "Ȏ",
        "ö",
        "ȍ",
        "Õ",
        "Ǒ",
        "Ȱ",
        "Ó",
        "ô",
        "Ö",
        "õ",
        "Ǿ",
        "ȏ",
        "ơ",
    },
    "OE": {"Œ", "œ"},
    "OI": {"ƣ", "Ƣ"},
    "P": {"ƥ"},
    "Q": {"Ǫ", "Ɋ", "ɋ", "ǭ", "Ǭ", "ǫ"},
    "R": {"ŗ", "ʳ", "ŕ", "Ȑ", "ɍ", "Ř", "ʶ", "ř", "ʴ", "ȑ", "Ŕ", "Ɍ", "ȓ", "Ȓ", "ʵ", "Ŗ"},
    "S": {"ś", "Ş", "Ș", "š", "ȿ", "ș", "Ŝ", "ſ", "ş", "Š", "ŝ", "Ś"},
    "T": {"Ŧ", "Ƭ", "ȶ", "ť", "ț", "Ʈ", "ƫ", "Ť", "Ⱦ", "ţ", "Ţ", "ŧ", "Ț", "ƭ"},
    "U": {
        "ů",
        "Ȗ",
        "Ú",
        "ú",
        "ų",
        "Ȕ",
        "Ű",
        "Ǔ",
        "ǜ",
        "Ŭ",
        "ȕ",
        "Ʉ",
        "ü",
        "ǖ",
        "Ü",
        "Ù",
        "Ū",
        "Ũ",
        "û",
        "ǘ",
        "Ǖ",
        "ū",
        "Ǜ",
        "ǚ",
        "ũ",
        "Ǚ",
        "Ʊ",
        "Ư",
        "Ǘ",
        "ȗ",
        "Û",
        "ű",
        "Ų",
        "Ů",
        "ǔ",
        "ư",
        "ŭ",
        "ù",
    },
    "V": {"Ʋ"},
    "W": {"ŵ", "ʷ", "Ŵ"},
    "Y": {"Ý", "ƴ", "ý", "Ÿ", "Ɏ", "Ȳ", "ɏ", "ÿ", "Ƴ", "ŷ", "ʸ", "Ŷ", "ȳ"},
    "Z": {"Ź", "ź", "ȥ", "ż", "ƶ", "Ż", "ɀ", "Ž", "Ȥ", "ž", "Ƶ"},
}


def num_string_series(num=0, nb_car=1):
    """
    Fonction qui renvoie un style de generate_series postgesql :
            exemple résultat -> 0000000018
        :param num: De type int
        :param nb_car: De type int, nombre de caractères souhaités
        :return: De type string
    """
    nb_init = "00000000000000000000000000000000000000000000000000{0}"
    num = int(num)

    # un entier est positif, nul ou négatif : le dernier cas est le "sinon" (pas de 4e issue)
    return nb_init.format(abs(num))[-nb_car:]


def iter_slice(iterable, taille, form=tuple):
    """
    Parcourir n'importe quel itérable, par tailles
        exemple :
            l = [1, 2, 3, 4, 5, 6, 7, 8, 9]
            rows = iter_slice(l, 4)
            for r in rows:
                print(r)
            ... (1, 2, 3, 4)
            ... (5, 6, 7, 8)
            ... (9, )
        :param iterable: List, tuple, set, str etc...
        :param taille: Nombre
        :param form: Format de sortie, par default tuple, mais on peut choisir, list, set ...
        :return: Générateur par tranches
    """
    i_t = iter(iterable)

    for first in i_t:
        yield form(chain((first,), islice(i_t, taille - 1)))


class Timer:
    """
    Timer
    """

    def __init__(self):
        self.start = time.time()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        duree = time.time() - self.start
        LOGGER_DJANGO.info(f'{duree}s')
        return False

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        duree = time.time() - self.start
        return f"intermédiaire : {duree}s"


def alpha(v_s):
    """
    Fonction qui supprime les tabulations, saut de lignes CR/LF, les .0 et les espaces devant
    et derrière
        :param v_s: String à corriger
        :return: String corrigé
    """
    intermediate = str(v_s).replace("\n", "").replace("\t", "").replace("\r", "").strip()
    return intermediate.replace(".0", "") if intermediate.endswith(".0") else intermediate.strip()


def pages(iterable):
    """
    Fonction qui renvoie les pages à la façon des pages à imprimer
        :param iterable: Un itérable, qui comporte des chiffres et un séparateur
        :return: La liste complète des pages une à une
    """
    if iterable is None:
        return None

    return iterable


def delete_file(file):
    """
    Fonction qui supprime un fichier
        :param file: Chemin vers le fichier à supprimer
        :return: None
    """
    if os.path.isfile(file):
        os.remove(file)


def encoding_detect(path_file):
    """Fonction qui renvoi l'encoding le plus probable de du fichier passé en paramètre"""
    try:
        detector = UniversalDetector()

        with open(path_file, "rb") as file:
            for line in file:
                detector.feed(line)

                if detector.done:
                    break

            detector.close()

    except Exception as except_error:
        raise EncodingError(f"encoding_detect : {path_file.name !r}") from except_error

    return detector.result["encoding"]


def slicing_parser(iterable):
    """Fonction qui retourne un itemgetter sur un iterabble de nombre formant le nombre de
    caractères (tranches) à récupérer par item getter. Des tranches de slices
        exemple:
            ... iterable = [2, 5, 4]
            ... parse_slicing = slicing_parser(iterable)
            équivalent à
            ... parse_slicing = itemgetter(slice(0, 2, None), slice(2, 7, None), slice(7, 11, None))
        :param iterable: la ligne à slicer : slicing = (2, 5, 4)
        :return: itemgetter(slice(0, 2, None), slice(2, 7, None), slice(7, 11, None))
    """
    start_iter = iter(iterable[:-1])
    end_iter = iter(iterable)
    return itemgetter(
        *(slice(k, v) for k, v in zip(accumulate(chain([0], start_iter)), accumulate(end_iter)))
    )


# def pprint_dict(dict_pp):
#     from pprint imports pformat
#     from yapf.yapflib.yapf_api imports FormatCode
#
#     dict_string = pformat(dict_pp)
#     formatted_code, _ = FormatCode(dict_string)
#     print("formated : ",formatted_code)
#     return formatted_code


def get_client_ip(request):
    """Récupère l'adresse ip si elle existe
    :param request:
    :return:
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0]

    return request.META.get("REMOTE_ADDR")


def _without_thousands_separator(test_value):
    """Valeur portant un point et une virgule : le premier rencontré est le séparateur de
    milliers (supprimé), le second le séparateur décimal (remplacé par un point)
    """
    first = next(letter for letter in test_value if letter in {".", ","})
    to_delete, to_replace = (".", ",") if first == "." else (",", ".")

    return test_value.replace(to_delete, "").replace(to_replace, ".")


def get_decimal(value):
    """Normalise un nombre saisi (séparateurs français ou anglais) en notation à point,
    la valeur est renvoyée telle quelle si elle contient autre chose que des chiffres
    """
    test_value = str(value).strip().replace(" ", "")
    test_decimal = [
        val
        for val in test_value
        if val not in {"0", "1", "2", "3", "4", "5", "6", "7", "8", "9", ",", ".", "-", "+"}
    ]

    if test_decimal:
        return value

    if "." in test_value and "," in test_value:
        return _without_thousands_separator(test_value)

    return test_value.replace(",", ".")


def get_zero_decimal(value):
    """Comme get_decimal, sans signe, le % retiré, zéro si la valeur est vide"""
    test_value = str(value).strip().replace(" ", "").replace("%", "")
    test_decimal = [
        val
        for val in test_value
        if val not in {"0", "1", "2", "3", "4", "5", "6", "7", "8", "9", ",", "."}
    ]

    if test_decimal:
        return value

    if "." in test_value and "," in test_value:
        return _without_thousands_separator(test_value)

    return test_value.replace(",", ".") or "0"


def format_siret(siret):
    """
    Formate un n° de SIREN (9 chiffres) ou SIRET (14 chiffres)
        :param siret: N° de SIREN ou SIRET
        :return: N° formaté : "000 000 000" ou "000 000 000 00000" ou tel quel sans espaces
    """
    if siret is None or not siret:
        return ""

    value = str(siret).replace(" ", "")

    if len(value) == 9 and value.isdigit():
        return f"{value[:3]} {value[3:6]} {value[6:]}"

    if len(value) == 14 and value.isdigit():
        return f"{value[:3]} {value[3:6]} {value[6:9]} {value[9:]}"

    return value


def get_module_object(function_path_point: AnyStr):
    """Retourne l'objet au sens python
    :param function_path_point: path de la fonction pointée (ex. home.file_func.function)
    :return: l'objet au sens python
    """
    module_path, function_name = function_path_point.rsplit(".", 1)
    module = importlib.import_module(module_path)
    function = getattr(module, function_name)

    return function
