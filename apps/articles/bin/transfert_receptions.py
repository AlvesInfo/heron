"""Transfert des articles de réception BBGR vers le tiers BBGR006."""

from copy import deepcopy

import django

import apps.core.functions.functions_setups  # noqa: F401  (amorçage Django pour le lancement en script)
from apps.accountancy.models import VatSage
from apps.articles.models import Article, ArticleAccount
from apps.centers_purchasing.models import ChildCenterPurchase
from heron.loggers import LOGGER_IMPORT


def transfert_receptions_articles():
    """Copie les articles de réception BBGR001 vers le tiers BBGR006."""
    articles = Article.objects.filter(
        third_party_num="BBGR001",
        reference__in=(
            "PLV-PLV",
            "PLV-CONSOMMABLE",
            "PLV-AUDITION",
            "PLV-ACCESS OPTIQUE",
            "PLV-ACCESSOIRES",
            "PLV-ACCESS AUDIO",
            "FRAMES-MONTURE SOL",
            "FRAMES-MONTURE OPT",
            "FRAMES-CONSOMMABLE",
            "FRAMES-ACCESS OPTIQUE",
            "CONTACT-CONTACTO SOL",
            "CASES-CONSOMMABLE",
            "AUDIO-CONSOMMABLE",
            "AUDIO-ACCESS AUDIO",
            "ACCESSORIES-MONTURE OPT",
            "ACCESSORIES-CONSOMMABLE",
            "ACCESSORIES-ACCESS OPTIQUE",
        ),
    ).values()

    for article in articles:
        a_dict = deepcopy(article)
        del a_dict["uuid_identification"]
        del a_dict["created_at"]
        del a_dict["modified_at"]
        del a_dict["id"]
        a_dict["third_party_num_id"] = "BBGR006"
        try:
            obj, created = Article.objects.get_or_create(**a_dict)
            LOGGER_IMPORT.info("%s %s", obj, created)
        except Article.DoesNotExist:
            LOGGER_IMPORT.exception("Article introuvable au transfert des réceptions")
        except django.db.utils.IntegrityError:
            LOGGER_IMPORT.exception("Erreur d'intégrité au transfert des réceptions")


def transfert_receptions_accounts():
    """Copie les comptes des articles de réception BBGR001 vers ceux de BBGR006."""
    articles_uuid = Article.objects.filter(
        third_party_num="BBGR001",
        reference__in=(
            "PLV-PLV",
            "PLV-CONSOMMABLE",
            "PLV-AUDITION",
            "PLV-ACCESS OPTIQUE",
            "PLV-ACCESSOIRES",
            "PLV-ACCESS AUDIO",
            "FRAMES-MONTURE SOL",
            "FRAMES-MONTURE OPT",
            "FRAMES-CONSOMMABLE",
            "FRAMES-ACCESS OPTIQUE",
            "CONTACT-CONTACTO SOL",
            "CASES-CONSOMMABLE",
            "AUDIO-CONSOMMABLE",
            "AUDIO-ACCESS AUDIO",
            "ACCESSORIES-MONTURE OPT",
            "ACCESSORIES-CONSOMMABLE",
            "ACCESSORIES-ACCESS OPTIQUE",
        ),
    ).values("uuid_identification", "reference")

    for article in articles_uuid:
        accounts = ArticleAccount.objects.filter(article=article.get("uuid_identification")).values(
            "purchase_account", "sale_account", "vat", "child_center"
        )

        for account in accounts:
            child = deepcopy(account.get("child_center"))
            vat = deepcopy(account.get("vat"))
            del account["child_center"]
            del account["vat"]

            try:
                obj, created = ArticleAccount.objects.get_or_create(
                    article=Article.objects.get(
                        third_party_num="BBGR006", reference=article.get("reference")
                    ),
                    child_center=ChildCenterPurchase.objects.get(code=child),
                    vat=VatSage.objects.get(vat=vat),
                    **account,
                )
                LOGGER_IMPORT.info("%s %s", obj, created)
            except (Article.DoesNotExist, ArticleAccount.DoesNotExist):
                LOGGER_IMPORT.exception("Article ou compte introuvable au transfert des comptes")
            except django.db.utils.IntegrityError:
                LOGGER_IMPORT.exception("Erreur d'intégrité au transfert des comptes")


if __name__ == "__main__":
    transfert_receptions_articles()
    transfert_receptions_accounts()
