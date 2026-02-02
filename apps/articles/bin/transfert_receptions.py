from copy import deepcopy
import django

from apps.core.functions.functions_setups import *
from apps.articles.models import Article, ArticleAccount
from apps.centers_purchasing.models import ChildCenterPurchase
from apps.accountancy.models import VatSage


def transfert_receptions_articles():
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
            print(obj, created)
        except Article.DoesNotExist as e:
            print(str(e)[:100])
        except django.db.utils.IntegrityError as e:
            print(str(e)[:100])


def transfert_receptions_accounts():
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
        accounts = ArticleAccount.objects.filter(
            article=article.get("uuid_identification")
        ).values("purchase_account", "sale_account", "vat", "child_center")

        for account in accounts:
            child = deepcopy(account.get("child_center"))
            vat = deepcopy(account.get("vat"))
            del account["child_center"]
            del account["vat"]

            try:
                obj, created = ArticleAccount.objects.get_or_create(
                    article=Article.objects.get(third_party_num="BBGR006", reference=article.get("reference")),
                    child_center=ChildCenterPurchase.objects.get(code=child),
                    vat=VatSage.objects.get(vat=vat),
                    **account,
                )
                print(obj, created)
            except (Article.DoesNotExist, ArticleAccount.DoesNotExist) as e:
                print(str(e)[:100])
            except django.db.utils.IntegrityError as e:
                print(str(e)[:100])


if __name__ == "__main__":
    transfert_receptions_articles()
    transfert_receptions_accounts()
