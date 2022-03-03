# pylint: disable=C0411, E1101, C0413, I1101, E0611, R1710
"""Module de gestion des connection oracle de base

Commentaire:

created at: 2019-11-05
created by: Paulo ALVES

modified at: 2019-12-27
modified by: Paulo ALVES

"""
import sys
import os
from datetime import datetime
import logging

import cx_Oracle as Cx

from core.functions.functions_setups import settings

os.environ["NLS_LANG"] = "FRENCH_FRANCE.UTF8"

logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.DEBUG)


class OracleCnx:
    """
    Classe qui se connecte a une base de donnee ORACLE
            pour se connecter :
                oracle_cnx = InterrogationBaseoracle('localhost', 1527, 'BASE', 'LOGIN', 'PASSWORD',
                LOG_FILE)
                oracle_cnx.Get_connection()
            pour se deconnecter :
                oracle_cnx.close()
        si l'on veut une ecrire les erreurs dans un fichier de log
        on lui passe LOG_FILE = "/Chemin/fichier.txt"
    """

    def __init__(self, log_file=None):
        self.cnx = None
        self.host = settings.config("HOST_DATABASE_CG")
        self.port = settings.config("PORT_DATABASE_CG")
        self.database = settings.config("NAME_DATABASE_CG")
        self.username = settings.config("USER_DATABASE_CG")
        self.password = settings.config("PWD_DATABASE_CG")
        self.log_file = log_file

    def get_cnx(self):
        """
            Initie une connexion a Oracle
        """
        try:
            dsn_str = Cx.makedsn(self.host, self.port, service_name=self.database)
            self.cnx = Cx.connect(
                user=self.username,
                password=self.password,
                dsn=dsn_str,
                encoding="UTF-8",
                nencoding="UTF-16",
            )
            return self.cnx
        except Cx.Error:
            log_line = "{0} | Erreur de Connection a Oracle : {1}\n".format(
                datetime.now().isoformat(), sys.exc_info()[1]
            )
            logging.debug(log_line)
            # write_log(self.log_file, log_line)
            # envoi_mail_erreur(log_line)
            return None

    def close_cnx(self):
        """
            Ferme la connexion a Oracle
        """
        try:
            self.cnx.close()
        except Cx.Error:
            log_line = "{0} | Fermeture de Connection a Oracle Impossible : {1}\n".format(
                datetime.now().isoformat(), sys.exc_info()[1]
            )
            logging.debug(log_line)
            # write_log(self.log_file, log_line)
            # envoi_mail_erreur(log_line)

    def query_select(self, sql_requete=None, params=None):
        """
        retourne le resultat d'un requête sql Oracle
        on lui envoie en parametre la requête sql_requete
        exemple:
            query_select("SELECT * FROM table")
        """
        if params is None:
            params = {}

        if sql_requete:
            cur = self.cnx.cursor()
            try:
                if params:
                    return cur.execute(sql_requete, params).fetchall()

                return cur.execute(sql_requete).fetchall()

            except Cx.Error:
                log_line = "{0} | Erreur de requête Oracle : {1}\n".format(
                    datetime.now().isoformat(), sys.exc_info()[1]
                )
                logging.debug(log_line)

            finally:
                cur.close()

    def query_select_dict(self, sql_requete=None, params=None):
        """
        retourne le resultat d'un requête sql Oracle
        on lui envoie en parametre la requête sql_requete
        exemple:
            query_select("SELECT * FROM table")
        """
        if sql_requete:
            cur = self.cnx.cursor()
            try:
                if params:
                    cur.execute(sql_requete, params)
                else:
                    cur.execute(sql_requete)

                description_list = [str(i[0]).lower() for i in cur.description]
                for row in cur.fetchall():
                    yield dict(zip(description_list, row))
            except Cx.Error:
                log_line = "{0} | Erreur de requête Oracle : {1}\n".format(
                    datetime.now().isoformat(), sys.exc_info()[1]
                )
                logging.debug(log_line)
                # write_log(self.log_file, log_line)
                # envoi_mail_erreur(log_line)
                return None

            finally:
                cur.close()

        return None
