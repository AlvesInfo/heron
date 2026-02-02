from copy import deepcopy
from apps.core.functions.functions_setups import *
from apps.articles.models import Article, ArticleAccount


def transfert_receptions_articles():
    articles = Article.objects.filter(
        third_party_num="BBGR001",
        reference__in=(
            "PLV-PLV",
            "PLV-AUDITION",
            "PLV-ACCESS OPTIQUE",
            "PLV-ACCESSOIRES",
            "PLV-ACCESS AUDIO",
            "FRAMES-CONSOMMABLE",
            "CONTACT-CONTACTO SOL",
            "CASES-CONSOMMABLE",
            "AUDIO-CONSOMMABLE",
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
        obj, created = Article.objects.get_or_create(**a_dict)
        print(obj, created)


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
            obj, created = ArticleAccount.objects.get_or_create(
                article=Article.objects.filter(reference=article.get("reference"))[0],
                **account,
            )
            print(obj, created)


if __name__ == "__main__":
    transfert_receptions_articles()
    transfert_receptions_accounts()
