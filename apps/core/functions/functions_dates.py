"""
Module d'itilisation des dates
"""
import datetime
import calendar
from datetime import timedelta
from functools import lru_cache

from dateutil.relativedelta import relativedelta
import pendulum

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


def get_date_apostrophe(dte: [pendulum, datetime, str]):
    """Renvoi "de" où "d'" en fonction du mois reçu"""
    if isinstance(dte, (str,)):
        if not dte:
            return "de "

        return "d'" if str(dte).lower()[0] in {"a", "o"} else "de "

    return "d'" if dte.month in {4, 8, 10} else "de "


def lower_mois_string_sans_accents(dte):
    """Fonction qui renvoie le nom du mois sans accents
    :param dte: 17/01/2017
    :return: Janvier
    """
    return f"{MONTHS[dte.month]}"


def first_day_month(dte):
    """Fonction qui retourne le premier jour du mois
    :param dte: 17/01/2017
    :return: '2017-01-01' au format datetime.date(2017, 1, 1)
    """
    return datetime.date(dte.year, dte.month, 1)


def last_day_month(dte):
    """Fonction qui retourne le dernier jour du mois
    :param dte: 17/01/2017
    :return: '2017-01-01' au format datetime.date(2017, 1, 31)
    """
    return datetime.date(dte.year, dte.month, days_of_month(dte))


def year_month(dte):
    """Fonction qui retourne l'année et le mois
    :param dte: date
    :return: 2018_10
    """
    return f"{dte.year}_{dte.month}"


def date_moins_x_mois(dte: datetime.date, mois: int) -> datetime.date:
    """Fonction qui retourne la date avec x mois en moins
    :param dte: date
    :param mois: nombre de mois antérieurs
    :return: la date moins x mois
    """
    d_mois = mois - 1
    annee = dte.year - d_mois // 12
    n_m = dte.month
    jour = dte.day
    mod_mois = d_mois % 12
    v_mois = n_m if mod_mois == 0 else n_m - mod_mois

    if v_mois < 1:
        annee -= 1
        n_m = 12 + v_mois
    else:
        n_m = v_mois

    if days_of_month(datetime.date(annee, n_m, 1)) < jour:
        jour = days_of_month(datetime.date(annee, n_m, 1))

    return datetime.date(annee, n_m, jour)


def date_string_series(dte=None):
    """Fonction qui renvoie une date sous forme de string :
    :param dte: de type date
    :return: de type string ex.: 2017_02_01
    """
    if dte is None:
        dte = datetime.datetime.now()

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
    """Fonction qui renvoie le nombre de secondes entre maintenant et le 01/01/2000 - 00:00 :
        exemple résultat -> 1497797172
    :return: de type string
    """
    past = datetime.datetime(2000, 1, 1, 0, 0)
    now = datetime.datetime.now()
    delta = now - past
    delta = str(abs(delta.days * 24 * 3600 + delta.seconds))

    return delta


def date_string_4(dte):
    """Fonction qui renvoie la date au format 30/01/2017
    :param dte: date
    :return: 30/01/2017
    """
    jd = str(dte.day)
    if len(jd) == 1:
        jd = f"0{jd}"

    jm = str(dte.month)
    if len(jm) == 1:
        jm = f"0{jm}"

    jy = str(dte.year)
    if len(jy) == 2:
        jy = f"20{jy}"

    return f"{jd}/{jm}/{jy}"


def date_string_2(dte):
    """Fonction qui renvoie la date au format 30/01/17
    :param dte: date
    :return: 30/01/17
    """
    jd = str(dte.day)
    if len(jd) == 1:
        jd = f"0{jd}"

    jm = str(dte.month)
    if len(jm) == 1:
        jm = f"0{jm}"

    jy = str(dte.year)
    jy = jy[-2:]

    return f"{jd}/{jm}/{jy}"


def lower_mois_string_avec_accents(dte):
    """Fonction qui renvoie le nom du mois avec accents
    :param dte: 17/01/2017
    :return: Janvier
    """
    return f"{MONTHS[dte.month].capitalize()}"


def long_date_string(dte):
    """Fonction qui renvoie le nom du mois (avec accents), avec l'année
    :param dte: 17/01/2017
    :return: Janvier 2017
    """
    return f"{MONTHS[dte.month].capitalize()} {dte.year}"


