from django.db import models
from heron.models import FlagsTable
from apps.users.models import User


class Incoice(FlagsTable):

    user_modify = models.ForeignKey(User, on_delete=models.PROTECT, related_name="+")
    user_create = models.ForeignKey(User, on_delete=models.PROTECT, related_name="+")
    user_delete = models.ForeignKey(User, on_delete=models.PROTECT, related_name="+")
