from django.utils.translation import gettext_lazy as _
from django.db import models

from apps.users.models import User


class DatesTable(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("created at"))
    modified_at = models.DateTimeField(auto_now=True, verbose_name=_("modified at"))

    class Meta:
        abstract = True


class FlagsTable(DatesTable):
    flag_delete = models.BooleanField(null=True)
    flag_to_delete = models.BooleanField(null=True)
    flag_active = models.BooleanField(null=True)
    flag_export = models.BooleanField(null=True)
    flag_to_validated = models.BooleanField(null=True)
    flag_valide = models.BooleanField(null=True)

    class Meta:
        abstract = True
