"""Module des Mixins.

Commentaire:

created at: 2023-07-01
created by: Paulo ALVES

modified at:
modified by:
"""

from typing import TYPE_CHECKING, Any, cast

from django.core.exceptions import ImproperlyConfigured
from django.db.models import QuerySet
from django.http import HttpRequest

if TYPE_CHECKING:
    from apps.users.models import User


class ChildCenterMixin:
    """class de récupération."""

    # Attributs fournis par la vue Django qui mixe cette classe (ListView, UpdateView...)
    queryset: QuerySet | None = None
    model: Any = None
    ordering: Any = None
    request: HttpRequest

    def get_ordering(self):
        """Return the field or fields to use for ordering the queryset."""
        return self.ordering

    def get_queryset(self):
        """Return the list of items for this view.

        The return value must be an iterable and may be an instance of
        `QuerySet` in which case `QuerySet` specific behavior will be enabled.
        """
        code_child_center = cast("User", self.request.user).code_child_center

        if self.queryset is not None:
            if code_child_center != "*":
                queryset = self.queryset.filter(child_center__in=code_child_center.split("|"))
            else:
                queryset = self.queryset

            if isinstance(queryset, QuerySet):
                queryset = queryset.all()

        elif self.model is not None:
            if code_child_center != "*":
                queryset = self.model._default_manager.filter(
                    child_center__in=code_child_center.split("|")
                )
            else:
                queryset = self.model._default_manager.all()

        else:
            cls_name = self.__class__.__name__
            raise ImproperlyConfigured(
                f"{cls_name} is missing a QuerySet. Define "
                f"{cls_name}.model, {cls_name}.queryset, or override "
                f"{cls_name}.get_queryset()."
            )
        ordering = self.get_ordering()

        if ordering:
            if isinstance(ordering, str):
                ordering = (ordering,)
            queryset = queryset.order_by(*ordering)

        return queryset