def long_date_string_s(dte):
    """Fonction qui renvoie le nom du mois en minuscule séparer par _, avec l'année
    :param dte: 17/02/2017
    :return: février_2017
    """
    return f"{MONTHS[dte.month]}_{dte.year}"


def long_date_string_upper_s(dte):
    """Fonction qui renvoie le nom du mois en majuscule séparer par _, avec l'année
    :param dte: 17/02/2017
    :return: FÉVRIER_2017
    """
    return f"{MONTHS[dte.month].upper()}_{dte.year}"


def long_date_string_d_upper(dte):
    """Fonction qui renvoie DE suivi du nom du mois (en majuscule), avec l'année
    :param dte: 17/02/2017
    :return: DE FÉVRIER 2017
    """
    m = dte.month
    prefix = "D'" if m in {4, 10} else "DE"

    return f"{prefix}{MONTHS[m].upper()} {dte.year}"


def short_date_string(dte):
    """Fonction qui renvoie le nom du mois en abrégé, avec l'année
    :param dte: 17/01/2017
    :return: Janv. 2017
    """
    return f"{TRUNC_MONTHS[dte.month].capitalize()} {dte.year}"


def days_of_month(dte):
    """Fonction qui retourne le nombre de jours dans le mois
    :param dte: 17/01/2017
    :return: 31
    """
    return calendar.monthrange(dte.year, dte.month)[1]


def next_month(dte):
    """Fonction qui retourne une date le mois d'après
    :param dte: 17/01/2017
    :return: 17/02/2017
    """
    return dte + relativedelta(months=+1)


def previous_month(dte):
    """Fonction qui retourne une date le mois d'avant
    :param dte: 17/01/2017
    :return: 17/02/2017
    """
    return dte + relativedelta(months=-1)


def between_month(dte):
    """Fonction qui retourne le betwwen du mois entier
    :param dte: 17/01/2017
    :return: between '2017-01-01' and '2017-01-31'
    """
    return (
        f"between '{datetime.date(dte.year, dte.month, 1)}' "
        f"and '{datetime.date(dte.year, dte.month, days_of_month(dte))}'"
    )


def between_periode(dte_d, dte_f):
    """Fonction qui retourne le betwwen de la période entière
    :param dte_d: 17/01/2017
    :param dte_f: 15/02/2017
    :return: between '2017-01-01' and '2017-02-28'
    """
    dte_01, dte_02 = controle_between(dte_d, dte_f)
    first_day = datetime.date(dte_01.year, dte_01.month, 1)
    last_day = datetime.date(dte_02.year, dte_02.month, days_of_month(dte_02))

    return f"between '{first_day}' and '{last_day}'"


def between_dates(dte_d, dte_f):
    """Fonction qui retourne le betwwen entre 2 dates
    :param dte_d: 17/01/2017
    :param dte_f: 15/02/2017
    :return: between '2017-01-17' and '2017-02-15'
    """
    dte_01, dte_02 = controle_between(dte_d, dte_f)
    first_day = datetime.date(dte_01.year, dte_01.month, dte_01.day)
    last_day = datetime.date(dte_02.year, dte_02.month, dte_02.day)

    return f"between '{first_day}' and '{last_day}'"


def controle_between(dte_d, dte_f):
    """Fonction qui renvoie l'ordre des dates reçues
    :param dte_d: date
    :param dte_f: date
    :return: date_plus_petite, date_plus_grande
    """
    if dte_d > dte_f:
        dte_d, dte_f = dte_f, dte_d

    return dte_d, dte_f


def dic_date(dte):
    return {
        "dte": dte,
        "dte_str_2": date_string_2(dte),
        "dte_str_4": date_string_4(dte),
        "short_dte_str": short_date_string(dte),
        "long_dte_str": long_date_string(dte),
        "long_date_string_s": long_date_string_s(dte),
        "long_dte_str_upper_s": long_date_string_upper_s(dte),
        "days_month": days_of_month(dte),
        "between": between_month(dte),
        "annee": dte.year,
        "mois": dte.month,
        "jour_d": dte.day,
        "jour_f": days_of_month(dte),
        f"sql_dte_first": f"'{datetime.date(dte.year, dte.month, 1)}'",
        f"sql_dte_last": f"'{datetime.date(dte.year, dte.month, days_of_month(dte))}'",
        f"periode": f"du {date_string_2(dte)} au "
        f"{date_string_2(datetime.date(dte.year, dte.month, days_of_month(dte)))}",
    }


