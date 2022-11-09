import pendulum
from django.db import connection
from django.shortcuts import render, redirect, reverse

from heron.loggers import LOGGER_VIEWS
from apps.core.functions.functions_postgresql import query_file_dict_cursor
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.validation_purchases.excel_outputs import (
    excel_integration_purchases,
)

# CONTROLES ETAPE 2 - CONTROLE INTEGRATION


def integration_purchases(requests):
    """View de l'étape 2 des écrans de contrôles
    Visualisation pour la validation des montants par fournisseurs par mois, intégrés ou saisis
    """
    sql_context_file = "apps/validation_purchases/sql_files/sql_integration_purchases.sql"
    with connection.cursor() as cursor:
        elements = query_file_dict_cursor(cursor, file_path=sql_context_file)
        context = {
            "titre_table": "Contrôle des Intégrations - Achats",
            "controles_exports": elements,
        }
    return render(requests, "validation_purchases/integration_purchases.html", context=context)


def integration_purchases_export(request):
    """
    Export Excel de la liste des Centrales Mères
    :param request: Request Django
    :return: response_file
    """

    try:
        if request.method == "GET":
            today = pendulum.now()
            file_name = (
                f"LISTING_DES_FACTURES_INTEGREES_{today.format('Y_M_D')}{today.int_timestamp}.xlsx"
            )

            return response_file(
                excel_integration_purchases,
                file_name,
                CONTENT_TYPE_EXCEL,
            )

    except:
        LOGGER_VIEWS.exception("view : integration_purchases_export")

    return redirect(reverse("validation_purchases:integration_purchases"))


# CONTROLES ETAPE 2.A - LISTING FACTURES


def integration_supplier_purchases(requests, third_party_num, big_category, month):
    """View de l'étape 2.A des écrans de contrôles"""
    sql_context_file = "apps/validation_purchases/sql_files/sql_integration_supplier_purchases.sql"
    with connection.cursor() as cursor:
        elements = query_file_dict_cursor(
            cursor,
            file_path=sql_context_file,
            parmas_dict={
                "third_party_num": third_party_num,
                "big_category": big_category,
                "month": month,
            },
        )
        titre_table = elements[0]
        mois = (
            pendulum.parse(titre_table.get("date_month").isoformat())
            .format("MMMM YYYY", locale="fr")
            .capitalize()
        )
        context = {
            "titre_table": f"Contrôle : {titre_table.get('supplier')}  - {mois}",
            "controles_exports": elements,
        }
    return render(requests, "validation_purchases/listing_invoices_suppliers.html", context=context)


def integration_supplier_purchases_export(requests):
    """View de l'étape 2.A des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(requests, "validation_purchases/listing_invoices_suppliers.html", context=context)


# CONTROLES ETAPE 2.B - DETAILS FACTURES


def details_purchases(requests, third_party_num, invoice_number):
    """View de l'étape 2.B des écrans de contrôles"""
    sql_context_file = "apps/validation_purchases/sql_files/sql_details_purchases.sql"
    with connection.cursor() as cursor:
        elements = query_file_dict_cursor(
            cursor,
            file_path=sql_context_file,
            parmas_dict={
                "third_party_num": third_party_num,
                "invoice_number": invoice_number,
            },
        )
        titre_table = elements[0]
        context = {
            "titre_table": (
                f"Contrôle : {titre_table.get('supplier')} - "
                f"Facture N°: {titre_table.get('invoice_number')}"
            ),
            "controles_exports": elements,
        }
    return render(requests, "validation_purchases/details_invoices_suppliers.html", context=context)


def details_purchases_export(requests):
    """View de l'étape 2.B des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(requests, "validation_purchases/details_invoices_suppliers.html", context=context)


# CONTROLES ETAPE 2.2 - FACTURES SANS CCT


def without_cct_purchases(requests):
    """View de l'étape 2.2 des écrans de contrôles"""
    context = {"titre_table": "Listing Factures sans CCT - Achats"}
    return render(
        requests, "validation_purchases/without_cct_invoices_suppliers.html", context=context
    )


def without_cct_purchases_export(requests):
    """View de l'étape 2.2 des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(
        requests, "validation_purchases/without_cct_invoices_suppliers.html", context=context
    )


# CONTROLES ETAPE 3.1 - CONTROLE FAMILLES


def families_invoices_purchases(requests):
    """View de l'étape 3.1 des écrans de contrôles"""
    context = {"titre_table": f"Controle des familles - Achats"}
    return render(
        requests, "validation_purchases/families_invoices_suppliers.html", context=context
    )


def families_invoices_purchases_export(requests):
    """View de l'étape 3.1 des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(
        requests, "validation_purchases/families_invoices_suppliers.html", context=context
    )


# CONTROLES ETAPE 3.1 A - CONTROLE ARTICLES/FAMILLES


def articles_families_invoices_purchases(requests):
    """View de l'étape 3.1 A des écrans de contrôles"""
    context = {"titre_table": f"Controle des familles par articles - Achats"}
    return render(
        requests, "validation_purchases/articles_families_invoices_suppliers.html", context=context
    )


def articles_families_invoices_purchases_export(requests):
    """View de l'étape 3.1 A des écrans de contrôles"""
    context = {"titre_table": "Export Excel"}
    return render(
        requests, "validation_purchases/articles_families_invoices_suppliers.html", context=context
    )


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
