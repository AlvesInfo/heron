"""
Module Utilitaires
"""
import os
import glob
from itertools import chain, islice, accumulate
import re
import time
from decimal import Decimal
import datetime
from typing import Iterable
from operator import itemgetter
from chardet.universaldetector import UniversalDetector
from decimal import Decimal
from pathlib import Path
import lxml.html


import pendulum
from pendulum.exceptions import ParserError


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
    string_series = ""

    if num > 0:
        string_series = nb_init.format(num)[-nb_car:]
    elif num == 0:
        string_series = nb_init.format(0)[-nb_car:]
    elif num < 0:
        string_series = nb_init.format(abs(num))[-nb_car:]

    return string_series


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
    try:
        i_t = iter(iterable)
        while True:
            yield form(chain((next(i_t),), islice(i_t, taille - 1)))
    except StopIteration:
        pass


def iter_slicing(iterable):
    iterable_2 = chain([0], iterable[:-1])
    return [slice(k, v) for k, v in zip(iterable_2, iterable)]


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
        print(f"{duree}s")
        return False

    def __str__(self):
        duree = time.time() - self.start
        return f"intermédiaire : {duree}s"


def format_line_to_dos(ligne, mode):
    """
    Fonction qui remet les sauts de lignes correctement pour un environnement donné
        :param ligne: Ligne à transformer
        :param mode: Unix = 0 | Mac = 1 | DOS = 2 | Unix-vers-Dos = 3
        :return: Ligne transformée
    """
    if mode == 0:
        ligne_modif = ligne.replace("\r\n", "\n").replace("\r", "\n")

    elif mode == 1:
        ligne_modif = ligne.replace("\r\n", "\r").replace("\n", "\r")

    elif mode == 2:
        ligne_modif = re.sub("\r\n$", "\n", ligne)
        ligne_modif = re.sub("\n\n$", "\n", ligne_modif)
        ligne_modif = re.sub("\n$", "\r\n", ligne_modif)
        ligne_modif = re.sub("\r$", "", ligne_modif)

    else:
        ligne_modif = ligne.replace("\n", "\r\n")

    return ligne_modif


def verif_chiffres(numbers, l_g=None, between=None):
    """
    Fonction qui vérifie un nombre
        :param numbers: Nombre à vérifier
        :param l_g: Si l'on veut vérifier le nombre de chiffres
        :param between: Si l'on veut vérifier un intervalle,
                        doit être un tuple ou une liste (1998, 2010)
        :return: True si valide sinon None
    """
    number = None
    num = str(numbers)

    try:
        n_b = int(num)

        if l_g is not None:
            if len(num) == l_g:
                number = True

        elif between is not None and isinstance(between, (tuple, list)):
            premier, dernier = between
            if premier > dernier:
                premier, dernier = dernier, premier
            number = True if premier <= n_b <= dernier else None
    except ValueError:
        number = None

    return number


def alpha(v_s):
    """
    Fonction qui supprime les tabulations, saut de lignes CR/LF, les .0 et les espaces devant
    et derrière
        :param v_s: String à corriger
        :return: String corrigé
    """
    intermediate = str(v_s).replace("\n", "").replace("\t", "").replace("\r", "").strip()
    return intermediate.replace(".0", "") if intermediate.endswith(".0") else intermediate.strip()


def get_doublons(iterable):
    """
    Fonction qui retourne les doublons d'un itérateur
        :param iterable: N'importe quel itérable, de même type
        :return: Set des doublons
    """
    test = ""
    doublons = set()
    for k in sorted(iterable):
        if k == test:
            doublons.add(k)
        else:
            test = k

    return doublons


