# pylint: disable=E0401
# ruff: noqa: E722
"""
FR : View des lancements de la facturations
EN : View of invoicing launches

Commentaire:

created at: 2023-06-07
created by: Paulo ALVES

modified at: 2023-06-07
modified by: Paulo ALVES
"""

import uuid
import threading
import zipfile
from zipfile import ZipFile
from pathlib import Path

import pendulum
from django.shortcuts import render, redirect, reverse, HttpResponse
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count
from django.utils import timezone
from django.db import transaction

from heron import celery_app
from heron.loggers import LOGGER_VIEWS
from apps.core.bin.content_types import CONTENT_TYPE_FILE
from apps.core.functions.functions_setups import settings
from apps.core.functions.functions_dates import get_date_apostrophe, long_date_string
from apps.core.models import SSEProgress
from apps.periods.forms import MonthForm
from apps.invoices.bin.generate_invoices_pdf import get_invoices_in_progress
from apps.invoices.bin.invoices_insertions import invoices_insertion
from apps.invoices.models import Invoice, SaleInvoice
from apps.edi.models import EdiImport, EdiValidation, EdiImportControl
from apps.invoices.bin.pre_controls import control_insertion, control_emails, control_alls_missings
from apps.invoices.bin.finalize import finalize_global_invoices, set_validations
from apps.invoices.loops.send_emails_with_gmail import send_invoices_emails_gmail
from apps.articles.models import Article
from apps.centers_purchasing.sql_files.sql_elements import (
    articles_acuitis_without_accounts,
)


def generate_invoices_insertions(request):
    """Vue de l'intégration des factures définitives"""

    titre_table = "Génération de la facturation"

    # On contrôle qu'il n'y ai pas des factures non finalisées, mais envoyées par mail
    not_finalize = control_insertion()

    edi_invoices_exists = EdiImport.objects.filter(valid=True).exists()
    form = MonthForm(request.POST or None)
    context = {
        "margin_table": 50,
        "titre_table": titre_table,
        "news": edi_invoices_exists,
        "form": form,
        "titre_periode": "MOIS DE FACTURATION",
        "submit_url": "invoices:generate_invoices_insertions",
        "progress_title": "Génération de la facturation",
        "progress_icon": "📄",
    }

    # On contrôle qu'il y ait des factures à générer
    if not edi_invoices_exists:
        request.session["level"] = 50
        messages.add_message(request, 50, "Il n'y a aucune facture à générer !")
        context["not_finalize"] = True

        return render(request, "invoices/insertion_invoices.html", context=context)

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
        context = {
            "margin_table": 50,
            "titre_table": titre_table,
            "not_finalize": True,
            "submit_url": "invoices:generate_invoices_insertions",
            "progress_title": "Génération de la facturation",
            "progress_icon": "📄",
        }
        return render(request, "invoices/insertion_invoices.html", context=context)

    all_missings = control_alls_missings()

    if all_missings:
        context["all_missings"] = all_missings
        return render(request, "invoices/insertion_invoices.html", context=context)

    insertion, pdf_invoices, email_invoices = get_invoices_in_progress()

    # Si l'on envoie un POST alors, on lance l'import en tâche de fond celery
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
        user_pk = request.user.id

        # On récupère la date de facturation
        periode_dict = form.cleaned_data
        date_facturation = str(periode_dict.get("periode")).split("_")[1]

        # Générer un job_id unique
        job_id = str(uuid.uuid4())

        # Créer le SSEProgress AVANT de lancer la tâche
        total_files = 15
        task_type = "invoices_insertion"
        custom_title = "Génération de la facturation"

        progress = SSEProgress.objects.create(
            job_id=job_id,
            user_id=user_pk,
            total_items=total_files,
            task_type=task_type,
            custom_title=custom_title,
            metadata={"success": [], "failed": []},
        )
        progress.mark_as_started()

        # On lance la génération des factures de vente et d'achat en threading
        thread = threading.Thread(
            target=invoices_insertion,
            args=(user_uuid, date_facturation, job_id),
            daemon=True,
        )
        thread.start()

        # Retourner JSON immédiatement
        return JsonResponse({"success": True, "job_id": job_id})

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

    # On contrôle qu'il n'y ai pas des factures non finalisées, mais envoyées par mail
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
    context = {
        "margin_table": 50,
        "titre_table": titre_table,
        "news": sales_invoices_exists,
    }

    if not sales_invoices_exists:
        request.session["level"] = 50
        messages.add_message(request, 50, "Il n'y a aucun pdf à générer !")
        context["en_cours"] = False

        return render(request, "invoices/generate_pdf_invoices.html", context=context)

    insertion, pdf_invoices, email_invoices = get_invoices_in_progress()

    # Si l'on envoie un POST alors, on lance l'import en tâche de fond celery
    if all(
        [request.method == "POST", not insertion, not pdf_invoices, not email_invoices]
    ):
        user_pk = request.user.pk
        celery_app.signature(
            "celery_pdf_launch", kwargs={"user_pk": str(user_pk)}
        ).apply_async()
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


