from django.urls import path

from apps.articles.views import (
    SuppliersArticlesList,
    ArticlesList,
    ArticleCreate,
    ArticleUpdate,
    articles_export_list,
)

app_name = "apps.articles"

urlpatterns = [
    # Articles
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
]
