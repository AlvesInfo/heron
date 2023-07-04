import pendulum
from django.db import connection
from django.shortcuts import render, redirect, reverse

from heron.loggers import LOGGER_VIEWS
from apps.core.functions.functions_postgresql import query_file_dict_cursor
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.validation_purchases.excel_outputs.excel_suppliers_m_vs_m1 import (
    excel_suppliers_m_vs_m1,
)
from apps.centers_clients.models import Maison


# CONTROLES ETAPE 5.A - Contrôle Fournisseurs M vs M-1


def suppliers_m_purchases(request, client):
    """View de l'étape 5.A - Contrôle Fournisseurs M vs M-1"""
    with connection.cursor() as cursor:
        sql_context_file = "apps/validation_purchases/sql_files/sql_suppliers_m_vs_m1.sql"
        elements = query_file_dict_cursor(
            cursor=cursor, file_path=sql_context_file, parmas_dict={"client": client}
        )
        mois_dict = {}
        mois = 4

        for _ in range(4):
            mois_dict[f"M{mois-1}"] = (
                (
                    pendulum.now()
                    .subtract(months=mois)
                    .start_of("month")
                    .format("MMMM YYYY", locale="fr")
                )
                .capitalize()
                .replace(" ", "<br>")
            )
            mois -= 1

        context = {
            "titre_table": "5.A - Contrôle Fournisseurs M vs M-1",
            "clients": elements,
            "cct_client": client,
            "maison": Maison.objects.get(cct=client),
            "mois_dict": mois_dict,
            "chevron_retour": reverse("validation_purchases:refac_cct_purchases"),
        }

    return render(request, "validation_purchases/suppliers_m_vs_m1.html", context=context)


def suppliers_m_purchases_export(request, client):
    """Export Excel du Contrôle Fournisseurs M vs M-1
    :param client: CCT client X3
    :param request: Request Django
    :return: response_file"""
    try:
        if request.method == "GET":
            today = pendulum.now()
            file_name = (
                f"CONTROLE_{client}_M_VS_M-1_"
                f"{today.format('Y_M_D')}{today.int_timestamp}.xlsx"
            )

            return response_file(
                excel_suppliers_m_vs_m1,
                file_name,
                CONTENT_TYPE_EXCEL,
                client,
            )

    except:
        LOGGER_VIEWS.exception("view : suppliers_m_purchases_export")

    return redirect(
        reverse("validation_purchases:suppliers_m_purchases", kwargs={"client": client})
    )
