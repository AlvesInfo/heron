from django.urls import path

from apps.articles.views import (
    # ARTICLES
    SuppliersArticlesList,
    ArticlesList,
    ArticleCreate,
    ArticleUpdate,
    articles_search_list,
    articles_export_list,
    ArticleAccountCreate,
    ArticleAccountUpdate,
    delete_articles_account_vat,
    # NOUVEAUX ARTICLES
    new_articles_list,
    articles_new_validation,
    articles_news_export_list,
    # ARTICLES SANS COMPTES
    articles_without_account_list,
    articles_without_account_export_list,
    update_articles_without_account,
    # ARTICLES AVEC COMPTES
    articles_account_list
)

app_name = "apps.articles"

urlpatterns = [
    # Articles
    *[
        path(
            "suppliers_articles_list/<str:category>/",
            SuppliersArticlesList.as_view(),
            name="suppliers_articles_list",
        ),
        path(
            "articles_list/<str:third_party_num>/<str:category>/",
            ArticlesList.as_view(),
            name="articles_list",
        ),
        path(
            "article_create/<str:third_party_num>/<str:category>/",
            ArticleCreate.as_view(),
            name="article_create",
        ),
        path(
            "article_update/<str:third_party_num>/<int:pk>/",
            ArticleUpdate.as_view(),
            name="article_update",
        ),
        path(
            "articles_export_list/<str:third_party_num>/<str:category>/",
            articles_export_list,
            name="articles_export_list",
        ),
        path(
            "articles_search_list/",
            articles_search_list,
            name="articles_search_list",
        ),
        # COMPTES PAR TAUX DE TVA ET CENTRALE DES ARTICLES
        path(
            "articles_account_vat_create/<int:article_pk>/",
            ArticleAccountCreate.as_view(),
            name="articles_account_vat_create",
        ),
        path(
            "articles_account_vat_update/<int:article_pk>/<int:pk>/",
            ArticleAccountUpdate.as_view(),
            name="articles_account_vat_update",
        ),
        path(
            "delete_articles_account_vat/",
            delete_articles_account_vat,
            name="delete_articles_account_vat",
        ),
    ],
    # NOUVEAUX ARTICLES
    *[
        path(
            "new_articles_list/",
            new_articles_list,
            name="new_articles_list",
        ),
        path(
            "articles_new_validation/",
            articles_new_validation,
            name="articles_new_validation",
        ),
        path(
            "articles_news_export_list/",
            articles_news_export_list,
            name="articles_news_export_list",
        ),
    ],
    # ARTICLES SANS COMPTES
    *[
        path(
            "articles_without_account_list/",
            articles_without_account_list,
            name="articles_without_account_list",
        ),
        path(
            "articles_without_account_export_list/",
            articles_without_account_export_list,
            name="articles_without_account_export_list",
        ),
        path(
            "update_articles_without_account/",
            update_articles_without_account,
            name="update_articles_without_account",
        ),
    ],
    # ARTICLES AVEC COMPTES
    *[
        path(
            "articles_account_list/",
            articles_account_list,
            name="articles_account_list",
        ),
        # path(
        #     "articles_without_account_export_list/",
        #     articles_without_account_export_list,
        #     name="articles_without_account_export_list",
        # ),
    ],
]
