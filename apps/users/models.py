import uuid

from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from django.conf import settings
from django.db import models, connection
from django.db.utils import IntegrityError
from django.utils import timezone
from django.contrib.auth.models import Group
from django.contrib.sessions.models import Session
from django.core.mail import send_mail

from apps.core.functions.functions_utilitaires import num_string_series
from apps.core.functions.functions_dates import time_string_series


class UserManager(BaseUserManager, models.Manager):
    num = num_string_series(time_string_series(), 10)

    def _create_user(
        self, username, email, password, is_superuser=False, is_staff=False, **extra_fields
    ):
        email = self.normalize_email(email)
        if not email:
            raise ValueError("The given email must be set")
        if not username:
            raise ValueError("The given username must be set")

        user = self.model(
            username=username,
            email=email,
            is_superuser=is_superuser,
            is_staff=is_staff,
            is_active=True,
            **extra_fields,
        )

        if password:
            user.set_password(password)

        user.save(using=self._db)
        return user

    def create_user(
        self, username, email, password, is_superuser=False, is_staff=False, **extra_fields
    ):
        return self._create_user(
            username, email, password, is_superuser=is_superuser, is_staff=is_staff, **extra_fields
        )

    def create_superuser(self, username, email, password, **extra_fields):
        return self._create_user(username, email, password, True, True, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=80, null=True, blank=True)
    first_name = models.CharField(max_length=80, null=True, blank=True)
    last_name = models.CharField(max_length=80, null=True, blank=True)
    email = models.EmailField(unique=True)
    date_joined = models.DateTimeField(default=timezone.now)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    fonction = models.CharField(max_length=80, null=True, blank=True)
    subordonates = models.ManyToManyField("self", through="UserChief", symmetrical=False)
    secure_session_key = models.CharField(null=True, blank=True, max_length=50)

    # Identification
    uuid_identification = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        first_name = "" if not self.first_name else (self.first_name + " ")
        last_name = "" if not self.last_name else (self.last_name + " ")

        return f"{first_name} {last_name}"

    @property
    def ref_id(self):
        return self.__str__()

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_short_name(self):
        return self.email

    def in_groups(self):
        if self.is_superuser:
            return Group.objects.all()

        return Group.objects.filter(user=self)

    def in_groups_names(self):
        if self.is_superuser:
            return AuthGroupName.objects.filter(group__in=Group.objects.all()).order_by(
                "group_name"
            )

        return AuthGroupName.objects.filter(group__in=Group.objects.filter(user=self)).order_by(
            "group_name"
        )

    def get_subordonates(self):
        user = User.objects.filter(pk=self.pk)
        subordonates = User.objects.filter(
            pk__in=UserChief.objects.filter(chief=user[0]).values("subordonate_id")
        )

        if self.is_superuser:
            staffs = User.objects.exclude(is_superuser=True)
            return subordonates.union(staffs)

        return subordonates

    def email_user(self, subject, message, from_email=None, **kwargs):
        """Email this user."""
        send_mail(subject, message, from_email, [self.email], **kwargs)

    class Meta:
        """class Meta du modèle django"""

        verbose_name = "user"
        verbose_name_plural = "users"
        db_table = "auth_user"


class UserSession(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_column="user",
    )
    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        db_column="session",
    )


class UserChief(models.Model):
    chief = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="chief",
        on_delete=models.CASCADE,
        db_column="chief",
    )
    subordonate = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="subordonate",
        on_delete=models.CASCADE,
        db_column="subordonate",
    )


class AuthGroupName(models.Model):
    group = models.OneToOneField(Group, on_delete=models.PROTECT)
    group_name = models.CharField(unique=True, max_length=80)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return self.group_name


class AuthGroupAccessStaff(models.Model):
    """Table des groupes auxquels les Admin délégués (STAFF) ont le droit d'accèder.
    Aux imports de staf en masse les staff se verront attribués les droits auxquels
    ils ont le droit
    """

    group = models.OneToOneField(Group, on_delete=models.PROTECT)

    def __str__(self):
        """Texte renvoyé dans les selects et à l'affichage de l'objet"""
        return self.group


class UploadUserFile(models.Model):
    file = models.FileField(upload_to="users/")
    base_name_file = models.CharField(blank=True, null=True, max_length=255)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        db_column="user",
    )
    type_insert = models.IntegerField(choices=((0, "users"), (1, "staff"), (2, "admin")), default=0)
