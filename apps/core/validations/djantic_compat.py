"""Compatibilité djantic2 (pydantic 2) avec Python 3.14 et aide de configuration des schémas.

- `schema_config` : construit le `model_config` attendu par djantic2 (`model` et `include`) avec
  un type accepté par mypy (`ConfigDict` ne connaît pas ces deux clés).
- Annotations différées (PEP 649) : la métaclasse de djantic2 lit `namespace["__annotations__"]`
  à la création de la classe ; depuis Python 3.14 l'espace de noms ne contient plus ce
  dictionnaire mais une fonction d'annotation. Sans ce correctif, les champs déclarés dans les
  schémas (`created_at: datetime = now`, clés étrangères typées `str`, …) sont ignorés au profit
  des seuls champs du modèle Django. Chargé par `apps/__init__.py`, donc avant tout schéma.
"""

from collections.abc import Iterable
from typing import Any, cast

from annotationlib import Format, call_annotate_function, get_annotate_from_class_namespace
from django.db import models
from djantic.main import ModelSchemaMetaclass
from pydantic import ConfigDict


def schema_config(model: type[models.Model], include: Iterable[str] | None = None) -> ConfigDict:
    """Configuration djantic2 d'un schéma : modèle Django et colonnes incluses.

    :param model: modèle Django validé par le schéma
    :param include: colonnes du schéma ; None pour tous les champs du modèle et les annotations
    :return: dictionnaire à affecter à `model_config`
    """
    config: dict[str, Any] = {"model": model}

    if include is not None:
        config["include"] = list(include)

    return cast("ConfigDict", config)


_original_new = ModelSchemaMetaclass.__new__


def _new_with_annotations(mcs, name: str, bases: tuple, namespace: dict, **kwargs):
    """Matérialise `__annotations__` depuis la fonction d'annotation avant la métaclasse djantic."""
    if "__annotations__" not in namespace:
        annotate = get_annotate_from_class_namespace(namespace)

        if annotate is not None:
            namespace["__annotations__"] = call_annotate_function(annotate, Format.VALUE)

    return _original_new(mcs, name, bases, namespace, **kwargs)


ModelSchemaMetaclass.__new__ = _new_with_annotations
