# pylint: disable=E0401,E1101,C0303,R0913
"""
FR : Module d'envoi des emails
EN : Send emails module
Commentaire:

created at: 2023-06-13
created by: Paulo ALVES

modified at: 2023-06-13
modified by: Paulo ALVES
"""
import os
import smtplib
import ssl
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

import dkim

from apps.core.functions.functions_setups import settings
from heron.loggers import LOGGER_EMAIL

try:
    PROTOCOL = settings.SECURE_PROXY_SSL_HEADER[1]
except AttributeError:
    PROTOCOL = "http"

EMAIL_HOST = settings.EMAIL_HOST
EMAIL_PORT = settings.EMAIL_PORT
EMAIL_HOST_USER = settings.EMAIL_HOST_USER
EMAIL_HOST_PASSWORD = settings.EMAIL_HOST_PASSWORD
ENV_ROOT = settings.path_env
DOMAIN = settings.DOMAIN
DKIM_PEM_FILE = settings.DKIM_PEM_FILE

TEMPLATE_ROOT = os.path.join(settings.APPS_DIR, "services/templates/services")


def prepare_mail(message, subject, email_text="", email_html="", context=None):
    """Préparation smtp mail pour l'envoie du mail"""
    if not context:
        context = {}

    subject_mail = subject
    translate_email_text = email_text
    translate_email_html = email_html

    for i in range(10):
        subject_mail = subject_mail.replace(f"{str(i)}", context.get(str(i)))
        translate_email_text = translate_email_text.replace(f"{str(i)}", context.get(str(i)))
        translate_email_html = translate_email_html.replace(f"{str(i)}", context.get(str(i)))

    subject_mail = subject_mail.replace("{", "").replace("}", "")
    translate_email_text = translate_email_text.replace("{", "").replace("}", "")
    translate_email_html = translate_email_html.replace("{", "").replace("}", "")

    message["From"] = EMAIL_HOST_USER
    message["Subject"] = subject_mail
    message.attach(MIMEText(translate_email_text, "text"))
    message.attach(MIMEText(translate_email_html, "html"))


def send_mass_mail(email_list=None):
    """Envoi des mails en masse"""
    if email_list is None:
        email_list = []

    if not email_list:
        return {"Send invoices email : Il n'y a rien à envoyer"}

    with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
        print("server.ehlo() : ", server.ehlo())
        server.starttls(context=ssl.create_default_context())
        server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)

        for email_to_send in email_list:
            mail_to, subject, email_text, email_html, context, attachement_file_list = email_to_send
            send_mail(
                server, mail_to, subject, email_text, email_html, context, attachement_file_list
            )

    return {"Send invoices email : ", f"{len(email_list)} ont été envoyés"}


def send_mail(server, mail_to, subject, email_text, email_html, context, attachement_file_list):
    """Envoi le mail avec le template souhaité"""

    message = MIMEMultipart("alternative")
    message["To"] = mail_to
    prepare_mail(message, subject, email_text, email_html, context)

    for file in attachement_file_list:
        with file.open("rb") as open_file:
            file_to_send = MIMEApplication(open_file.read())
            file_to_send.add_header("Content-Disposition", "attachment", filename=file.name)
            message.attach(file_to_send)

    # Mise en place de la signature DKIM
    dkim_file = Path(ENV_ROOT) / DKIM_PEM_FILE
    print("dkim_file : ", dkim_file)

    with dkim_file.open() as pem_file:
        dkim_private_key = pem_file.read()
        sig = dkim.sign(
            message=message.as_bytes(),
            logger=LOGGER_EMAIL,
            selector="email".encode(),
            domain=DOMAIN.encode(),
            privkey=dkim_private_key.encode(),
            include_headers=[b"from", b"to"],
        ).decode()
        message["DKIM-Signature"] = sig.lstrip("DKIM-Signature: ")

    server.sendmail(EMAIL_HOST_USER, mail_to, message.as_string())