def invoices_pdf_files(request):
    """View pour download les factures pdf"""
    # On va récupérer les dates initiiales à l'arrivée sur la vue à la date de la période en cours
    form = MonthForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        periode_dict = form.cleaned_data
        dte_d, dte_f = str(periode_dict.get("periode")).split("_")

    else:
        edi_validation = EdiValidation.objects.filter(
            Q(final=False) | Q(final__isnull=True)
        ).first()
        initial_period = pendulum.parse(edi_validation.billing_period.isoformat())
        dte_d = initial_period.start_of("month").date().isoformat()
        dte_f = initial_period.end_of("month").date().isoformat()
        initial_value = f"{dte_d}_{dte_f}"
        form = MonthForm(initial={"periode": initial_value})

    # On récupère les pdf de la période
    pdf_invoices = (
        SaleInvoice.objects.exclude(global_invoice_file__isnull=True)
        .exclude(global_invoice_file="")
        .filter(invoice_date__range=(dte_d, dte_f))
        .values("cct", "parties__name_cct", "invoice_month", "global_invoice_file")
        .annotate(dcount=Count("cct"))
        .order_by("cct")
    )

    # On va poser le zip de toutes les factures pdf
    file_name_zip = f"PDF_ALLS_{dte_d}_{dte_f}.zip"
    alls = {
        "cct": " ",
        "parties__name_cct": "Fichier zip de toutes les factures",
        "global_invoice_file": file_name_zip,
        "dcount": 1,
    }

    # On remplit le contexte
    context = {
        "margin_table": 50,
        "titre_table": "Factures de vente",
        "form": form,
        "alls": alls,
        "invoices": pdf_invoices,
        "dte_d": pendulum.parse(dte_d).date(),
        "dte_f": pendulum.parse(dte_f).date(),
    }

    return render(request, "invoices/invoices_pdf_list.html", context=context)


