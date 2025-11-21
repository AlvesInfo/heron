# pylint: disable=E0401
"""
FR: Module de contrôles avant le lancement des refacturations
EN: Checks module before launching re-invoicing

Commentaire:

created at: 2023-03-12
created by: Paulo ALVES

modified at: 2023-03-12
modified by: Paulo ALVES
"""

from concurrent.futures import ThreadPoolExecutor, as_completed

from django.db.models import Q
from django.shortcuts import reverse

from apps.core.functions.functions_setups import connection
from apps.invoices.sql_files.sql_controls import (
    SQL_ARTICLES_NEWS,
    SQL_ARTCILES_EDI_CONTROL,
    SQL_TIERS_CONTROL,
    SQL_GROUPING_CONTROL,
    SQL_ACCOUNTS_EDI_IMPORT_CONTROL,
    SQL_ACCOUNTS_ARTICLES,
    SQL_VAT_CONTROL,
    SQL_VAT_REGIME_CONTROL,
    SQL_INTEGRATIONS_CONTROLS,
    SQL_CCT_CONTROL,
    SQL_CATEGORY_CONTROL,
    SQL_SUB_CATEGORY_CONTROL,
    SQL_CENTER_CONTROL,
    SQL_SIGNBOARD_CONTROL,
    SQL_SALES_AXE_BU,
    SQL_INTEGRATIONS,
    SQL_FAMILLES,
    SQL_FRANCHISEUR,
    SQL_CLIENT_NEWS,
    SQL_ABONNEMENTS,
    SQL_RFA,
    SQL_CCT_M,
    SQL_SUPPLIERS_M,
    SQL_CA_COSIUM,
)
from apps.centers_purchasing.sql_files.sql_elements import (
    articles_acuitis_without_accounts,
)
from apps.edi.bin.reset_import import reset_all_imports
from apps.articles.models import Article
from apps.invoices.models import SaleInvoice
from apps.edi.models import EdiImport, EdiImportControl, EdiValidation


