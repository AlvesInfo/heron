# pylint: disable=E0401,W0621
"""
FR : Tests de la configuration, des modèles, des formulaires et des sérialiseurs de l'app users
EN : Tests for users app configuration, models, forms and serializers

created at: 2026-10-12
created by: Paulo ALVES
"""
import importlib

import pytest
from django.apps import apps as django_apps
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.sessions.models import Session
from django.core import mail
from django.utils import timezone

from apps.users import urls as users_urls
from apps.users.Exceptions import UsersError
from apps.users.apps import UsersConfig
from apps.users.forms.forms_django import forms as users_forms
from apps.users.forms.forms_django.forms import (
    ChangeEmailForm,
    GroupAccessStaffForm,
    InsertStaffsForm,
    UpdateGroupesForm,
    UpdateProfilForm,
    UploadStaffsForm,
    UserLoginForm,
    UserRegisterForm,
)
from apps.users.forms.forms_serializers.serializer_for_insert_users import UsersSerializer, UsersSerializerUsers
from apps.users.models import AuthGroupAccessStaff, AuthGroupName, UploadUserFile, User, UserChief, UserSession
from apps.users.tests.conftest import PASSWORD

pytestmark = pytest.mark.django_db


# CONFIGURATION ====================================================================================


def test_app_config_routes_et_admin():
    config = django_apps.get_app_config("users")
    names = [pattern.name for pattern in users_urls.urlpatterns]

    assert isinstance(config, UsersConfig)
    assert config.name == "apps.users"
    assert len(names) == len(set(names)) == 15
    assert User in admin.site._registry  # pylint: disable=W0212
    assert issubclass(UsersError, Exception)
    assert importlib.import_module("apps.users.forms") is not None


# MODÈLES ==========================================================================================


def test_manager_creation(make_user):
    user = User.objects.create_user("paul", "Paul@Heron.local", PASSWORD, code_child_center="ACF", first_name="Paul")
    admin_user = User.objects.create_superuser("root", "root@heron.local", PASSWORD, code_child_center="ACF")
    no_password = User.objects.create_user("sans", "sans@heron.local", None, code_child_center="ACF")

    assert user.email == "Paul@heron.local"
    assert user.check_password(PASSWORD)
    assert (user.is_staff, user.is_superuser, user.is_active) == (False, False, True)
    assert (admin_user.is_staff, admin_user.is_superuser) == (True, True)
    assert no_password.has_usable_password() is False or no_password.password == ""
    assert make_user().code_child_center == "ACU"

    with pytest.raises(ValueError, match="email"):
        User.objects.create_user("x", "", PASSWORD)

    with pytest.raises(ValueError, match="username"):
        User.objects.create_user("", "x@heron.local", PASSWORD)


def test_affichages_et_noms(make_user):
    user = make_user(first_name="Paul", last_name="Alves")
    anonymous = make_user(email="anonyme@heron.local", username="anonyme")

    assert str(user) == "Paul  Alves "
    assert str(anonymous) == " "
    assert user.ref_id == str(user)
    assert user.get_full_name() == "Paul Alves"
    assert user.get_short_name() == "test@heron.local"


def test_groupes_de_l_utilisateur(make_user, make_superuser, make_group):
    compta = make_group("Comptabilité", "Compta")
    make_group("Achats")
    user = make_user()
    compta.user_set.add(user)
    admin_user = make_superuser()

    assert list(user.in_groups()) == [compta]
    assert [row.group_name for row in user.in_groups_names()] == ["Compta"]
    assert admin_user.in_groups().count() == 2
    assert [row.group_name for row in admin_user.in_groups_names()] == ["Achats", "Compta"]


def test_subordonnes(make_user, make_staff, make_superuser):
    staff = make_staff()
    subordinate = make_user(email="sub@heron.local", username="sub")
    other = make_user(email="other@heron.local", username="other")
    UserChief.objects.create(chief=staff, subordonate=subordinate)
    admin_user = make_superuser()

    assert list(staff.get_subordonates()) == [subordinate]
    assert set(admin_user.get_subordonates()) == {staff, subordinate, other}
    assert list(other.get_subordonates()) == []
    assert subordinate in staff.subordonates.all()


def test_email_user_et_tables_annexes(make_user, make_group):
    user = make_user()
    user.email_user("Sujet", "Message", from_email="noreply@heron.local")
    group = make_group("Comptabilité", "Compta")
    access = AuthGroupAccessStaff.objects.create(group=group)
    django_session = Session.objects.create(session_key="abc", session_data="", expire_date=timezone.now())
    session = UserSession.objects.create(user=user, session=django_session)
    upload = UploadUserFile.objects.create(base_name_file="users.xlsx", user=user)

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["test@heron.local"]
    assert str(AuthGroupName.objects.get(group=group)) == "Compta"
    assert str(access) == "Comptabilité"
    assert upload.type_insert == 0
    assert upload.get_type_insert_display() == "users"
    assert session.session.session_key == "abc"


# FORMULAIRES ======================================================================================


def test_formulaire_de_connexion():
    assert UserLoginForm({"email": "a@b.fr", "mot_de_passe": "x"}).is_valid()
    assert UserLoginForm({"email": "pas un email", "mot_de_passe": "x"}).is_valid() is False


