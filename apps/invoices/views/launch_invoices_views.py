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

from heron import celery_app
from apps.periods.forms import MonthForm
from apps.invoices.bin.generate_invoices_pdf import get_invoices_in_progress
from apps.edi.models import EdiImport
from apps.invoices.models import SaleInvoice


def generate_invoices_insertions(request):
    """Vue de l'intégration des factures définitives"""

    titre_table = "Génération de la facturation"
    edi_invoices_exists = EdiImport.objects.filter(valid=True).exists()
    form = MonthForm(request.POST or None)
    context = {
        "margin_table": 50,
        "titre_table": titre_table,
        "news": edi_invoices_exists,
        "form": form,
        "titre_periode": "MOIS DE FACTURATION",
    }

    if not edi_invoices_exists:
        request.session["level"] = 50
        messages.add_message(request, 50, "Il n'y a aucune facture à générer !")
        context["en_cours"] = True

        return render(request, "invoices/insertion_invoices.html", context=context)

    insertion, pdf_invoices = get_invoices_in_progress()

    # Si l'on envoie un POST alors on lance l'import en tâche de fond celery
    if all([request.method == "POST", not insertion, not pdf_invoices, form.is_valid()]):
        user_uuid = request.user.uuid_identification

        # On récupère la date de facturation
        periode_dict = form.cleaned_data
        date_facturation = str(periode_dict.get("periode")).split("_")[1]

        # On lance la génération des factures de vente et d'achat
        celery_app.signature(
            "invoices_insertions_launch",
            kwargs={
                "user_uuid": user_uuid,
                "invoice_date": date_facturation,
            },
        ).delay()
        insertion = True

    if insertion:
        titre_table = (
            "INSERTION DES FACTURES EN COURS, VEUILLEZ REESSSAYEZ PLUS TARD !"
            "(N'OUBLIEZ PAS DE REGARDER LES TRACES APRES LA GENERATION)"
        )

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
    context = {"margin_table": 50, "titre_table": titre_table, "news": sales_invoices_exists}

    if not sales_invoices_exists:
        request.session["level"] = 50
        messages.add_message(request, 50, "Il n'y a aucune facture à générer !")
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
    context = {"margin_table": 50, "titre_table": titre_table, "news": sales_invoices_exists}

    if not sales_invoices_exists:
        request.session["level"] = 50
        messages.add_message(request, 50, "Il n'y a aucune facture à envoyer !")
        context["en_cours"] = False

        return render(request, "invoices/send_email_invoices.html", context=context)

    # Si l'on envoie un POST alors on lance l'import en tâche de fond celery
    if request.method == "POST":
        user_pk = request.user.pk
        celery_app.signature(
            "celery_send_invoices_emails", kwargs={"user_pk": str(user_pk)}
        ).apply_async()

    return render(request, "invoices/send_email_invoices.html", context=context)
