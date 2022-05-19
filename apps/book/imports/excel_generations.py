# pylint: disable=
"""
FR : Module générique de donwload de fichiers
EN : Generic file download module

Commentaire:

created at: 2021-09-08
created by: Paulo ALVES

modified at: 2022-05-19
modified by: Paulo ALVES
"""

import io
import shutil
from pathlib import Path

from heron.settings import MEDIA_EXCEL_FILES_DIR
from apps.book.models import Society
from apps.book.excel_outputs.book_excel_societies_list import excel_liste_societies


def writre_book_files():
    files_to_write = [
        ("tiers", f"LISTING_DES_TIERS.xlsx"),
        ("clients", f"LISTING_DES_CLIENTS.xlsx"),
        ("suppliers", f"LISTING_DES_FOURNISSEURS.xlsx"),
    ]

    for society_type, file_name in files_to_write:
        file_io = io.BytesIO()
        excel_liste_societies(file_io, file_name, Society, society_type)
        file_io.seek(0)
        new_file = Path(MEDIA_EXCEL_FILES_DIR) / file_name

        with new_file.open('wb') as write_file:
            shutil.copyfileobj(file_io, write_file, -1)

        file_io.close()
