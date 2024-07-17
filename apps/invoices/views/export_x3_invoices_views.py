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
from zipfile import ZipFile
from pathlib import Path

from django.db import transaction
from django.db.models import Q
from django.shortcuts import render, HttpResponse, redirect, reverse
from django.contrib import messages
from celery import group
from django.views.generic import ListView

from heron import celery_app
from heron.loggers import LOGGER_X3, LOGGER_VIEWS
from apps.core.bin.content_types import CONTENT_TYPE_FILE
from apps.core.functions.functions_setups import settings
from apps.invoices.models import Invoice, SaleInvoice, ExportX3
from apps.invoices.bin.invoives_nums import (
    get_gaspar_num,
    get_bispar_num,
    get_bispard_num,
    get_bicpar_num,
    get_zip_num,
)
from apps.edi.models import EdiValidation


@transaction.atomic
def generate_exports_X3(request):
    """
    View de lancement des exports X3, (GASPAR - OD, BICPAR - Clients, BISPAR - Fournisseurs)
    :param request:
    :return:
    """
    titre_table = (
        "Génération des fichiers pour imports X3 <br>"
        "(GASPAR - OD, BICPAR - Clients, BISPARD - Fournisseurs)"
    )

    context = {
        "margin_table": 50,
        "titre_table": titre_table,
        "export": True,
    }
    sales = SaleInvoice.objects.filter(Q(export__isnull=True) | Q(export=False))
    purchases = Invoice.objects.filter(Q(export__isnull=True) | Q(export=False))

    if not any([sales.exists(), purchases.exists()]):
        context["export"] = False
        request.session["level"] = 50
        messages.add_message(request, 50, "Il n'y a rien a exporter")

        return render(request, "invoices/export_x3_invoices.html", context=context)

    if request.method == "POST":
        # On lance la génération des factures de vente et d'achat
        user_pk = request.user.pk
        file_name_odana = f"AC00_{str(get_gaspar_num())}.txt"
        file_name_sale = f"AC00_{str(get_bicpar_num())}.txt"
        file_name_purchase = f"AC00_{str(get_bispard_num())}.txt"
        file_name_gdaud = f"GA00_{str(get_bispar_num())}.txt"
        file_name_zip = f"AC00_{str(get_zip_num())}.zip"
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

        files_list = [
            (Path(settings.EXPORT_DIR) / file_name_odana),
            (Path(settings.EXPORT_DIR) / file_name_sale),
            (Path(settings.EXPORT_DIR) / file_name_purchase),
            (Path(settings.EXPORT_DIR) / file_name_gdaud),
        ]

        # On check si il y a eu des erreurs
        if all(result_list):
            # Si on n'a pas d'erreur, on enregistre les fichiers dans la table
            edi_validations = EdiValidation.objects.filter(
                Q(final=False) | Q(final__isnull=True)
            ).first()
            export_x3, _ = ExportX3.objects.get_or_create(uuid_edi_validation=edi_validations)

            with ZipFile((Path(settings.EXPORT_DIR) / file_name_zip), "w") as zip_file:
                for file in files_list:
                    if file.is_file():
                        zip_file.write(file, file.name)

            export_x3.odana_file = file_name_odana
            export_x3.sale_file = file_name_sale
            export_x3.purchase_file = file_name_purchase
            export_x3.ga_file = file_name_gdaud
            export_x3.alls_zip_file = file_name_zip
            export_x3.save()
            sales.update(export=True)
            purchases.update(export=True)
            request.session["level"] = 20
            messages.add_message(request, 20, "Les fichiers d'export X3 ont bien été générés !")

        else:
            # En cas d'erreur, on supprime les fichiers générés
            for file in files_list:
                if file.is_file():
                    file.unlink()

            request.session["level"] = 50
            messages.add_message(
                request, 50, "Une erreur c'est produite veuillez consulter les traces !"
            )

        LOGGER_X3.warning(f"{str(result_list)}, {str(all(result_list))}, {str(type(result_list))}")

    return render(request, "invoices/export_x3_invoices.html", context=context)


class ExportX3Files(ListView):
    """View pour download des fihiers X3 générés"""

    model = ExportX3
    context_object_name = "exports"
    template_name = "invoices/export_x3_list.html"
    extra_context = {"titre_table": "Fichiers X3"}


def get_export_x3_file(request, file_name):
    """Récupération des fichiers d'export X3 produits
    :param request: Request Django
    :param file_name: Paramètres get du nom du fichier à télécharger
    :return: response_file
    """
    try:
        if request.method == "GET":
            file_path = Path(settings.EXPORT_DIR) / file_name
            content_type = CONTENT_TYPE_FILE.get(file_path.suffix, "text/plain")
            response = HttpResponse(file_path.open("rb").read(), content_type=content_type)
            response["Content-Disposition"] = f"attachment; filename={file_name}"
            return response

    except:
        LOGGER_VIEWS.exception("view : get_export_x3_file")

    return redirect(reverse("home"))
