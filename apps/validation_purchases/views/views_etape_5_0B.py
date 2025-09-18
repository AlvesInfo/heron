import pendulum
from django.db import connection
from django.shortcuts import render, redirect, reverse

from heron.loggers import LOGGER_VIEWS
from apps.core.functions.functions_postgresql import query_file_dict_cursor
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.validation_purchases.excel_outputs.excel_third_suppliers_m_vs_m1 import (
    excel_third_suppliers_m_vs_m1,
)


# CONTROLES ETAPE 5.B - Contrôle Details Fournisseurs M vs M-1


def third_suppliers_m_purchases(request, client, third_party_num):
    """View de l'étape 5.B - Contrôle Details Fournisseurs M vs M-1"""
    with connection.cursor() as cursor:
        sql_context_file = "apps/validation_purchases/sql_files/sql_third_suppliers_m_vs_m1.sql"
        elements = query_file_dict_cursor(
            cursor,
            file_path=sql_context_file,
            parmas_dict={"client": client, "third_party_num": third_party_num},
        )

        context = {
            "titre_table": "5.B - Contrôle Details Fournisseurs M vs M-1",
            "clients": elements,
            "cct_client": client,
            "third_party_num": third_party_num,
            "chevron_retour": reverse(
                "validation_purchases:suppliers_m_purchases", kwargs={"client": client}
            ),
        }

    return render(request, "validation_purchases/third_suppliers_m_vs_m1.html", context=context)


def third_suppliers_m_purchases_export(request, client, third_party_num):
    """Export Excel du Contrôle Fournisseurs M vs M-1
    :param client: CCT X3 Client
    :param third_party_num: Tiers fournisseur
    :param request: Request Django
    :return: response_file"""
    try:
        if request.method == "GET":
            today = pendulum.now()
            file_name = (
                f"CONTROLE_{client}_{third_party_num}_M_VS_M-1_"
                f"{today.format('Y_M_D')}{today.int_timestamp}.xlsx"
            )

            return response_file(
                excel_third_suppliers_m_vs_m1,
                file_name,
                CONTENT_TYPE_EXCEL,
                client,
                third_party_num,
            )

    except:
        LOGGER_VIEWS.exception("view : refac_cct_purchases_export")

    return redirect(reverse("validation_purchases:refac_cct_purchases"))