def separate_month(dte_debut, dte_fin):
    """Retourne une liste des mois entre deux dates
    :param dte_debut: Date de début
    :param dte_fin: Date de fin
    :return: [
            {'periode': 'du 01/02/17 au 31/07/17',
            'between_periode': "between '2017-02-01' and '2017-07-31'",
            'nb_mois': 6
            },
            {
            'dte': datetime.date(2017, 1, 1),
            'dte_str_2': '01/01/17',
            'dte_str_4': '01/01/2017',
            'short_dte_str': 'Janv.2017'
            'long_dte_str': 'Janvier 2017',
            'days_month': 31,
            'between': "BETWEEN '2017-01-01' and '2017-01-31'",
            'annee': 2017,
            'mois': 1,
            'jour_f': 31,
            'sql_dte_first': "'2017-01-01'",
            'sql_dte_last': "'2017-01-31'",
            'periode': 'du 01/01/17 au 31/01/17'
            }, ....
        ]
    """
    dte_d, dte_f = controle_between(
        datetime.date(dte_debut.year, dte_debut.month, 1),
        datetime.date(dte_fin.year, dte_fin.month, 1),
    )
    delta = True
    nb_mois = 0
    list_month = [nb_mois]
    date_en_cours = dte_d

    while delta:
        nb_mois += 1
        list_month[0] = nb_mois
        list_month.append(dic_date(date_en_cours))
        date_en_cours += relativedelta(months=+1)

        if date_en_cours >= dte_f:
            delta = False

    if nb_mois > 1:
        nb_mois += 1
        list_month[0] = nb_mois
        list_month.append(dic_date(date_en_cours))

    bet = between_periode(dte_d, dte_f)
    periode = (
        f"du {date_string_2(dte_d)} au "
        f"{date_string_2(datetime.date(dte_f.year, dte_f.month, days_of_month(dte_f)))}"
    )

    list_month[0] = {
        "nb_mois": nb_mois,
        "between_periode": bet,
        "periode": periode,
        "dte_d": dte_d,
        "dte_f": datetime.date(dte_f.year, dte_f.month, days_of_month(dte_f)),
    }

    return list_month


def separate_month_a_date(dte_d, dte_f):
    """
    {'periode': 'du 01/02/17 au 31/07/17',
    'between_periode': "between '2017-02-01' and '2017-07-31'",
    'nb_mois': 6
    },
    """
    periode = separate_month(dte_d, dte_f)

    bet_d = f"{dte_d}"
    bet_f = f"{dte_f}"

    periode[0]["periode"] = (
        periode[0]["periode"][:3] + date_string_2(dte_d) + periode[0]["periode"][11:]
    )
    periode[0]["periode"] = periode[0]["periode"][:15] + date_string_2(dte_f)

    debut = periode[0]["between_periode"][:9]
    fin = periode[0]["between_periode"][19:]
    periode[0]["between_periode"] = debut + bet_d + fin

    debut = periode[0]["between_periode"][:26]
    fin = periode[0]["between_periode"][36:]
    periode[0]["between_periode"] = debut + bet_f + fin

    nb = 1

    periode[nb]["periode"] = (
        periode[nb]["periode"][:3] + date_string_2(dte_d) + periode[nb]["periode"][11:]
    )

    debut = periode[nb]["between"][:9]
    fin = periode[nb]["between"][19:]
    periode[nb]["between"] = debut + bet_d + fin

    nb = len(periode) - 1

    periode[nb]["periode"] = periode[nb]["periode"][:15] + date_string_2(dte_f)

    debut = periode[nb]["between"][:26]
    fin = periode[nb]["between"][36:]
    periode[nb]["between"] = debut + bet_f + fin

    return periode


