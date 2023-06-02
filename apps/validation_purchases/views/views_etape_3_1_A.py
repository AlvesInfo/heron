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
from django.db import connection
from django.shortcuts import render
from django.db.models import CharField, Value, Case, When, Q, F

from apps.core.functions.functions_postgresql import query_file_yield_dict_cursor

from apps.edi.models import EdiImport

# CONTROLES ETAPE 3.1 A - CONTROLE ARTICLES/FAMILLES


def articles_families_invoices_purchases(request, third_party_num):
    """View de l'étape 3.1 A des écrans de contrôles"""

    parmas_dict = {"third_party_num": third_party_num} if third_party_num != "alls" else {}

    context = {"titre_table": "3.1 A - Controle des familles par articles - Achats"}

    with connection.cursor() as cursor:
        sql_context_file = "apps/validation_purchases/sql_files/sql_families_invoices.sql"
        context["controles_exports"] = (
            query_file_yield_dict_cursor(
                cursor, file_path=sql_context_file, parmas_dict=parmas_dict
            ),
        )

    return render(
        request,
        "validation_purchases/articles_families_invoices_suppliers.html",
        context=context,
    )


def articles_families_invoices_purchases_export(request):
    """View de l'étape 3.1 A des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(
        request, "validation_purchases/articles_families_invoices_suppliers.html", context=context
    )


s = EdiImport.objects.exclude(Q(valid=False) | Q(valid__isnull=True)).values(
    "third_party_num",
)
