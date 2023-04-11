from pathlib import Path

import pendulum
from django.shortcuts import render
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.shortcuts import redirect, HttpResponse
from django.conf import settings

from heron.loggers import LOGGER_VIEWS
from apps.edi.models import EdiImport
from apps.core.bin.api_get_models import (
    get_articles_alls,
    get_articles,
    get_societies_alls,
    get_societies,
    get_maisons_alls,
    get_maisons,
    get_maisons_in_use,
    get_unity_alls,
    get_unity,
    get_vat_alls,
    get_vat,
)

MODEL_DICT = {
    "articles_alls": get_articles_alls,
    "articles": get_articles,
    "societies_alls": get_societies_alls,
    "societies": get_societies,
    "maisons_alls": get_maisons_alls,
    "maisons": get_maisons,
    "maisons_in_use": get_maisons_in_use,
    "unites_alls": get_unity_alls,
    "unites": get_unity,
    "vats_alls": get_vat_alls,
    "vats": get_vat,
}


def pdf_view(request):
    context = {
        "maison": EdiImport.objects.filter(
            sale_invoice=True,
            big_category="f2dda460-20db-4b05-8bb8-fa80a1ff146b",
            cct_uuid_identification__isnull=False,
        ),
        "invoice_date": pendulum.today().date(),
    }
    content = render_to_string("core/marchandises.html", context)

    media_file = Path(settings.MEDIA_DIR) / "files/your-template-static.html"

    with media_file.open("w", encoding="utf8") as static_file:
        static_file.write(content)

    return render(request, "core/marchandises.html", context)


def api_models_query(request, models, query):
    """View pour les api dans les dropdown semantic"""

    if request.is_ajax() and request.method == "GET":
        dic = {"success": "ko"}

        try:
            str_query = str(query).replace("%", r"\%").replace("'", "").lower()
            results_func = MODEL_DICT.get(str(models))

            if results_func is not None:
                results = results_func(str_query)
                dic = {"success": list(results)}

        except:
            LOGGER_VIEWS.exception("view : article_rest_api_query")

        response = JsonResponse(dic)
        return HttpResponse(response)

    return redirect("home")


def api_models_query_third_party_num(request, models, third_party_num, query):
    """View pour les api dans les dropdown semantic"""

    if request.is_ajax() and request.method == "GET":
        dic = {"success": "ko"}

        try:
            str_query = str(query).replace("%", r"\%").replace("'", "").lower()
            results_func = MODEL_DICT.get(str(models))

            if results_func is not None:
                results = results_func(str_query, third_party_num)
                dic = {"success": list(results)}

        except:
            LOGGER_VIEWS.exception("view : article_rest_api_query")

        response = JsonResponse(dic)
        return HttpResponse(response)

    return redirect("home")
