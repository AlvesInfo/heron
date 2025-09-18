"""Module de gestion des Exeptions du module heron


"""


class HeronError(Exception):
    """Exception niveau module"""


class LaunchDoesNotExistsError(Exception):
    """Exception niveau module"""


class EmailException(Exception):
    """Exception niveau module pour les smails"""


class ArticlesWithoutAccountException(Exception):
    """Exception niveau module pour les artilces sans comptes"""


class ArticlesAccountValidationException(Exception):
    """Exception niveau module pour les artilces sans comptes"""


class ArticlesAccountException(Exception):
    """Exception niveau module pour les artilces sans comptes"""
