"""
FR : Module de post traitement après import data
EN : Post-processing module after data import

Commentaire:

created at: 2023-05-13
created by: Paulo ALVES

modified at: 2023-05-13
modified by: Paulo ALVES
"""
from apps.centers_purchasing.bin.duplicates import duplicates_delete_accounts
from apps.centers_purchasing.bin.update_account_article import set_update_articles_account


def post_axe_pro_account():
    """
    Post traitement de l'import des axe_pro/comptes : purge des doublons créés par l'import
    (rubrique nulle hors unicité SQL, la ligne importée gagne), puis mise à jour des articles
    :return:  None
    """
    duplicates_delete_accounts()
    set_update_articles_account()