def periode_dates_oracle(dte_d, dte_f):
    periode = separate_month(dte_d, dte_f)

    nb = len(periode) - 1

    list_periode = []

    for i, r in enumerate(periode):
        if i == 0:
            continue
        if i == 1:
            debut = dte_d
            if nb == 1:
                fin = dte_f
            else:
                fin = datetime.date(dte_d.year, dte_d.month, days_of_month(dte_d))
        elif i == nb:
            debut = dte_d if nb == 1 else datetime.date(dte_f.year, dte_f.month, 1)
            fin = dte_f
        else:
            dte = r["dte"]
            debut = datetime.date(dte.year, dte.month, 1)
            fin = datetime.date(dte.year, dte.month, days_of_month(dte))
        between = f"BETWEEN DATE '{debut}' AND DATE '{fin}'"
        list_periode.append(between)

    return list_periode


def date_mois_x_semaines_lundi(dte, nb_semaines):
    dtel = dte - datetime.timedelta(weeks=nb_semaines)
    jour = dtel.weekday()

    return dtel - datetime.timedelta(days=jour)


def first_day_week_of_month(dte_m):
    """Retourne la date du debut de la semaine du même mois
    :param dte_m: date
    :return: debut semaine
    """
    w = dte_m.weekday()
    month = dte_m.month
    year = dte_m.year
    dte = dte_m - datetime.timedelta(days=w)
    month_dte = dte.month

    return datetime.date(year, month, 1) if month != month_dte else dte


def first_day_string_week_of_month(dte_m):
    """Retourne la date au format string du debut de la semaine du même mois
    :param dte_m: date
    :return: debut semaine
    """
    return first_day_week_of_month(dte_m).isoformat()[:10]


def last_day_week_of_month(dte_m):
    """Retourne la date de fin de la semaine du même mois
    :param dte_m: date
    :return: debut semaine
    """
    w = dte_m.weekday()
    month = dte_m.month
    year = dte_m.year
    dtf = dte_m + datetime.timedelta(days=6 - w)
    month_dte = dtf.month

    if month != month_dte:
        dtf = datetime.date(year, month, days_of_month(dte_m))

    return dtf


def last_day_string_week_of_month(dte_m):
    """Retourne la date au format string de fin de la semaine du même mois
    :param dte_m: date
    :return: debut semaine
    """
    return last_day_week_of_month(dte_m).isoformat()[:10]


def complete_week_of_month(dte_m):
    """Retourne les jours de la semaine du même mois sinon le jour est None
    :param dte_m: date
    :return: [j1, j2, j3, j4, j5, j5, j7]
    """
    first_day = first_day_week_of_month(dte_m)
    last_day = last_day_week_of_month(dte_m)
    w_d = first_day.weekday()
    w_f = last_day.weekday()
    j = 0
    days = []

    for i in range(7):
        if i < w_d or i > w_f:
            days.append(None)
        else:
            days.append(first_day + datetime.timedelta(days=j))
            j += 1

    return days


def complete_string_week_of_month(dte_m):
    """Retourne une list de date au foramt string du même mois sinon None de la semaine
    :param dte_m: date
    :return: list de tous les jours
    """
    return [d.isoformat()[:10] if d else None for d in complete_week_of_month(dte_m)]


def week_of_month(dte_m):
    """Retourne les jours de la semaine du même mois sinon le jour est None
    :param dte_m: date
    :return: [j1, j2, j3, j4, j5, j5, j7]
    """
    first_day = first_day_week_of_month(dte_m)
    last_day = last_day_week_of_month(dte_m)
    w_d = first_day.weekday()
    w_f = last_day.weekday()
    j = 0
    days = []

    for i in range(7):
        if w_d <= i <= w_f:
            days.append(first_day + datetime.timedelta(days=j))
            j += 1

    return days


def string_week_of_month(dte_m):
    """Retourne une list de date au foramt string du même mois sinon None de la semaine
    :param dte_m: date
    :return: list de tous les jours
    """
    return [d.isoformat()[:10] if d else None for d in week_of_month(dte_m)]


def first_day_week(dte_m):
    """Retourne la date du debut de la semaine
    :param dte_m: date
    :return: debut semaine
    """
    return dte_m - datetime.timedelta(days=dte_m.weekday())


def first_day_string_week(dte_m):
    """Retourne la date au format string du debut de la semaine
    :param dte_m: date
    :return: debut semaine
    """
    return first_day_week(dte_m).isoformat()[:10]


def last_day_week(dte_m):
    """Retourne la date de fin de la semaine
    :param dte_m: date
    :return: debut semaine
    """
    return dte_m + datetime.timedelta(days=6 - dte_m.weekday())


