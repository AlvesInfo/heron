from django.shortcuts import render


# CONTROLES ETAPE 5.1

def balance_suppliers_purchases(requests):
    """View de l'étape 5.5 des écrans de contrôles"""
    context = {"titre_table": "Contrôle Soldes Fournisseurs - Achats"}
    return render(requests, "validation_purchases/balance_suppliers.html", context=context)


def balance_suppliers_purchases_export(requests):
    """View de l'étape 5.5 des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(requests, "validation_purchases/balance_suppliers.html", context=context)


def invoices_suppliers_purchases(requests):
    """View de l'étape 5.5 B des écrans de contrôles"""
    context = {"titre_table": "Contrôle Factures Fournisseurs - Achats"}
    return render(requests, "validation_purchases/invoices_suppliers.html", context=context)


def invoices_suppliers_purchases_export(requests):
    """View de l'étape 5.5 B des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(requests, "validation_purchases/invoices_suppliers.html", context=context)


# CONTROLES ETAPE 5.5

def sage_controls_globals_purchases(requests):
    """View de l'étape 5.5 des écrans de contrôles"""
    context = {"titre_table": "Contrôle Intégration Sage X3 - Achats"}
    return render(requests, "validation_purchases/sage_controls.html", context=context)


def validation_purchases_export_globals(requests):
    """View de l'étape 5.5 des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(requests, "validation_purchases/sage_controls.html", context=context)


def sage_controls_details_purchases(requests):
    """View de l'étape 5.5 A des écrans de contrôles"""
    context = {"titre_table": "Contrôle Intégration Sage X3 - Achats", "details": True}
    return render(requests, "validation_purchases/sage_controls.html", context=context)


def validation_purchases_export_details(requests):
    """View de l'étape 5.5 A des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(requests, "validation_purchases/sage_controls.html", context=context)


def sage_controls_familles_purchases(requests):
    """View de l'étape 5.5 B des écrans de contrôles"""
    context = {
        "titre_table": "Contrôle Intégration Sage X3 - Détails Achats",
        "details_familles": True,
        "details": True,
    }
    return render(requests, "validation_purchases/sage_controls.html", context=context)


def validation_purchases_export_familles(requests):
    """View de l'étape 5.5 B des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(requests, "validation_purchases/sage_controls.html", context=context)
