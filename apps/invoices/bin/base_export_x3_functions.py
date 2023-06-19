# pylint: disable=E0401
"""
FR : Module des fonctions qui renvoient les données cleannées des indicateurs des imports X3
EN : Module of functions that return clean data from X3 import indicators

Commentaire:

created at: 2023-06-17
created by: Paulo ALVES

modified at: 2023-06-17
modified by: Paulo ALVES
"""
from decimal import Decimal
from pathlib import Path

from psycopg2 import sql


def get_rows(connection, apps_dir, fcy, file_name):
    """Fonction qui renvoie les lignes du fichier d'export à remplir
    :param connection: connction django
    :param apps_dir: directory de l'application
    :param fcy: société pour laquelle le fichier est à générer
    :param file_name: nom du fichier à utiliser
    :return: generateur des lignes de la requête
    """
    sql_file = Path(apps_dir) / f"invoices/sql_files/{file_name}.sql"

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


def get_d_invoices(file, d_line, idtlin=1):
    """Fonction qui écrit dans un fichier en place la ligne D pour les bispa et bicpa
    :param file: fichier dans lequel il faut écrire
    :param d_line: ligne D à transformer et écrire
    :param idtlin: identifiant de la ligne
    :return: None
    """
    d_line[1] = idtlin
    file.write(get_clean_line(d_line))


def get_d_od_ana(file, d_line, idtlin=1):
    """Fonction qui écrit dans un fichier en place la ligne D pour les gaspar od analytique
    :param file: fichier dans lequel il faut écrire
    :param d_line: ligne D à transformer et écrire
    :param idtlin: identifiant de la ligne
    :return: None
    """
    d_line[1] = idtlin
    d_line[3] = idtlin
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


def get_e(file, e_line, idtlin=1):
    """Fonction qui écrit dans un fichier en place la ligne E des paiements
    :param file: fichier dans lequel il faut écrire
    :param e_line: ligne E à transformer et écrire
    :param idtlin: identifiant de la ligne
    :return: None
    """
    e_line[1] = idtlin
    file.write(get_clean_line(e_line))


def split_line(line_to_split, slicing_parts):
    """Fontion qui renvoie le split des lignes
    :param line_to_split: ligne complète de la requête à spliter
    :param slicing_parts: slice itemgetter
    :return: ligne_g, ligne_d, ligne_a, ....
    """
    return slicing_parts(line_to_split)


def get_file(export_dir, fcy, get_function_num):
    """Renvoie un fichier de type pathlib.PATH
    :param export_dir: directory des fichiers
    :param fcy: société
    :param get_function_num: fonction à uitiliser pour la numérotation des fichiers
    :return: fichier de type pathlib.PATH
    """
    file_num = get_function_num()

    file = Path(export_dir) / f"{fcy}_{file_num}.txt"
    print(file.name)
    return file.open("w", encoding="iso8859_1", errors="replace", newline="")
