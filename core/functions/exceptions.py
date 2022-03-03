"""Module des exceptions personalisées pour les fonctions
"""


class DatesFunctionsError(Exception):
    """Exceptions pour le module fonctions_dates
    """


class OracleConnectionError(Exception):
    """Exceptions pour les connection Cx_Oracle
    """


class MySqlConnectionError(Exception):
    """Exceptions pour les connection MySql
    """


class FtpError(Exception):
    """Exceptions pour le module fonctions_ftp
    """


class ExtensionError(Exception):
    """Exceptions pour les défaut d'exception
    """


class ExcelError(Exception):
    """Exceptions pour les défauts des fonctions excel
    """


class ImportExcelError(Exception):
    """Exceptions pour les défauts des imports des models fixtures
    """


class ProjetError(Exception):
    """Exceptions pour les défauts sur l'app Projet
    """
