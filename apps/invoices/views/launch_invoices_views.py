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
from django.shortcuts import render, redirect, reverse
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.db import transaction

from heron import celery_app
from apps.core.functions.functions_dates import get_date_apostrophe, long_date_string
from apps.periods.forms import MonthForm
from apps.invoices.bin.generate_invoices_pdf import get_invoices_in_progress
from apps.invoices.models import Invoice, SaleInvoice
from apps.edi.models import EdiImport, EdiValidation
from apps.invoices.bin.pre_controls import control_insertion
from apps.invoices.bin.finalize import finalize_global_invoices


def generate_invoices_insertions(request):
    """Vue de l'intégration des factures définitives"""

    titre_table = "Génération de la facturation"

    # On contrôle qu'il n'y ait pas des factures non finalisées, mais envoyées par mail
    not_finalize = control_insertion()

    if not_finalize:
        request.session["level"] = 50
        messages.add_message(
            request,
            50,
            (
                "Vous ne pouvez pas Générer la facturation, "
                "car celle-ci a déjà été envoyée par mail, "
                "mais non finalisée"
            ),
        )
        context = {"margin_table": 50, "titre_table": titre_table, "not_finalize": True}
        return render(request, "invoices/insertion_invoices.html", context=context)

    edi_invoices_exists = EdiImport.objects.filter(valid=True).exists()
    form = MonthForm(request.POST or None)
    context = {
        "margin_table": 50,
        "titre_table": titre_table,
        "news": edi_invoices_exists,
        "form": form,
        "titre_periode": "MOIS DE FACTURATION",
    }

    # On contrôle qu'il y ait des factures à générer
    if not edi_invoices_exists:
        request.session["level"] = 50
        messages.add_message(request, 50, "Il n'y a aucune facture à générer !")
        context["en_cours"] = True

        return render(request, "invoices/insertion_invoices.html", context=context)

    insertion, pdf_invoices, email_invoices = get_invoices_in_progress()

    # Si l'on envoie un POST alors on lance l'import en tâche de fond celery
    if all(
        [
            request.method == "POST",
            not insertion,
            not pdf_invoices,
            not email_invoices,
            form.is_valid(),
        ]
    ):
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

    if email_invoices:
        titre_table = "LES FACTURES SONT EN COURS D'ENVOI PAR MAIL !"

    context["en_cours"] = any([insertion, pdf_invoices, email_invoices])
    context["titre_table"] = titre_table

    return render(request, "invoices/insertion_invoices.html", context=context)


def generate_pdf_invoice(request):
    """Vue de génération des factures en pdf"""
    titre_table = "Génération des factures de ventes en pdf"

    # On contrôle qu'il n'y ait pas des factures non finalisées, mais envoyées par mail
    not_finalize = control_insertion()

    if not_finalize:
        request.session["level"] = 50
        messages.add_message(
            request,
            50,
            (
                "Vous ne pouvez pas Générer les pdf, "
                "car les factures sont déjà envoyées par mail, "
                "mais non finalisée"
            ),
        )
        context = {"margin_table": 50, "titre_table": titre_table, "not_finalize": True}
        return render(request, "invoices/generate_pdf_invoices.html", context=context)

    # On contrôle qu'il y ait des pdf à générer
    sales_invoices_exists = SaleInvoice.objects.filter(
        final=False, printed=False, type_x3__in=(1, 2)
    ).exists()
    context = {"margin_table": 50, "titre_table": titre_table, "news": sales_invoices_exists}

    if not sales_invoices_exists:
        request.session["level"] = 50
        messages.add_message(request, 50, "Il n'y a aucune facture à générer !")
        context["en_cours"] = False

        return render(request, "invoices/generate_pdf_invoices.html", context=context)

    insertion, pdf_invoices, email_invoices = get_invoices_in_progress()

    # Si l'on envoie un POST alors on lance l'import en tâche de fond celery
    if all([request.method == "POST", not insertion, not pdf_invoices, not email_invoices]):
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

    if email_invoices:
        titre_table = "LES FACTURES SONT EN COURS D'ENVOI PAR MAIL !"

    context["en_cours"] = any([insertion, pdf_invoices, email_invoices])
    context["titre_table"] = titre_table

    return render(request, "invoices/generate_pdf_invoices.html", context=context)