def get_list_duplicates(lst, equals=lambda x, y: x == y):
    """
    Fonction qui retourne les doublons d'une liste
        :param lst: Liste à vérifier
        :param equals: Fonction à utiliser, pour le test des doublons
        :return: Une liste des doublons
    """
    if not isinstance(lst, list):
        raise TypeError("This function works only with lists.")

    verif_list = lst[:]
    doublons = []
    i_1 = 0
    l_g = len(verif_list) - 1

    # On itère sur la liste
    while i_1 < l_g:
        # On récupère chaque élément de la liste, sauf le dernier
        elem = verif_list[i_1]

        # On le compare à l'élément suivant et chaque élément après l'élément suivant
        i_2 = i_1 + 1
        while i_2 <= l_g:
            # En cas d'égalité, on retire l'élément de la liste, et on décrémente la longueur de la
            # liste ainsi amputée
            if equals(elem, verif_list[i_2]):
                del verif_list[i_2]
                doublons.append(elem)
                l_g -= 1

            i_2 += 1

        i_1 += 1

    return doublons


def iter_in_elements(iterable, require_elemnts):
    """
    Fonction generatrice qui yield les éléments de l'itérateur, que l'on veut garder
        :param iterable: Itérable
        :param require_elemnts: Set des éléments à garder, commence à 0
        :return: Générateur des éléments
    """
    return (v for k, v in enumerate(iterable) if k in require_elemnts)


def iter_out_elements(iterable, del_elemts):
    """
    Fonction generatrice qui yield les éléments de l'itérateur, que l'on veut garder
        :param iterable: Itérable
        :param del_elemts: Set des éléments à supprimer, commence à 0
        :return: Générateur des éléments
    """
    return (v for k, v in enumerate(iterable) if k not in del_elemts)


def iter_in_elements_order(iterable, require_elemnts):
    """
    Fonction generatrice qui yield les éléments de l'itérateur, que l'on veut garder
        :param iterable: Itérable
        :param require_elemnts: Liste de int, des éléments à garder, commence à 0
        :return: Générateur des éléments
    """
    return (iterable[j] for j in require_elemnts)


def pages(iterable):
    """
    Fonction qui renvoie les pages à la façon des pages à imprimer
        :param iterable: Un itérable, qui comporte des chiffres et un séparateur
        :return: La liste complète des pages une à une
    """
    if iterable is None:
        return None

    return iterable


def move_file(file, new_file):
    """
    Fonction de déplcement d'un fichier
        :param file: Chemin du fichier complet à déplacer
        :param new_file: Chemin du fichier complet de l'endroit de destination
        :return: None
    """
    if os.path.isfile(file):
        base_error_dir = os.path.dirname(new_file)

        if not os.path.isdir(base_error_dir):
            os.makedirs(base_error_dir)

        os.rename(file, new_file)


def delete_file(file):
    """
    Fonction qui supprime un fichier
        :param file: Chemin vers le fichier à supprimer
        :return: None
    """
    if os.path.isfile(file):
        os.remove(file)


def replace_null_csv(reader):
    """
    Fonction qui renvoie une liste, les valeurs <NULL> remplacées en None, de tous les élements
    des lignes d'un csv
        :param reader: objet csv.reader
        :return: yield une liste de chaque ligne transformée
    """
    for csv_line in reader:
        nullable = (None if str(x) == "<NULL>" else x for x in csv_line)
        yield nullable


def reset_dir_files(path, extenstion=None, reverse=None, first=None, name_part=None):
    """
    Fonction qui supprime les fichiers présents dans un répertoire
        :param path: Répertoire concerné
        :param extenstion: Extension du fichier 'csv', 'xls', 'xlsx', 'txt' ....
        :param reverse: Tri de la liste, reverse=None -> ascendante et reverse=True -> descendante
        :param first: Si l'on veut tous les fichiers -> first=None, le premier fichier -> first=True
        :param name_part:   Partie d'un nom à rechercher -> name="TEST",
                            tous les fichiers  -> name=None
        :return: None
    """
    path_name = f"{path}/*." if name_part is None else f"{path}/*{str(name_part)}*."
    path = f"{path_name}*" if extenstion is None else f"{path_name}{extenstion}"
    list_files = glob.glob(path)

    if reverse is None:
        list_files.sort()
    else:
        list_files.sort(reverse=True)

    if list_files:
        if first is None:
            for file in list_files:
                delete_file(file)
        else:
            delete_file(list_files[0])


