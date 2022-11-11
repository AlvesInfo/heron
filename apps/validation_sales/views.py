from django.shortcuts import render


# CONTROLES ETAPE 5

def sage_controls_globals_sales(request):
    """View de l'étape 5.5 des écrans de contrôles"""
    context = {"titre_table": "Contrôle Intégration Sage X3 - Ventes"}
    return render(request, "validation_sales/sage_controls.html", context=context)


def validation_sales_export_globals(request):
    """View de l'étape 5.5 des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(request, "validation_sales/sage_controls.html", context=context)


def sage_controls_details_sales(request):
    """View de l'étape 5.5 A des écrans de contrôles"""
    context = {"titre_table": "Contrôle Intégration Sage X3 - Ventes", "details": True}
    return render(request, "validation_sales/sage_controls.html", context=context)


def validation_sales_export_details(request):
    """View de l'étape 5.5 A des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(request, "validation_sales/sage_controls.html", context=context)


def sage_controls_familles_sales(request):
    """View de l'étape 5.5 B des écrans de contrôles"""
    context = {
        "titre_table": "Contrôle Intégration Sage X3 - Détails Ventes",
        "details_familles": True,
        "details": True,
    }
    return render(request, "validation_sales/sage_controls.html", context=context)


def validation_sales_export_familles(request):
    """View de l'étape 5.5 B des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(request, "validation_sales/sage_controls.html", context=context)


# CONTROLES ETAPE 5.3

def compare_turnover_sales(request):
    """View de l'étape 5.3 des écrans de contrôles"""
    context = {
        "titre_table": "Comparaison CA vs Ventes par maisons et famille de produit ",
    }
    return render(request, "validation_sales/compare_turnover_sales.html", context=context)


def compare_turnover_sales_export(request):
    """View de l'étape 5.3 des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(request, "validation_sales/compare_turnover_sales.html", context=context)


def compare_turnover_sales_details(request):
    """View de l'étape 5.3 A des écrans de contrôles"""
    context = {
        "titre_table": "Comparaison CA vs Ventes par maisons et famille de produit ",
        "details": True,
    }
    return render(request, "validation_sales/compare_turnover_sales.html", context=context)


def compare_turnover_sales_export_details(request):
    """View de l'étape 5.3 A des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(request, "validation_sales/compare_turnover_sales.html", context=context)


# CONTROLES ETAPE 5

def controls_cct_sales(request):
    """View de l'étape 5 des écrans de contrôles"""
    context = {
        "titre_table": "Contrôle refac M M-1 par CCT",
    }
    return render(request, "validation_sales/controls_cct_sales.html", context=context)


def controls_cct_sales_export(request):
    """View de l'étape 5 des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(request, "validation_sales/controls_cct_sales.html", context=context)


def controls_cct_sales_suppliers(request):
    """View de l'étape 5A des écrans de contrôles"""
    context = {
        "titre_table": f"Contrôle refac M M-1 Fournisseurs pour le CCT : {'AF001'}",
        "details": True
    }
    return render(request, "validation_sales/controls_cct_sales.html", context=context)


def controls_cct_sales_suppliers_export(request):
    """View de l'étape 5A des écrans de contrôles"""
    context = {"titre_table": "Export Excel Détails"}
    return render(request, "validation_sales/controls_cct_sales.html", context=context)


def controls_cct_sales_suppliers_details(request):
    """View de l'étape 5B des écrans de contrôles"""
    context = {
        "titre_table": f"Détails des factures Fournisseurs pour le CCT : {'AF001'}",
        "details": True
    }
    return render(request, "validation_sales/controls_cct_sales.html", context=context)


def controls_cct_sales_suppliers_details_export(request):
    """View de l'étape 5B des écrans de contrôles"""
    context = {"titre_table": "Export Excel Détails des factures Fournisseurs"}
    return render(request, "validation_sales/controls_cct_sales.html", context=context)
