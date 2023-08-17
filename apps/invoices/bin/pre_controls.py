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
from django.db.models import Q

from apps.invoices.sql_files.sql_controls import (
    SQL_ARTCILES_EDI_CONTROL,
    SQL_TIERS_CONTROL,
    SQL_GROUPING_CONTROL,
    SQL_ACCOUNTS_EDI_IMPORT_CONTROL,
    SQL_ACCOUNTS_ARTICLES,
    SQL_VAT_CONTROL,
    SQL_VAT_REGIME_CONTROL,
    SQL_CCT_CONTROL,
    SQL_CATEGORY_CONTROL,
    SQL_SUB_CATEGORY_CONTROL,
    SQL_CENTER_CONTROL,
    SQL_SIGNBOARD_CONTROL,
    SQL_SALES_AXE_BU,
)
from apps.articles.models import Article
from apps.edi.models import EdiImport, EdiImportControl, EdiValidation
from apps.centers_purchasing.sql_files.sql_elements import articles_acuitis_without_accounts


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
        cursor.execute(SQL_ACCOUNTS_EDI_IMPORT_CONTROL)
        missing_list = [missings[0] for missings in cursor.fetchall()]

        if missing_list:
            return (
                "Vous avez des comptes, qui ne sont pas "
                "dans le Dictionnaire des Comptes achat et vente"
            )

    return ""


def control_accounts_articles():
    """
    Controle que tous les articles aient un compte achat et vente.
    """

    with connection.cursor() as cursor:
        cursor.execute(SQL_ACCOUNTS_ARTICLES)
        missing_list = [missings[0] for missings in cursor.fetchall()]

        if missing_list:
            return (
                "Vous avez des comptes dans les articles, qui ne sont pas "
                "dans le Dictionnaire des Comptes achat et vente"
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


def control_axe_bu_od_ana():
    """
    Controle qu'il y ait les axes BU pour les clients/maisons, qui sont en OD_ANA.
    """
    with connection.cursor() as cursor:
        cursor.execute(SQL_SALES_AXE_BU)
        missing_list = [missings[0] for missings in cursor.fetchall()]

        if missing_list:
            return "Vous avez des axe bu manquants sur les Clients en OD ANA"

    return ""


def control_alls_missings():
    """
    Contrôle de tous les manquants dans edi_ediimport
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

        # AXE BU
        cursor.execute(SQL_SALES_AXE_BU)
        missing_list = [missings[0] for missings in cursor.fetchall()]
        controls_dict["axe_bu"] = (
            "Vous avez des axe bu manquants sur les Clients en OD ANA" if missing_list else ""
        )

    return {key: value for key, value in controls_dict.items() if value}


def control_validations():
    """
    Contrôle que toutes les validations sont faites
    """
    controls_list = []
    imports_validation = EdiImportControl.objects.filter(
        Q(valid=False) | Q(valid__isnull=True)
    ).exists()

    if imports_validation:
        controls_list.append("Vous avez des imports non validés")

    edi_validations = EdiValidation.objects.filter(Q(final=False) | Q(final__isnull=True)).first()

    # Mise à jour du contrôle des nouveaux articles
    if Article.objects.filter(
        Q(new_article=True)
        | Q(error_sub_category=True)
        | Q(axe_bu__isnull=True)
        | Q(axe_prj__isnull=True)
        | Q(axe_pro__isnull=True)
        | Q(axe_pys__isnull=True)
        | Q(axe_rfa__isnull=True)
        | Q(big_category__isnull=True)
    ).exists():
        edi_validations.articles_news = False
    else:
        edi_validations.articles_news = True

    # Mise à jour du contrôle des articles sans comptes
    if EdiImport.objects.raw(articles_acuitis_without_accounts):
        edi_validations.articles_without_account = False
    else:
        edi_validations.articles_without_account = True

    edi_validations.save()

    validations = {
        "articles_news": "La Validation sur Ecran 1.1 Nouveaux Articles",
        "articles_without_account": "La Validation sur Ecran 1.2 Articles sans Comptes",
        "integration": "La Validation sur Ecran 2.1 Intégrations",
        "cct": "La Validation sur Ecran 2.2 Contrôle CCT",
        "families": "La Validation sur Ecran 3.1 Contrôles Familles",
        "franchiseurs": "La Validation sur Ecran 3.2 Contrôle Franchiseurs",
        "clients_news": "La Validation sur Ecran 3.3 Nouveaux CLients",
        "subscriptions": "La Validation sur Ecran 3.5 Abonnements",
        "rfa": "La Validation sur Ecran 3.6 Contrôle période RFA",
        "refac_cct": "La Validation sur Ecran 5.0 Contrôle Refac par CCT",
        "suppliers": "La Validation sur Ecran 5.1 Contrôle Fournisseurs",
        "validation_ca": "La Validation sur Ecran 5.3 Comparaison CA/Ventes",
    }

    for key, value in edi_validations.__dict__.items():
        if key in validations and not value:
            controls_list.append(validations.get(key))

    print(controls_list)
    return controls_list
