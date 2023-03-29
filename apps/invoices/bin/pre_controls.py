# pylint: disable=E0401
"""
FR : Module de contrôles avant le lancement des refacturations
EN : Checks module before launching re-invoicing

Commentaire:

created at: 2023-03-12
created by: Paulo ALVES

modified at: 2023-03-12
modified by: Paulo ALVES
"""
from django.db import connection

from apps.invoices.sql_files.sql_controls import (
    SQL_ARTCILES_EDI_CONTROL,
    SQL_TIERS_CONTROL,
    SQL_GROUPING_CONTROL,
    SQL_ACCOUNTS_CONTROL,
    SQL_VAT_CONTROL,
    SQL_VAT_REGIME_CONTROL,
    SQL_CCT_CONTROL,
    SQL_CATEGORY_CONTROL,
    SQL_SUB_CATEGORY_CONTROL,
    SQL_CENTER_CONTROL,
    SQL_SIGNBOARD_CONTROL,
)


def control_articles_axes():
    """
    Controle que tous les axes (BU, PRJ, PRO, PYS, RFA) soient saisis dans edi_ediimport
    """

    with connection.cursor() as cursor:
        cursor.execute(SQL_ARTCILES_EDI_CONTROL)
        missing_list = [missings[0] for missings in cursor.fetchall()]

        if missing_list:
            return "Vous avez des manquants sur les axes, dans les imports ou les saisies"

    return ""


def control_tiers():
    """
    Controle que tous les tiers X3 dans edi_ediimport
    """

    with connection.cursor() as cursor:
        cursor.execute(SQL_TIERS_CONTROL)
        missing_list = [missings[0] for missings in cursor.fetchall()]

        if missing_list:
            return "Vous avez des manquants sur les tiers X3, dans les imports ou les saisies"

    return ""


def control_groupings():
    """
    Controle que tous les ensembles ("AXE PRO", "REGROUPEMENT DE FACTURATION")
    soient décrits dans le Dictionnaire Axe Pro/Regroupement de facturation.
    Url : /centers_purchasing/axe_grouping_list/
    """

    with connection.cursor() as cursor:
        cursor.execute(SQL_GROUPING_CONTROL)
        missing_list = [missings[0] for missings in cursor.fetchall()]

        if missing_list:
            return "Vous avez des axes, qui ne sont pas dans les regroupement de facturations"

    return ""


def control_accounts():
    """
    Controle que tous les ensembles ("Centrale fille", "Grande Catégorie", "AXE PRO", "TVA")
    soient décrits dans le Dictionnaire des Comptes debit crédit.
    Url : /centers_purchasing/account_axe_list/
    """

    with connection.cursor() as cursor:
        cursor.execute(SQL_ACCOUNTS_CONTROL)
        missing_list = [missings[0] for missings in cursor.fetchall()]

        if missing_list:
            return (
                "Vous avez des comptes, qui ne sont pas "
                "dans le Dictionnaire des Comptes debit crédit"
            )

    return ""


def control_vat():
    """
    Controle que tous les TVA soient saisis dans edi_ediimport
    """

    with connection.cursor() as cursor:
        cursor.execute(SQL_VAT_CONTROL)
        missing_list = [missings[0] for missings in cursor.fetchall()]

        if missing_list:
            return "Vous avez des manquants sur les TVA X3, dans les imports ou les saisies"

    return ""


def control_vat_regime():
    """
    Controle que tous les régimes de TVA soient saisis dans edi_ediimport
    """

    with connection.cursor() as cursor:
        cursor.execute(SQL_VAT_REGIME_CONTROL)
        missing_list = [missings[0] for missings in cursor.fetchall()]

        if missing_list:
            return "Vous avez des manquants sur les régimes de TAX, dans les imports ou les saisies"

    return ""


def control_cct():
    """
    Controle que tous les CCT X3 soient saisis dans edi_ediimport
    """

    with connection.cursor() as cursor:
        cursor.execute(SQL_CCT_CONTROL)
        missing_list = [missings[0] for missings in cursor.fetchall()]

        if missing_list:
            return "Vous avez des manquants sur les CCT X3, dans les imports ou les saisies"

    return ""


def control_categories():
    """
    Controle que toutes les Grandes Catégories soient saisies dans edi_ediimport
    """

    with connection.cursor() as cursor:
        cursor.execute(SQL_CATEGORY_CONTROL)
        missing_list = [missings[0] for missings in cursor.fetchall()]

        if missing_list:
            return (
                "Vous avez des manquants sur les Grandes Catégories, "
                "dans les imports ou les saisies"
            )

    return ""


