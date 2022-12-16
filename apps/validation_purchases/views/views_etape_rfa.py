from django.shortcuts import render


# CONTROLES ETAPE RFA - CONTROLE RFA PAR CCT


def rfa_cct_invoices_purchases(request):
    """View de l'étape RFA PAR CCT des écrans de contrôles"""
    context = {"titre_table": "Controle des RFA par CCT- Achats"}
    return render(request, "validation_purchases/rfa_cct_invoices_suppliers.html", context=context)


def rfa_cct_invoices_purchases_export(request):
    """View de l'étape RFA PAR CCT des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(request, "validation_purchases/rfa_cct_invoices_suppliers.html", context=context)


# CONTROLES ETAPE RFA - CONTROLE RFA PAR PRJ


def rfa_prj_invoices_purchases(request):
    """View de l'étape RFA PAR PRJ des écrans de contrôles"""
    context = {"titre_table": "Controle des RFA par PRJ - Achats"}
    return render(request, "validation_purchases/rfa_prj_invoices_suppliers.html", context=context)


def rfa_prj_invoices_purchases_export(request):
    """View de l'étape RFA PAR PRJ des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(request, "validation_purchases/rfa_prj_invoices_suppliers.html", context=context)
