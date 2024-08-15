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
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email import encoders
from email.mime.base import MIMEBase
from threading import Lock
from typing import Union

import dkim
from bs4 import BeautifulSoup

from apps.core.functions.functions_setups import settings
from apps.core.exceptions import EmailException
from heron.loggers import LOGGER_EMAIL

EMAIL_HOST = settings.EMAIL_HOST
EMAIL_PORT = settings.EMAIL_PORT
EMAIL_HOST_USER = settings.EMAIL_HOST_USER
EMAIL_HOST_PASSWORD = settings.EMAIL_HOST_PASSWORD
ENV_ROOT = settings.path_env
DOMAIN = settings.DOMAIN
DKIM_PEM_FILE = settings.DKIM_PEM_FILE


class SingletonMeta(type):
    """
    This is a thread-safe implementation of Singleton.
    """

    _instances = {}
    _nb_instances = 0
    _lock: Lock = Lock()
    """
    We now have a lock object that will be used to synchronize threads during
    first access to the Singleton.
    """

    def __call__(cls, *args, **kwargs):
        """
        Possible changes to the value of the `__init__` argument do not affect
        the returned instance.
        """
        # Now, imagine that the program has just been launched. Since there's no
        # Singleton instance yet, multiple threads can simultaneously pass the
        # previous conditional and reach this point almost at the same time. The
        # first of them will acquire lock and will proceed further, while the
        # rest will wait here.
        with cls._lock:
            # The first thread to acquire the lock, reaches this conditional,
            # goes inside and creates the Singleton instance. Once it leaves the
            # lock block, a thread that might have been waiting for the lock
            # release may then enter this section. But since the Singleton field
            # is already initialized, the thread won't create a new object.
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance

        cls._nb_instances += 1

        return cls._instances[cls]


class SmtpServer(metaclass=SingletonMeta):
    """Singleton du serveur de mail"""

    server_mail: Union[smtplib.SMTP, smtplib.SMTP_SSL] = None

    def __init__(self):
        """Initialisation"""
        self.__enter__()

    def __enter__(self):
        """Context manager à l'entrée"""
        self.connect()
        return self

    def __exit__(self, *args, **kwargs):
        """Context manager à la sortie"""
        if self.__class__._nb_instances > 0:
            self.__class__._nb_instances -= 1

        if self.__class__._nb_instances == 0 and self.server_mail is not None:
            self.server_mail.ehlo()
            self.server_mail.quit()
            self.server_mail = None

    def re_connect(self):
        """Reconnexion au serveur SMTP"""

        if settings.EMAIL_USE_SSL:
            self.server_mail = smtplib.SMTP_SSL(
                settings.EMAIL_HOST, settings.EMAIL_PORT
            )

        else:
            self.server_mail = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)

        self.server_mail.ehlo()

        if settings.EMAIL_USE_TLS:
            self.server_mail.starttls()

        self.server_mail.ehlo()
        self.server_mail.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)

    def connect(self, force: bool = False):
        """Connection au serveur SMTP
        :param force: pour forcer une connection après
        """
        if self.server_mail is None or force:
            self.re_connect()

    def server(self):
        self.connect()
        return self.server_mail

    def quit(self):
        self.__exit__()

    def nb_connect(self):
        return self.__class__._nb_instances


def prepare_mail(message, body, subject, email_text="", email_html="", context=None):
    """Préparation smtp mail pour l'envoie du mail"""
    if not context:
        context = {}

    subject_mail = subject.format(**context)
    translate_email_html = email_html.format(**context)
    translate_email_text = (
        BeautifulSoup(translate_email_html, "lxml").get_text() or email_text
    )

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
        for email_to_send in email_list:
            mail_to, subject, email_text, email_html, context, attachement_file_list = (
                email_to_send
            )
            send_mail(
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


def send_mail(mail_to, subject, email_text, email_html, context, attachement_file_list):
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

    with dkim_file.open() as pem_file, SmtpServer() as smtp:
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

        attemps = 3

        while True:
            try:
                smtp.server_mail.sendmail(EMAIL_HOST_USER, mail_to, message.as_string())
            except smtplib.SMTPServerDisconnected as error:
                if not attemps:
                    raise smtplib.SMTPServerDisconnected() from error
                smtp.connect(force=True)
                attemps -= 1


if __name__ == "__main__":
    # a = SmtpServer()
    # print("1 ======")
    # print(a.nb_connect())
    # b = SmtpServer()
    # print("2 ======")
    # print(a.nb_connect())
    # print(b.nb_connect())
    #
    # print("3 ======")
    # c = SmtpServer()
    # print(a.nb_connect())
    # print(b.nb_connect())
    # print(c.nb_connect())
    #
    # print("4 ======")
    # a.quit()
    # print(a.nb_connect())
    # print(b.nb_connect())
    # print(c.nb_connect())

    with SmtpServer() as server:
        print("5 ======")
        print(server.nb_connect())
        server.quit()
        # print(a.nb_connect())
        # print(b.nb_connect())
        # print(c.nb_connect())

    # print("6 ======")
    # print(a.nb_connect())
    # print(b.nb_connect())
    # print(c.nb_connect())
    #
    # print("7 ======")
    #
    # b.quit()
    # c.quit()
    # print(a.nb_connect())
    # print(b.nb_connect())
    # print(c.nb_connect())
    #
    # print("8 ======")
    # a.quit()
    # print(a.nb_connect())
    # print(b.nb_connect())
    # print(c.nb_connect())
