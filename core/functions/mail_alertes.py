"""
Module pour envoi mails
"""
import os

from smtplib import SMTP, SMTP_SSL

from email import encoders
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.utils import formatdate


class ServeurSMTP:
    """
    Class pour initialiser le serveur SMTP
    """
    def __init__(
            self,
            email="",
            port=25,
            login="",
            senha="",
            tls=False,
            ssl=False
    ):
        """
        Conserve les paramètres d'un compte mail sur un serveur SMTP
        """
        self.email = email
        self.port = port
        self.login = login
        self.password = senha
        self.tls = tls
        self.ssl = ssl


class MessageSMTP:
    """
    Class pour message SMTP
    """
    def __init__(
            self,
            exped="",
            to=(),
            cc=(),
            bcc=(),
            sujet="",
            corps="",
            attach_files=(),
            encoding='UTF-8',
            text_type='plain'
    ):
        self.expediteur = exped

        if isinstance(to, str):
            to = to.split(';')

        if to in ([], ['']):
            raise ValueError("échec: pas de destinataire!")

        if isinstance(cc, str):
            cc = cc.split(';')

        if isinstance(bcc, str):
            bcc = bcc.split(';')

        if isinstance(attach_files, str):
            attach_files = attach_files.split(';')

        if encoding is None or encoding == "":
            encoding = 'UTF-8'

        if not attach_files:
            # message sans pièce jointe
            msg = MIMEText(corps, text_type, _charset=encoding)
        else:
            # message "multipart" avec une ou plusieurs pièce(s) jointe(s)
            msg = MIMEMultipart('alternatives')

        msg['From'] = exped
        msg['To'] = ', '.join(to)
        msg['Cc'] = ', '.join(cc)
        msg['Bcc'] = ', '.join(bcc)
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = sujet
        msg['Charset'] = encoding
        msg['Content-Type'] = 'text/' + text_type + '; charset=' + encoding

        if attach_files:
            msg.attach(MIMEText(corps, text_type, _charset=encoding))

            # ajout des pièces jointes
            for fichier in attach_files:
                part = MIMEBase('application', "octet-stream")
                try:
                    with open(fichier, "rb") as file:
                        part.set_payload(file.read())
                except Exception as msg_error:
                    raise ValueError(f"échec à la lecture d'un fichier joint ({msg_error})")
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    'attachment',
                    filename="%s" % (os.path.basename(fichier),)
                )
                msg.attach(part)

        # compactage final du message dans les 2 cas (avec ou sans pièce(s) jointe(s))
        self.mail = msg.as_string()

        # construction de la liste complète de tous les destinataires (to + cc + bcc)
        self.destinataires = to
        self.destinataires.extend(cc)
        self.destinataires.extend(bcc)


def envoi_mail(message, serveur):
    """
    Envoie le message correctement compacté au serveur SMTP donné
    """

    # connexion au serveur SMTP
    smtp = None
    try:
        print('connexion au serveur')
        if serveur.ssl:
            smtp = SMTP_SSL(serveur.email, serveur.port)
        else:
            smtp = SMTP(serveur.email, serveur.port)
    except Exception as msg_error:
        if smtp is not None:
            smtp.quit()
        return "échec: serveur non reconnu: (" + str(msg_error) + ")"

    # smtp.set_debuglevel(1)
    smtp.ehlo()
    if serveur.tls:
        smtp.starttls()
    smtp.ehlo()

    # ouverture de session
    if serveur.login != "":
        try:
            # print(serveur.login)
            smtp.login(serveur.login, serveur.password)
        except Exception as msg_error:
            if smtp is not None:
                smtp.quit()
            return "échec: login ou mdp non reconnu (" + str(msg_error) + ")"

    # envoi du mail
    try:
        smtp.sendmail(message.expediteur, message.destinataires, message.mail)
    except Exception as msg_error:
        if smtp is not None:
            smtp.quit()
        return "KO : échec à l'envoi de mail (" + str(msg_error) + ")"

    # ici, l'envoi a été réussi
    smtp.quit()
    return None  # retourner une chaine vide est la signature d'un envoi réussi
