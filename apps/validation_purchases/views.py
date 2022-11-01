from django.shortcuts import render


# CONTROLES ETAPE 2 - CONTROLE INTEGRATION

def integrations_purchases(requests):
    """View de l'étape 2 des écrans de contrôles"""
    context = {"titre_table": "Contrôle des Intégrations - Achats"}
    return render(requests, "validation_purchases/integrations_purchases.html", context=context)


def integrations_purchases_export(requests):
    """View de l'étape 2 des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(requests, "validation_purchases/integrations_purchases.html", context=context)


# CONTROLES ETAPE 2.A - LISTING FACTURES

def listing_purchases(requests):
    """View de l'étape 2.A des écrans de contrôles"""
    context = {"titre_table": "Listing des Factures Intégrées - Achats"}
    return render(requests, "validation_purchases/listing_invoices_suppliers.html", context=context)


def listing_purchases_export(requests):
    """View de l'étape 2.A des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(requests, "validation_purchases/listing_invoices_suppliers.html", context=context)


# CONTROLES ETAPE 2.B - DETAILS FACTURES

def details_purchases(requests):
    """View de l'étape 2.B des écrans de contrôles"""
    context = {"titre_table": f"Détails Facture {'Fournisseur'} - {'N° Facture'} - Achats"}
    return render(requests, "validation_purchases/details_invoices_suppliers.html", context=context)


def details_purchases_export(requests):
    """View de l'étape 2.B des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(requests, "validation_purchases/details_invoices_suppliers.html", context=context)


# CONTROLES ETAPE 2.2 - FACTURES SANS CCT

def without_cct_purchases(requests):
    """View de l'étape 2.2 des écrans de contrôles"""
    context = {"titre_table": f"Listing Factures sans CCT - Achats"}
    return render(requests, "validation_purchases/without_cct_invoices_suppliers.html", context=context)


def without_cct_purchases_export(requests):
    """View de l'étape 2.2 des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(requests, "validation_purchases/without_cct_invoices_suppliers.html", context=context)


# CONTROLES ETAPE 3.1 - CONTROLE FAMILLES

def families_invoices_purchases(requests):
    """View de l'étape 3.1 des écrans de contrôles"""
    context = {"titre_table": f"Controle des familles - Achats"}
    return render(requests, "validation_purchases/families_invoices_suppliers.html", context=context)


def families_invoices_purchases_export(requests):
    """View de l'étape 3.1 des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(requests, "validation_purchases/families_invoices_suppliers.html", context=context)


# CONTROLES ETAPE 3.1 A - CONTROLE ARTICLES/FAMILLES

def articles_families_invoices_purchases(requests):
    """View de l'étape 3.1 A des écrans de contrôles"""
    context = {"titre_table": f"Controle des familles par articles - Achats"}
    return render(requests, "validation_purchases/articles_families_invoices_suppliers.html", context=context)


def articles_families_invoices_purchases_export(requests):
    """View de l'étape 3.1 A des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(requests, "validation_purchases/articles_families_invoices_suppliers.html", context=context)


# CONTROLES ETAPE RFA - CONTROLE RFA PAR CCT

def rfa_cct_invoices_purchases(requests):
    """View de l'étape RFA PAR CCT des écrans de contrôles"""
    context = {"titre_table": f"Controle des RFA par CCT- Achats"}
    return render(requests, "validation_purchases/rfa_cct_invoices_suppliers.html", context=context)


def rfa_cct_invoices_purchases_export(requests):
    """View de l'étape RFA PAR CCT des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(requests, "validation_purchases/rfa_cct_invoices_suppliers.html", context=context)


# CONTROLES ETAPE RFA - CONTROLE RFA PAR PRJ

def rfa_prj_invoices_purchases(requests):
    """View de l'étape RFA PAR PRJ des écrans de contrôles"""
    context = {"titre_table": f"Controle des RFA par PRJ - Achats"}
    return render(requests, "validation_purchases/rfa_prj_invoices_suppliers.html", context=context)


def rfa_prj_invoices_purchases_export(requests):
    """View de l'étape RFA PAR PRJ des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(requests, "validation_purchases/rfa_prj_invoices_suppliers.html", context=context)


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