def last_day_string_week(dte_m):
    """Retourne la date au format string de fin de la semaine
    :param dte_m: date
    :return: debut semaine
    """
    return last_day_week(dte_m).isoformat()[:10]


def complete_week(dte_m):
    """Retourne les jours de la semaine
    :param dte_m: date
    :return: [j1, j2, j3, j4, j5, j5, j7]
    """
    first_day = first_day_week(dte_m)
    return [first_day + datetime.timedelta(days=i) for i in range(7)]


def complete_string_week(dte_m):
    """Retourne une list de date au foramt string du même mois sinon None de la semaine
    :param dte_m: date
    :return: list de tous les jours
    """
    return [d.isoformat()[:10] for d in complete_week(dte_m)]


def nombre_semaine_entre_date(dte_d, dte_f):
    dte__d, dte__f = controle_between(dte_d, dte_f)
    return date_mois_x_semaines_lundi(dte__d, 0), date_mois_x_semaines_lundi(dte__f, 0)


def between_list_mois(dte_d, dte_f):
    dd, df = controle_between(dte_d, dte_f)
    delta = True
    nb_mois = 0
    date_en_cours = dd
    mois = [(dd.year, dd.month)]
    between_mois = []

    while delta:
        date_en_cours += relativedelta(months=+1)

        if date_en_cours <= df:
            nb_mois += 1
            mois.append((date_en_cours.year, date_en_cours.month))

        else:
            delta = False

    for i, m in enumerate(mois):
        if i == 0 and i == nb_mois:
            between_mois.append(between_dates(dd, df))
        elif i == 0:
            d = datetime.date(m[0], m[1], days_of_month(datetime.date(m[0], m[1], 1)))
            between_mois.append(between_dates(dd, d))
        elif i == nb_mois:
            d = datetime.date(m[0], m[1], 1)
            between_mois.append(between_dates(d, df))
        else:
            d = datetime.date(m[0], m[1], 1)
            between_mois.append(between_month(d))

    return between_mois


def between_list_semaine(dte_d, dte_f):
    dd, df = controle_between(dte_d, dte_f)
    j = 7 - dd.isoweekday()
    delta = True
    date_en_cours = dd
    between_semaine = []
    i = 0

    while delta:
        d = date_en_cours if i == 0 else date_en_cours - relativedelta(days=-1)
        if j != 1:
            date_en_cours += relativedelta(days=+j)
            j = 7
        else:
            date_en_cours += relativedelta(days=+j)

        if date_en_cours <= df:
            between_semaine.append(between_dates(d, date_en_cours))
        else:
            between_semaine.append(between_dates(d, df))
            delta = False

        i += 1

    return between_semaine


def date_adp(dte):
    try:
        return int(dte[:2]), int(dte[2:4]), int(dte[-4:])
    except:
        return None


def date_file_today():
    return datetime.datetime.date(datetime.datetime.now()).isoformat().replace("-", "_")


# Générateur de jours ouvrés français en python
def easter_date(year):
    """Calcule la date du jour de Pâques d'une année donnée
    Voir https://github.com/dateutil/dateutil/blob/master/dateutil/easter.py
        :return: datetime
    """
    a = year // 100
    b = year % 100
    c = (3 * (a + 25)) // 4
    d = (3 * (a + 25)) % 4
    e = (8 * (a + 11)) // 25
    f = (5 * a + b) % 19
    g = (19 * f + c - e) % 30
    h = (f + 11 * g) // 319
    j = (60 * (5 - d) + b) // 4
    k = (60 * (5 - d) + b) % 4
    m = (2 * j - k - g + h) % 7
    n = (g - h + m + 114) // 31
    p = (g - h + m + 114) % 31
    day = p + 1
    month = n
    return datetime.datetime(year, month, day)


