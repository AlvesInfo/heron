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
from apps.edi.models import EdiImportControl


def set_validations():
    """Vérifie qu'il n'y a pas de validations non valides et orphelines"""
    # on récupère le set des validations avec valid = False
    valid_control = set(
        EdiImportControl.objects.filter(valid=False).values_list(
            "uuid_identification", flat=True
        )
    )

    # si l'on a pas de validations orphelines on shorcut
    if not valid_control:
        return

    invoices_details = set(
        InvoiceCommonDetails.objects.filter(uuid_control__in=valid_control).values_list(
            "uuid_control", flat=True
        )
    )

    to_suppress = valid_control ^ invoices_details

    # Suppression des controles orphelins
    if to_suppress:
        EdiImportControl.objects.filter(uuid_identification__in=to_suppress).delete()

    # Mise à jour des contrôles non valides
    to_update = valid_control.difference(to_suppress)
    EdiImportControl.objects.filter(uuid_identification__in=to_update).update(
        valid=True
    )


def finalize_global_invoices(user):
    """Finalisation de la facturation par flag des champs "final" """
    Invoice.objects.filter(Q(final__isnull=True) | Q(final=False)).update(
        final=True,
        final_at=timezone.now(),
        modified_by=user,
        modified_at=timezone.now(),
    )

    InvoiceDetail.objects.filter(Q(final__isnull=True) | Q(final=False)).update(
        final=True,
        final_at=timezone.now(),
        modified_by=user,
        modified_at=timezone.now(),
    )

    InvoiceCommonDetails.objects.filter(Q(final__isnull=True) | Q(final=False)).update(
        final=True,
        final_at=timezone.now(),
        modified_by=user,
        modified_at=timezone.now(),
    )

    SaleInvoice.objects.filter(Q(final__isnull=True) | Q(final=False)).update(
        final=True,
        final_at=timezone.now(),
        modified_by=user,
        modified_at=timezone.now(),
    )

    SaleInvoiceDetail.objects.filter(Q(final__isnull=True) | Q(final=False)).update(
        final=True,
        final_at=timezone.now(),
        modified_by=user,
        modified_at=timezone.now(),
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
        Q(final__isnull=True)
        | Q(final=False)
        | Q(send_email__isnull=True)
        | Q(send_email=False)
    ).update(final=True, send_email=True)


def finalize_export_invoices():
    """Finalisation des exports de la facturation par flag du champ : "export" """
    Invoice.objects.filter(Q(export__isnull=True) | Q(export=False)).update(export=True)

    InvoiceDetail.objects.filter(Q(export__isnull=True) | Q(export=False)).update(
        export=True
    )

    InvoiceCommonDetails.objects.filter(
        Q(export__isnull=True) | Q(export=False)
    ).update(export=True)

    SaleInvoice.objects.filter(Q(export__isnull=True) | Q(export=False)).update(
        export=True
    )

    SaleInvoiceDetail.objects.filter(Q(export__isnull=True) | Q(export=False)).update(
        export=True
    )
