"""
FR : Export Excel générique : une ou plusieurs feuilles « titre, date d'édition, entêtes
     (éventuellement fusionnées), lignes alternées, mise en page », avec des points d'extension
     pour les cas particuliers (écriture spécifique des lignes, traitement après écriture,
     pied de page, zéros masqués).
     Chaque module d'export d'une app se réduit à ses colonnes, sa requête et un appel à
     `excel_list_export` (une feuille) ou `excel_sheets_export` (plusieurs feuilles).
EN : Generic Excel export (single or multi sheet) with extension hooks

Commentaire:

created at: 2026-10-11
created by: Paulo ALVES
"""
import io
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Sequence

from heron.loggers import LOGGER_EXPORT_EXCEL
from apps.core.functions.functions_excel_optimized import GenericExcelOptimized
from apps.core.excel_outputs.excel_writer import (
    columns_headers_writer,
    output_day_writer,
    sheet_formatting,
    titre_page_writer,
)

KO_MESSAGE = {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}
PAGE_NUMBERS_FOOTER = "&R&P/&N"

# writer(excel, sheet, columns, rows, f_lignes, f_lignes_odd) -> sauts de page (liste) ou None
RowsWriter = Callable[[GenericExcelOptimized, int, Sequence[dict], Iterable, list, list], Any]
# after_rows(excel, sheet, first_row, nb_rows)
AfterRows = Callable[[GenericExcelOptimized, int, int, int], None]


def ok_message(file_name: str) -> dict:
    """Message de succès standard des exports"""
    return {"OK": f"GENERATION DU FICHIER {file_name} TERMINEE AVEC SUCCES"}


def with_headers(columns: Sequence[dict], headers: dict[int, str]) -> list[dict]:
    """
    Copie des colonnes avec de nouvelles entêtes : `with_headers(COLUMNS, {3: "Mois M-1"})`.
    Évite de modifier les listes de colonnes partagées au niveau des modules.
    """
    return [
        {**column, "entete": headers[index]} if index in headers else dict(column)
        for index, column in enumerate(columns)
    ]


def month_headers(columns: Sequence[dict], indexes: Iterable[int], months: Iterable[str]) -> list[dict]:
    """Copie des colonnes dont les entêtes `indexes` reçoivent les libellés `months`, dans l'ordre"""
    return with_headers(columns, dict(zip(indexes, months)))


@dataclass
class SheetSpec:  # pylint: disable=R0903
    """Description d'une feuille : contenu, entêtes et mise en page"""

    name: str
    title: str
    columns: Sequence[dict] | Callable[[], Sequence[dict]]
    rows: Iterable | Callable[[], Iterable] = ()
    orientation: str = "portrait"
    repeat_row: tuple = (0, 5)
    fit_page: tuple = (1, 0)
    header_row: int = 3
    odd_color: str = "#D9D9D9"
    odd_first: bool = False
    merged_headers: Sequence[tuple] = ()
    hide_zero: bool = False
    write_headers: bool = True
    writer: RowsWriter | None = None
    after_rows: AfterRows | None = None
    footer: str | None = None
    extra_formatting: dict = field(default_factory=dict)


def write_alternate_rows(
    excel: GenericExcelOptimized, sheet: int, first_row: int, rows: Iterable, f_lignes: list, f_lignes_odd: list
) -> int:
    """
    Écrit les lignes à partir de first_row en alternant les formats selon la parité de la ligne
    (formats préparés une seule fois) ; renvoie le nombre de lignes écrites.
    """
    even, odd = excel.prepare_row_formats(f_lignes), excel.prepare_row_formats(f_lignes_odd)
    count = 0

    for count, row in enumerate(rows, 1):
        index = first_row + count - 1
        excel.write_rows_with_prepared_formats(sheet, index, 0, row, even if index % 2 == 0 else odd)

    return count


