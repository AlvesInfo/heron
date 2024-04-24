# pylint: disable=E0401,W0702,W1203,R0914
"""Module d'export du fichier excel pour les factures du tiers pas mois

Commentaire:

created at: 2022-05-12
created by: Paulo ALVES

modified at: 2022-05-12
modified by: Paulo ALVES
"""
import io
from typing import Dict
from pathlib import Path

import pendulum
from django.db import connection
from django.db.models import Q

from heron.settings.base import APPS_DIR
from heron.loggers import LOGGER_EXPORT_EXCEL
from apps.core.functions.functions_excel import GenericExcel
from apps.core.excel_outputs.excel_writer import (
    f_entetes,
    f_ligne,
    titre_page_writer,
    output_day_writer,
    columns_headers_writer,
    sheet_formatting,
    rows_writer,
)
from apps.edi.models import EdiValidation

COLUMNS = [
    {
        "entete": "Enseigne",
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
        "width": 15,
    },
    {
        "entete": "Pays",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "left",
            },
        },
        "width": 14,
    },
    {
        "entete": "CCT",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "left",
            },
        },
        "width": 51,
    },
    {
        "entete": "Type",
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
        "width": 10,
    },
    {
        "entete": "Date\nOuverture",
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
                "num_format": "dd/mm/yy",
            },
        },
        "width": 10,
    },
    {
        "entete": "Date\nFermeture",
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
                "num_format": "dd/mm/yy",
            },
        },
        "width": 10,
    },
    {
        "entete": "M-3",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "num_format": "#,##0.00",
            },
        },
        "width": 11,
    },
    {
        "entete": "M-2",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "num_format": "#,##0.00",
            },
        },
        "width": 11,
    },
    {
        "entete": "M-1",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "num_format": "#,##0.00",
            },
        },
        "width": 11,
    },
    {
        "entete": "M",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "num_format": "#,##0.00",
            },
        },
        "width": 11,
    },
    {
        "entete": "Variation\nM vs M-1",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "num_format": "#,##0.00",
            },
        },
        "width": 14,
    },
    {
        "entete": "Commentaire",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{},
        },
        "width": 50,
    },
]


def get_rows(file_path: Path, parmas_dict: Dict = None):
    """Renvoie les résultats de la requête nécessaire à l'export excel
    :param file_path: file pathlib.PATH
    :param parmas_dict: paramètre de la requête
    :return: resultats de la requête
    """
    parmas_dict = parmas_dict or {}

    with file_path.open("r") as sql_file, connection.cursor() as cursor:
        query = sql_file.read()
        # print(cursor.mogrify(query, parmas_dict).decode())
        # LOGGER_EXPORT_EXCEL.exception(f"{cursor.mogrify(query).decode()!r}")
        # print(query)
        cursor.execute(query, parmas_dict)
        return cursor.fetchall()


def excel_refac_cct(file_io: io.BytesIO, file_name: str, params_dict: Dict) -> Dict:
    """Fonction de génération du fichier de liste des Tiers, Fournisseurs, Clients"""
    titre = "5.0 - Contrôle Refac M M-1 par CCT"
    list_excel = [file_io, ["REFAC PAR CCT"]]
    excel = GenericExcel(list_excel, in_memory=True)
    file_path = Path(f"{str(APPS_DIR)}/validation_purchases/sql_files/sql_refac_cct.sql")
    get_clean_rows = [row[:-1] for row in get_rows(file_path, params_dict)]
    mois = -3
    start_date = pendulum.parse(
        EdiValidation.objects.filter(Q(final=False) | Q(final__isnull=True))
        .first()
        .billing_period.isoformat()
    )

    for i, column_dict in enumerate(COLUMNS, 1):
        if 6 < i < 11:
            column_dict["entete"] = (
                (start_date.add(months=mois).start_of("month").format("MMMM YYYY", locale="fr"))
                .capitalize()
                .replace(" ", "\n")
            )
            mois += 1

    try:
        titre_page_writer(excel, 1, 0, 0, COLUMNS, titre)
        output_day_writer(excel, 1, 1, 0)
        columns_headers_writer(excel, 1, 3, 0, COLUMNS)
        f_lignes = [dict_row.get("f_ligne") for dict_row in COLUMNS]
        f_lignes_odd = [
            {**dict_row.get("f_ligne"), **{"bg_color": "#D9D9D9"}} for dict_row in COLUMNS
        ]
        rows_writer(excel, 1, 4, 0, get_clean_rows, f_lignes, f_lignes_odd)

        # Pose des conditions pour avoir les cellules en rouge si la maison est fermée
        # et qu'il y a de la facturation dessus
        style = {"font_color": "#FFFFFF", "bg_color": "red", "bold": True}
        nb_rows = 5 + len(get_clean_rows)

        for i in range(5, nb_rows):
            excel.conditional_value(
                num_sheet=1,
                str_plage=f"F{i}",
                valeur=0,
                type_format="formula",
                criteria=f'=IF(J{i}=0,False,IF(F{i}="",False,True))',
                style=style,
            )
            excel.conditional_value(
                num_sheet=1,
                str_plage=f"J{i}",
                valeur=0,
                type_format="formula",
                criteria=f'=IF(J{i}=0,False,IF(F{i}="",False,True))',
                style=style,
            )
            excel.conditional_value(
                num_sheet=1,
                str_plage=f"A{i}",
                valeur=0,
                type_format="formula",
                criteria=f'=IF(J{i}=0,False,IF(D{i}="BLOCAGE",True,False))',
                style=style,
            )
            excel.conditional_value(
                num_sheet=1,
                str_plage=f"B{i}",
                valeur=0,
                type_format="formula",
                criteria=f'=IF(J{i}=0,False,IF(D{i}="BLOCAGE",True,False))',
                style=style,
            )
            excel.conditional_value(
                num_sheet=1,
                str_plage=f"C{i}",
                valeur=0,
                type_format="formula",
                criteria=f'=IF(J{i}=0,False,IF(D{i}="BLOCAGE",True,False))',
                style=style,
            )
            excel.conditional_value(
                num_sheet=1,
                str_plage=f"D{i}",
                valeur=0,
                type_format="formula",
                criteria=f'=IF(J{i}=0,False,IF(D{i}="BLOCAGE",True,False))',
                style=style,
            )
            excel.conditional_value(
                num_sheet=1,
                str_plage=f"J{i}",
                valeur=0,
                type_format="formula",
                criteria=f'=IF(J{i}=0,False,IF(D{i}="BLOCAGE",True,False))',
                style=style,
            )

        sheet_formatting(
            excel, 1, COLUMNS, {"sens": "portrait", "repeat_row": (0, 3), "fit_page": (1, 0)}
        )

    except:
        LOGGER_EXPORT_EXCEL.exception(f"{file_name!r}")
        return {"KO": "ERREUR DANS LA GENERATION DU FICHIER"}

    finally:
        excel.excel_close()

    return {"OK": f"GENERATION DU FICHIER {file_name} TERMINEE AVEC SUCCES"}
