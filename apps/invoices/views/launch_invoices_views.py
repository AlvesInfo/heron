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
from django.shortcuts import render
from django.contrib import messages

from apps.invoices.bin.generate_invoices_pdf import get_invoices_in_progress, celery_pdf_launch
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
            user_pk = request.user.uuid_identification
            # celery_pdf_launch(user_pk)
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
        # final=False, printed=False, type_x3__in=(1, 2)
        type_x3__in=(1, 2)
    ).exists()

    if request.method == "POST" and not sales_invoices_exists:
        request.session["level"] = 50
        messages.add_message(request, 50, "Il n'y a aucunes factures à traiter !")
        titre_table = "Génération des factures de ventes en pdf"

    else:
        # Si l'on envoie un POST alors on lance l'import en tâche de fond celery
        if all([request.method == "POST", not insertion, not pdf_invoices]):
            user_pk = request.user.pk
            celery_pdf_launch(user_pk)
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
