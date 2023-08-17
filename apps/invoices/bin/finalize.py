# pylint: disable=E0401,C0413
"""
FR : Finalisation des factures
EN : Send invoices by email module
Commentaire:

created at: 2023-06-13
created by: Paulo ALVES

modified at: 2023-08-17
modified by: Paulo ALVES
"""
import os
import sys
import platform
from typing import AnyStr

import django

BASE_DIR = r"/"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")

django.setup()

from django.db.models import Q
from django.utils import timezone

from apps.invoices.models import (
    Invoice,
    InvoiceDetail,
    InvoiceCommonDetails,
    SaleInvoice,
    SaleInvoiceDetail,
)


def finalize_global_invoices(user):
    """Finalisation de la facturation par flag des champs "final" """
    Invoice.objects.filter(Q(final__isnull=True) | Q(final=False)).update(
        final=True, final_at=timezone.now(), modified_by=user, modified_at=timezone.now()
    )

    InvoiceDetail.objects.filter(Q(final__isnull=True) | Q(final=False)).update(
        final=True, final_at=timezone.now(), modified_by=user, modified_at=timezone.now()
    )

    InvoiceCommonDetails.objects.filter(Q(final__isnull=True) | Q(final=False)).update(
        final=True, final_at=timezone.now(), modified_by=user, modified_at=timezone.now()
    )

    SaleInvoice.objects.filter(Q(final__isnull=True) | Q(final=False)).update(
        final=True, final_at=timezone.now(), modified_by=user, modified_at=timezone.now()
    )

    SaleInvoiceDetail.objects.filter(Q(final__isnull=True) | Q(final=False)).update(
        final=True, final_at=timezone.now(), modified_by=user, modified_at=timezone.now()
    )


def finalize_emails_invoices():
    """Finalisation de la facturation par flag des champs "send_email" """

    SaleInvoice.objects.filter(Q(send_email__isnull=True) | Q(send_email=False)).update(
        send_email=True
    )


def finalize_cct_email_invoice(cct: AnyStr):
    """
    Finalisation de la facturation par flag des champs "send_email"
    :param cct: client Héron
    :return:
    """

    SaleInvoice.objects.filter(cct=cct).filter(
        Q(final__isnull=True) | Q(final=False) | Q(send_email__isnull=True) | Q(send_email=False)
    ).update(final=True, send_email=True)


def finalize_export_invoices():
    """Finalisation des exports de la facturation par flag du champ : "export" """
    Invoice.objects.filter(Q(export__isnull=True) | Q(export=False)).update(export=True)

    InvoiceDetail.objects.filter(Q(export__isnull=True) | Q(export=False)).update(export=True)

    InvoiceCommonDetails.objects.filter(Q(export__isnull=True) | Q(export=False)).update(
        export=True
    )

    SaleInvoice.objects.filter(Q(export__isnull=True) | Q(export=False)).update(export=True)

    SaleInvoiceDetail.objects.filter(Q(export__isnull=True) | Q(export=False)).update(export=True)
