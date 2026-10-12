
from django.http import JsonResponse
from django.shortcuts import redirect

from apps.core.functions.functions_http import is_ajax
from heron.loggers import LOGGER_VIEWS
from apps.accountancy.bin.api_get_models_accountacy import get_vat_alls, get_vat
from apps.core.bin.api_get_models import (
    get_articles_alls,
    get_articles,
    get_societies_alls,
    get_societies,
    get_maisons_alls,
    get_maisons,
    get_maisons_in_use,
    get_cct_in_use_active,
    get_unity_alls,
    get_unity,
    get_account,
)

MODEL_DICT = {
    "articles_alls": get_articles_alls,
    "articles": get_articles,
    "societies_alls": get_societies_alls,
    "societies": get_societies,
    "maisons_alls": get_maisons_alls,
    "maisons": get_maisons,
    "maisons_in_use": get_maisons_in_use,
    "cct_in_use_active": get_cct_in_use_active,
    "unites_alls": get_unity_alls,
    "unites": get_unity,
    "vats_alls": get_vat_alls,
    "vats": get_vat,
    "accounts": get_account,
}


def _is_alls_model(models):
    """Les clés *_alls du MODEL_DICT renvoient tous les enregistrements, sans texte de recherche"""
    return str(models).endswith("_alls")


def api_models_query(request, models, query):
    """View pour les api dans les dropdown semantic"""

    if is_ajax(request) and request.method == "GET":
        dic = {"success": "ko"}

        try:
            str_query = str(query).replace("%", r"\%").replace("'", "").lower()
            results_func = MODEL_DICT.get(str(models))

            if results_func is not None:
                results = results_func() if _is_alls_model(models) else results_func(str_query)
                dic = {"success": list(results)}

        except Exception:
            LOGGER_VIEWS.exception("view : article_rest_api_query")

        return JsonResponse(dic)

    return redirect("home")


def api_models_query_third_party_num(request, models, third_party_num, query):
    """View pour les api dans les dropdown semantic"""

    if is_ajax(request) and request.method == "GET":
        dic = {"success": "ko"}

        try:
            str_query = str(query).replace("%", r"\%").replace("'", "").lower()
            results_func = MODEL_DICT.get(str(models))

            if results_func is not None:
                results = (
                    results_func(third_party_num)
                    if _is_alls_model(models)
                    else results_func(str_query, third_party_num)
                )
                dic = {"success": list(results)}

        except Exception:
            LOGGER_VIEWS.exception("view : article_rest_api_query")

        return JsonResponse(dic)

    return redirect("home")
