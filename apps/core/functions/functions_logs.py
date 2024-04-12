"""
Module d'écriture ou envoie de logs par mails
"""
import sys
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import platform

BASE_DIR = r"C:\SitesWeb\heron"

if platform.uname().node == "DESKP082":
    sys.path.insert(0, BASE_DIR)
    sys.path.append(BASE_DIR)
else:
    BASE_DIR = "/home/paulo/heron"

from heron.settings import (
    EMAIL_HOST,
    EMAIL_PORT,
    EMAIL_HOST_USER,
    EMAIL_HOST_PASSWORD,
    EMAIL_USE_SSL,
    EMAIL_USE_TLS,
    LOG_DIR,
)

LOG_FILE = os.path.join(LOG_DIR, "log_mise_a_jour.log")
LOG_FILE_DIVERS = os.path.join(LOG_DIR, "log_divers.log")


class LogError(Exception):
    """Exception niveau module"""


def write_log(fichier=None, line_to_write=None):
    """
    Fonction pour écrire une ligne de log dans un fichier.
        :param fichier: Fichier ou écrire la ligne.
        :param line_to_write: Ligne à écrire
        :return: None
    """
    if fichier and line_to_write:
        if not os.path.isfile(fichier):
            open(fichier, "a").close()

        with open(fichier, "a", encoding="utf-8") as log_file:
            log_file.write(line_to_write)


def envoi_mail_erreur(erreur, subject_error=None):
    """
    Fonction qui envoi les erreurs par mail
        :param erreur: Erreur à envoyer
        :param subject_error: Sujet de l'erreur
        :return: None
    """
    msg = MIMEMultipart()
    msg["From"] = EMAIL_HOST_USER
    msg["To"] = EMAIL_HOST_USER

    msg["Subject"] = "Erreur B.I" if subject_error is None else subject_error
    message = erreur
    msg.attach(MIMEText(message))

    if EMAIL_USE_SSL:
        mailserver = smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT)
    else:
        mailserver = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)

    mailserver.ehlo()

    if EMAIL_USE_TLS:
        mailserver.starttls()

    mailserver.ehlo()
    mailserver.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
    mailserver.sendmail(EMAIL_HOST_USER, msg["To"], msg.as_string())
    mailserver.quit()


def log_dispatch(log, dir_log=LOG_FILE):
    """
    Fonction de dispatch du log d'erreur
        :param log: log à envoyer
        :param dir_log: répertoire de log
        :return: None
    """
    envoi_mail_erreur(log)
    write_log(dir_log, log)


if __name__ == "__main__":
    envoi_mail_erreur("test d'envoie de message suite au passage à google", "erreur mail")