def control_articles_axes():
    """
    Controle que tous les axes (BU, PRJ, PRO, PYS, RFA) soient saisis dans edi_ediimport
    """

    with connection.cursor() as cursor:
        cursor.execute(SQL_ARTCILES_EDI_CONTROL)
        missing_list = [missings[0] for missings in cursor.fetchall()]

        if missing_list:
            return (
                "Vous avez des manquants sur les axes, dans les imports ou les saisies"
            )

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
    Url: /centers_purchasing/axe_grouping_list/
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
    Url: /centers_purchasing/account_axe_list/
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
                "Vous avez des manquants sur les Rubriques Presta, "
                "dans les imports ou les saisies"
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
    Contrôle de tous les manquants dans edi_ediimport - Version parallèle
    Exécute toutes les requêtes en parallèle en utilisant le pool Django existant
    Maintient l'ordre dans control_dict
    """
    # Définir toutes les requêtes dans l'ordre avec leur clé et message
    queries = [
        # TIERS X3 ("third_party_num")
        (0, "tiers", SQL_TIERS_CONTROL, ("Il manque des tiers X3", "")),
        # TVA X3
        (
            1,
            "tva",
            SQL_VAT_CONTROL,
            ("Il manque des TVA X3", ""),
        ),
        # REGIME DE TAXE X3
        (
            2,
            "regimes",
            SQL_VAT_REGIME_CONTROL,
            ("Il manque des régimes de TVA", ""),
        ),
        # GRANDE CATEGORIES
        (
            3,
            "categories",
            SQL_CATEGORY_CONTROL,
            ("Il manque des Grandes Catégories", ""),
        ),
        # RUBRIQUES PRESTA
        (
            4,
            "rubriques_presta",
            SQL_SUB_CATEGORY_CONTROL,
            ("Il manque des Rubriques Presta", ""),
        ),
        # REGROUPEMENT FACTURATION
        (
            5,
            "regroupements",
            SQL_GROUPING_CONTROL,
            (
                (
                    "Vous avez des axes, qui ne sont pas dans les regroupement de facturations"
                    " (Menu : paramétrage -> FACTURATION -> Axe PRO/Regroupements)"
                ),
                "",
            ),
        ),
        # CENTRALE FILLE
        (
            6,
            "center_purchase",
            SQL_CENTER_CONTROL,
            ("Il manque des Centrales Filles", ""),
        ),
        # ENSEIGNE
        (
            7,
            "signboard",
            SQL_SIGNBOARD_CONTROL,
            ("Il manque des Enseignes", ""),
        ),
        # AXE BU
        (
            8,
            "axe_bu",
            SQL_SALES_AXE_BU,
            (
                "Vous avez des axe bu manquants sur les Clients en OD ANA",
                "",
            ),
        ),
        # ARTICLES
        (
            9,
            "articles",
            SQL_ARTCILES_EDI_CONTROL,
            ("Il manque des axes, sur les articles", ""),
        ),
        # NOUVEAUX ARTICLES
        (
            10,
            "articles_news",
            SQL_ARTICLES_NEWS,
            (
                "Il y a des nouveaux articles : 1.1 Nouveaux Articles",
                reverse("articles:new_articles_list"),
            ),
        ),
        # ARTICLES SANS COMPTES
        (
            11,
            "articles_without_account",
            SQL_ACCOUNTS_ARTICLES,
            (
                "Il y a des articles sans comptes : 1.2 Articles sans Comptes",
                reverse("articles:articles_without_account_list"),
            ),
        ),
        # VALIDATIONS
        (
            12,
            "integrations",
            SQL_INTEGRATIONS_CONTROLS,
            (
                "Il manque des contrôles : 2.1 Intégrations",
                reverse("validation_purchases:integration_purchases"),
            ),
        ),
        (
            13,
            "integrations",
            SQL_INTEGRATIONS,
            (
                "Il manque des validations : 2.1 Intégrations",
                reverse("validation_purchases:integration_purchases"),
            ),
        ),
        # CCT X3
        (
            14,
            "cct",
            SQL_CCT_CONTROL,
            (
                "Il manque des CCT : 2.2 Contrôle CCT",
                reverse("validation_purchases:without_cct_purchases"),
            ),
        ),
        (
            15,
            "familles",
            SQL_FAMILLES,
            (
                "Il manque la validation : 3.1 Contrôles Familles",
                reverse("validation_purchases:families_invoices_purchases"),
            ),
        ),
        (
            16,
            "franchiseur",
            SQL_FRANCHISEUR,
            (
                "Il manque la validation : 3.1 Contrôles CCT/Franchiseurs",
                reverse("validation_purchases:cct_franchiseurs_purchases"),
            ),
        ),
        (
            17,
            "clients_new",
            SQL_CLIENT_NEWS,
            (
                "Il manque la validation : 3.3 Contrôle Nouveaux Clients",
                reverse("validation_purchases:clients_news_purchases"),
            ),
        ),
        (
            18,
            "abonnements",
            SQL_ABONNEMENTS,
            (
                "Il manque la validation : 3.5 Contrôle Abonnements",
                reverse("validation_purchases:subscriptions_purchases"),
            ),
        ),
        (
            19,
            "rfa",
            SQL_RFA,
            (
                "Il manque la validation : 3.6 Contrôle période RFA",
                reverse("validation_purchases:control_rfa_period"),
            ),
        ),
        (
            20,
            "cct_m",
            SQL_CCT_M,
            (
                "Il manque la validation : 5.0 Contrôle Refac M/M-1 CCT",
                reverse("validation_purchases:refac_cct_purchases"),
            ),
        ),
        (
            21,
            "suppliers_m",
            SQL_SUPPLIERS_M,
            (
                "Il manque la validation : 5.1 Contrôle Fournisseurs M/M-1",
                reverse("validation_purchases:balance_suppliers_purchases"),
            ),
        ),
        (
            22,
            "ca_cosium",
            SQL_CA_COSIUM,
            (
                "Il manque la validation : 5.3 Contrôle CA Cosium/Ventes Héron",
                reverse("validation_purchases:ca_cct"),
            ),
        ),
    ]

    def execute_query(index, key, sql, message):
        """Execute une requête et retourne l'index,
        la clé et le message si des résultats existent
        """
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute(sql)
            missing_list = [missings[0] for missings in cursor.fetchall()]
            return index, key, message if missing_list else ""

    # Exécuter toutes les requêtes en parallèle avec ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=8) as executor:
        # Soumettre toutes les requêtes
        futures = {
            executor.submit(execute_query, index, key, sql, message): index
            for index, key, sql, message in queries
        }

        # Collecter les résultats en préservant l'ordre
        results = [None] * len(queries)
        for future in as_completed(futures):
            index, key, message = future.result()
            results[index] = (key, message)

    # Construire le dictionnaire avec seulement les éléments non vides
    return {key: message for key, message in results if message}


def control_insertion():
    """
    Contrôle que la facturation soit finalizée, pour les factures envoyées par mail
    :return: True si non finalisé, false si finalisé
    """
    sql_control = """
    select 
        1
    from "invoices_invoicecommondetails" "ii"
    join (
        select 
            "uuid_identification"
        from "edi_edivalidation"
        where "final" = false 
        and articles_news = true
        and articles_without_account = true
        and integration = true
        and cct = true
        and families = true
        and franchiseurs = true
        and clients_news = true
        and subscriptions = true
        and refac_cct = true
        and suppliers = true
        and validation_ca = true
        and rfa = true
        limit 1 
    ) "ev" 
    on "ii"."uuid_validation" ="ev"."uuid_identification"
    join "invoices_saleinvoicedetail" "sd" 
    on "ii"."import_uuid_identification" = "sd"."import_uuid_identification"
    join "invoices_saleinvoice" "sa"
    on "sd"."uuid_invoice" = "sa"."uuid_identification"
    where "sa"."send_email" = true
    limit 1
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_control)
        control = cursor.fetchone()

    if control:
        # S'il y a des factures envoyées par mail et non finalisées,
        # alors on supprime tous les imports
        reset_all_imports()

        return True

    return False


def control_emails():
    """
    Contrôle qu'il y ait des factures à envoyer par mail
    :return: True s'il en reste, false sinon
    """
    emails_to_send = SaleInvoice.objects.filter(
        final=False,
        printed=True,
        type_x3__in=(1, 2),
        send_email=False,
    )

    return emails_to_send


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

    edi_validations = (
        EdiValidation.objects.filter(Q(final=False) | Q(final__isnull=True))
        .order_by("-id")
        .first()
    )

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
        "cct": "La Validation sur Ecran 2.2 Contrôle CCT",
        "integration": "La Validation sur Ecran 2.1 Intégrations",
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


def articles_are_valid():
    """Retourne si tous les articles sont valides"""
    return not Article.objects.filter(new_article=True).exists()


def control_all():
    """Contrôle des validations"""


if __name__ == "__main__":
    print(control_alls_missings())
