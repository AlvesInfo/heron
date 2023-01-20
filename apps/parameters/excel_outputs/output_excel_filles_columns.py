# pylint: disable=C0302,R0903
"""Module pour la définition des colonnes excel pour le module Centrales Mères

Commentaire:

created at: 2022-05-12
created by: Paulo ALVES

modified at: 2022-05-12
modified by: Paulo ALVES
"""

from apps.core.excel_outputs.excel_writer import (
    f_entetes,
    f_ligne,
)


columns_list_categories = [
    {
        "entete": "Classement",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#CCC0DA",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "center",
            },
        },
        "width": 11,
    },
    {
        "entete": "Code",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#CCC0DA",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "center",
            },
        },
        "width": 11,
    },
    {
        "entete": "Nom",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#CCC0DA",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "left",
            },
        },
        "width": 25,
    },   {
        "entete": "Classement",
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
        "width": 11,
    },
    {
        "entete": "Code",
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
        "width": 11,
    },
    {
        "entete": "Nom",
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
        "width": 25,
    },
]
