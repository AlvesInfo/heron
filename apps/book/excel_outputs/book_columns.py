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
            "entete": "N° de tiers x3",
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
            "entete": "Name",
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
            "entete": "Intitulé court",
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
            "entete": "Raison sociale",
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
            "entete": "N° siret",
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
            "entete": "N° tva intracommunataire",
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
            "width": 18,
        },
        {
            "entete": "Vat number",
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
            "entete": "Catégorie client",
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
            "entete": "Catégorie fournisseur",
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
            "entete": "Code naf",
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
            "entete": "Conditions de paiement",
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
            "entete": "Régime de taxe",
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
            "entete": "Code comptable fournisseur",
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
            "entete": "Régime de taxe",
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
            "entete": "Code comptable client",
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
            "entete": "Tiers divers",
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
    ]

    columns_list_suppliers = [
        {
            "entete": "N° de tiers x3",
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
            "entete": "Name",
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
            "entete": "Intitulé court",
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
            "entete": "Raison sociale",
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
            "entete": "N° siret",
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
            "entete": "N° tva intracommunataire",
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
            "width": 18,
        },
        {
            "entete": "Vat number",
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
            "entete": "Catégorie client",
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
            "entete": "Catégorie fournisseur",
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
            "entete": "Code naf",
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
            "entete": "Conditions de paiement",
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
            "entete": "Régime de taxe",
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
            "entete": "Code comptable fournisseur",
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
            "entete": "Régime de taxe",
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
            "entete": "Code comptable client",
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
    ]

    columns_list_clients = [
        {
            "entete": "N° de tiers x3",
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
            "entete": "Name",
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
            "entete": "Intitulé court",
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
            "entete": "Raison sociale",
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
            "entete": "N° siret",
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
            "entete": "N° tva intracommunataire",
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
            "width": 18,
        },
        {
            "entete": "Vat number",
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
            "entete": "Catégorie client",
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
            "entete": "Catégorie fournisseur",
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
            "entete": "Code naf",
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
            "entete": "Conditions de paiement",
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
            "entete": "Régime de taxe",
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
            "entete": "Code comptable fournisseur",
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
            "entete": "Régime de taxe",
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
            "entete": "Code comptable client",
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
    ]
