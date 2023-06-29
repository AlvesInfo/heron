# pylint: disable=E0401,R0914
"""
FR : Module d'export X3 des factures d'achat
EN : X3 export module for purchase invoices

Commentaire:

created at: 2023-06-17
created by: Paulo ALVES

modified at: 2023-06-17
modified by: Paulo ALVES
"""
from operator import itemgetter

from apps.core.functions.functions_setups import connections, settings
from apps.invoices.bin.invoives_nums import get_bispa_num
from apps.invoices.bin.base_export_x3_functions import (
    get_rows,
    get_t,
    get_d_invoices,
    get_a,
    get_e,
    split_line,
    get_file,
)


def write_bispar(fcy, nb_fac=5000):
    """Fonction iter les lignes à écrire
    :param fcy: société pour laquelle le fichier est à générer
    :param nb_fac: nombre de factures max par fichiers
    :return: generateur des lignes de la requête
    """
    connection = connections["heron"]
    rows = get_rows(connection, settings.APPS_DIR, fcy, "sql_export_x3_purchase_gdaud_incoices")

    try:
        row = next(rows)
    except StopIteration:
        return

    file = get_file(settings.EXPORT_DIR, fcy, get_bispa_num)
    invoice_number, *line_to_write, test_a = row
    invoice = invoice_number
    slicing_bispar = itemgetter(
        slice(0, 17, None),
        slice(17, 30, None),
        slice(30, 44, None),
        slice(44, len(line_to_write), None),
    )
    line_t, line_d, line_a, line_e = split_line(line_to_write, slicing_bispar)
    invoice_d = str(line_d)
    invoice_e = line_e
    d_line = 1
    a_line = 1

    # On écrit les premières lignes, car nous avons enrobé rows de "iter"
    get_t(file=file, t_line=line_t)
    get_d_invoices(file=file, d_line=line_d)

    if test_a:
        get_a(file=file, a_line=line_a, idtlin=a_line)

    i = 1
    d_line += 1

    for row in rows:
        a_line += 1
        invoice_number, *line_to_write, test_a = row
        line_t, line_d, line_a, line_e = split_line(line_to_write, slicing_bispar)

        if invoice != invoice_number:
            i += 1

            if i > nb_fac:
                # On écrit le E de la dernière ligne
                get_e(file, invoice_e)

                if not file.closed:
                    file.close()

                file = get_file(settings.EXPORT_DIR, fcy, get_bispa_num)
                i = 1

            else:
                get_e(file, invoice_e)

            get_t(file=file, t_line=line_t)
            invoice = invoice_number
            invoice_e = line_e
            invoice_d = ""
            d_line = 1
            a_line = 1

        if invoice_d != str(line_d):
            invoice_d = str(line_d)

            get_d_invoices(file=file, d_line=line_d, idtlin=d_line)
            d_line += 1
            a_line = 1

        if test_a:
            get_a(file=file, a_line=line_a, idtlin=a_line)

    # On écrit le E de la dernière ligne
    get_e(file, invoice_e)

    if not file.closed:
        file.close()


if __name__ == "__main__":
    write_bispar("GA00")