def test_formulaire_creation_choix_des_groupes(make_superuser, make_staff, make_group):
    """Le superuser voit tous les groupes sauf Admin, le staff seulement les siens (hors Admin)"""
    admin_group = make_group("Admin")
    compta = make_group("Comptabilité", "Compta")
    make_group("Achats")
    staff = make_staff()
    staff.groups.add(compta, admin_group)

    superuser_choices = UserRegisterForm(make_superuser()).fields["groups"].choices
    staff_choices = UserRegisterForm(staff).fields["groups"].choices

    assert sorted(superuser_choices) == [("Achats", "Achats"), ("Comptabilité", "Compta")]
    assert list(staff_choices) == [("Comptabilité", "Compta")]


@pytest.mark.parametrize(
    ("data", "field", "message"),
    [
        ({"password": PASSWORD, "password_verif": "autre"}, "password", "identiques"),
        ({"email": "staff@heron.local", "password": PASSWORD, "password_verif": PASSWORD}, "email", "existe déja"),
        ({"password": "", "password_verif": ""}, "password", "obligatoire"),
        ({"password": "1234", "password_verif": "1234"}, "password", "court"),
    ],
)
def test_formulaire_creation_erreurs(make_staff, data, field, message):
    make_staff()
    form = UserRegisterForm(make_staff("chef@heron.local", "chef"), {"email": "nouveau@heron.local", **data})

    assert form.is_valid() is False
    assert any(message in error for error in form.errors[field])


def test_formulaire_creation_valide(make_superuser):
    form = UserRegisterForm(make_superuser(), {"email": "nouveau@heron.local", "password": PASSWORD, "password_verif": PASSWORD})

    assert form.is_valid(), form.errors


def test_formulaire_profil(make_user):
    user = make_user(first_name="Paul", function="Dev")
    form = UpdateProfilForm(user)
    mismatch = UpdateProfilForm(user, {"password": PASSWORD, "password_verif": "autre"})
    valid = UpdateProfilForm(user, {"password": PASSWORD, "password_verif": PASSWORD})
    no_password = UpdateProfilForm(user, {"username": "paul"})

    assert form.fields["first_name"].initial == "Paul"
    assert form.fields["fonction"].initial == "Dev"
    assert form.fields["last_name"].initial == ""
    assert mismatch.is_valid() is False
    assert "identiques" in str(mismatch.errors)
    assert valid.is_valid()
    assert no_password.is_valid()


def test_formulaire_groupes_et_acces_staff(make_staff, make_user, make_group):
    compta = make_group("Comptabilité", "Compta")
    achats = make_group("Achats")
    staff = make_staff()
    staff.groups.add(compta, achats)
    target = make_user()
    target.groups.add(achats)
    AuthGroupAccessStaff.objects.create(group=compta)

    groups_form = UpdateGroupesForm(staff, target)
    access_form = GroupAccessStaffForm()

    assert sorted(groups_form.fields["groups"].choices) == sorted([(compta.id, "Compta"), (achats.id, "Achats")])
    assert groups_form.fields["groups"].initial == [achats.id]
    assert set(access_form.fields["group"].choices) == {(compta.id, "Comptabilité"), (achats.id, "Achats")}
    assert access_form.fields["group"].initial == [compta.id]
    assert GroupAccessStaffForm({"group": [str(achats.id)]}).is_valid()
    assert GroupAccessStaffForm({}).is_valid()


def test_formulaires_fichiers_et_email(settings):
    """Hors DEBUG le fichier téléversé passe par l'antivirus, en DEBUG non"""
    initial_debug = settings.DEBUG
    assert "file_staffs" in InsertStaffsForm().fields
    assert InsertStaffsForm().fields["file_staffs"].required is False
    assert UploadStaffsForm.Meta.fields == ("file",)
    assert ChangeEmailForm({"last_email": "a@b.fr", "email": "c@d.fr", "email_verif": "c@d.fr"}).is_valid()
    assert ChangeEmailForm({"last_email": "a@b.fr", "email": "x", "email_verif": "x"}).is_valid() is False

    try:
        settings.DEBUG = True
        assert not importlib.reload(users_forms).UploadStaffsForm.base_fields["file"].validators
        settings.DEBUG = False
        assert importlib.reload(users_forms).UploadStaffsForm.base_fields["file"].validators
    finally:
        settings.DEBUG = initial_debug
        importlib.reload(users_forms)


# SÉRIALISEURS =====================================================================================


def test_serialiseur_staffs(make_user):
    make_user(email="existe@heron.local", username="existe")
    valid = UsersSerializer(data={"email": "new@heron.local", "password": PASSWORD, "code_child_center": "ACF", "username": "u" * 100, "function": None})
    duplicate = UsersSerializer(data={"email": "existe@heron.local", "password": PASSWORD, "code_child_center": "ACF"})
    missing = UsersSerializer(data={"email": "new2@heron.local"})

    assert valid.is_valid(), valid.errors
    assert len(valid.validated_data["username"]) == 80
    assert duplicate.is_valid() is False
    assert "email" in duplicate.errors
    assert missing.is_valid() is False
    assert {"password", "code_child_center"} <= set(missing.errors)


def test_serialiseur_utilisateurs():
    serializer = UsersSerializerUsers(
        data={"email": "Nouveau@Heron.LOCAL", "password": PASSWORD, "code_child_center": "ACF", "function": "", "last_name": "N" * 90}
    )

    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["email"] == "nouveau@heron.local"
    assert serializer.validated_data["function"] == "Utilisateur"
    assert len(serializer.validated_data["last_name"]) == 80
    assert Group.objects.count() == 0
