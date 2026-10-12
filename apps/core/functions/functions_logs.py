"""
Module d'écriture ou envoie de logs par mails
"""
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from django.conf import settings

LOG_FILE = os.path.join(settings.LOG_DIR, "log_mise_a_jour.log")
LOG_FILE_DIVERS = os.path.join(settings.LOG_DIR, "log_divers.log")


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
    msg["From"] = settings.EMAIL_HOST_USER
    msg["To"] = settings.EMAIL_HOST_USER

    msg["Subject"] = "Erreur B.I" if subject_error is None else subject_error
    message = erreur
    msg.attach(MIMEText(message))

    if settings.EMAIL_USE_SSL:
        mailserver = smtplib.SMTP_SSL(settings.EMAIL_HOST, settings.EMAIL_PORT)
        mailserver.ehlo()
    else:
        mailserver = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
        mailserver.starttls()
        mailserver.ehlo()

    mailserver.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
    mailserver.sendmail(settings.EMAIL_HOST_USER, msg["To"], msg.as_string())
    mailserver.quit()


if __name__ == "__main__":
    envoi_mail_erreur("test d'envoie de message suite au passage à google", "erreur mail")
