"""
Module qui gère les fichiers Excel - Version optimisée

L'optimisation principale est le cache des formats pour éviter de recréer
un objet format à chaque cellule écrite.
"""
import hashlib
import json
from typing import Dict, List, Any, Optional, Tuple

import xlsxwriter

from apps.core.functions.functions_excel import GenericExcel


class GenericExcelOptimized(GenericExcel):
    """
    Version optimisée de GenericExcel avec cache des formats.

    L'amélioration principale est que les formats sont créés une seule fois
    et réutilisés, au lieu d'être recréés à chaque appel write_rows().
    """

    def __init__(self, excel_workbooks, in_memory=None):
        super().__init__(excel_workbooks, in_memory)
        self._format_cache: Dict[str, xlsxwriter.format.Format] = {}

    def _get_format_key(self, style: Optional[Dict[str, Any]]) -> str:
        """Génère une clé unique pour un style donné."""
        if style is None:
            return "__none__"
        # Conversion en JSON trié pour avoir une clé stable
        return hashlib.md5(
            json.dumps(style, sort_keys=True, default=str).encode()
        ).hexdigest()

    def _get_cached_format(
        self, style: Optional[Dict[str, Any]]
    ) -> Optional[xlsxwriter.format.Format]:
        """
        Retourne un format depuis le cache, ou le crée s'il n'existe pas.

        Args:
            style: Dictionnaire de style ou None

        Returns:
            Format xlsxwriter ou None si style est None
        """
        if style is None:
            return None

        key = self._get_format_key(style)

        if key not in self._format_cache:
            self._format_cache[key] = self.workbook.add_format(style)

        return self._format_cache[key]

    def prepare_row_formats(
        self, styles: List[Dict[str, Any]]
    ) -> List[Optional[xlsxwriter.format.Format]]:
        """
        Pré-crée tous les formats pour une ligne et les met en cache.

        Args:
            styles: Liste des styles pour chaque colonne

        Returns:
            Liste des formats xlsxwriter pré-créés
        """
        return [self._get_cached_format(style) for style in styles]

    def write_row(self, num_sheet, row, col, valeur, style=None):
        """
        Ecriture d'une seule cellule (version optimisée avec cache).
        """
        feuille = num_sheet - 1
        wsexcel = self.worksheets[feuille]
        f_m = self._get_cached_format(style)

        if f_m:
            wsexcel.write(row, col, valeur, f_m)
        else:
            wsexcel.write(row, col, valeur)

    def write_rows(self, num_sheet, row, col, valeurs, styles=None):
        """
        Ecriture de plusieurs cellules adjacentes (version optimisée).

        Les formats sont mis en cache et réutilisés au lieu d'être
        recréés à chaque appel.
        """
        nb_col = len(valeurs)
        feuille = num_sheet - 1
        wsexcel = self.worksheets[feuille]

        # Normaliser styles en liste
        if styles is None:
            styles_list = [None] * nb_col
        elif isinstance(styles, dict):
            styles_list = [styles] * nb_col
        elif len(styles) != nb_col:
            styles_list = [styles[0] if styles else None] * nb_col
        else:
            styles_list = styles

        # Écriture avec formats cachés
        for num, val in enumerate(valeurs):
            f_m = self._get_cached_format(styles_list[num])
            if f_m:
                wsexcel.write(row, col + num, val, f_m)
            else:
                wsexcel.write(row, col + num, val)

    def write_rows_with_prepared_formats(
        self,
        num_sheet: int,
        row: int,
        col: int,
        valeurs: Tuple,
        formats: List[Optional[xlsxwriter.format.Format]],
    ):
        """
        Écriture ultra-rapide avec des formats déjà préparés.

        Cette méthode évite complètement la recherche dans le cache
        car les formats sont passés directement.

        Args:
            num_sheet: Numéro de la feuille (commence à 1)
            row: Numéro de ligne
            col: Numéro de colonne de départ
            valeurs: Tuple des valeurs à écrire
            formats: Liste des formats pré-créés (via prepare_row_formats)
        """
        wsexcel = self.worksheets[num_sheet - 1]

        for num, val in enumerate(valeurs):
            fmt = formats[num] if num < len(formats) else None
            if fmt:
                wsexcel.write(row, col + num, val, fmt)
            else:
                wsexcel.write(row, col + num, val)

    def get_cache_stats(self) -> Dict[str, int]:
        """Retourne des statistiques sur le cache de formats."""
        return {
            "formats_cached": len(self._format_cache),
        }