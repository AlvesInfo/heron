# pylint: disable=W0702,W1203
"""Module d'export du fichier excel pour les centrales Mères

Commentaire:

created at: 2022-05-12
created by: Paulo ALVES

modified at: 2022-05-12
modified by: Paulo ALVES
"""

import io

from heron.loggers import EXPORT_EXCEL_LOGGER
from apps.core.functions.functions_excel import GenericExcel
from apps.core.excel_outputs.excel_writer import (
    titre_page_writer,
    output_day_writer,
    columns_headers_writer,
    sheet_formatting,
    rows_writer,
)
from apps.book.models import Society
from apps.articles.models import Article
from apps.articles.excel_outputs.output_excel_articles_columns import columns_list_articles


def get_clean_rows(third_party_num) -> iter:
    """Retourne les lignes à écrire"""
    return (
        [
            article.reference,
            article.ean_code,
            article.libelle,
            article.libelle_heron,
            article.brand,
            article.manufacturer,
            str(article.big_category),
            article.sub_familly,
            article.budget_code,
            article.famille_supplier,
            "" if not article.axe_bu else article.axe_bu.section,
            "" if not article.axe_prj else article.axe_prj.section,
            "" if not article.axe_pro else article.axe_pro.section,
            "" if not article.axe_pys else article.axe_pys.section,
            "" if not article.axe_rfa else article.axe_rfa.section,
            article.made_in,
            article.customs_code,
            "X" if article.new_article else "",
            article.comment,
        ]
        for article in Article.objects.filter(supplier_id=third_party_num)
    )


def excel_liste_articles(file_io: io.BytesIO, file_name: str, third_party_num: str) -> dict:
    """Fonction de génération du fichier de liste des Centrales Mère"""
    import time
    start = time.time()
    titre_list = file_name.split("_")
    titre = (
        " ".join(titre_list[:-4])
        + f" DU FOURNISSEUR : {str(Society.objects.get(third_party_num=third_party_num))}"
    )
    list_excel = [file_io, [titre[:30]]]
    excel = GenericExcel(list_excel)
    columns = columns_list_articles

    try:
        titre_page_writer(excel, 1, 0, 0, columns, titre)
        output_day_writer(excel, 1, 1, 0)
        columns_headers_writer(excel, 1, 3, 0, columns)
        f_lignes = [dict_row.get("f_ligne") for dict_row in columns]
        f_lignes_odd = [
            {**dict_row.get("f_ligne"), **{"bg_color": "#EBF1DE"}} for dict_row in columns
        ]
        rows_writer(excel, 1, 4, 0, get_clean_rows(third_party_num), f_lignes, f_lignes_odd)
        sheet_formatting(
            excel, 1, columns, {"sens": "landscape", "repeat_row": (0, 5), "fit_page": (1, 0)}
        )

    except:
        EXPORT_EXCEL_LOGGER.exception(f"{file_name!r}")
        return {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}

    finally:
        excel.excel_close()

    print(f"temps d'exécution : {(time.time()-start):02} s")
    EXPORT_EXCEL_LOGGER.exception(f"{file_name!r} - temps d'exécution : {(time.time()-start):02} s")
    return {"OK": f"GENERATION DU FICHIER {file_name} TERMINEE AVEC SUCCES"}