@lru_cache(maxsize=256)
def is_holiday(the_date):
    """Vérifie si la date donnée est un jour férié
    :param the_date: datetime
    :return: bool
    """
    year = the_date.year
    easter = easter_date(year)
    days = {
        datetime.datetime(year, 1, 1),  # Premier de l'an
        easter + timedelta(days=1),  # Lundi de Pâques
        datetime.datetime(year, 5, 1),  # Fête du Travail
        datetime.datetime(year, 5, 8),  # Victoire de 1945
        easter + timedelta(days=39),  # Ascension
        easter + timedelta(days=49),  # Pentecôte
        datetime.datetime(year, 7, 14),  # Fête Nationale
        datetime.datetime(year, 8, 15),  # Assomption
        datetime.datetime(year, 11, 1),  # Toussaint
        datetime.datetime(year, 11, 11),  # Armistice 1918
        datetime.datetime(year, 12, 25),  # Noël
    }
    return the_date in days


def is_business_day(dte: datetime.datetime):
    """Vérifie si le jour est ouvré
    :param dte: date du jour à vérifier
    :return: True if business day
    """
    return dte.weekday() not in {5, 6}


def is_business_day_and_not_holiday(dte: datetime.datetime, days_off=(6, 7)):
    """Vérifie si le jour est ouvré
    :param dte: date du jour à vérifier
    :param days_off: jours non ouvrés de la semaine
    :return: True if business day
    """
    return not any([is_holiday(dte), dte.isoweekday() in days_off])


def business_days(date_from, date_to, days_off=(6, 7)):
    """Générateur retournant les jours ouvrés dans la période [date_from:date_to]
    :param date_from: Date de début de la période
    :param date_to: Date de fin de la période
    :param days_off: jours non ouvrés de la semaine
    :return: Générateur
    """
    while date_from <= date_to:
        # Un jour est ouvré s'il n'est ni férié, ni samedi, ni dimanche
        if not is_holiday(date_from) and date_from.isoweekday() not in days_off:
            yield date_from
        date_from += timedelta(days=1)


# Fin du générateur des jours fériés en français
def get_hours(hours: str):
    """Retourne une heure ou None
    :param hours: heure à vérifier
    :return: heure au format "03:00" ou None
    """
    hours_to_parse = str(hours).lower().replace("h", ":")

    if hours_to_parse is None or ":" not in hours_to_parse or "-" in hours_to_parse:
        return None

    left, right = hours_to_parse.split(":")

    list_hours = [left.isdigit(), right.isdigit()]

    if not all(list_hours) and len(list_hours) != 2:
        return None

    if int(left) > 24 or int(right) > 59:
        return None

    format_hours = hours_to_parse

    if hours_to_parse.startswith("0") and len(left) == 2:
        format_hours = hours_to_parse[1:]

    return format_hours


def yes_no_to_bool(value: str):
    """Retourne la valeur booleenne de type 0 ou 1
    :param value: valeur à parser
    :return: valeur booleene pour la table 0 ou 1
    """
    if value.lower() in {"oui", "yes", "y", "true"}:
        return 1

    if value.lower() in {"non", "no", "n", "false"}:
        return 0

    return None


def get_opening_day():
    """Retourne le type de jour de la date du jour
    :return: le texte adapté à la date du jour
    """
    dte = datetime.datetime.now()

    if not is_business_day(dte) and not is_holiday(dte):
        return "Weekend et jours fériés"

    if dte.hour < 9:
        return "Avant 9h00 en jours ouvrés"

    if dte.hour > 18:
        return "Après 18h00 en jours ouvrés"

    return "Jours et heures ouvrés"


def get_last_days_opening(
    dte: pendulum.datetime, days: int, days_off: tuple = (6, 7)
) -> pendulum.datetime:
    """Fonction qui retourne le premier jour travaillé
    avant ou après le nombre de jours défini
    et à partir du jour demandé.
        :param dte: date de départ
        :type dte: pendulum.datetime
        :param days: jours à reculer ou à avancer
        :type days: int
        :param days_off: jours non ouvrés de la semaine
        :type days_off: tupe ou autre itérateur acceptant la méthode in
        :return: date travaillée
        :rtype: pendulum.datetime.naive
    """
    sens = int(days / abs(days)) if days else 1
    k = i = int(sens * 1)
    days += i
    dte_after = dte

    while i != days:
        dte_after = dte.subtract(days=abs(i)) if sens < 0 else dte.add(days=i)

        if not is_business_day_and_not_holiday(dte_after.naive(), days_off=days_off):
            days += k

        i += int(sens * 1)

    return dte_after.naive()


def date_today():
    """
    Fonction qui renvoie la date du jour
    :return: Date du jour
    """
    return datetime.date.today()
