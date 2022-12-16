from django.shortcuts import render


# CONTROLES ETAPE 5.1


def balance_suppliers_purchases(request):
    """View de l'étape 5.5 des écrans de contrôles"""
    context = {"titre_table": "Contrôle Soldes Fournisseurs - Achats"}
    return render(request, "validation_purchases/balance_suppliers.html", context=context)


def balance_suppliers_purchases_export(request):
    """View de l'étape 5.5 des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(request, "validation_purchases/balance_suppliers.html", context=context)


def invoices_suppliers_purchases(request):
    """View de l'étape 5.5 B des écrans de contrôles"""
    context = {"titre_table": "Contrôle Factures Fournisseurs - Achats"}
    return render(request, "validation_purchases/invoices_suppliers.html", context=context)


def invoices_suppliers_purchases_export(request):
    """View de l'étape 5.5 B des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(request, "validation_purchases/invoices_suppliers.html", context=context)
