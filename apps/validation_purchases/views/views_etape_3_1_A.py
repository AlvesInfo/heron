# pylint: disable=E1101,W1203
"""
FR : Views de contrôles étapes 3.1
EN : Views of controls steps 3.1

Commentaire:

created at: 2021-12-30
created by: Paulo ALVES

modified at: 2023-06-02
modified by: Paulo ALVES
"""
from django.shortcuts import render

from apps.edi.models import EdiImport

# CONTROLES ETAPE 3.1 A - CONTROLE ARTICLES/FAMILLES


def articles_families_invoices_purchases(request):
    """View de l'étape 3.1 A des écrans de contrôles"""
    context = {
        "titre_table": "3.1 A - Controle des familles par articles - Achats",
        "controles_exports": ""
    }
    return render(
        request, "validation_purchases/articles_families_invoices_suppliers.html", context=context
    )


def articles_families_invoices_purchases_export(request):
    """View de l'étape 3.1 A des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(
        request, "validation_purchases/articles_families_invoices_suppliers.html", context=context
    )


s = EdiImport.objects.annotate(

)