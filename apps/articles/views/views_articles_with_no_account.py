# pylint: disable=E0401,
"""
Views des Articles sans comptes comptables
"""
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, redirect, reverse
from django.db.models import Max, Value, CharField, Exists, OuterRef, Count, FilteredRelation, Q
from django.db.models.functions import Coalesce, Cast

from apps.core.functions.functions_http import get_pagination_buttons
from apps.articles.models import Article
from apps.edi.models import EdiImport
from apps.centers_purchasing.models import AccountsAxeProCategory


# ECRANS DES ARTICLES SANS COMPTES COMPTABLES EN ACHATS ET VENTES ==================================
def articles_without_account_list(request):
    """Affichage de tous les articles qui n'ont pas de comptes comptable X3, présents
    dans les imports
    """
    limit = 200

    queryset = (
        EdiImport.objects.annotate(
            supplierm=Max("supplier"),
            libellem=Max("libelle"),
            sub_categoryc=Coalesce(Cast("sub_category", output_field=CharField()), Value("")),
        )
        .annotate(
            without=Exists(
                AccountsAxeProCategory.objects.annotate(
                    sub_categoryc=Coalesce(
                        Cast("sub_category", output_field=CharField()), Value("")
                    ),
                ).filter(
                    child_center=OuterRef("code_center"),
                    axe_pro=OuterRef("axe_pro"),
                    big_category=OuterRef("big_category"),
                    sub_categoryc=OuterRef("sub_categoryc"),
                    vat=OuterRef("vat"),
                )
            ),
            article=Article.objects.filter(
                third_party_num=OuterRef("third_party_num"),
                reference=OuterRef("reference_article"),
            ).values("pk"),
        )
        .annotate()
        .values(
            "code_center",
            "third_party_num",
            "supplierm",
            "reference_article",
            "libellem",
            "axe_pro__section",
            "big_category__name",
            "sub_category__name",
            "vat",
            "article",
        )
        .exclude(without=True)
        .annotate(Count("id"))
    )
    paginator = Paginator(queryset, limit)
    page = request.GET.get("page")

    try:
        articles = paginator.page(page)
    except PageNotAnInteger:
        articles = paginator.page(1)
    except EmptyPage:
        articles = paginator.page(paginator.num_pages)

    count = queryset.count()
    titre_count = ""

    if count == 1:
        titre_count = " (1 article sans comptes)"

    if count > 1:
        titre_count = f" ({str(count)} articles sans comptes)"

    context = {
        "articles": articles,
        "pagination": get_pagination_buttons(
            articles.number, paginator.num_pages, nbre_boutons=5, position_color="darkgrey"
        ),
        "num_items": paginator.count,
        "num_pages": paginator.num_pages,
        "start_index": (articles.start_index() - 1) if articles.start_index() else 0,
        "end_index": articles.end_index(),
        "titre_table": f"1.2 - Articles sans comptes{titre_count}",
        "url_validation": reverse("articles:articles_new_validation"),
        "url_redirect": reverse("articles:new_articles_list"),
    }
    return render(request, "articles/articles_without_account.html", context=context)


"""
SELECT 
    "edi_ediimport"."third_party_num", 
    "edi_ediimport"."reference_article", 
    "edi_ediimport"."code_center", 
    "edi_ediimport"."axe_pro", 
    "edi_ediimport"."uuid_big_category", 
    "edi_ediimport"."vat", 
    MAX("edi_ediimport"."supplier") AS "supplierm", 
    MAX("edi_ediimport"."libelle") AS "libellem", 
    COALESCE(CAST("edi_ediimport"."uuid_sub_big_category" AS varchar), '') AS "sub_categoryc", 
    (
        SELECT U0."uuid_identification" 
        FROM "articles_article" U0 
        WHERE (
            U0."reference" = "edi_ediimport"."reference_article" 
            AND U0."third_party_num" = "edi_ediimport"."third_party_num"
        )
    ) AS "article", 
    COUNT("edi_ediimport"."id") AS "id__count" 
    FROM "edi_ediimport" 
    WHERE NOT (
        EXISTS(
            SELECT (1) AS "a" 
            FROM "centers_purchasing_accountsaxeprocategory" U0 
            WHERE (
                U0."axe_pro" = "edi_ediimport"."axe_pro" 
                AND U0."uuid_big_category" = "edi_ediimport"."uuid_big_category" 
                AND U0."child_center" = "edi_ediimport"."code_center" 
                AND COALESCE(CAST(U0."uuid_sub_category" AS varchar), '') = COALESCE(CAST("edi_ediimport"."uuid_sub_big_category" AS varchar), '') 
                AND U0."vat" = "edi_ediimport"."vat"
            ) 
            LIMIT 1
        )
    ) 
    GROUP BY 
        "edi_ediimport"."third_party_num", 
        "edi_ediimport"."reference_article", 
        "edi_ediimport"."code_center", 
        "edi_ediimport"."axe_pro", 
        "edi_ediimport"."uuid_big_category", 
        "edi_ediimport"."vat", 
        COALESCE(CAST("edi_ediimport"."uuid_sub_big_category" AS varchar), ''), 
        (
            SELECT U0."uuid_identification" 
            FROM "articles_article" U0 
            WHERE (
                U0."reference" = "edi_ediimport"."reference_article" 
                AND U0."third_party_num" = "edi_ediimport"."third_party_num"
            )
        ) 
        ORDER BY "edi_ediimport"."third_party_num" ASC, "article" ASC
"""
