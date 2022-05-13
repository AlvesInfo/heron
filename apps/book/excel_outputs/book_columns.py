# pylint: disable=C0302,R0903
"""Module pour la définition des colonnes excel pour le module book

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


class SocietiesColumns:
    """Class pour choix des colonnes en fonction du type des sociétés"""

    columns_list_tiers = [
        {
            "entete": "N° de tiers X3",
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
            "width": 14,
        },
        {
            "entete": "Nom du tiers",
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
            "entete": "Nom court",
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
            "entete": "Raison sociale",
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
            "entete": "N° Siret",
            "f_entete": {
                **f_entetes,
                **{
                    "bg_color": "#dce7f5",
                },
            },
            "f_ligne": {**f_ligne, **{}},
            "width": 14,
        },
        {
            "entete": "N° tva intracommunataire",
            "f_entete": {
                **f_entetes,
                **{
                    "bg_color": "#dce7f5",
                },
            },
            "f_ligne": {**f_ligne, **{}},
            "width": 18,
        },
        {
            "entete": "N° tva",
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
            "entete": "Code NAF",
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
            "width": 8,
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
            "width": 8,
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
                    "align": "center",
                },
            },
            "width": 12,
        },
        {
            "entete": "Réviseur",
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
            "width": 8,
        },
        {
            "entete": "Catégorie Client",
            "f_entete": {
                **f_entetes,
                **{
                    "bg_color": "#dce7f5",
                },
            },
            "f_ligne": {**f_ligne, **{}},
            "width": 11,
        },
        {
            "entete": "Catégorie Fournisseur",
            "f_entete": {
                **f_entetes,
                **{
                    "bg_color": "#dce7f5",
                },
            },
            "f_ligne": {**f_ligne, **{}},
            "width": 11,
        },
        {
            "entete": "Code budget",
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
            "width": 7,
        },
        {
            "entete": "Client",
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
            "entete": "Représentant",
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
            "entete": "Prospect",
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
            "entete": "Fournisseur",
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
            "entete": "Tiers Divers",
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
            "entete": "Prestataire",
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
            "entete": "Transporteur",
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
            "entete": "Donneur d'ordre",
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
            "entete": "Personne physique",
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
            "entete": "conditions de paiement",
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
            "entete": "régime de taxe",
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
            "width": 7,
        },
        {
            "entete": "Code comptable Founisseur",
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
            "entete": "Condition de paiement",
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
            "entete": "régime de taxe",
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
            "width": 7,
        },
        {
            "entete": "Code comptable Client",
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
    ]

    columns_list_suppliers = [
        {
            "entete": "N° de tiers X3",
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
            "width": 14,
        },
        {
            "entete": "Nom du tiers",
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
            "entete": "Nom court",
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
            "entete": "Raison sociale",
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
            "entete": "N° Siret",
            "f_entete": {
                **f_entetes,
                **{
                    "bg_color": "#dce7f5",
                },
            },
            "f_ligne": {**f_ligne, **{}},
            "width": 14,
        },
        {
            "entete": "N° tva intracommunataire",
            "f_entete": {
                **f_entetes,
                **{
                    "bg_color": "#dce7f5",
                },
            },
            "f_ligne": {**f_ligne, **{}},
            "width": 18,
        },
        {
            "entete": "N° tva",
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
            "entete": "Code NAF",
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
            "width": 8,
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
            "width": 8,
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
                    "align": "center",
                },
            },
            "width": 12,
        },
        {
            "entete": "Réviseur",
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
            "width": 8,
        },
        {
            "entete": "Catégorie Client",
            "f_entete": {
                **f_entetes,
                **{
                    "bg_color": "#dce7f5",
                },
            },
            "f_ligne": {**f_ligne, **{}},
            "width": 11,
        },
        {
            "entete": "Catégorie Fournisseur",
            "f_entete": {
                **f_entetes,
                **{
                    "bg_color": "#dce7f5",
                },
            },
            "f_ligne": {**f_ligne, **{}},
            "width": 11,
        },
        {
            "entete": "Code budget",
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
            "width": 7,
        },
        {
            "entete": "Fournisseur",
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
            "entete": "Nom Fournisseur pour l'edi",
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
            "entete": "Identifiant Fournisseur pour l'edi",
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
            "entete": "conditions de paiement",
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
            "entete": "régime de taxe",
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
            "width": 7,
        },
        {
            "entete": "Code comptable Founisseur",
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
            "entete": "Condition de paiement",
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
            "entete": "régime de taxe",
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
            "width": 7,
        },
        {
            "entete": "Code comptable Client",
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
    ]

    columns_list_clients = [
        {
            "entete": "N° de tiers X3",
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
            "width": 14,
        },
        {
            "entete": "Nom du tiers",
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
            "entete": "Nom court",
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
            "entete": "Raison sociale",
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
            "entete": "N° Siret",
            "f_entete": {
                **f_entetes,
                **{
                    "bg_color": "#dce7f5",
                },
            },
            "f_ligne": {**f_ligne, **{}},
            "width": 14,
        },
        {
            "entete": "N° tva intracommunataire",
            "f_entete": {
                **f_entetes,
                **{
                    "bg_color": "#dce7f5",
                },
            },
            "f_ligne": {**f_ligne, **{}},
            "width": 18,
        },
        {
            "entete": "N° tva",
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
            "entete": "Code NAF",
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
            "width": 8,
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
            "width": 8,
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
                    "align": "center",
                },
            },
            "width": 12,
        },
        {
            "entete": "Réviseur",
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
            "width": 8,
        },
        {
            "entete": "Catégorie Client",
            "f_entete": {
                **f_entetes,
                **{
                    "bg_color": "#dce7f5",
                },
            },
            "f_ligne": {**f_ligne, **{}},
            "width": 11,
        },
        {
            "entete": "Catégorie Fournisseur",
            "f_entete": {
                **f_entetes,
                **{
                    "bg_color": "#dce7f5",
                },
            },
            "f_ligne": {**f_ligne, **{}},
            "width": 11,
        },
        {
            "entete": "Code budget",
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
            "width": 7,
        },
        {
            "entete": "Client",
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
            "entete": "conditions de paiement",
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
            "entete": "régime de taxe",
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
            "width": 7,
        },
        {
            "entete": "Code comptable Founisseur",
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
            "entete": "Condition de paiement",
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
            "entete": "régime de taxe",
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
            "width": 7,
        },
        {
            "entete": "Code comptable Client",
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
    ]