def send_email_pdf_invoice(request):
    """Vue d'envoi de toutes les factures pdf, par mail"""
    titre_table = "Envoi Global, par mail des factures de vente"

    # On contrôle qu'il n'y ait pas des factures non finalisées, mais envoyées par mail
    not_finalize = control_insertion()

    if not_finalize:
        request.session["level"] = 50
        messages.add_message(
            request,
            50,
            (
                "Vous ne pouvez pas Envoyer par mail les pdf, "
                "car ils ont déjà été envoyées, "
                "mais non finalisée"
            ),
        )
        context = {"margin_table": 50, "titre_table": titre_table, "not_finalize": True}
        return render(request, "invoices/send_email_invoices.html", context=context)

    # On contrôle qu'il y ait des pdf à envoyer par mail
    sales_invoices_exists = SaleInvoice.objects.filter(
        final=False, send_email=False, type_x3__in=(1, 2), printed=True
    ).exists()
    context = {"margin_table": 50, "titre_table": titre_table, "news": sales_invoices_exists}

    if not sales_invoices_exists:
        request.session["level"] = 50
        messages.add_message(request, 50, "Il n'y a aucune facture à envoyer !")
        context["en_cours"] = False

        return render(request, "invoices/send_email_invoices.html", context=context)

    insertion, pdf_invoices, email_invoices = get_invoices_in_progress()

    # Si l'on envoie un POST alors on lance l'import en tâche de fond celery
    if all([request.method == "POST", not insertion, not pdf_invoices, not email_invoices]):
        user_pk = request.user.pk
        celery_app.signature(
            "celery_send_invoices_emails", kwargs={"user_pk": str(user_pk)}
        ).apply_async()
        email_invoices = True

    if insertion:
        titre_table = "INSERTION DES FACTURES EN COURS, VEUILLEZ REESSSAYEZ PLUS TARD !"

    if pdf_invoices:
        titre_table = (
            "GENERATION DES PDF EN COURS, VEUILLEZ REESSSAYEZ PLUS TARD ! "
            "(N'OUBLIEZ PAS DE REGARDER LES TRACES APRES LA GENERATION)"
        )

    if email_invoices:
        titre_table = "LES FACTURES SONT EN COURS D'ENVOI PAR MAIL !"

    context["en_cours"] = any([insertion, pdf_invoices, email_invoices])
    context["titre_table"] = titre_table

    return render(request, "invoices/send_email_invoices.html", context=context)


@transaction.atomic
def finalize_period(request):
    """
    Finalisation de la période de facturation et création d'une nouvelle entrée dans edi_validation
    :return:
    """
    titre_table = "Finalisation de la période de facturation "

    # On contrôle qu'il n'y ait pas des factures non finalisées et envoyées par mail
    not_finalize = control_insertion()
    edi_validation = EdiValidation.objects.filter(Q(final=False) | Q(final__isnull=True)).first()
    initial_period = pendulum.parse(edi_validation.billing_period.isoformat()).add(months=1)
    initial_value = (
        f"{initial_period.start_of('month').date().isoformat()}"
        "_"
        f"{initial_period.end_of('month').date().isoformat()}"
    )
    form = MonthForm(request.POST or None, initial={"periode": initial_value})

    context = {
        "margin_table": 50,
        "titre_table": titre_table,
        "not_finalize": not_finalize,
        "form": form,
        "select_width": 300,
        "titre_periode": "NOUVELLE PERIODE DE FACTURATION",
    }

    if not_finalize and request.method == "POST" and form.is_valid():
        # On récupère la période de facturation
        periode_dict = form.cleaned_data
        periode_facturation = str(periode_dict.get("periode")).split("_")[0]
        edi_validation.final_at = timezone.now()
        edi_validation.final = True
        edi_validation.save()

        edi_validation, _ = EdiValidation.objects.get_or_create(billing_period=periode_facturation)

        # On met final = true dans toutes les tables de facturation
        finalize_global_invoices(request.user)
        edi_validation.created_by = request.user

        request.session["level"] = 20
        messages.add_message(
            request,
            20,
            "La précédente période de facturation a bien ete finalisée !",
        )

        return redirect(reverse("invoices:finalize_period"))

    if any(
        [
            SaleInvoice.objects.filter(Q(export__isnull=True) | Q(export=False)).exists(),
            Invoice.objects.filter(Q(export__isnull=True) | Q(export=False)).exists(),
        ]
    ):
        context["not_finalize"] = False
        request.session["level"] = 50
        messages.add_message(
            request,
            50,
            (
                "Vous ne pouvez pas finaliser la facturation, "
                "car les fichiers d'imports X3 n'ont pas été générés!"
            ),
        )

    elif not not_finalize:
        exist_message = [message for message in messages.get_messages(request)]

        if not exist_message:
            request.session["level"] = 50
            messages.add_message(
                request,
                50,
                "il n'y a rien à finaliser!",
            )
    else:
        titre_table = (
            titre_table
            + get_date_apostrophe(edi_validation.billing_period)
            + long_date_string(edi_validation.billing_period)
        )

    context["titre_table"] = titre_table

    return render(request, "invoices/finalize_invoices.html", context=context)
