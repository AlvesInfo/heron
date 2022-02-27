from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import Group
from django.contrib.sessions.models import Session
from django.core.mail import send_mail


class UserManager(BaseUserManager, models.Manager):

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
    username = models.CharField(max_length=80)
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    email = models.EmailField(unique=True)
    date_joined = models.DateTimeField(default=timezone.now)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    fonction = models.CharField(max_length=80, null=True, blank=True)
    subordonates = models.ManyToManyField("self", through="UserChief", symmetrical=False)
    secure_session_key = models.CharField(null=True, blank=True, max_length=50)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"
        db_table = "auth_user"

    def __str__(self):
        first_name = "" if not self.first_name else f"{self.first_name} "
        last_name = "" if not self.last_name else f"{self.last_name} "
        return f"{first_name} {last_name}"

    @property
    def ref_id(self):
        return self.__str__()

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_short_name(self):
        return self.email

    def get_user_groups(self):
        if self.is_superuser:
            return Group.objects.all()

        return Group.objects.filter(user=self)

    def send_email_user(self, subject, message, from_email=None, **kwargs):
        """Email this user."""
        send_mail(subject, message, from_email, [self.email], **kwargs)


class UserSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)


class UserChief(models.Model):
    chief = models.ForeignKey("User", related_name="chief", on_delete=models.CASCADE)
    subordonate = models.ForeignKey("User", related_name="subordonate", on_delete=models.CASCADE)


class AuthGroupName(models.Model):
    group = models.OneToOneField(Group, on_delete=models.PROTECT)
    group_name = models.CharField(unique=True, max_length=80)

    def __str__(self):
        return self.group_name
