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
        return {"purchase_invoice": "on", "sale_invoice": "on"}

    if sens == "1":
        return {"purchase_invoice": "off", "sale_invoice": "on"}

    return {"purchase_invoice": "on", "sale_invoice": "off"}