def list_file(path, extension=None, reverse=None, first=None, name_part=None):
    """
    Fonction qui renvoie la liste des fichiers présente dans un répertoire
        :param path: Répertoire de recherche
        :param extension: Extension du fichier 'csv', 'xls', 'xlsx', 'txt' ....
        :param reverse: Tri de la liste, reverse=None -> ascendante et reverse=True -> descendante
        :param first: Si l'on veut tous les fichiers -> first=None, le premier fichier -> first=True
        :param name_part: Partie d'un nom à rechercher -> name="TEST",
                            tous les fichiers -> name=None
        :return: La liste des fichiers ou le fichier sinon None
    """
    path_name = f"{path}/*." if name_part is None else f"{path}/{str(name_part)}"

    if name_part is None:
        path_name = f"{path_name}*" if extension is None else f"{path_name}{extension}"

    list_files = glob.glob(path_name)

    if reverse is None:
        list_files.sort()
    else:
        list_files.sort(reverse=True)

    if first is None:
        return list_files or None

    return list_files[0] if list_files else None


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


def get_decimal_zero(num):
    """
    Fonction qui vérifie les chiffres en Decimal
        :param num: chiffres qui vient en argument
        :return: Decimal(0) ou num
    """

    if not isinstance(num, (Decimal,)):
        return Decimal(0)

    return num


def str_amount(decimal_amount):
    """
    Fonction qui retourne un montant à deux chiffres après la virgule
        :param decimal_amount: montant avec séparateur.
        :return: str montant à deux chiffres après la virgule
    """
    amount, *dec = str(decimal_amount).split(".")

    if not dec:
        return f"{amount}.00"

    cents = dec[0] + "00"

    return f"{amount}.{cents[:2]}"


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


def get_file_date(file: Path) -> str:
    """Fonction qui vérifie si il y a la date dans le nom du fichier,
    sur les huits derniers caractères
        :param file: fichier de type pathlib.Path
        :return: date or None
    """
    file_date = file.stem.split(".")[0][-8:]

    try:
        return pendulum.parse(file_date)

    except ParserError:
        pass


def str_to_json(value: str) -> str:
    return (
        value.replace("'': '", '"": "')
        .replace("{'", '{"')
        .replace("' :", '" :')
        .replace("'}", '"}')
        .replace("':", '":')
        .replace(": '", ': "')
        .replace(":'", ':"')
        .replace(r"\xa0", " ")
        .replace("\\", "")
    )


def get_html_to_text(value):
    try:
        return "" if value is None else lxml.html.fromstring(value).text_content()[:32767]
    except lxml.etree.ParserError:
        return ""


def get_decimal(value):
    test_value = str(value).strip().replace(" ", "")
    test_decimal = [
        val
        for val in test_value
        if val not in {"0", "1", "2", "3", "4", "5", "6", "7", "8", "9", ",", "."}
    ]

    if test_decimal:
        return value

    if "." in test_value and "," in test_value:
        to_replace = ""
        to_delete = ""
        for letter in test_value:
            if letter == ".":
                to_delete = letter
                to_replace = ","
                break

            if letter == ",":
                to_delete = letter
                to_replace = "."
                break

        return test_value.replace(to_delete, "").replace(to_replace, ".")

    return test_value.replace(",", ".")


def get_zero_decimal(value):
    test_value = str(value).strip().replace(" ", "")
    test_decimal = [
        val
        for val in test_value
        if val not in {"0", "1", "2", "3", "4", "5", "6", "7", "8", "9", ",", "."}
    ]

    if test_decimal:
        return value

    if "." in test_value and "," in test_value:
        to_replace = ""
        to_delete = ""
        for letter in test_value:
            if letter == ".":
                to_delete = letter
                to_replace = ","
                break

            if letter == ",":
                to_delete = letter
                to_replace = "."
                break

        return test_value.replace(to_delete, "").replace(to_replace, ".")

    return test_value.replace(",", ".") or "0"
