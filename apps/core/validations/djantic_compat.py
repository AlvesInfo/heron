"""Compatibilité djantic 0.7 avec Python 3.14 (annotations différées, PEP 649).

La métaclasse de djantic lit `namespace["__annotations__"]` à la création de la classe ; depuis
Python 3.14 l'espace de noms ne contient plus ce dictionnaire mais une fonction d'annotation
(`__annotate_func__`). Sans ce correctif, les champs déclarés dans les schémas
(`created_at: datetime = now`, clés étrangères typées `str`, …) sont ignorés au profit des seuls
champs du modèle Django. Chargé par `apps/__init__.py`, donc avant tout schéma.
"""

from annotationlib import Format, call_annotate_function, get_annotate_from_class_namespace
from djantic.main import ModelSchemaMetaclass

_original_new = ModelSchemaMetaclass.__new__


def _new_with_annotations(mcs, name: str, bases: tuple, namespace: dict):
    """Matérialise `__annotations__` depuis la fonction d'annotation avant la métaclasse djantic."""
    if "__annotations__" not in namespace:
        annotate = get_annotate_from_class_namespace(namespace)

        if annotate is not None:
            namespace["__annotations__"] = call_annotate_function(annotate, Format.VALUE)

    return _original_new(mcs, name, bases, namespace)


ModelSchemaMetaclass.__new__ = _new_with_annotations