def get_pdf_file(request, file_name):
    """Récupération des fichiers pdf des factures de ventes générées
    :param request: Request Django
    :param file_name: Paramètres get du nom du fichier à télécharger
    :return: response_file
    """
    try:
        if request.method == "GET":
            # Si la demande est pour le zip global, on zippe à la volée toutes les factures
            if file_name.startswith("PDF_ALLS"):
                _, _, dte_d, dte_f, *_ = file_name.split("_")
                dte_f = dte_f.replace(".zip", "")

                # On récupère les pdf de la période
                pdf_invoices = (
                    SaleInvoice.objects.exclude(global_invoice_file__isnull=True)
                    .exclude(global_invoice_file="")
                    .filter(invoice_date__range=(dte_d, dte_f))
                    .values(
                        "cct",
                        "parties__name_cct",
                        "invoice_month",
                        "global_invoice_file",
                    )
                    .annotate(dcount=Count("cct"))
                )
                compression = zipfile.ZIP_DEFLATED

                with ZipFile(
                    (Path(settings.SALES_INVOICES_FILES_DIR) / file_name), "w"
                ) as zip_file:
                    # On itère sur les pdf pour les zipper
                    for pdf_invoice in pdf_invoices:
                        file = Path(
                            settings.SALES_INVOICES_FILES_DIR
                        ) / pdf_invoice.get("global_invoice_file")
                        zip_file.write(
                            file, file.name, compress_type=compression, compresslevel=9
                        )

            file_path = Path(settings.SALES_INVOICES_FILES_DIR) / file_name
            content_type = CONTENT_TYPE_FILE.get(file_path.suffix, "text/plain")
            response = HttpResponse(
                file_path.open("rb").read(), content_type=content_type
            )
            response["Content-Disposition"] = f"attachment; filename={file_name}"

            return response

    except:
        LOGGER_VIEWS.exception("view : get_pdf_file")

    return redirect(reverse("home"))


def send_email_pdf_invoice(request):
    """Vue d'envoi de toutes les factures pdf, par mail"""

    if request.method == "POST" and "email_essais" in request.POST:
        return redirect(reverse("invoices:send_email_essais"))

    titre_table = "Envoi Global, par mail des factures de vente"

    # On contrôle qu'il y ait des pdf à envoyer par mail
    sales_invoices_exists = SaleInvoice.objects.filter(
        final=False, send_email=False, type_x3__in=(1, 2), printed=True
    ).exists()

    context = {
        "margin_table": 50,
        "titre_table": titre_table,
        "news": sales_invoices_exists,
        "not_finalize": not sales_invoices_exists,
    }

    if not sales_invoices_exists:
        request.session["level"] = 50
        messages.add_message(request, 50, "Il n'y a aucune facture pdf à envoyer !")
        context["en_cours"] = False

        return render(request, "invoices/send_email_invoices.html", context=context)

    insertion, pdf_invoices, email_invoices = get_invoices_in_progress()

    # Si l'on envoie un POST alors, on lance l'import en tâche de fond celery
    if all(
        [request.method == "POST", not insertion, not pdf_invoices, not email_invoices]
    ):
        user_pk = request.user.pk
        # celery_app.signature(
        #     "celery_send_invoices_emails", kwargs={"user_pk": str(user_pk)}
        # ).apply_async()
        # celery_app.signature(
        #     "celery_send_invoices_emails_gmail", kwargs={"user_pk": str(user_pk)}
        # ).apply_async()
        # email_invoices = True

        # Préparation des envois pas emails
        job_id = str(uuid.uuid4())
        total_emails = (
            SaleInvoice.objects
            .filter(
                final=False,
                printed=True,
                send_email=False,
                type_x3__in=[1, 2],
            )
            .values('cct', 'global_invoice_file', 'invoice_month')
            .distinct()
            .count()
        )
        task_type = "send_invoices_emails"
        custom_title = "Envoi Global, par mail des factures de vente"
        target = send_invoices_emails_gmail
        args = (user_pk, job_id)

        progress = SSEProgress.objects.create(
            job_id=job_id,
            user_id=user_pk,
            total_items=total_emails,
            task_type=task_type,
            custom_title=custom_title,
            metadata={"success": [], "failed": []},
        )
        progress.mark_as_started()

        # Lancement d'un thread séparé
        thread = threading.Thread(
            target=target,
            args=args,
            daemon=True,
        )
        thread.start()

        # Retourner JSON immédiatement
        return JsonResponse({"success": True, "job_id": job_id})

    if insertion:
        titre_table = "INSERTION DE FACTURES EN COURS, VEUILLEZ REESSSAYEZ PLUS TARD !"

    if pdf_invoices:
        titre_table = (
            "GENERATION DE PDF EN COURS, VEUILLEZ REESSSAYEZ PLUS TARD ! "
            "(N'OUBLIEZ PAS DE REGARDER LES TRACES APRES LA GENERATION)"
        )

    if email_invoices:
        titre_table = "LES FACTURES SONT EN COURS D'ENVOI PAR MAIL !"

    context["en_cours"] = any([insertion, pdf_invoices, email_invoices])
    context["titre_table"] = titre_table
    print(context["not_finalize"], context["en_cours"], context["news"])
    return render(request, "invoices/send_email_invoices.html", context=context)


