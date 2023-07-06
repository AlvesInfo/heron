import pendulum
from django.db import connection
from django.shortcuts import render, redirect, reverse

from heron.loggers import LOGGER_VIEWS
from apps.core.functions.functions_postgresql import query_file_dict_cursor
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.validation_purchases.excel_outputs.excel_familly_ca_cct import (
    excel_familly_ca_cct,
)

# CONTROLES ETAPE 5.3A - Contrôle CA Cosium / Ventes Héron par familles


def ca_familly_cct(request, client):
    """View de l'étape 5.3A - Contrôle CA Cosium / Ventes Héron par familles"""
    with connection.cursor() as cursor:
        sql_context_file = "apps/validation_purchases/sql_files/sql_ca_familly_cct.sql"
        elements = query_file_dict_cursor(
            cursor, file_path=sql_context_file, parmas_dict={"client": client}
        )
        mois_dict = {}
        mois = 1

        for _ in range(1, 3):
            mois_dict[f"M{mois-1}"] = (
                pendulum.now()
                .subtract(months=mois)
                .start_of("month")
                .format("MMMM YYYY", locale="fr")
            ).upper()
            mois += 1

        context = {
            "titre_table": "5.3A - Contrôle CA Cosium/Ventes Héron par familles",
            "clients": elements,
            "cct_client": client,
            "mois_dict": mois_dict,
            "chevron_retour": reverse("validation_purchases:ca_cct"),
        }

    return render(request, "validation_purchases/ca_familly_cct.html", context=context)


def ca_familly_cct_export(request, client):
    """Export Excel 5.3A - Contrôle CA Cosium / Ventes Héron par familles
    :param client: CCT client X3
    :param request: Request Django
    :return: response_file"""
    try:
        if request.method == "GET":
            today = pendulum.now()
            file_name = "CONTROLE_CA_CCT_" f"{today.format('Y_M_D')}{today.int_timestamp}.xlsx"

            return response_file(
                excel_familly_ca_cct,
                file_name,
                CONTENT_TYPE_EXCEL,
                client,
            )

    except:
        LOGGER_VIEWS.exception("view : ca_familly_cct_export")

    return redirect(reverse("validation_purchases:ca_familly_cct"))
