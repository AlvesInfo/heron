"""Module de gestion des Exeptions du module heron


"""


class HeronError(Exception):
    """Exception niveau module"""


class LaunchDoesNotExistsError(Exception):
    """Exception niveau module"""


class EmailException(Exception):
    """Exception niveau module pour les smails"""
