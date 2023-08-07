# pylint: disable=E0401,W0702
"""
Views des Articles sans comptes comptables
"""
import pendulum
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, redirect, reverse

from heron.loggers import LOGGER_EXPORT_EXCEL
from apps.core.functions.functions_http_response import response_file, CONTENT_TYPE_EXCEL
from apps.core.functions.functions_http import get_pagination_buttons
from apps.articles.excel_outputs.output_excel_articles_without_account_list import (
    excel_liste_articles_without_account,
)
from apps.centers_purchasing.bin.update_account_article import (
    set_update_articles_confict_account,
    update_axes_edi,
)
from apps.edi.models import EdiImport


# ECRANS DES ARTICLES SANS COMPTES COMPTABLES EN ACHATS ET VENTES ==================================
def articles_without_account_list(request):
    """Affichage de tous les articles qui n'ont pas de comptes comptables X3, présents
    dans les imports
    """
    page = request.GET.get("page")

    if page is None:
        # On met à jour les comptes comptable des articles
        set_update_articles_confict_account()

        # Mise à jour des articles de la table edi_ediimport avec les axes de la table articles
        update_axes_edi()

    limit = 100
    articles_without_account_queryset = EdiImport.objects.raw(
        """
        with "amounts" as (
            select 
                "vt"."id",
                "vt"."ccm_vat" as "vat_vat"
            from (
                select
                    "ee"."id",
                    case 
                        when "ccm"."sage_vat_by_default" = '001' and "ee"."vat_rate" = 0 then '001'
                        when "ccm"."sage_vat_by_default" = '001' then "ee"."vat"
                        else "ccm"."sage_vat_by_default"
                    end as "ccm_vat"        
                from "edi_ediimport" "ee" 
                join "centers_clients_maison" "ccm" 
                on "ee"."cct_uuid_identification" = "ccm"."uuid_identification"
                join (
                        select distinct
                            "vtr"."vat_regime", 
                            "vd"."vat",
                            round(("vtr"."rate" / 100)::numeric, 5) as "vat_rate"
                        from "accountancy_vatratsage" "vtr"
                        join (
                            select
                                max("vat_start_date") as "vat_start_date",
                                "vat",
                                "vat_regime"
                            from "accountancy_vatratsage"
                            where "vat_start_date" <= now()::date 
                            group by "vat", "vat_regime"
                        ) "vd"
                        on "vtr"."vat" = "vd"."vat"
                        and "vtr"."vat_start_date" = "vd"."vat_start_date"
                ) avr
                on "avr"."vat" = "ccm"."sage_vat_by_default" 
            ) "vt" 
        ),
        "ventes" as (
            select 
                "ee"."id",
                "ee"."code_center",
                "ee"."third_party_num",
                "bs"."short_name" as "tiers",
                "aa"."reference",
                "aa"."libelle",
                coalesce("pro"."section", 'DIV') as "pro",
                "pc"."name" as "category",
                coalesce("ps"."name", '') as "rubrique", 
                "aa"."uuid_identification"  as "article",
                "amo"."vat_vat",
                "av"."vat_regime" as "vat_reg"
            from "edi_ediimport" "ee" 
            join "amounts" "amo"
              on "amo"."id" = "ee"."id"   
            join "articles_article" "aa" 
              on "ee"."third_party_num" = "aa"."third_party_num" 
             and "ee"."reference_article" = "aa"."reference" 
            left join "articles_articleaccount" "ac"
              on "aa"."uuid_identification" = "ac"."article"
             and "ee"."code_center" = "ac"."child_center"
             and "amo"."vat_vat" = "ac"."vat" 
            join "accountancy_sectionsage" "pro" 
               on "pro"."uuid_identification" = "ee"."axe_pro"
            join "parameters_category" "pc" 
               on "pc"."uuid_identification" = "ee"."uuid_big_category" 
             left join "parameters_subcategory" "ps" 
               on "ps"."uuid_identification" = "ee"."uuid_sub_big_category"
            join "book_society" "bs" 
              on "ee"."third_party_num" = "bs"."third_party_num"
            left join "accountancy_vatsage" "av"
              on "amo"."vat_vat" = "av"."vat"
            where "ee"."sale_invoice" = true
              and "ee"."valid" = true
              and "ac"."sale_account" isnull
        ),
        "achats" as (
            select 
                "ee"."id",
                "ee"."code_center", 
                "ee"."third_party_num", 
                "bs"."short_name" as "tiers",
                "aa"."reference",
                "aa"."libelle",
                coalesce("pro"."section", 'DIV') as "pro",
                "pc"."name" as "category",
                coalesce("ps"."name", '') as "rubrique",
                "aa"."uuid_identification" as "article",
                "ee"."vat" as "vat_vat",
                "av"."vat_regime" as "vat_reg"
            from "edi_ediimport" "ee" 
            left join "book_society" "bs" 
              on "ee"."third_party_num"
               = "bs"."third_party_num" 
            left join "articles_article" "aa"  
              on "ee"."reference_article" = "aa"."reference" 
             and "ee"."third_party_num" = "aa"."third_party_num" 
            left join "articles_articleaccount" "ac" 
              on "aa"."uuid_identification" = "ac"."article" 
             and "ee"."vat" = "ac"."vat"
             and "ee"."code_center" = "ac"."child_center" 
            join "accountancy_sectionsage" "pro" 
               on "pro"."uuid_identification" = "ee"."axe_pro"
            left join "parameters_category" "pc" 
              on "ee"."uuid_big_category"
               = "pc"."uuid_identification" 
            left join "parameters_subcategory" "ps" 
              on "ee"."uuid_sub_big_category" = "ps"."uuid_identification"
            left join "accountancy_vatsage" "av"
              on "ee"."vat" = "av"."vat"
            where "ac"."article" isnull
        ),
        "alls" as (
            select 
                "id",
                "code_center", 
                "third_party_num", 
                "tiers", 
                "reference", 
                "libelle", 
                "pro", 
                "category", 
                "rubrique", 
                "article", 
                "vat_vat",
                "vat_reg"
            from "ventes"
            union all
            select 
                "id",
                "code_center", 
                "third_party_num", 
                "tiers", 
                "reference", 
                "libelle", 
                "pro", 
                "category", 
                "rubrique", 
                "article", 
                "vat_vat",
                "vat_reg"
            from "achats"
        )
        select 
            max("id") as "id",
            "code_center", 
            "third_party_num", 
            "tiers", 
            "reference", 
            "libelle", 
            "pro", 
            "category", 
            "rubrique", 
            "article", 
            "vat_vat",
            "vat_reg"
        from "alls"
        group by "code_center", 
                 "third_party_num", 
                 "tiers", 
                 "reference", 
                 "libelle", 
                 "pro", 
                 "category", 
                 "rubrique", 
                 "article", 
                 "vat_vat",
                 "vat_reg"
        order by "third_party_num",
                 "category", 
                 "rubrique",
                 "pro",
                 "reference",
                 "vat_vat"
        """
    )
    # print(str(articles_without_account_queryset.query))
    paginator = Paginator(articles_without_account_queryset, limit)

    try:
        articles = paginator.page(page)
    except PageNotAnInteger:
        articles = paginator.page(1)
    except EmptyPage:
        articles = paginator.page(paginator.num_pages)

    context = {
        "articles": articles,
        "pagination": get_pagination_buttons(
            articles.number, paginator.num_pages, nbre_boutons=5, position_color="cadetblue"
        ),
        "num_items": paginator.count,
        "num_pages": paginator.num_pages,
        "start_index": (articles.start_index() - 1) if articles.start_index() else 0,
        "end_index": articles.end_index(),
        "titre_table": (
            f'1.2 - Articles sans comptes'
        ),
        # "url_validation": reverse("articles:articles_new_validation"),
        "url_redirect": reverse("articles:articles_without_account_list"),
    }
    return render(request, "articles/articles_without_account.html", context=context)


def articles_without_account_export_list(_):
    """
    Export Excel de la liste des Sociétés
    :param _: Request Django
    :return: response_file
    """
    try:
        today = pendulum.now()
        file_name = (
            f"LISTING_DES_ARTICLES_SANS_COMPTES_{today.format('Y_M_D')}_{today.int_timestamp}.xlsx"
        )

        return response_file(excel_liste_articles_without_account, file_name, CONTENT_TYPE_EXCEL)

    except:
        print('exception("view : articles_without_account_export_list")')
        LOGGER_EXPORT_EXCEL.exception("view : articles_without_account_export_list")

    return redirect(reverse("articles:articles_without_account_list"))
