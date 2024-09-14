# pylint: disable=E0401,E1101,C0303,R0913,W0613,R0914
"""
FR : Module d'envoi des emails
EN : Send emails module
Commentaire:

created at: 2023-06-13
created by: Paulo ALVES

modified at: 2023-06-13
modified by: Paulo ALVES
"""
import smtplib
import ssl
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email import encoders
from email.mime.base import MIMEBase

import dkim
from bs4 import BeautifulSoup

from apps.core.functions.functions_setups import settings
from apps.core.exceptions import EmailException
from heron.loggers import LOGGER_EMAIL

EMAIL_HOST = settings.EMAIL_HOST
EMAIL_PORT = settings.EMAIL_PORT
EMAIL_HOST_USER = settings.EMAIL_HOST_USER
EMAIL_HOST_PASSWORD = settings.EMAIL_HOST_PASSWORD
DEFAULT_FROM_EMAIL = settings.DEFAULT_FROM_EMAIL

ENV_ROOT = settings.path_env
DOMAIN = settings.DOMAIN
DKIM_PEM_FILE = settings.DKIM_PEM_FILE


def prepare_mail(message, body, subject, email_text="", email_html="", context=None):
    """Préparation smtp mail pour l'envoie du mail"""
    if not context:
        context = {}

    subject_mail = subject.format(**context)
    translate_email_html = email_html.format(**context)
    translate_email_text = BeautifulSoup(translate_email_html, "lxml").get_text()

    message["From"] = EMAIL_HOST_USER
    message["Subject"] = subject_mail
    body.attach(MIMEText(translate_email_text, "text"))
    body.attach(MIMEText(translate_email_html, "html"))


def send_mass_mail(email_list=None):
    """Envoi des mails en masse"""
    if email_list is None:
        email_list = []

    if not email_list:
        return {"Send invoices email : Il n'y a rien à envoyer"}

    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)

            for email_to_send in email_list:
                (
                    mail_to,
                    subject,
                    email_text,
                    email_html,
                    context,
                    attachement_file_list,
                ) = email_to_send
                send_mail(
                    server,
                    mail_to,
                    subject,
                    email_text,
                    email_html,
                    context,
                    attachement_file_list,
                )

    except (smtplib.SMTPException, ValueError) as error:
        raise EmailException("Erreur envoi email") from error

    return {"Send invoices email : ", f"{len(email_list)} ont été envoyés"}


def send_mail(server, mail_to, subject, email_text, email_html, context, attachement_file_list):
    """Envoi le mail avec le template souhaité"""
    message = MIMEMultipart()
    body = MIMEMultipart("alternative")

    prepare_mail(message, body, subject, email_text, email_html, context)
    message["To"] = ";".join(mail_to)
    message.attach(body)

    for file in attachement_file_list:
        payload = MIMEBase("application", "octet-stream")

        try:
            with open(file, "rb") as open_file:
                payload.set_payload(open_file.read())
        except Exception as msg_error:
            raise ValueError("échec à la lecture d'un fichier joint") from msg_error

        encoders.encode_base64(payload)

        payload.add_header("Content-Disposition", "attachment", filename=f"{file.name}")
        message.attach(payload)

    # Mise en place de la signature DKIM
    dkim_file = Path(ENV_ROOT).parent / DKIM_PEM_FILE

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

    server.sendmail(DEFAULT_FROM_EMAIL, mail_to, message.as_string())
