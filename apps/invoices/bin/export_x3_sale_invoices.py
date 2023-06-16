# pylint: disable=E0401
"""
FR : Module d'export X3 des factures de vente
EN : Provisional insert module

Commentaire:

created at: 2023-06-16
created by: Paulo ALVES

modified at: 2023-06-16
modified by: Paulo ALVES
"""
from decimal import Decimal
from pathlib import Path
import csv

import pendulum

from apps.core.functions.functions_setups import connection, settings


def get_rows(fcy, dte_d, dte_f):
    """Fonction qui renvoie les lignes du fichier BICPAR à remplir
    :param fcy: société pour laquelle le fichier est à générer
    :param dte_d: date début période
    :param dte_f: date fin période
    :return: generateur des lignes de la requête
    """
    with connection.cursor() as cursor, Path("export_gaspa.sql").open("r") as sql_file:
        # print(
        #     cursor.mogrify(sql_file.read(), {"fcy": fcy, "dte_d": dte_d, "dte_f": dte_f}).decode()
        # )
        cursor.execute(sql_file.read(), {"fcy": fcy, "dte_d": dte_d, "dte_f": dte_f})

        yield from cursor.fetchall()


def get_clean_line(line_to_clean):
    """Function qui renvoie la ligne formatée à écrire
    :param line_to_clean: list de la ligne à cleaner
    :return: La ligne formatée
    """
    return (
        ";".join(
            str(value).replace(".", ",")
            if isinstance(value, (Decimal,))
            else str(value).replace("None", "").replace(";", ".")
            for value in line_to_clean
        )
        + "\r\n"
    )


def get_g(file, g_line):
    """Fonction qui écrit dans un fichier en place la ligne G
    :param file: fichier dans lequel il faut écrire
    :param g_line: ligne G à transformer et écrire
    :return: None
    """
    file.write(get_clean_line(g_line))


def get_d_social(file, d_line, idtlin=1):
    """Fonction qui écrit dans un fichier en place la ligne D en soial
    :param file: fichier dans lequel il faut écrire
    :param d_line: ligne D à transformer et écrire
    :param idtlin: identifiant de la ligne
    :return: None
    """
    d_line[1] = idtlin
    d_line[3] = idtlin
    file.write(get_clean_line(d_line))


def get_d_analytique(file, d_line, idtlin=1, fcy=1):
    """Fonction qui écrit dans un fichier en place la ligne D en analytique
    :param file: fichier dans lequel il faut écrire
    :param d_line: ligne D à transformer et écrire
    :param idtlin: identifiant de la ligne
    :param fcy: société pour laquelle le fichier est à générer
    :return: None
    """
    d_line[1] = idtlin
    d_line[2] = 2
    d_line[3] = idtlin
    d_line[6] = "AFR" if fcy == 1 else "ADE"
    d_line[7] = "FRA" if fcy == 1 else "GER"
    file.write(get_clean_line(d_line))


def get_a(file, a_line, idtlin=1):
    """Fonction qui écrit dans un fichier en place la ligne A d'analytique
    :param file: fichier dans lequel il faut écrire
    :param a_line: ligne A à transformer et écrire
    :param idtlin: identifiant de la ligne
    :return: None
    """
    a_line[1] = idtlin
    file.write(get_clean_line(a_line))


def split_line(line_to_split):
    """Fontion qui renvoie le split des lignes
    :param line_to_split:
    :return: ligne_g, ligne_d, ligne_a
    """
    return line_to_split[:11], line_to_split[11:28], line_to_split[28:]


def get_file(fcy, num_file="", file_month=None):
    """Renvoie un fichier de type pathlib.PATH
    :param fcy: société
    :param num_file: n° à ajouter au nom du fichier
    :param file_month: mois du fichier
    :return: fichier de type pathlib.PATH
    """
    num, _ = Numerotation.objects.get_or_create(type_num="gaspa_file")
    num.num += 1
    num.save()

    file = (
        Path(settings.EXPORT_DIR) / f"{FCY_DIR.get(fcy, '')}"
        f"/GASPAR_REP_{SOCIETES.get(fcy, 'INCON')}_{file_month}{num_file}{num.num:010}.txt"
    )
    print(file.name)
    return file.open("w", encoding="iso8859_1", errors="replace", newline="")


