"""Vues API génériques de core : requêtes sur modèles et statut de téléchargement."""

from collections.abc import Callable

from django.http import JsonResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_GET

from apps.accountancy.bin.api_get_models_accountacy import get_vat, get_vat_alls
from apps.core.bin.api_get_models import (
    get_account,
    get_articles,
    get_articles_alls,
    get_cct_in_use_active,
    get_maisons,
    get_maisons_alls,
    get_maisons_in_use,
    get_societies,
    get_societies_alls,
    get_unity,
    get_unity_alls,
)
from apps.core.functions.functions_http import is_ajax
from apps.core.functions.functions_http_response import download_status_key
from heron.loggers import LOGGER_VIEWS

MODEL_DICT: dict[str, Callable] = {
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
    """Les clés *_alls du MODEL_DICT renvoient tous les enregistrements, sans texte de recherche."""
    return str(models).endswith("_alls")


def api_models_query(request, models, query):
    """View pour les api dans les dropdown semantic."""
    if is_ajax(request) and request.method == "GET":
        dic: dict = {"success": "ko"}

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
    """View pour les api dans les dropdown semantic."""
    if is_ajax(request) and request.method == "GET":
        dic: dict = {"success": "ko"}

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


@require_GET
def download_status(request, token):
    """Indique au JavaScript de la page si le téléchargement portant ce jeton est terminé.

    Le marqueur posé en session par response_file est consommé à la première lecture positive.
    """
    complete = bool(request.session.pop(download_status_key(token), False))
    return JsonResponse({"complete": complete})
