# pylint: disable=E0401
# ruff: noqa: E722
"""
FR : View des essais

Commentaire:

created at: 2024-08-13
created by: Paulo ALVES

modified at: 2024-08-13
modified by: Paulo ALVES
"""

import zipfile
from zipfile import ZipFile
from pathlib import Path

import pendulum
from django.shortcuts import render, redirect, reverse, HttpResponse
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from django.db import transaction

from heron import celery_app
from heron.loggers import LOGGER_VIEWS
from apps.core.bin.content_types import CONTENT_TYPE_FILE
from apps.core.functions.functions_setups import settings
from apps.core.functions.functions_dates import get_date_apostrophe, long_date_string
from apps.periods.forms import MonthForm
from apps.invoices.bin.generate_invoices_pdf import get_invoices_in_progress
from apps.invoices.models import Invoice, SaleInvoice
from apps.edi.models import EdiImport, EdiValidation, EdiImportControl
from apps.invoices.bin.pre_controls import control_insertion
from apps.invoices.bin.finalize import finalize_global_invoices
from apps.articles.models import Article
from apps.centers_purchasing.sql_files.sql_elements import (
    articles_acuitis_without_accounts,
)


def send_email_essais(request):
    """Vue des essais d'envois par mails en mass"""
    user_pk = request.user.pk
    celery_app.signature(
        "celery_send_emails_essais", kwargs={"user_pk": str(user_pk)}
    ).apply_async()
    return redirect(reverse("invoices:send_email_pdf_invoice"))