@transaction.atomic
def finalize_period(request):
    """
    Finalisation de la période de facturation et création d'une nouvelle entrée dans edi_validation
    :return:
    """
    titre_table = "Finalisation de la période de facturation "

    # on va vérifier qu'il n'y a pas de nouveaux articles
    new_articles = Article.objects.filter(
        Q(new_article=True)
        | Q(error_sub_category=True)
        | Q(axe_bu__isnull=True)
        | Q(axe_prj__isnull=True)
        | Q(axe_pro__isnull=True)
        | Q(axe_pys__isnull=True)
        | Q(axe_rfa__isnull=True)
        | Q(big_category__isnull=True)
    )

    if new_articles:
        request.session["level"] = 50
        messages.add_message(
            request,
            50,
            "il reste des nouveaux articles, à compléter!",
        )
        return redirect(reverse("articles:new_articles_list"))

    without_accounts = EdiImport.objects.raw(articles_acuitis_without_accounts)
    # print(without_accounts)

    if without_accounts:
        request.session["level"] = 50
        messages.add_message(
            request,
            50,
            "il reste des nouveaux comptes, à compléter!",
        )
        return redirect(reverse("articles:articles_without_account_list"))

    set_validations()

    integration_valid = EdiImportControl.objects.filter(
        Q(valid=False) | Q(valid__isnull=True)
    )
    # print(integration_valid)

    if integration_valid:
        request.session["level"] = 50
        messages.add_message(
            request,
            50,
            "Les Intégration ne sont pas toutes validées",
        )
        return redirect(reverse("validation_purchases:integration_purchases"))

    not_cct = EdiImport.objects.filter(cct_uuid_identification__isnull=True)
    # print(integration_valid)

    if not_cct:
        request.session["level"] = 50
        messages.add_message(
            request,
            50,
            "Ils manquent des cct dans les factures!",
        )
        return redirect(reverse("validation_purchases:without_cct_purchases"))

    # On met à True les validations vérifiées
    edi_validation = (
        EdiValidation.objects.filter(Q(final=False) | Q(final__isnull=True))
        .order_by("-id")
        .first()
    )
    edi_validation.articles_news = True
    edi_validation.articles_without_account = True
    edi_validation.integration = True
    edi_validation.cct = True
    edi_validation.save()

    # On contrôle qu'il n'y ai pas des factures non finalisées et envoyées par mail
    not_finalize = control_insertion()
    initial_period = pendulum.parse(edi_validation.billing_period.isoformat()).add(
        months=1
    )
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

        edi_validation = EdiValidation.objects.create(
            billing_period=periode_facturation, created_by=request.user
        )

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

    if not not_finalize:
        exist_message = [message for message in messages.get_messages(request)]

        if not exist_message:
            request.session["level"] = 50
            messages.add_message(
                request,
                50,
                "il n'y a rien à finaliser!",
            )
    elif any(
        [
            SaleInvoice.objects.filter(
                Q(export__isnull=True) | Q(export=False)
            ).exists(),
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

    else:
        titre_table = (
            titre_table
            + get_date_apostrophe(edi_validation.billing_period)
            + long_date_string(edi_validation.billing_period)
        )

    context["titre_table"] = titre_table

    return render(request, "invoices/finalize_invoices.html", context=context)
