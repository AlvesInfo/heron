# pylint: disable=E0401
"""
FR : View des lancements de la facturations
EN : View of invoicing launches

Commentaire:

created at: 2023-06-07
created by: Paulo ALVES

modified at: 2023-06-07
modified by: Paulo ALVES
"""
import pendulum
from django.shortcuts import render
from django.contrib import messages

from heron import celery_app
from apps.invoices.bin.generate_invoices_pdf import get_invoices_in_progress
from apps.edi.models import EdiImport
from apps.invoices.models import SaleInvoice


def generate_invoices_insertions(request):
    """Vue de l'intégration des factures définitives"""
    request.session["level"] = 20
    insertion, pdf_invoices = get_invoices_in_progress()
    titre_table = "Insertion des factures intégrées"
    edi_invoices_exists = EdiImport.objects.filter(valid=True).exists()

    if not edi_invoices_exists:
        request.session["level"] = 50
        messages.add_message(request, 50, "Il n'y a aucunes factures à traiter !")

    else:
        # Si l'on envoie un POST alors on lance l'import en tâche de fond celery
        if all([request.method == "POST", not insertion, not pdf_invoices]):
            user_uuid = request.user.uuid_identification
            celery_app.signature(
                "invoices_insertions_launch",
                kwargs={"user_uuid": user_uuid, "invoice_date": pendulum.date(2023, 5, 31)},
            ).delay()
            insertion = True

        if insertion:
            titre_table = "INSERTION DES FACTURES EN COURS, VEUILLEZ REESSSAYEZ PLUS TARD !"

        if pdf_invoices:
            titre_table = "GENERATION DES PDF EN COURS, VEUILLEZ REESSSAYEZ PLUS TARD !"

    context = {
        "en_cours": any([insertion, pdf_invoices]),
        "margin_table": 50,
        "titre_table": titre_table,
    }

    return render(request, "invoices/insertion_invoices.html", context=context)


def generate_pdf_invoice(request):
    """Vue de génération des factures en pdf"""
    request.session["level"] = 20
    insertion, pdf_invoices = get_invoices_in_progress()
    titre_table = "Génération des factures de ventes en pdf"
    sales_invoices_exists = SaleInvoice.objects.filter(
        final=False, printed=False, type_x3__in=(1, 2)
    ).exists()

    if request.method == "POST" and not sales_invoices_exists:
        request.session["level"] = 50
        messages.add_message(request, 50, "Il n'y a aucunes factures à traiter !")
        titre_table = "Génération des factures de ventes en pdf"

    else:
        # Si l'on envoie un POST alors on lance l'import en tâche de fond celery
        if all([request.method == "POST", not insertion, not pdf_invoices]):
            user_pk = request.user.pk
            celery_app.signature("celery_pdf_launch", kwargs={"user_pk": user_pk}).delay()
            pdf_invoices = True

        if insertion:
            titre_table = "INSERTION DES FACTURES EN COURS, VEUILLEZ REESSSAYEZ PLUS TARD !"

        if pdf_invoices:
            titre_table = (
                "GENERATION DES PDF EN COURS, VEUILLEZ REESSSAYEZ PLUS TARD ! "
                "(N'OUBLIEZ PAS DE REGARDER LES TRACES APRES LA GENERATION)"
            )

    context = {
        "en_cours": any([insertion, pdf_invoices]),
        "margin_table": 50,
        "titre_table": titre_table,
    }

    return render(request, "invoices/generate_pdf_invoices.html", context=context)
