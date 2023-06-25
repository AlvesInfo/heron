# pylint: disable=E0401,R0914
"""
FR : Module d'export X3 des OD ANALYTIQUES
EN : X3 export module of ANALYTICAL ODs

Commentaire:

created at: 2023-06-18
created by: Paulo ALVES

modified at: 2023-06-18
modified by: Paulo ALVES
"""
from operator import itemgetter

from apps.core.functions.functions_setups import connection, settings
from apps.invoices.bin.invoives_nums import get_gaspar_num
from apps.invoices.bin.base_export_x3_functions import (
    get_rows,
    get_t,
    get_d_od_ana,
    get_a,
    split_line,
    get_file,
)


def write_odana(fcy, nb_fac=5000):
    """Fonction iter les lignes à écrire
    :param fcy: société pour laquelle le fichier est à générer
    :param nb_fac: nombre de factures max par fichiers
    :return: generateur des lignes de la requête
    """
    rows = get_rows(connection, settings.APPS_DIR, fcy, "sql_export_x3_odana_incoices")

    try:
        row = next(rows)
    except StopIteration:
        return

    file = get_file(settings.EXPORT_DIR, fcy, get_gaspar_num)
    invoice_number, *line_to_write, test_a = row
    invoice = invoice_number
    slicing_bispar = itemgetter(
        slice(0, 11, None),
        slice(11, 27, None),
        slice(27, len(line_to_write), None),
    )
    line_t, line_d, line_a = split_line(line_to_write, slicing_bispar)
    invoice_d = str(line_d[:13])
    d_line = 1
    a_line = 1

    # On écrit les premières lignes, car nous avons enrobé rows de "iter"
    get_t(file=file, t_line=line_t)
    get_d_od_ana(file=file, d_line=line_d)
    get_a(file=file, a_line=line_a, idtlin=a_line)

    i = 1
    d_line += 1

    for row in rows:
        a_line += 1
        invoice_number, *line_to_write, test_a = row
        line_t, line_d, line_a = split_line(line_to_write, slicing_bispar)

        if invoice != invoice_number:
            i += 1

            if i > nb_fac:
                if not file.closed:
                    file.close()

                file = get_file(settings.EXPORT_DIR, fcy, get_gaspar_num)
                i = 1

            get_t(file=file, t_line=line_t)
            invoice = invoice_number
            invoice_d = ""
            d_line = 1
            a_line = 1

        if invoice_d != str(line_d[:13]):
            invoice_d = str(line_d[:13])
            get_d_od_ana(file=file, d_line=line_d, idtlin=d_line)
            d_line += 1
            a_line = 1

        get_a(file=file, a_line=line_a, idtlin=a_line)

    if not file.closed:
        file.close()


if __name__ == "__main__":
    write_odana("AC00")
