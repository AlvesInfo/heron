from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.db import models

from apps.users.models import User


class DatesTable(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("created at"))
    modified_at = models.DateTimeField(auto_now=True, verbose_name=_("modified at"))

    class Meta:
        abstract = True


class FlagsTable(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("created at"))
    modified_at = models.DateTimeField(auto_now=True, verbose_name=_("modified at"))
    active = models.BooleanField(default=False)
    to_delete = models.BooleanField(default=False)
    visible = models.BooleanField(default=True)
    flag_delete = models.BooleanField(null=True)
    flag_to_delete = models.BooleanField(null=True)
    flag_active = models.BooleanField(null=True)
    flag_export = models.BooleanField(null=True)
    flag_to_validated = models.BooleanField(null=True)
    flag_valide = models.BooleanField(null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, related_name="+"
    )
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, related_name="+"
    )
    delete_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, related_name="+"
    )

    class Meta:
        abstract = True
