# pylint: disable=C0411, C0303, E1101, C0413, I1101, R1710
"""Module pour récupérer les fichier sur un ftp

Commentaire:

created at: 2022-02-03
created by: Paulo ALVES

modified at: 2022-02-04
modified by: Paulo ALVES
"""
import logging
import ftplib
from ftplib import all_errors
from pathlib import Path
import shutil

from apps.core.functions.exceptions import FtpError

logger = logging.getLogger("django")


class FtpFiles(ftplib.FTP):
    """Récupération de fichiers sur un FTP"""

    def __init__(self, host, port, user_login, senha):
        """Instanciation des variables
            :param host: Adresse ip du serveur FTP
            :param port: port du serveur FTP
            :param user_login: Nom de login
            :param senha: Mot de passe
        """
        ftplib.FTP.__init__(self, "")
        self.host = host
        self.port = port
        self.user = user_login
        self.password = senha
        self.get_connection()

    def get_connection(self):
        """Fonction de connection au site FTP
        """
        try:
            self.connect(self.host, self.port)
            self.login(self.user, self.password)

        except OSError as erreur:
            logger.exception("Ftp impossible à atteindre, connexion réseau impossible")
            raise FtpError from erreur

        except TypeError as erreur:
            logger.exception("Ftp TypeError")
            raise FtpError from erreur

        except all_errors as erreur:
            logger.exception("Une erreur c'est procuite à la connexion FTP")
            raise FtpError from erreur

    @staticmethod
    def get_command(command, *args):
        """Fonction d'envoi des commandes au site FTP
            :param command: commande à envoyer
            :param args: arguments de la commande envoyée
            :return: commande
        """
        try:
            return command(*args)

        except all_errors as erreur:
            logger.exception("Une erreur c'est produite à la connexion FTP")
            raise FtpError from erreur

    def send_files(self, files_to_send, ftp_dir, move_file_dir=None):
        """Fonction pour dépôt de fichiers sur le FTP
            :param files_to_send: fichier ou itérable des fichiers à déposer
            :param ftp_dir: Répertoire du FTP ou déposer les fichiers
            :param move_file_dir: Répertoire ou déplacer les fichiers après dépot
            :return: None
        """
        try:
            if isinstance(files_to_send, (str,)):
                files = [Path(files_to_send)]

            else:
                files = [Path(fichier) for fichier in files_to_send]

            self.cwd(ftp_dir)
            list_dir = self.nlst()

            for file in files:

                if file.name not in list_dir and file.is_file():
                    send_test = False
                    with open(file, "rb") as send_file:
                        try:
                            self.storbinary("STOR " + file.name, send_file)
                            send_test = True

                        except all_errors as err:
                            print(f"placer log ici {err}")

                    if move_file_dir is not None and send_test:
                        file_move = Path(move_file_dir) / file.name
                        shutil.move(file, file_move)

        except FtpError:
            logger.exception("Erreur dans send files")

    def get_files(self, files_to_get, files_dir, ftp_dir, ftp_move_dir=None):
        """Fonction qui récupère les fichier sur le FTP
            :param files_to_get: plusieurs solutions possibles:
                    '__all__'                   : on récupère tous les fichiers
                    ['test.csv', 'test.json']   : on récupère les fichiers d'une liste
                    '__first__'                 : on récupère le fichier le plus récent
                    '__last__'                  : on récupère le fichier le plus plus ancien
            :param files_dir: Répertoire local où déposé les fichiers
            :param ftp_dir: Répertoire du FTP ou récupérer les fichiers
            :param ftp_move_dir: plusieurs solutions possibles:
                    None (default): On laisse les fichiers ou ils sont sur le FTP
                    '__delete__'  : On supprime les fichiers récupérés du FTP
                    '/dir/to/move': Répertoire ou on déplace les fichiers récupérés sur le FTP
            :return: None
        """
        try:
            self.cwd(ftp_dir)
            ftp_files_list = sorted(self.nlst(), key=lambda x: self.voidcmd(f"MDTM {x}"))
            ftp_files_to_get = []

            # Si on veut tous les fichiers
            if files_to_get == "__all__":
                ftp_files_to_get = ftp_files_list

            # Si on veut des fichiers choisis
            elif isinstance(files_to_get, (list, tuple)):
                ftp_files_to_get = [f for f in files_to_get if f in ftp_files_list]

            # Si on veut le fichier le plus récent
            elif files_to_get == "__first__":
                ftp_files_to_get = [ftp_files_list[-1]]

            # Si on veut le fichier le plus ancien
            elif files_to_get == "__last__":
                ftp_files_to_get = [ftp_files_list[0]]

            # On sauvegarde chaque fichier à récupérer
            for ftp_file in ftp_files_to_get:
                self.get_file(files_dir, ftp_file)

                if ftp_move_dir is not None:
                    self.post_get_file(ftp_file, ftp_move_dir)

            return ftp_files_to_get

        except IndexError:
            logger.warning("le répertoire du ftp, demandé est vide")

        except FtpError:
            logger.exception("la récupération des fichiers sur le ftp a généré une erreur")

    def get_file(self, files_dir, ftp_file):
        """Fonction de sauvegarde en local du fichier récupéré sur le ftp
            :param files_dir: Répertoire local ou déposé les fichiers
            :param ftp_file: fichier à récupérer
            :return: None Errors
        """
        try:
            file_to_save = Path(files_dir) / ftp_file
            with open(file_to_save, "wb") as file:
                self.retrbinary("RETR " + ftp_file, file.write)

        except all_errors as erreur:
            raise FtpError from erreur

    def post_get_file(self, ftp_file, ftp_move_dir):
        """Fonction de traitement Post get_files
            :param ftp_file: fichier du TP à traiter
            :param ftp_move_dir: plusieurs solutions possibles:
                                '__delete__'  : On supprime les fichiers récupérés du FTP
                                '/dir/to/move': Répertoire ou on déplace les fichiers récupérés
            :return: None or Errors
        """
        try:
            if ftp_move_dir == "__delete__":
                self.delete(ftp_file)
            else:
                file_path_destination = ftp_move_dir + "/" + ftp_file
                self.rename(ftp_file, file_path_destination)

        except all_errors as erreur:
            raise FtpError from erreur
