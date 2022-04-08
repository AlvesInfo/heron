# pylint: disable=
"""Module des Exception du module data_flux

Commentaire:

created at: 2021-10-30
created by: Paulo ALVES

modified at: 2021-10-30
modified by: Paulo ALVES
"""


class ValidationFormError(Exception):
    """Exception du module de Validation"""


class IsValidError(ValidationFormError, AssertionError):
    """Exception sur appel de forms.errors avant fomrs.is_valid()"""


class FluxtypeError(ValidationFormError):
    """Le lux de validation doit être un dictionnaire"""
