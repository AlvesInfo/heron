# pylint: disable=E0401,E1101
"""Module d'export du fichier excel des ventes Héron non finalisées (version optimisée)

Commentaire:

created at: 2023-06-20
created by: Paulo ALVES

modified at: 2025-01-14
modified by: Optimized version
"""

import io
from pathlib import Path
from typing import List, Dict, Any, Tuple, Iterator

from psycopg2 import sql

from heron.loggers import LOGGER_EXPORT_EXCEL
from apps.core.functions.functions_setups import settings, connection
from apps.core.functions.functions_excel_optimized import GenericExcelOptimized
from apps.core.excel_outputs.excel_writer import (
    titre_page_writer,
    output_day_writer,
    columns_headers_writer,
    sheet_formatting,
)
from apps.validation_purchases.excel_outputs.columns_excel import columns_purchases_heron


class PurchasesExcelExporter:
    """Classe pour gérer l'export Excel des ventes non finalisées"""

    SHEET_NAME = "ACHATS HERON"
    TITLE = "ACHATS HERON A FINALISER"
    START_ROW = 4
    SHEET_NUMBER = 1
    ODD_ROW_COLOR = "#D9D9D9"

    def __init__(self, file_io: io.BytesIO, file_name: str):
        self.file_io = file_io
        self.file_name = file_name
        self.columns = columns_purchases_heron
        self._excel: GenericExcelOptimized | None = None
        self._formats_even = None
        self._formats_odd = None
        self._f_lignes: List[Dict[str, Any]] = []
        self._f_lignes_odd: List[Dict[str, Any]] = []

    def _init_formats(self) -> None:
        """Initialise et pré-crée les formats de lignes une seule fois"""
        self._f_lignes = [col.get("f_ligne") for col in self.columns]
        self._f_lignes_odd = [
            {**col.get("f_ligne", {}), "bg_color": self.ODD_ROW_COLOR}
            for col in self.columns
        ]
        # Pré-création des formats xlsxwriter (cache)
        self._formats_even = self._excel.prepare_row_formats(self._f_lignes)
        self._formats_odd = self._excel.prepare_row_formats(self._f_lignes_odd)

    def _get_prepared_formats(self, row_num: int):
        """Retourne les formats pré-créés selon la parité de la ligne"""
        return self._formats_even if row_num % 2 == 0 else self._formats_odd

    @staticmethod
    def _fetch_rows() -> Iterator[Tuple]:
        """Retourne un itérateur sur les lignes à écrire (optimisé mémoire)"""
        sql_file_path = (
            Path(settings.APPS_DIR) / "validation_purchases/sql_files/purchases_not_final.sql"
        )

        with (
            connection.cursor() as cursor,
            sql_file_path.open("r", encoding="utf-8") as sql_file,
        ):
            cursor.execute(sql.SQL(sql_file.read()))
            # Utilisation de fetchmany pour les grands datasets
            while True:
                rows = cursor.fetchmany(1000)
                if not rows:
                    break
                yield from rows

    def _write_rows(self, rows: Iterator[Tuple]) -> None:
        """Écrit les lignes de données dans la feuille Excel (version ultra-rapide)"""
        for idx, row in enumerate(rows, start=self.START_ROW):
            self._excel.write_rows_with_prepared_formats(
                self.SHEET_NUMBER, idx, 0, row, self._get_prepared_formats(idx)
            )

    def _setup_sheet(self) -> None:
        """Configure l'en-tête et le formatage de la feuille"""
        titre_page_writer(
            self._excel, self.SHEET_NUMBER, 0, 0, self.columns, self.TITLE
        )
        output_day_writer(self._excel, self.SHEET_NUMBER, 1, 0)
        columns_headers_writer(self._excel, self.SHEET_NUMBER, 3, 0, self.columns)

    def _finalize_sheet(self) -> None:
        """Applique le formatage final à la feuille"""
        sheet_formatting(
            self._excel,
            self.SHEET_NUMBER,
            self.columns,
            {"sens": "portrait", "repeat_row": (0, 5), "fit_page": (1, 0)},
        )

    def export(self) -> Dict[str, str]:
        """
        Génère le fichier Excel des ventes non finalisées.

        Returns:
            Dict avec clé 'OK' ou 'KO' selon le résultat
        """
        self._excel = GenericExcelOptimized([self.file_io, [self.SHEET_NAME]], in_memory=True)
        self._init_formats()

        try:
            self._setup_sheet()
            self._write_rows(self._fetch_rows())
            self._finalize_sheet()

            return {
                "OK": f"GENERATION DU FICHIER {self.file_name} TERMINEE AVEC SUCCES"
            }

        except Exception as exc:
            LOGGER_EXPORT_EXCEL.exception(f"{self.file_name!r}: {exc}")
            return {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}

        finally:
            if self._excel:
                self._excel.excel_close()


def excel_heron_purchases_not_final(file_io: io.BytesIO, file_name: str) -> Dict[str, str]:
    """
    Fonction de génération du fichier des ventes Héron non finalisées.

    Interface compatible avec l'ancienne version.

    Args:
        file_io: Buffer pour écrire le fichier Excel
        file_name: Nom du fichier pour les logs

    Returns:
        Dict avec clé 'OK' ou 'KO' selon le résultat
    """
    exporter = PurchasesExcelExporter(file_io, file_name)
    return exporter.export()
