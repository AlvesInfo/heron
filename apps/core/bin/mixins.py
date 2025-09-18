# pylint: disable=C0411,E0401,W0105,W0212,E1101,W1203
"""Module des Mixins

Commentaire:

created at: 2023-07-01
created by: Paulo ALVES

modified at:
modified by:
"""
from django.core.exceptions import ImproperlyConfigured
from django.db.models import QuerySet


class ChildCenterMixin:
    """class de récupération"""

    queryset = None
    model = None
    ordering = None
    request = None

    def get_ordering(self):
        """Return the field or fields to use for ordering the queryset."""
        return self.ordering

    def get_queryset(self):
        """
        Return the list of items for this view.
        The return value must be an iterable and may be an instance of
        `QuerySet` in which case `QuerySet` specific behavior will be enabled.
        """

        code_child_center = self.request.user.code_child_center

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
            raise ImproperlyConfigured(
                "%(cls)s is missing a QuerySet. Define "
                "%(cls)s.model, %(cls)s.queryset, or override "
                "%(cls)s.get_queryset()." % {"cls": self.__class__.__name__}
            )
        ordering = self.get_ordering()

        if ordering:
            if isinstance(ordering, str):
                ordering = (ordering,)
            queryset = queryset.order_by(*ordering)

        return queryset
