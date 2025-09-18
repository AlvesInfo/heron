Appel Semantic api sur un dropdown pour récupérer les données dans celui-ci.
---
La fonction js de remplissage à l'appel du dropdown est dans le fichier ajax_dropdown_model. 

Cette fonction instancie un dropdown Semantic UI, Elle est déjà appelée dans le template base_semantic.html.

Le dropdown doit avoir la class : ".field.remote .ui.dropdown"

Créer un select dans le template:
```html
<div class="field remote search">
   <label for="id_element_{{ num }}">Ligne {{ forloop.counter }} - CCT X3</label>
   <select name="element"
           class="ui search dropdown search-model"
           data-models="maisons_in_use"
           id="id_element_{{ num }}">
   </select>
</div>
```
Ou le nommage des data-models, doit correspondre à l'end-point de l'API.

L'Api appelle l'end-point, placé dans core/urls.py

```python
from django.urls import path

from apps.core.views import api_models_query
urlpatterns = [
    path(
        "api_models_query/<str:models>/<str:query>/", api_models_query, name="api_models_query"
    ),
],

```
 placée dans core/urls.py
La vue : api_models_query

```python
from django.http import JsonResponse
from django.shortcuts import redirect, HttpResponse

from heron.loggers import LOGGER_VIEWS


from apps.core.bin.api_get_models import (
    get_articles_alls,
    get_articles,
    get_societies_alls,
    get_societies,
    # ...
)

MODEL_DICT = {
    "articles_alls": get_articles_alls,
    "articles": get_articles,
    "societies_alls": get_societies_alls,
    "societies": get_societies,
    # ...
}


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
```

Va renvoyer les élements au dropdown, par un appel à la function qui sera nommée dans un dictionnaire ou la clé est le nom donné au "data-models" du select, dans le template HTML.

Un exemple de fonction pourrait être :
```python
from typing import AnyStr

from django.db.models import CharField, Value, F
from django.db.models.functions import Concat

from apps.book.models import Society


def get_societies_alls() -> Society.objects:
    """
    Recherche par API des tiers
    :return: queryset of dict
    """
    queryset = Society.objects.annotate(
        str_search=Concat(
            "third_party_num",
            Value("|"),
            "name",
            Value("|"),
            "immeuble",
            Value("|"),
            "adresse",
            Value("|"),
            "ville",
            Value("|"),
            "country__country_name",
            output_field=CharField(),
        ),
        pk=F("third_party_num"),
        model=Concat(
            "third_party_num",
            Value(" - "),
            "name",
            Value(" - "),
            "ville",
            Value(" - "),
            "country__country_name",
            output_field=CharField(),
        ),
    ).values("pk", "model")

    return queryset


def get_societies(str_query: AnyStr) -> Society.objects:
    """
    Recherche par API des tiers
    :param str_query: Texte à rechercher pour l'api dropdown
    :return: queryset of dict
    """
    queryset = get_societies_alls()

    return queryset.filter(str_search__icontains=str_query)[:50]
```
