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

    titre_table = "Insertion des factures intégrées"
    edi_invoices_exists = EdiImport.objects.filter(valid=True).exists()
    context = {"margin_table": 50, "titre_table": titre_table}

    if not edi_invoices_exists:
        request.session["level"] = 50
        messages.add_message(request, 50, "Il n'y a aucunes factures à traiter !")
        context["en_cours"] = True

        return render(request, "invoices/insertion_invoices.html", context=context)

    insertion, pdf_invoices = get_invoices_in_progress()

    # Si l'on envoie un POST alors on lance l'import en tâche de fond celery
    if all([request.method == "POST", not insertion, not pdf_invoices]):
        user_uuid = request.user.uuid_identification
        celery_app.signature(
            "invoices_insertions_launch",
            kwargs={
                "user_uuid": user_uuid,
                "invoice_date": pendulum.date(2023, 5, 31).isoformat(),
            },
        ).delay()
        insertion = True

    if insertion:
        titre_table = "INSERTION DES FACTURES EN COURS, VEUILLEZ REESSSAYEZ PLUS TARD !"

    if pdf_invoices:
        titre_table = "GENERATION DES PDF EN COURS, VEUILLEZ REESSSAYEZ PLUS TARD !"

    context["en_cours"] = any([insertion, pdf_invoices])
    context["titre_table"] = titre_table

    return render(request, "invoices/insertion_invoices.html", context=context)


def generate_pdf_invoice(request):
    """Vue de génération des factures en pdf"""
    titre_table = "Génération des factures de ventes en pdf"
    sales_invoices_exists = SaleInvoice.objects.filter(
        final=False, printed=False, type_x3__in=(1, 2)
    ).exists()
    context = {"margin_table": 50, "titre_table": titre_table}

    if request.method == "POST" and not sales_invoices_exists:
        request.session["level"] = 50
        messages.add_message(request, 50, "Il n'y a aucunes factures à traiter !")
        context["en_cours"] = False

        return render(request, "invoices/generate_pdf_invoices.html", context=context)

    insertion, pdf_invoices = get_invoices_in_progress()

    # Si l'on envoie un POST alors on lance l'import en tâche de fond celery
    if all([request.method == "POST", not insertion, not pdf_invoices]):
        user_pk = request.user.pk
        celery_app.signature("celery_pdf_launch", kwargs={"user_pk": str(user_pk)}).apply_async()
        pdf_invoices = True

    if insertion:
        titre_table = "INSERTION DES FACTURES EN COURS, VEUILLEZ REESSSAYEZ PLUS TARD !"

    if pdf_invoices:
        titre_table = (
            "GENERATION DES PDF EN COURS, VEUILLEZ REESSSAYEZ PLUS TARD ! "
            "(N'OUBLIEZ PAS DE REGARDER LES TRACES APRES LA GENERATION)"
        )

    context["en_cours"] = any([insertion, pdf_invoices])
    context["titre_table"] = titre_table

    return render(request, "invoices/generate_pdf_invoices.html", context=context)


def send_email_pdf_invoice(request):
    """Vue d'envoi des factures en pdf, par mail"""
    titre_table = "Envoi par mail des factures de vente"
    sales_invoices_exists = SaleInvoice.objects.filter(
        final=False, send_email=False, type_x3__in=(1, 2), printed=True
    ).exists()
    context = {"margin_table": 50, "titre_table": titre_table}

    if request.method == "POST" and not sales_invoices_exists:
        request.session["level"] = 50
        messages.add_message(request, 50, "Il n'y a aucunes factures à envoyer !")
        context["en_cours"] = False

        return render(request, "invoices/send_email_invoices.html", context=context)

    # Si l'on envoie un POST alors on lance l'import en tâche de fond celery
    if request.method == "POST":
        user_pk = request.user.pk
        celery_app.signature(
            "celery_send_invoices_emails", kwargs={"user_pk": str(user_pk)}
        ).apply_async()

    return render(request, "invoices/send_email_invoices.html", context=context)
