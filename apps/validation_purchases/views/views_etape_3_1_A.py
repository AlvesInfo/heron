from django.shortcuts import render


# CONTROLES ETAPE 3.1 A - CONTROLE ARTICLES/FAMILLES


def articles_families_invoices_purchases(request):
    """View de l'étape 3.1 A des écrans de contrôles"""
    context = {"titre_table": "Controle des familles par articles - Achats"}
    return render(
        request, "validation_purchases/articles_families_invoices_suppliers.html", context=context
    )


def articles_families_invoices_purchases_export(request):
    """View de l'étape 3.1 A des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(
        request, "validation_purchases/articles_families_invoices_suppliers.html", context=context
    )
