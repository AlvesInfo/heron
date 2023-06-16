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

from psycopg2 import sql

from apps.core.functions.functions_setups import connection, settings
from apps.invoices.bin.invoives_nums import get_bicpar_num


def get_rows(fcy):
    """Fonction qui renvoie les lignes du fichier BICPAR à remplir
    :param fcy: société pour laquelle le fichier est à générer
    :return: generateur des lignes de la requête
    """
    sql_file = Path(settings.APPS_DIR) / "invoices/sql_files/sql_export_x3_sale_incoices.sql"

    with connection.cursor() as cursor, sql_file.open("r") as sql_file:
        # print(cursor.mogrify(sql.SQL(sql_file.read()), {"fcy": fcy}).decode())
        cursor.execute(sql.SQL(sql_file.read()), {"fcy": fcy})

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


def get_t(file, t_line):
    """Fonction qui écrit dans un fichier en place la ligne G
    :param file: fichier dans lequel il faut écrire
    :param t_line: ligne G à transformer et écrire
    :return: None
    """
    file.write(get_clean_line(t_line))


def get_d_analytique(file, d_line, idtlin=1):
    """Fonction qui écrit dans un fichier en place la ligne D en analytique
    :param file: fichier dans lequel il faut écrire
    :param d_line: ligne D à transformer et écrire
    :param idtlin: identifiant de la ligne
    :return: None
    """
    d_line[1] = idtlin
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
    return line_to_split[:16], line_to_split[16:30], line_to_split[30:]


def get_file(fcy):
    """Renvoie un fichier de type pathlib.PATH
    :param fcy: société
    :return: fichier de type pathlib.PATH
    """
    file_num = get_bicpar_num()

    file = Path(settings.EXPORT_DIR) / f"{fcy}_{file_num}.txt"
    print(file.name)
    return file.open("w", encoding="iso8859_1", errors="replace", newline="")


def write_bicpar(fcy, nb_fac=5000):
    """Fonction iter les lignes à écrire
    :param fcy: société pour laquelle le fichier est à générer
    :param nb_fac: nombre de factures max par fichiers
    :return: generateur des lignes de la requête
    """
    rows = get_rows(fcy)

    try:
        row = next(rows)
    except StopIteration:
        return

    file = get_file(fcy)
    invoice_number, *line_to_write, test_a = row
    invoice = invoice_number
    line_t, line_d, line_a = split_line(line_to_write)
    invoice_d = str(line_d)
    d_line = 1
    a_line = 1

    # On écrit les premières lignes, car nous avons enrobé rows de "iter"
    get_t(file=file, t_line=line_t)
    get_d_analytique(file=file, d_line=line_d)

    if test_a:
        get_a(file=file, a_line=line_a, idtlin=a_line)

    i = 1
    d_line += 1

    for row in rows:
        a_line += 1
        invoice_number, *line_to_write, test_a = row
        line_t, line_d, line_a = split_line(line_to_write)

        if invoice != invoice_number:
            invoice = invoice_number
            d_line = 1
            a_line = 1

            if i > nb_fac:
                if not file.closed:
                    file.close()

                file = get_file(fcy)
                i = 1

            get_t(file=file, t_line=line_t)

        if invoice_d != str(line_d):
            invoice_d = str(line_d)

            get_d_analytique(file=file, d_line=line_d, idtlin=d_line)

            d_line += 1
            a_line = 1

        if test_a:
            get_a(file=file, a_line=line_a, idtlin=a_line)

        i += 1

    if not file.closed:
        file.close()


if __name__ == "__main__":
    write_bicpar("AC00")