def _write_sheet(excel: GenericExcelOptimized, sheet: int, spec: SheetSpec) -> None:
    """Écrit une feuille complète selon sa description"""
    columns = spec.columns() if callable(spec.columns) else spec.columns

    if spec.hide_zero:
        excel.sheet_hide_zero(sheet - 1)

    titre_page_writer(excel, sheet, 0, 0, columns, spec.title)
    output_day_writer(excel, sheet, 1, 0)

    for first_col, last_col, text, style in spec.merged_headers:
        excel.write_merge_h(sheet, spec.header_row - 1, first_col, last_col, text, style)

    if spec.write_headers:
        columns_headers_writer(excel, sheet, spec.header_row, 0, columns)

    f_lignes = [dict_row.get("f_ligne") for dict_row in columns]
    f_lignes_odd = [{**dict_row.get("f_ligne"), "bg_color": spec.odd_color} for dict_row in columns]
    rows = spec.rows() if callable(spec.rows) else spec.rows
    first_row = spec.header_row + 1
    page_breaks = None

    if spec.writer is not None:
        page_breaks = spec.writer(excel, sheet, columns, rows, f_lignes, f_lignes_odd)
        nb_rows = 0
    else:
        formats = (f_lignes_odd, f_lignes) if spec.odd_first else (f_lignes, f_lignes_odd)
        nb_rows = write_alternate_rows(excel, sheet, first_row, rows, *formats)

    if spec.after_rows is not None:
        spec.after_rows(excel, sheet, first_row, nb_rows)

    if page_breaks:
        excel.excel_sheet(sheet).set_h_pagebreaks(page_breaks)

    if spec.footer:
        excel.excel_sheet(sheet).set_footer(spec.footer, {"margin": 0.1})

    sheet_formatting(
        excel,
        sheet,
        columns,
        {
            "sens": spec.orientation,
            "repeat_row": spec.repeat_row,
            "fit_page": spec.fit_page,
            **spec.extra_formatting,
        },
    )


def excel_sheets_export(
    file_io: io.BytesIO, file_name: str, sheets: Sequence[SheetSpec], in_memory: bool = False
) -> dict:
    """
    Génère un classeur d'une ou plusieurs feuilles décrites par des SheetSpec.
    Toute erreur (requête ou écriture) est journalisée et donne le retour KO.
    """
    excel = GenericExcelOptimized([file_io, [spec.name for spec in sheets]], in_memory=in_memory)

    try:
        for number, spec in enumerate(sheets, 1):
            _write_sheet(excel, number, spec)

    except Exception:
        LOGGER_EXPORT_EXCEL.exception(f"{file_name!r}")
        return dict(KO_MESSAGE)

    finally:
        excel.excel_close()

    return ok_message(file_name)


def excel_list_export(
    file_io: io.BytesIO,
    file_name: str,
    *,
    sheet_name: str,
    title: str,
    columns: Sequence[dict] | Callable[[], Sequence[dict]],
    rows: Iterable | Callable[[], Iterable] = (),
    in_memory: bool = False,
    **options: Any,
) -> dict:
    """
    Export d'une feuille : titre (ligne 0), date d'édition (ligne 1), entêtes fusionnées
    éventuelles (ligne header_row - 1), entêtes de colonnes (ligne header_row), lignes à partir
    de header_row + 1, puis mise en page.
    :param rows: lignes, ou fonction sans argument les renvoyant (évaluée dans le try)
    :param columns: colonnes, ou fonction les renvoyant (entêtes calculées)
    :param in_memory: classeur généré en mémoire
    :param options: options de SheetSpec (orientation, repeat_row, fit_page, header_row, odd_color,
                    odd_first, merged_headers, hide_zero, write_headers, writer, after_rows, footer)
    :return: {"OK": ...} ou {"KO": ...}

    Les options sont transmises à `SheetSpec` (clé ou valeur inconnue -> TypeError/AttributeError).
    """
    spec = SheetSpec(
        name=sheet_name, title=title, columns=columns, rows=rows, **options
    )
    return excel_sheets_export(file_io, file_name, [spec], in_memory=in_memory)
