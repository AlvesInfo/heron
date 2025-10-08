"""
Fonction pour gérer la récupération des pièces jointes dans les mails
"""

import os
import sys
import shutil
import zipfile
from datetime import datetime
import email
import imaplib

from apps.core.functions.functions_setups import settings

EMAIL_HOST = settings.EMAIL_HOST
EMAIL_PORT = settings.EMAIL_PORT
EMAIL_HOST_USER = settings.EMAIL_HOST_USER
EMAIL_HOST_PASSWORD = settings.EMAIL_HOST_PASSWORD


class MailError(Exception):
    """Exception niveau module"""


class RecuperationDesPiecesJointesMails:
    """
    Module qui récupère les pièces jointes voulues, de la boite mail et les placent dans un
    répertoire

    exemple :
        RecuperationDesPiecesJointesMails(  fournisseur_imap,
                                            dossier_des_mails_a_recuperer,
                                            adresse_email,
                                            password_mail,
                                            repertoire_provisoire,
                                            fichiers_a_garder,
                                            LOG_FILE
                                        )

            fournisseur_imap : "imap.gmail.com"
            dossier_des_mails_a_recuperer (imap) : "INBOX"
            adresse_email : "exemple@gmail.com"
            password_mail : "passwordexemple"
            repertoire_provisoire : "/home/ubuntu/projet_ftp/pieces_jointes_provisoires"
            fichiers_a_garder: dict : {  'ACUITIS_AVAI': (
                                                     12,
                                                     '.xls',
                                                     '.xlsx',
                                                     '/home/ubuntu/projet_ftp/fichiers_stocks/',
                                                     True
                                                     ),
                                                }
            LOG_FILE : "/home/ubuntu/projet_ftp/depot_ftp_stock_csv.log"
    """

    def __init__(
        self,
        fimap=None,
        dossier=None,
        mail=None,
        pwd=None,
        repertoire=None,
        selection_fichiers=None,
        log_file_ftp=None,
    ):
        self.fimap = fimap
        self.dossier = dossier
        self.mail = mail
        self.pwd = pwd
        self.repertoire = repertoire
        self.selection_fichiers = selection_fichiers
        self.log_file = log_file_ftp

    def write_log_file(self, ligne_a_ecrire=None):
        """
        Fonction pour écrire dans le fichier de log
            :param ligne_a_ecrire: ligne de log à écrire
            :return: None
        """
        if self.log_file and ligne_a_ecrire:
            with open(self.log_file, "a", encoding="utf-8") as log_file:
                log_file.write(ligne_a_ecrire)
            log_file.close()

    @staticmethod
    def a_garder(dic, fichier, extension):
        """
        Fonction qui retourne True si le fichier est à garder avec le path du fichier
            :param dic: Dictionnaire des fichiers à garder
            :param fichier: Fichier à garder
            :param extension: Extension du fichier
            :return: True ou false si le fichier est à garder
        """
        test_a_garder = [False]

        for key, value in dic.items():
            test_fichier = os.path.basename(fichier)[0 : value[0]]

            if test_fichier == key and extension in value:
                test_a_garder[0] = True
                test_a_garder.append(value[3] + os.path.basename(fichier))

        return test_a_garder

    def liste_repertoire(self, path):
        """
        Fonction qui liste les répertoire inclus récursivement
            :param path: Répertoire
            :return: La liste des fichiers
        """
        list_rep = []
        for root, dirs, files in os.walk(path):
            if root != self.repertoire:
                list_rep.append(root)
        return list_rep

    @staticmethod
    def liste_fichiers_recursif(path):
        """
        Fonction qui créer une liste des fichiers des répertoires récursivement
            :param path: Répertoire
            :return: La liste des fichiers
        """
        list_fichiers = []

        for root, dirs, files in os.walk(path):
            for f_f in files:
                if os.path.splitext(f_f)[1] != ".py":
                    list_fichiers.append(os.path.join(root, f_f))

        return list_fichiers

    def suppression_repertoires_recursif(self, log=False):
        """
        Fonction qui supprime les repertoires inclus récursivement
            :param log: Fichier de log
            :return: None
        """
        try:
            for dossier, sous_dossiers, fichiers in os.walk(self.repertoire):
                if dossier not in self.repertoire:
                    for fichier in fichiers:
                        deplacer_de = os.path.join(dossier, fichier)
                        deplacer_vers = os.path.join(self.repertoire, fichier)
                        shutil.move(deplacer_de, deplacer_vers)

            reps = self.liste_repertoire(self.repertoire)

            for rep in reps:
                if os.path.isdir(rep):
                    shutil.rmtree(rep)

        except MailError:
            if log:
                ligne = (
                    f"{datetime.now().isoformat()} | Erreur de suppression de repertoires : "
                    f"{sys.exc_info()[1]} - {self.fimap}\n"
                )
                self.write_log_file(ligne)

    def suppression_fichiers_non_souhaite_recursif(self, log=False):
        """
        Fonction qui supprime les fichiers inclus récursivement
            :param log: Fichier de log
            :return: None
        """
        try:
            list_fichiers = self.liste_fichiers_recursif(self.repertoire)

            for fich in list_fichiers:
                test = self.a_garder(
                    self.selection_fichiers, fich, os.path.splitext(fich)[1]
                )

                if test[0]:
                    dest = test[1]
                    shutil.move(fich, dest)
                else:
                    os.remove(fich)
        except MailError:
            if log:
                ligne = (
                    f"{datetime.now().isoformat()} | Erreur de suppression des fichiers non "
                    f"souhaités : {sys.exc_info()[1]} - {self.fimap}\n"
                )
                self.write_log_file(ligne)

    def a_garder_plus_recent(self, log=False):
        """
        On ne garde que le fichier le plus récent pour les répertoires ciblés
            :param log: Fichier de log
            :return: None
        """
        try:
            for value in self.selection_fichiers.values():
                if value[4]:
                    liste_fichiers = []
                    dic_fichiers = {}
                    fichiers = [
                        value[3] + fichier
                        for fichier in os.listdir(value[3])
                        if os.path.isfile(os.path.join(value[3], fichier))
                    ]

                    for fichier in fichiers:
                        liste_fichiers.append(os.path.getmtime(fichier))
                        dic_fichiers[str(os.path.getmtime(fichier))] = fichier

                    liste_fichiers.reverse()

                    if liste_fichiers:
                        del dic_fichiers[str(liste_fichiers[0])]
                        for element in dic_fichiers.values():
                            if os.path.isfile(element):
                                os.remove(element)

        except MailError:
            if log:
                ligne = (
                    f"{datetime.now().isoformat()} | Erreur de suppression des fichiers plus "
                    f"anciens : {sys.exc_info()[1]} - {self.fimap}\n"
                )
                self.write_log_file(ligne)

    def liste_des_fichiers_recuperes(self, log=False):
        """
        Fonction qui récupère la liste des fichiers récupérés
            :param log: Fichier de log
            :return: None
        """
        liste_fichiers = []

        for value in self.selection_fichiers.values():
            fichiers = [
                fichier
                for fichier in os.listdir(value[3])
                if os.path.isfile(os.path.join(value[3], fichier))
            ]

            liste_fichiers = liste_fichiers + fichiers

        if log:
            for fichier in liste_fichiers:
                ligne = f"{datetime.now().isoformat()} | Recuperation par mail du fichier : {fichier}\n"
                self.write_log_file(ligne)

    def connexion_mail(self, log=False):
        """
        Fonction de connection au mails
            :param log: Fichier de log
            :return: La connection ou False
        """
        try:
            # connexion au serveur imap gmail
            mail = imaplib.IMAP4_SSL(self.fimap)
            mail.login(self.mail, self.pwd)
            return mail

        except MailError:
            if log:
                ligne = (
                    f"{datetime.now().isoformat()} | Erreur de connexion au mail : "
                    f"{sys.exc_info()[1]} - {self.fimap}\n"
                )

                self.write_log_file(ligne)
            return False

    def recuperation_pieces_jointes_mail_non_lus(self, log=False):
        """
        Fonction de récupération de l'ensemble des pièces jointes des mails non lus
            :param log: Fichier de log
            :return: None
        """
        m_c = self.connexion_mail(log)

        if m_c:
            try:
                # selection de la boite de reception
                m_c.select(self.dossier)
                # filtrage sur les mails non lus
                items = m_c.search(None, "UNSEEN")[1:]
                # recuperation de ID des mails
                items = items[0].split()

                for emailid in items:
                    # récupérer les elements du mail
                    data = m_c.fetch(emailid, "(RFC822)")[1]
                    # récupérer le contenu du mail
                    email_body = data[0][1]
                    # analyse du contenu du mail pour obtenir un objet de messagerie
                    mail = email.message_from_bytes(email_body)

                    # Vérifie s'il y as des fichiers attachés
                    if mail.get_content_maintype() != "multipart":
                        continue

                    # Utilisation de walk pour créer un générateur itérable
                    # des mails non récurrents
                    for part in mail.walk():
                        # pour sauter les conteneurs
                        if part.get_content_maintype() == "multipart":
                            continue

                        # si c'est une pièce jointe
                        if part.get("Content-Disposition") is None:
                            continue

                        filename = part.get_filename()
                        counter = 1

                        # s'il n'y a pas de nom de fichier, on en créer un avec un compteur pour
                        # éviter les doublons
                        if not filename:
                            filename = "part-%03d%s" % (counter, "bin")
                            counter += 1

                        att_path = self.repertoire + "/" + filename

                        # Si le fichier n'existe pas on l'importe
                        if not os.path.isfile(att_path):
                            f_p = open(att_path, "wb")
                            f_p.write(part.get_payload(decode=True))
                            f_p.close()

                            # Si le fichier est un zip alors on décompresse tous les fichiers de
                            # l'archive et on efface le zip
                            if zipfile.is_zipfile(att_path):
                                ext = os.path.splitext(os.path.basename(att_path))[1:]

                                if ext in {".xlsx", ".xls"}:
                                    pass

                                else:
                                    with zipfile.ZipFile(att_path) as z_file:
                                        z_file.extractall(self.repertoire)
                                    os.remove(att_path)

            except MailError:
                ligne = (
                    f"{datetime.now().isoformat()} | Erreur de récupération des mails : "
                    f"{sys.exc_info()[1]} - "
                    f"{self.fimap}\n"
                )
                self.write_log_file(ligne)

            finally:
                m_c.close()

    def boucle_de_recuperation_des_pieces_jointes(self):
        """
        Fonction complète de récupération des pièces jointes
            :return: None
        """
        self.recuperation_pieces_jointes_mail_non_lus(log=False)
        self.suppression_repertoires_recursif(log=False)
        self.suppression_fichiers_non_souhaite_recursif(log=False)
        # self.a_garder_plus_recent(log=True)
        self.liste_des_fichiers_recuperes(log=False)

    def recuperer_fichier_plus_recent(self):
        """
        Fonction complète de récupération de la pièce jointe la plus récente
            :return: None
        """
        self.recuperation_pieces_jointes_mail_non_lus(log=False)
        self.suppression_repertoires_recursif(log=False)
        self.suppression_fichiers_non_souhaite_recursif(log=False)
        self.a_garder_plus_recent(log=True)
        self.liste_des_fichiers_recuperes(log=False)
