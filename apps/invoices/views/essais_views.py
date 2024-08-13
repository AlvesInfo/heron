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

from django.shortcuts import redirect, reverse

from heron import celery_app


def send_email_essais(request):
    """Vue des essais d'envois par mails en mass"""
    user_pk = request.user.pk
    celery_app.signature(
        "celery_send_emails_essais", kwargs={"user_pk": str(user_pk)}
    ).apply_async()
    return redirect(reverse("invoices:send_email_pdf_invoice"))