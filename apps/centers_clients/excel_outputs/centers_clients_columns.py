# pylint: disable=C0302,R0903
"""Module pour la définition des colonnes excel pour le module centers_clients

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


columns_list_maisons = [
    {
        "entete": "CCT X3",
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
        "width": 12,
    },
    {
        "entete": "Centrale Fille",
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
        "width": 12,
    },
    {
        "entete": "Enseigne",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {**f_ligne, **{}},
        "width": 35,
    },
    {
        "entete": "Intitulé",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {**f_ligne, **{}},
        "width": 15,
    },
    {
        "entete": "Intitulé court",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#dce7f5",
            },
        },
        "f_ligne": {**f_ligne, **{}},
        "width": 15,
    },
    {
        "entete": "Catégorie Client",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#FFE699",
            },
        },
        "f_ligne": {**f_ligne, **{}},
        "width": 15,
    },
    {
        "entete": "Code maison",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#FFE699",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "center",
            },
        },
        "width": 12,
    },
    {
        "entete": "Code cosium",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#FFE699",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "center",
            },
        },
        "width": 12,
    },
    {
        "entete": "Code BBGR",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#FFE699",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "center",
            },
        },
        "width": 12,
    },
    {
        "entete": "Date d'ouveture",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#FFE699",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "center",
                "num_format": "dd/mm/yy",
            },
        },
        "width": 8,
    },
    {
        "entete": "Date de fermeture",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#FFE699",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "center",
                "num_format": "dd/mm/yy",
            },
        },
        "width": 8,
    },
    {
        "entete": "Date de signature contrat",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#FFE699",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "center",
                "num_format": "dd/mm/yy",
            },
        },
        "width": 8,
    },
    {
        "entete": "Date de signature de fin de contrat",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#FFE699",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "center",
                "num_format": "dd/mm/yy",
            },
        },
        "width": 8,
    },
    {
        "entete": "Date de renouvellement contrat",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#FFE699",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "center",
                "num_format": "dd/mm/yy",
            },
        },
        "width": 8,
    },
    {
        "entete": "Montant de droit d'entrée",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#C9C9C9",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "num_format": "#,##0.00",
            },
        },
        "width": 9,
    },
    {
        "entete": "montant de droit de renouvellement",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#C9C9C9",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "num_format": "#,##0.00",
            },
        },
        "width": 9,
    },
    {
        "entete": "Catégorie de prix",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#C9C9C9",
            },
        },
        "f_ligne": {**f_ligne, **{}},
        "width": 12,
    },
    {
        "entete": "Coéficient de vente générique",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#C9C9C9",
            },
        },
        "f_ligne": {**f_ligne, **{}},
        "width": 12,
    },
    {
        "entete": "Compte X3 par défaut au crédit",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#C9C9C9",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "center",
            },
        },
        "width": 12,
    },
    {
        "entete": "Compte X3 par défaut au débit",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#C9C9C9",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "center",
            },
        },
        "width": 12,
    },
    {
        "entete": "Compte X3 par défaut sur  provision",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#C9C9C9",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "center",
            },
        },
        "width": 12,
    },
    {
        "entete": "Compte X3 par défaut sur extourne",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#C9C9C9",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "center",
            },
        },
        "width": 12,
    },
    {
        "entete": "TVA X3 par défaut",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#C9C9C9",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "center",
            },
        },
        "width": 12,
    },
    {
        "entete": "Code plan sage",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#C9C9C9",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "center",
            },
        },
        "width": 12,
    },
    {
        "entete": "Fréquence des rfa",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#C9C9C9",
            },
        },
        "f_ligne": {**f_ligne, **{}},
        "width": 12,
    },
    {
        "entete": "Taux de remboursement rfa",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#C9C9C9",
            },
        },
        "f_ligne": {**f_ligne, **{}},
        "width": 12,
    },
    {
        "entete": "Nom pour l'identifiant Client",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#C9C9C9",
            },
        },
        "f_ligne": {**f_ligne, **{}},
        "width": 12,
    },
    {
        "entete": "Monaie",
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
        "width": 12,
    },
    {
        "entete": "Langue",
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
        "width": 12,
    },
    {
        "entete": "Tiers X3",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#C6E0B4",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "center",
            },
        },
        "width": 12,
    },
    {
        "entete": "Immeuble Tiers",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#C6E0B4",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "center",
            },
        },
        "width": 12,
    },
    {
        "entete": "Adresse Tiers",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#C6E0B4",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "center",
            },
        },
        "width": 12,
    },
    {
        "entete": "Code Postal Tiers",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#C6E0B4",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "center",
            },
        },
        "width": 12,
    },
    {
        "entete": "Ville Tiers",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#C6E0B4",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "center",
            },
        },
        "width": 12,
    },
    {
        "entete": "Pays Tiers",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#C6E0B4",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "center",
            },
        },
        "width": 12,
    },
    {
        "entete": "Téléphone Tiers",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#C6E0B4",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "center",
            },
        },
        "width": 12,
    },
    {
        "entete": "Mobile Tiers",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#C6E0B4",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "center",
            },
        },
        "width": 12,
    },
    {
        "entete": "e-mail Tiers",
        "f_entete": {
            **f_entetes,
            **{
                "bg_color": "#C6E0B4",
            },
        },
        "f_ligne": {
            **f_ligne,
            **{
                "align": "center",
            },
        },
        "width": 12,
    },
    {
        "entete": "Immeuble Client",
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
        "width": 12,
    },
    {
        "entete": "Adresse Client",
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
        "width": 12,
    },
    {
        "entete": "Code Postal Client",
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
        "width": 12,
    },
    {
        "entete": "Ville Client",
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
        "width": 12,
    },
    {
        "entete": "Pays Client",
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
        "width": 12,
    },
    {
        "entete": "Téléphone Client",
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
        "width": 12,
    },
    {
        "entete": "Mobile Client",
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
        "width": 12,
    },
    {
        "entete": "e-mail Client",
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
        "width": 12,
    },
]
