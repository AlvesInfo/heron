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
from pathlib import Path

from django.db.models import Q
from django.shortcuts import render
from django.contrib import messages
from celery import group

from heron import celery_app
from heron.loggers import LOGGER_X3
from apps.core.functions.functions_setups import settings
from apps.invoices.models import Invoice, SaleInvoice, ExportX3
from apps.invoices.bin.invoives_nums import get_gaspar_num
from apps.invoices.bin.invoives_nums import get_bispar_num
from apps.invoices.bin.invoives_nums import get_bicpar_num
from apps.edi.models import EdiValidation


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
        file_name_odana = f"AC00_{str(get_gaspar_num())}.txt"
        file_name_sale = f"AC00_{str(get_bicpar_num())}.txt"
        file_name_purchase = f"AC00_{str(get_bispar_num())}.txt"
        file_name_gdaud = f"GA00_{str(get_bispar_num())}.txt"
        tasks_list = [
            celery_app.signature(
                "launch_export_x3",
                kwargs={
                    "export_type": "odana",
                    "centrale": "AC00",
                    "file_name": file_name_odana,
                    "user_pk": str(user_pk),
                    "nb_fac": 50_000,
                },
            ),
            celery_app.signature(
                "launch_export_x3",
                kwargs={
                    "export_type": "sale",
                    "centrale": "AC00",
                    "file_name": file_name_sale,
                    "user_pk": str(user_pk),
                    "nb_fac": 50_000,
                },
            ),
            celery_app.signature(
                "launch_export_x3",
                kwargs={
                    "export_type": "purchase",
                    "centrale": "AC00",
                    "file_name": file_name_purchase,
                    "user_pk": str(user_pk),
                    "nb_fac": 50_000,
                },
            ),
            celery_app.signature(
                "launch_export_x3",
                kwargs={
                    "export_type": "gdaud",
                    "centrale": "GA00",
                    "file_name": file_name_gdaud,
                    "user_pk": str(user_pk),
                    "nb_fac": 50_000,
                },
            ),
        ]
        result_list = group(*tasks_list)().get(3600)

        file_odana = Path(settings.EXPORT_DIR) / file_name_odana
        file_sale = Path(settings.EXPORT_DIR) / file_name_sale
        file_purchase = Path(settings.EXPORT_DIR) / file_name_purchase
        file_gdaud = Path(settings.EXPORT_DIR) / file_name_gdaud

        # On check si il y a eu des erreurs
        if all([*[result_list], False]):
            # Si on n'a pas d'erreur, on enregistre les fichiers dans la table
            edi_validations = EdiValidation.objects.filter(
                Q(final=False) | Q(final__isnull=True)
            ).first()
            export_x3, _ = ExportX3.objects.get_or_create(uuid_edi_validation=edi_validations)
            export_x3.odana = file_name_odana
            export_x3.sale_file = file_name_sale
            export_x3.purchase_file = file_name_purchase
            export_x3.ga_file = file_name_gdaud
            export_x3.save()
            request.session["level"] = 20
            messages.add_message(request, 20, "Les fichiers d'import X3 ont bien été générés !")

        else:
            # En cas d'erreur, on supprime les fichiers générés
            if file_odana.is_file():
                file_odana.unlink()

            if file_sale.is_file():
                file_sale.unlink()

            if file_purchase.is_file():
                file_purchase.unlink()

            if file_gdaud.is_file():
                file_gdaud.unlink()

            request.session["level"] = 50
            messages.add_message(
                request, 50, "Une erreur c'est produite veuillez consulter les traces !"
            )

        LOGGER_X3.warning(f"{str(result_list)}, {str(all(result_list))}, {str(type(result_list))}")

    return render(request, "invoices/export_x3_invoices.html", context=context)
