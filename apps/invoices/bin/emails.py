# pylint: disable=E1101, C0303
"""Formulaire pour l'envoie des mails des campagnes marketing

Commentaire:

created at: 2020-12-22
created by: Paulo ALVES

modified at: 2020-12-22
modified by: Paulo ALVES
"""
import os
import io
import smtplib
import dkim
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

import pendulum
from django.template import loader
from apps.core.functions.functions_setups import settings
from heron.loggers import LOGGER_EMAIL

try:
    PROTOCOL = settings.SECURE_PROXY_SSL_HEADER[1]
except AttributeError:
    PROTOCOL = "http"

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sav.settings")

EMAIL_HOST = settings.EMAIL_HOST
EMAIL_PORT = settings.EMAIL_PORT
EMAIL_HOST_USER = settings.EMAIL_HOST_USER
EMAIL_HOST_PASSWORD = settings.EMAIL_HOST_PASSWORD
ENV_ROOT = settings.ENV_ROOT
DOMAIN = settings.DOMAIN
DKIM_PEM_FILE = "dkim.private.key"

TEMPLATE_ROOT = os.path.join(settings.APPS_DIR, "services/templates/services")


def prepare_mail(
    message, txt_campain_template_name=None, html_campain_template_name=None, context=None
):
    """prepare smtp mail pour l'envoie du mail"""
    message["From"] = EMAIL_HOST_USER
    num_demand = context.get("num_demand", "")
    date_demande = context.get("date_demande", "")
    num_client = context.get("num_client", "")
    message["Subject"] = f"Demande de SAV N° {num_demand}"

    if txt_campain_template_name is not None:
        text_template = Path(TEMPLATE_ROOT) / txt_campain_template_name
        with text_template.open() as template_file:
            string_io = io.StringIO()
            for line in template_file:
                text = (
                    line.replace("num_demand", str(num_demand))
                    .replace("date_demande", str(date_demande))
                    .replace("num_client", str(num_client))
                ) + "\n"
                string_io.write(text)
            message.attach(MIMEText(string_io.read(), "text"))

    if html_campain_template_name is not None:
        html_template = f"services/{html_campain_template_name}"
        print(html_template)
        html_email = loader.render_to_string(html_template, context or dict())
        message.attach(MIMEText(html_email, "html"))


def send_mail(
    mail_to,
    num_demand,
    date_demande,
    num_client,
    txt_campain_template_name=None,
    html_campain_template_name=None,
):
    """Envoi le mail avec le template souhaité"""
    print(
        mail_to,
        num_demand,
        date_demande,
        num_client,
        txt_campain_template_name,
        html_campain_template_name,
        EMAIL_HOST,
        EMAIL_PORT,
    )
    with smtplib.SMTP("pro1.mail.ovh.net", 587) as server:
        print(server)
        server.starttls(context=ssl.create_default_context())
        server.login("paulo.alves@4a-info.fr", "OVH3zfsdnvh$")

        context = {"num_demand": num_demand, "date_demande": date_demande, "num_client": num_client}
        message = MIMEMultipart("alternative")
        message["To"] = mail_to
        prepare_mail(message, txt_campain_template_name, html_campain_template_name, context)

        # Mise en place de la signature DKIM
        dkim_file = Path(ENV_ROOT) / DKIM_PEM_FILE

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


def main():
    email_to = ["paulo.alves@4a-info.fr", "test-7rly8d98l@srv1.mail-tester.com"]
    enum_demande = "9840000417"
    enum_client = "8900HHDUU"
    date_demande = pendulum.parse("2021-03-03").date().format("dddd DD MMMM YYYY", locale="fr")
    etxt_campain_template_name = "sav_html_email.txt"
    ehtml_campain_template_name = "sav_html_email.html"
    send_mail(
        email_to,
        enum_demande,
        enum_client,
        date_demande,
        etxt_campain_template_name,
        ehtml_campain_template_name,
    )


if __name__ == "__main__":
    main()
