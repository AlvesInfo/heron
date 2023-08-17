# pylint: disable=E0401
"""
FR : View des lancements des exports X3
EN : View of exports X3 launches

Commentaire:

created at: 2023-08-17
created by: Paulo ALVES

modified at: 2023-08-17
modified by: Paulo ALVES
"""
from django.db.models import Q
from django.shortcuts import render, redirect, reverse
from django.contrib import messages
from celery import group

from heron import celery_app
from apps.invoices.models import Invoice, SaleInvoice
from heron.loggers import LOGGER_INVOICES, LOGGER_X3


def generate_exports_X3(request):
    """
    View de lancement des exports X3, (GASPAR - OD, BICPAR - Clients, BISPAR - Fournisseurs)
    :param request:
    :return:
    """
    titre_table = (
        "Génération des fichiers pour imports X3 <br>"
        "(GASPAR - OD, BICPAR - Clients, BISPAR - Fournisseurs)"
    )

    context = {
        "margin_table": 50,
        "titre_table": titre_table,
        "export": True,
    }

    if not any(
        [
            SaleInvoice.objects.filter(Q(export__isnull=True) | Q(export=False)).exists(),
            Invoice.objects.filter(Q(export__isnull=True) | Q(export=False)).exists(),
        ]
    ):
        context["export"] = False
        request.session["level"] = 50
        messages.add_message(request, 50, "Il n'y a rien a exporter")

        return render(request, "invoices/export_x3_invoices.html", context=context)

    if request.method == "POST":
        # On lance la génération des factures de vente et d'achat
        user_pk = request.user.pk
        tasks_list = [
            celery_app.signature(
                "launch_export_x3",
                kwargs={
                    "export_type": "odana",
                    "centrale": "AC00",
                    "user_pk": str(user_pk)},
            ),
            celery_app.signature(
                "launch_export_x3",
                kwargs={
                    "export_type": "sale",
                    "centrale": "AC00",
                    "user_pk": str(user_pk)},
            ),
            celery_app.signature(
                "launch_export_x3",
                kwargs={
                    "export_type": "purchase",
                    "centrale": "AC00",
                    "user_pk": str(user_pk)},
            ),
            celery_app.signature(
                "launch_export_x3",
                kwargs={
                    "export_type": "gdaud",
                    "centrale": "GA00",
                    "user_pk": str(user_pk)},
            ),
        ]
        result = group(*tasks_list)().get(3600)
        print(result)
        LOGGER_X3.warning(str(result), str(all(result)))

    return render(request, "invoices/export_x3_invoices.html", context=context)
