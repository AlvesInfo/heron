from django_clamd.validators import validate_file_infection
from django.db import connection
from django.contrib.auth.models import Group
from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.conf import settings

from apps.users.models import User, AuthGroupName, UploadUserFile, AuthGroupAccessStaff


class UserLoginForm(forms.Form):
    email = forms.EmailField()
    mot_de_passe = forms.CharField(widget=forms.PasswordInput)


class UserRegisterForm(forms.Form):

    first_name = forms.CharField(required=False, max_length=80)
    last_name = forms.CharField(required=False, max_length=80)
    email = forms.EmailField(label="Adresse Email")
    username = forms.CharField(required=False, max_length=80)
    fonction = forms.CharField(required=False, max_length=80)
    password = forms.CharField(required=False, widget=forms.PasswordInput)
    password_verif = forms.CharField(required=False, widget=forms.PasswordInput)

    superuser = forms.BooleanField(required=False)
    staff = forms.BooleanField(required=False)

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        if self.user.is_superuser:
            rows_groups = AuthGroupName.objects.exclude(group__name__iexact="Admin").values_list(
                "group__name", "group_name"
            )

        else:
            sql_groups = """
            SELECT 
                r.name, r.group_name 
              FROM (
                SELECT 
                    user_id, group_id 
                  FROM auth_user_groups 
                 WHERE user_id = %s
            ) as u
            INNER JOIN (
                SELECT 
                    "name", group_name, auth_group.id
                  FROM auth_group 
                 INNER JOIN auth_group_name
                    ON auth_group.id = auth_group_name.group_id
                 WHERE UPPER("name") NOT LIKE %s
            ) as r
                ON u.group_id = r.id
             ORDER BY R.group_name
            """

            with connection.cursor() as cur:
                cur.execute(sql_groups, (self.user.pk, "%ADMIN%"))
                rows_groups = cur.fetchall()

        groups_choices = tuple(rows_groups)
        groups = forms.MultipleChoiceField(
            required=False,
            choices=groups_choices,
            widget=forms.CheckboxSelectMultiple(attrs={"class": "groupes"}),
            help_text="Vous devez sélectionner au moins un Groupe",
        )
        self.fields["groups"] = groups

    def clean(self, *args, **kwargs):
        email = self.cleaned_data.get("email")
        password = self.cleaned_data.get("password")
        password_verif = self.cleaned_data.get("password_verif")

        if password != password_verif:
            msg = "Les deux mots de passe doivent être identiques\n"
            self.add_error("password", msg)

        email_qs = User.objects.filter(email=email)

        if email_qs.exists():
            msg_email = f"l'email : {email},  existe déja\n"
            self.add_error("email", msg_email)

        # validation des mots de passe depuis les validator issus des settings
        try:
            validate_password(password)
        except ValidationError as errors:
            for msg in errors:
                self.add_error("password", msg)


class UpdateProfilForm(forms.Form):
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        utilisateur = User.objects.get(pk=self.user.id)

        username = forms.CharField(required=False, initial=utilisateur.username or "")
        self.fields["username"] = username

        fonction = forms.CharField(required=False, initial=utilisateur.fonction or "")
        self.fields["fonction"] = fonction

        first_name = forms.CharField(required=False, initial=utilisateur.first_name or "")
        self.fields["first_name"] = first_name

        last_name = forms.CharField(required=False, initial=utilisateur.last_name or "")
        self.fields["last_name"] = last_name

    password = forms.CharField(required=False, widget=forms.PasswordInput)
    password_verif = forms.CharField(required=False, widget=forms.PasswordInput)

    def clean(self, *args, **kwargs):
        password = self.cleaned_data.get("password")

        if password:
            password_verif = self.cleaned_data.get("password_verif")

            if password != password_verif:
                msg = "Les deux mots de passe doivent être identiques"
                raise forms.ValidationError(msg)

        return super().clean()


class UpdateGroupesForm(forms.Form):
    def __init__(self, user, user_to_form, *args, **kwargs):
        super().__init__(*args, **kwargs)

        groups = forms.MultipleChoiceField(
            required=True,
            choices=[(row.group_id, row.group_name) for row in user.in_groups_names()],
            widget=forms.CheckboxSelectMultiple(attrs={"class": "groupes"}),
            help_text="Vous devez sélectionner au moins un Groupe",
            initial=[row.id for row in user_to_form.in_groups()],
        )
        self.fields["groups"] = groups


def all_users_choices(user_id, is_superuser=None):
    cursor = connection.cursor()

    users = [(0, "---------")]

    if is_superuser:
        sql_users = """
SELECT 
    id, 
    CASE 
        WHEN first_name IS NULL AND last_name IS NULL THEN email
        WHEN (first_name || ' ' || last_name ) = ' ' THEN email 
        ELSE(first_name || ' ' || last_name ) 
    END AS user 
  FROM auth_user
 WHERE (
    email NOT LIKE 'defie@free.fr'
    AND is_superuser = 0
    ) 
    OR id = %s
 ORDER BY last_name
        """
        cursor.execute(sql_users, (user_id,))
        rows_users = cursor.fetchall()
        users = [(r[0], r[1]) for r in rows_users]

    initial_user = users[0][0]
    initial = (users[0][0], users[0][1])

    return users, initial_user, initial


class ChangePasswordForm(forms.Form):

    password = forms.CharField(required=True, widget=forms.PasswordInput)
    password_verif = forms.CharField(required=True, widget=forms.PasswordInput)


class InsertStaffsForm(forms.Form):

    file_satffs = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={"multiple": False}),
        label="Selectionnez un ou plusieurs fichiers sur votre ordinateur",
    )


class UploadStaffsForm(forms.ModelForm):
    if not settings.DEBUG:
        file = forms.FileField(validators=[validate_file_infection])

    class Meta:
        """class Meta du modèle django"""
        model = UploadUserFile
        fields = ("file",)


class GroupAccessStaffForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        group = forms.MultipleChoiceField(
            choices=[(row.id, row.name) for row in Group.objects.all()],
            widget=forms.SelectMultiple(attrs={"class": "ui fluid dropdown"}),
            label="",
            initial=[
                row for row in AuthGroupAccessStaff.objects.all().values_list("group_id", flat=True)
            ],
            required=False,
        )

        self.fields["group"] = group


class ChangeEmailForm(forms.Form):
    last_email = forms.EmailField(label="Ancienne Email")
    email = forms.EmailField(label="Email")
    email_verif = forms.EmailField(label="Vérifaction Email")
