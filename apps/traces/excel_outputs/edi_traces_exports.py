"""Module d'export du fichier excel pour les lectures traces,
sortie Excel par pagination tel qu'à l'écran

Commentaire:

created at: 2022-12-21
created by: Paulo ALVES

modified at: 2022-12-21
modified by: Paulo ALVES
"""
import io

import html2text

from apps.core.excel_outputs.excel_writer import (
    f_entetes,
    f_ligne,
)
from apps.data_flux.models import Trace
from apps.core.excel_outputs.generic_list_export import excel_list_export

COLUMNS = [
    {
        "entete": "N° Trace",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "center",
            },
        },
        "width": 35,
    },
    {
        "entete": "Date Import",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{"align": "center", "num_format": "dd/mm/yyyy hh:mm:ss"},
        },
        "width": 18,
    },
    {
        "entete": "Fichier",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
        },
        "width": 60,
    },
    {
        "entete": "Traitement",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
        },
        "width": 46,
    },
    {
        "entete": "erreur",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
                "rotation": 90,
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "font_color": "red",
                "align": "center",
                "bold": True
            },
        },
        "width": 3,
    },
    {
        "entete": "Erreur",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "text_wrap": True,
            },
        },
        "width": 60,
    },
    {
        "entete": "Détails",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "text_wrap": True,
            },
        },
        "width": 60,
    },
]


def get_rows(start_index: int, end_index: int):
    """Renvoie les résultats de la requête nécessaire à l'export excel
    :param start_index: index initial slicing queryset
    :param end_index: index final slicing queryset
    :return: resultats de la requête
    """

    rows = Trace.objects.all().order_by("-created_at")[start_index:end_index]

    return [
        (
            str(row.uuid_identification),
            row.created_at.replace(tzinfo=None),
            row.file_name,
            row.trace_name,
            "X" if row.errors else "",
            str(html2text.html2text(row.comment or "")).replace("\n", ""),
            "\n".join(
                [
                    (
                        f"ligne n° : {r.num_line} - {r.designation} :"
                        f"\n    Champ en erreur: {e.attr_name}"
                        f"\n    Colonne du fichier: {e.file_column}"
                        f"\n    Erreur : {e.message}"
                        f"\n    Attendu : {e.data_expected}"
                        f"\n    Reçu : {e.data_received}"
                    )
                    for r in row.line_trace.all()
                    for e in r.error_line.all()]
            ),
        )
        for row in rows
    ]


def excel_edi_traces(file_io: io.BytesIO, file_name: str, start_index: int, end_index: int) -> dict:
    """Fonction de génération du fichier Excel des traces affichées à l'écran
    :param file_io: io.BytesIO file
    :param file_name: nom du fichier
    :param start_index: index initial slicing queryset
    :param end_index: index final slicing queryset
    :return: dict de résultat de l'export
    """
    titre_list = file_name.split("_")
    titre = " ".join(titre_list[:-3])
    get_clean_rows = get_rows(start_index, end_index)

    return excel_list_export(
        file_io,
        file_name,
        sheet_name=titre,
        title=titre,
        columns=COLUMNS,
        rows=get_clean_rows,
        orientation="landscape",
    )
