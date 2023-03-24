# pylint: disable=
"""
FR : Module des outils de gestion de l'application edi
EN : Edi application management tools module

Commentaire:

created at: 2023-01-18
created by: Paulo ALVES

modified at: 2023-01-18
modified by: Paulo ALVES
"""


def get_sens(sens: str):
    """Retourne le sens de facturation AC, AC/VE, VE"""
    if sens == "2":
        return {"purchase_invoice": "true", "sale_invoice": "true"}

    if sens == "1":
        return {"purchase_invoice": "false", "sale_invoice": "true"}

    return {"purchase_invoice": "true", "sale_invoice": "false"}