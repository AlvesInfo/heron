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
from apps.core.functions.functions_utilitaires import iter_slice
from apps.core.exceptions import EmailException
from heron.loggers import LOGGER_EMAIL

EMAIL_HOST = settings.EMAIL_HOST
EMAIL_PORT = settings.EMAIL_PORT
EMAIL_HOST_USER = settings.EMAIL_HOST_USER
EMAIL_HOST_PASSWORD = settings.EMAIL_HOST_PASSWORD
ENV_ROOT = settings.path_env
DOMAIN = settings.DOMAIN
DKIM_PEM_FILE = settings.DKIM_PEM_FILE


class SmtpServer:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SmtpServer, cls).__new__(cls, *args, **kwargs)

        return cls._instance

    def __init__(
        self,
        host: str = EMAIL_HOST,
        port: int = EMAIL_PORT,
        username: str = EMAIL_HOST_USER,
        password: str = EMAIL_HOST_PASSWORD,
        cls_smtp: smtplib.SMTP = smtplib.SMTP,
        use_starttls: bool = True,
        **kwargs,
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_starttls = use_starttls
        self.cls_smtp = cls_smtp
        self.kws_smtp = kwargs or {}
        self.connection = None

    def __enter__(self):
        self.connect()

    def __exit__(self, *args):
        self.close()

    def connect(self):
        """Connect to the SMTP Server"""
        self.connection = self.get_server()

    def close(self):
        """Close (quit) the connection"""
        if self.connection:
            self.connection.quit()
            self.connection = None

    def get_server(self) -> smtplib.SMTP:
        """Connect and get the SMTP Server"""
        user = self.username
        password = self.password

        server = self.cls_smtp(self.host, self.port, **self.kws_smtp)

        if self.use_starttls:
            server.starttls()

        if user is not None or password is not None:
            server.login(user, password)

        return server

    @property
    def is_alive(self):
        """bool: Check if there is a connection to the SMTP server"""
        return self.connection is not None


def prepare_mail(message, body, subject, email_text="", email_html="", context=None):
    """Préparation smtp mail pour l'envoie du mail"""
    if not context:
        context = {}

    subject_mail = subject.format(**context)
    translate_email_html = email_html.format(**context)
    translate_email_text = BeautifulSoup(translate_email_html, "lxml").get_text() or email_text

    message["From"] = EMAIL_HOST_USER
    message["Subject"] = subject_mail
    body.attach(MIMEText(translate_email_text, "text"))
    body.attach(MIMEText(translate_email_html, "html"))


def send_mass_mail(email_list):
    """Envoi des mails en masse"""
    if email_list is None:
        email_list = []

    if not email_list:
        return {"Send invoices email : Il n'y a rien à envoyer"}

    try:
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls(context=ssl.create_default_context())
        server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)

        for emails_slice in iter_slice(email_list, 50):
            server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
            server.starttls(context=ssl.create_default_context())
            server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)

            for email_to_send in emails_slice:
                send_mail(server, *email_to_send)

            server.close()

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

    server.sendmail(EMAIL_HOST_USER, mail_to, message.as_string())