def write_bicpar(fcy, dte_d, dte_f, nb_fac, num_file=""):
    """Fonction iter les lignes à écrire
    :param fcy: société pour laquelle le fichier est à générer
    :param dte_d: date début période
    :param dte_f: date fin période
    :param nb_fac: nombre de factures max par fichiers
    :param num_file: n° à ajouter au nom du fichier
    :return: generateur des lignes de la requête
    """
    rows = get_rows(fcy, dte_d, dte_f)

    try:
        row = next(rows)
    except StopIteration:
        return

    file = get_file(fcy, num_file, f"{dte_d.month:0>2}")
    am_id, aml_id, *line_to_write, test_a = row
    line_g, line_d, line_a = split_line(line_to_write)
    d_lin, test_am, test_aml = 1, am_id, aml_id
    i = 1

    get_g(file=file, g_line=line_g)
    get_d_social(file=file, d_line=line_d, idtlin=d_lin)

    if test_a:
        get_d_analytique(file=file, d_line=line_d, idtlin=d_lin, fcy=fcy)
        get_a(file=file, a_line=line_a, idtlin=d_lin),

    for row in rows:
        am_id, aml_id, *line_to_write, test_a = row
        line_g, line_d, line_a = split_line(line_to_write)
        d_lin += 1

        if test_am != am_id:
            d_lin, test_am = 1, am_id
            i += 1

            if i > nb_fac:
                if not file.closed:
                    file.close()

                file = get_file(fcy, num_file, f"{dte_d.month:0>2}")
                i = 1

            get_g(file=file, g_line=line_g)

        get_d_social(file=file, d_line=line_d, idtlin=d_lin)

        if test_a:
            get_d_analytique(file=file, d_line=line_d, idtlin=d_lin, fcy=fcy)
            get_a(file=file, a_line=line_a, idtlin=d_lin),

    if not file.closed:
        file.close()


if __name__ == "__main__":
    societe = 1
    par_jour = False
    nb_in_file = 5000
    months = [
        # pendulum.date(2019, 1, 1),
        # pendulum.date(2019, 2, 1),
        # pendulum.date(2019, 3, 1),
        # pendulum.date(2019, 4, 1),
        # pendulum.date(2019, 5, 1),
        # pendulum.date(2019, 6, 1),
        # pendulum.date(2019, 7, 1),
        # pendulum.date(2019, 8, 1),
        # pendulum.date(2019, 9, 1),
        # pendulum.date(2019, 10, 1),
        # pendulum.date(2019, 11, 1),
        # pendulum.date(2019, 12, 1),
        # pendulum.date(2020, 1, 1),
        # pendulum.date(2020, 2, 1),
        # pendulum.date(2020, 3, 1),
        # pendulum.date(2020, 4, 1),
        # pendulum.date(2020, 5, 1),
        # pendulum.date(2020, 6, 1),
        # pendulum.date(2020, 7, 1),
        # pendulum.date(2020, 8, 1),
        # pendulum.date(2020, 9, 1),
        # pendulum.date(2020, 10, 1),
        # pendulum.date(2020, 11, 1),
        # pendulum.date(2020, 12, 1),
        # pendulum.date(2021, 1, 1),
        # pendulum.date(2021, 2, 1),
        # pendulum.date(2021, 3, 1),
        # pendulum.date(2021, 4, 1),
        # pendulum.date(2021, 5, 1),
        # pendulum.date(2021, 6, 1),
        # pendulum.date(2021, 7, 1),
        # pendulum.date(2021, 8, 1),
        # pendulum.date(2021, 9, 1),
        # pendulum.date(2021, 10, 1),
        # pendulum.date(2021, 11, 1),
        # pendulum.date(2021, 12, 1),
        # pendulum.date(2022, 1, 1),
        # pendulum.date(2022, 2, 1),
        # pendulum.date(2022, 3, 1),
        # pendulum.date(2022, 4, 1),
        # pendulum.date(2022, 5, 1),
        # pendulum.date(2022, 6, 1),
        # pendulum.date(2022, 7, 1),
        # pendulum.date(2022, 8, 1),
        # pendulum.date(2022, 9, 1),
        # pendulum.date(2022, 10, 1),
        # pendulum.date(2022, 11, 1),
        # pendulum.date(2022, 12, 1),
    ]

    for month in months:
        last_day = month.days_in_month
        range_day = last_day + 1
        annee = month.year
        mois = month.month

        if par_jour:
            for j in range(1, range_day):
                dted = pendulum.date(annee, mois, j)
                dtef = pendulum.date(annee, mois, j)
                date_file = dted.format("_YYYY_MM_DD_", locale="fr")
                write_gaspa(societe, dted, dtef, nb_in_file, date_file)
        else:
            dted = pendulum.date(annee, mois, 1)
            dtef = pendulum.date(annee, mois, last_day)
            date_file = dted.format("_YYYY_MM_DD_", locale="fr") + dtef.format(
                "_YYYY_MM_DD_", locale="fr"
            )
            write_gaspa(societe, dted, dtef, nb_in_file, date_file)