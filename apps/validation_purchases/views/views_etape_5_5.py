from django.shortcuts import render


# CONTROLES ETAPE 5.5


def sage_controls_globals_purchases(request):
    """View de l'étape 5.5 des écrans de contrôles"""
    context = {"titre_table": "Contrôle Intégration Sage X3 - Achats"}
    return render(request, "validation_purchases/sage_controls.html", context=context)


def validation_purchases_export_globals(request):
    """View de l'étape 5.5 des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(request, "validation_purchases/sage_controls.html", context=context)


def sage_controls_details_purchases(request):
    """View de l'étape 5.5 A des écrans de contrôles"""
    context = {"titre_table": "Contrôle Intégration Sage X3 - Achats", "details": True}
    return render(request, "validation_purchases/sage_controls.html", context=context)


def validation_purchases_export_details(request):
    """View de l'étape 5.5 A des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(request, "validation_purchases/sage_controls.html", context=context)


def sage_controls_familles_purchases(request):
    """View de l'étape 5.5 B des écrans de contrôles"""
    context = {
        "titre_table": "Contrôle Intégration Sage X3 - Détails Achats",
        "details_familles": True,
        "details": True,
    }
    return render(request, "validation_purchases/sage_controls.html", context=context)


def validation_purchases_export_familles(request):
    """View de l'étape 5.5 B des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(request, "validation_purchases/sage_controls.html", context=context)