def control_sub_categories():
    """
    Controle que toutes les Rubriques Presta soient saisies dans edi_ediimport
    """

    with connection.cursor() as cursor:
        cursor.execute(SQL_SUB_CATEGORY_CONTROL)
        missing_list = [missings[0] for missings in cursor.fetchall()]

        if missing_list:
            return (
                "Vous avez des manquants sur les Rubriques Presta, dans les imports ou les saisies"
            )

    return ""


def control_alls_missings():
    """
    Contrôle de tous les manques dans edi_ediimport
    """
    controls_dict = {}

    with connection.cursor() as cursor:
        # ARTICLES
        cursor.execute(SQL_ARTCILES_EDI_CONTROL)
        missing_list = [missings[0] for missings in cursor.fetchall()]
        controls_dict["articles"] = (
            "Vous avez des manquants sur les axes, dans les imports ou les saisies"
            if missing_list
            else ""
        )
        # TIERS X3 ("third_party_num")
        cursor.execute(SQL_TIERS_CONTROL)
        missing_list = [missings[0] for missings in cursor.fetchall()]
        controls_dict["tiers"] = (
            "Vous avez des manquants sur les tiers X3, dans les imports ou les saisies"
            if missing_list
            else ""
        )

        # TVA X3
        cursor.execute(SQL_VAT_CONTROL)
        missing_list = [missings[0] for missings in cursor.fetchall()]
        controls_dict["tva"] = (
            "Vous avez des manquants sur les TVA X3, dans les imports ou les saisies"
            if missing_list
            else ""
        )

        # REGIME DE TAXE X3
        cursor.execute(SQL_VAT_REGIME_CONTROL)
        missing_list = [missings[0] for missings in cursor.fetchall()]
        controls_dict["regimes"] = (
            "Vous avez des manquants sur les régimes de TAX, dans les imports ou les saisies"
            if missing_list
            else ""
        )

        # CCT X3
        cursor.execute(SQL_CCT_CONTROL)
        missing_list = [missings[0] for missings in cursor.fetchall()]
        controls_dict["cct"] = (
            "Vous avez des manquants sur les CCT X3, dans les imports ou les saisies"
            if missing_list
            else ""
        )

        # GRANDE CATEGORIES
        cursor.execute(SQL_CATEGORY_CONTROL)
        missing_list = [missings[0] for missings in cursor.fetchall()]
        controls_dict["categories"] = (
            "Vous avez des manquants sur les Grandes Catégories, dans les imports ou les saisies"
            if missing_list
            else ""
        )

        # RUBRIQUES PRESTA
        cursor.execute(SQL_SUB_CATEGORY_CONTROL)
        missing_list = [missings[0] for missings in cursor.fetchall()]
        controls_dict["rubriques_presta"] = (
            "Vous avez des manquants sur les Rubriques Presta, dans les imports ou les saisies"
            if missing_list
            else ""
        )

        # REGROUPEMENT FACTURATION
        cursor.execute(SQL_GROUPING_CONTROL)
        missing_list = [missings[0] for missings in cursor.fetchall()]
        controls_dict["regroupements"] = (
            (
                "Vous avez des axes, qui ne sont pas dans les regroupement de facturations "
                "(Menu : paramétrage -> FACTURATION -> Axe PRO/Regroupements)"
            )
            if missing_list
            else ""
        )

        # COMPTES DEBIT / CREDITS
        cursor.execute(SQL_ACCOUNTS_CONTROL)
        missing_list = [missings[0] for missings in cursor.fetchall()]
        controls_dict["debit_credit"] = (
            (
                "Vous avez des comptes, qui ne sont pas dans le "
                "Dictionnaire des Comptes debit crédit. "
                "(Menu : paramétrage -> FACTURATION -> Axe PRO/Comptes)"
            )
            if missing_list
            else ""
        )

        # CENTRALE FILLE
        cursor.execute(SQL_CENTER_CONTROL)
        missing_list = [missings[0] for missings in cursor.fetchall()]
        controls_dict["center_purchase"] = (
            "Vous avez des manquants sur les Centrales Filles, dans les imports ou les saisies"
            if missing_list
            else ""
        )

        # ENSEIGNE
        cursor.execute(SQL_SIGNBOARD_CONTROL)
        missing_list = [missings[0] for missings in cursor.fetchall()]
        controls_dict["signboard"] = (
            "Vous avez des manquants sur les Enseignes, dans les imports ou les saisies"
            if missing_list
            else ""
        )

    return {key: value for key, value in controls_dict.items() if value}
