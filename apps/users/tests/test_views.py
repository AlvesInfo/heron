# pylint: disable=E0401,W0621,R0913
"""
FR : Tests des vues de l'app users (connexion, création, profil, groupes, téléversements, email)
EN : Tests for users app views

created at: 2026-10-12
created by: Paulo ALVES
"""
import pytest
from django.contrib.auth.models import Group
from django.contrib.messages import get_messages
from django.contrib.sessions.models import Session
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse

from apps.users.models import AuthGroupAccessStaff, UploadUserFile, User, UserChief, UserSession
from apps.users.tests.conftest import PASSWORD, staff_csv, users_xlsx

pytestmark = pytest.mark.django_db

AJAX = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}


# CONNEXION / DÉCONNEXION ==========================================================================


def test_connexion(client, make_user):
    """Connexion réussie (session unique), mot de passe faux, formulaire invalide"""
    user = make_user(password=PASSWORD)
    url = reverse("accounts:login")

    assert client.get(url).status_code == 200

    response = client.post(url, {"email": user.email, "mot_de_passe": PASSWORD})
    assert response.status_code == 302
    assert response.url == "/"
    assert UserSession.objects.filter(user=user).count() == 1

    # Une seconde connexion depuis un autre navigateur supprime la première session (cascade)
    first_key = client.session.session_key
    other = Client()
    other.post(url, {"email": user.email, "mot_de_passe": PASSWORD})
    assert UserSession.objects.filter(user=user).count() == 1
    assert Session.objects.filter(session_key=first_key).exists() is False
    assert UserSession.objects.get(user=user).session_id == other.session.session_key

    wrong = Client().post(url, {"email": user.email, "mot_de_passe": "faux"})
    assert wrong.status_code == 200
    assert [m.message for m in get_messages(wrong.wsgi_request)] == ["Email ou mot de passe, non trouvés"]

    invalid = Client().post(url, {"email": "pas un email", "mot_de_passe": "x"})
    assert invalid.status_code == 200
    assert invalid.context["form"].errors


def test_connexion_avec_page_suivante(client, make_user):
    """La page suivante n'est suivie que si son domaine est dans la liste blanche"""
    from apps.core.functions import functions_http  # pylint: disable=C0415

    user = make_user(password=PASSWORD)
    allowed = f"http://{functions_http.DOMAINS_WHITELIST[0]}/accounts/profil/"
    url = reverse("accounts:login")

    response = client.post(f"{url}?next={allowed}", {"email": user.email, "mot_de_passe": PASSWORD})
    assert response.status_code == 302
    assert response.url == allowed

    forbidden = Client().post(f"{url}?next=http://pirate.example/", {"email": user.email, "mot_de_passe": PASSWORD})
    assert forbidden.url == "/"

    # Une url relative interne (cas du décorateur login_required) est suivie
    relative = Client().post(f"{url}?next=/accounts/profil/", {"email": user.email, "mot_de_passe": PASSWORD})
    assert relative.url == "/accounts/profil/"


def test_deconnexion(logged_client):
    response = logged_client.get(reverse("accounts:logout"))

    assert response.status_code == 302
    assert response.url == "/"
    assert "_auth_user_id" not in logged_client.session


# CRÉATION D'UTILISATEUR ===========================================================================


def test_creation_par_superuser(superuser_client, make_group):
    make_group("Comptabilité")
    make_group("Achats")
    url = reverse("accounts:register")

    assert superuser_client.get(url).status_code == 200

    response = superuser_client.post(
        url,
        {"email": "nouveau@heron.local", "first_name": "Paul", "password": PASSWORD, "password_verif": PASSWORD, "staff": "on", "groups": ["Comptabilité", "Achats"]},
    )
    created = User.objects.get(email="nouveau@heron.local")

    assert response.status_code == 200
    assert response.context["message_success"] is True
    assert (created.username, created.is_staff, created.is_superuser, created.code_child_center) == ("nouveau", True, False, "ACU")
    assert set(created.groups.values_list("name", flat=True)) == {"Comptabilité", "Achats"}


def test_creation_par_staff_et_superuser_cree_un_superuser(staff_client, superuser_client, make_group):
    """Un staff ne peut créer ni staff ni superuser ; redirection sur next"""
    compta = make_group("Comptabilité")
    staff_client.user.groups.add(compta)
    url = reverse("accounts:register")

    response = staff_client.post(
        url + "?next=/accounts/profil/",
        {"email": "a@heron.local", "username": "alpha", "password": PASSWORD, "password_verif": PASSWORD, "superuser": "on", "staff": "on", "groups": ["Comptabilité"]},
    )
    alpha = User.objects.get(email="a@heron.local")
    assert response.status_code == 302
    assert response.url == "/accounts/profil/"
    assert (alpha.username, alpha.is_staff, alpha.is_superuser) == ("alpha", False, False)

    superuser_client.post(url, {"email": "b@heron.local", "password": PASSWORD, "password_verif": PASSWORD, "superuser": "on"})
    beta = User.objects.get(email="b@heron.local")
    assert (beta.is_staff, beta.is_superuser) == (True, True)

    # Un next vers un domaine étranger est ramené à la racine (pas de redirection ouverte)
    pirate = superuser_client.post(
        url + "?next=http://pirate.example/", {"email": "c@heron.local", "password": PASSWORD, "password_verif": PASSWORD}
    )
    assert pirate.status_code == 302
    assert pirate.url == "/"


def test_creation_formulaire_invalide_et_utilisateur_simple(superuser_client, logged_client):
    url = reverse("accounts:register")

    invalid = superuser_client.post(url, {"email": "pas un email"})
    assert invalid.status_code == 200
    assert invalid.context["form"].errors
    assert logged_client.get(url).status_code == 200

    plain = logged_client.post(url, {"email": "c@heron.local", "password": PASSWORD, "password_verif": PASSWORD})
    assert plain.status_code == 302
    assert plain.url == "/"
    assert User.objects.filter(email="c@heron.local").exists() is False


# PROFIL ===========================================================================================


def test_profil(logged_client):
    url = reverse("accounts:user_profil")
    user = logged_client.user

    assert logged_client.get(url).status_code == 200

    response = logged_client.post(url, {"first_name": "Paul", "fonction": "Dev", "username": ""})
    user.refresh_from_db()
    assert response.context["message"] == "Votre profil à bien été changé"
    assert (user.first_name, user.function, user.username) == ("Paul", "Dev", "test")

    response = logged_client.post(url, {"username": "paulo", "password": PASSWORD, "password_verif": PASSWORD})
    user.refresh_from_db()
    assert response.context["message"] == "Votre profil et votre mot passe ont bien été changés"
    assert user.check_password(PASSWORD)
    assert user.username == "paulo"
    assert logged_client.session["_auth_user_id"] == str(user.pk)

    mismatch = logged_client.post(url, {"password": PASSWORD, "password_verif": "autre"})
    assert mismatch.status_code == 200
    assert "message" not in mismatch.context


# GESTION DES GROUPES ==============================================================================


def test_gestion_groupes_acces(logged_client, staff_client, make_group):
    url = reverse("accounts:update_user_groupes")

    plain = logged_client.get(url)
    assert plain.status_code == 302
    assert plain.url == "/"

    assert staff_client.get(url).context["not_in_groups"] is True

    staff_client.user.groups.add(make_group("Comptabilité"))
    assert staff_client.get(url).context["subordinate"] is True


def test_gestion_groupes_avec_subordonnes(staff_client, superuser_client, make_group, make_user):
    compta = make_group("Comptabilité", "Compta")
    staff_client.user.groups.add(compta)
    subordinate = make_user(first_name="Sub", last_name="Ordonné")
    subordinate.groups.add(compta)
    UserChief.objects.create(chief=staff_client.user, subordonate=subordinate)
    url = reverse("accounts:update_user_groupes")

    response = staff_client.get(url)
    assert response.status_code == 200
    assert response.context["initial"] == (subordinate.pk, "Sub Ordonné")
    assert response.context["form"].fields["groups"].initial == [compta.id]

    admin_response = superuser_client.get(url)
    assert {pk for pk, _, _ in admin_response.context["users"]} == {staff_client.user.pk, subordinate.pk}


def test_gestion_groupes_superuser_seul(make_superuser):
    client = Client()
    client.force_login(make_superuser())

    assert client.get(reverse("accounts:update_user_groupes")).context["not_users"] is True


def test_modification_groupes(superuser_client, make_group, make_user, no_error_mail):
    compta = make_group("Comptabilité", "Compta")
    achats = make_group("Achats")
    user = make_user()
    user.groups.add(compta)
    url = reverse("accounts:modification_groupes")

    response = superuser_client.post(url, {"pk": user.pk, "groups[]": [achats.id]}, **AJAX)
    assert response.json() == {"success": "ok"}
    assert list(user.groups.values_list("name", flat=True)) == ["Achats"]

    assert superuser_client.post(url, {"pk": "None"}, **AJAX).json() == {"success": "ko"}
    assert superuser_client.post(url, {"pk": user.pk}).json() == {"success": "ko"}
    assert superuser_client.get(url).status_code == 405
    assert no_error_mail == []

    unknown_group = superuser_client.post(url, {"pk": user.pk, "groups[]": [achats.id + 100]}, **AJAX)
    assert unknown_group.json() == {"success": "ko"}
    assert [kind for kind, _ in no_error_mail] == ["log", "mail"]
    assert "modification-groupes" in no_error_mail[0][1][1]


def test_affichage_groupes(superuser_client, make_group, make_user, no_error_mail):
    compta = make_group("Comptabilité")
    user = make_user()
    user.groups.add(compta)
    url = reverse("accounts:affichage_groupes")

    assert superuser_client.post(url, {"pk": user.pk}, **AJAX).json() == {"success": [compta.id]}
    assert superuser_client.post(url, {"pk": user.pk + 100}, **AJAX).json() == {"success": "ko"}
    assert superuser_client.post(url, {"pk": "abc"}, **AJAX).json() == {"success": "ko"}
    assert len(no_error_mail) == 4

    plain = superuser_client.post(url, {"pk": user.pk})
    assert plain.status_code == 302
    assert plain.url == "/"


def test_groupes_acces_staff(superuser_client, make_group):
    compta = make_group("Comptabilité")
    achats = make_group("Achats")
    url = reverse("accounts:groups_access_staff")

    assert superuser_client.get(url).status_code == 200

    superuser_client.post(url, {"group": [compta.id, achats.id]})
    assert set(AuthGroupAccessStaff.objects.values_list("group_id", flat=True)) == {compta.id, achats.id}

    superuser_client.post(url, {"group": [achats.id]})
    assert list(AuthGroupAccessStaff.objects.values_list("group_id", flat=True)) == [achats.id]
    assert Group.objects.count() == 2


# TÉLÉVERSEMENTS ===================================================================================


@pytest.mark.usefixtures("media_tmp", "clamd_off")
@pytest.mark.parametrize(
    ("route", "good_name", "good_content", "bad_name", "type_insert", "label"),
    [
        ("staff_insertions", "staffs.csv", staff_csv(["a@b.fr;a;b;c;d;e"]), "staffs.xlsx", 1, "un csv"),
        ("users_insertions", "users.xlsx", users_xlsx([["a@b.fr", "a", "b", "c", "d"]]), "users.csv", 0, "un fichier excel"),
    ],
)
def test_televersement(staff_client, route, good_name, good_content, bad_name, type_insert, label):
    """Ecran, téléversement valide, mauvaise extension, doublon, fichier absent"""
    url = reverse(f"accounts:{route}")

    page = staff_client.get(url)
    assert page.status_code == 200
    assert list(page.context["files_upload"]) == []

    response = staff_client.post(url, {"file": SimpleUploadedFile(good_name, good_content)})
    uploaded = UploadUserFile.objects.get(base_name_file=good_name)
    assert response.json()["isValid"] is True
    assert f"deleteUpload({uploaded.pk}" in response.json()["htmlFile"]
    assert (uploaded.user, uploaded.type_insert) == (staff_client.user, type_insert)
    assert list(staff_client.get(url).context["files_upload"]) == [uploaded]

    duplicate = staff_client.post(url, {"file": SimpleUploadedFile(good_name, good_content)})
    assert duplicate.json() == {"isValid": False, "message": f"Erreur : - Le fichier {good_name}, a déjà été téléversé !"}

    bad = staff_client.post(url, {"file": SimpleUploadedFile(bad_name, b"x")})
    assert bad.json()["isValid"] is False
    assert f"pas {label}" in bad.json()["message"]

    missing = staff_client.post(url, {})
    assert missing.json()["isValid"] is False


@pytest.mark.usefixtures("media_tmp")
def test_televersement_formulaire_invalide(staff_client, monkeypatch):
    """Un fichier refusé par la validation (antivirus) n'est pas enregistré"""
    from django.core.exceptions import ValidationError  # pylint: disable=C0415
    from apps.users import views as users_views  # pylint: disable=C0415

    def _infected(_value):
        raise ValidationError("fichier infecté")

    monkeypatch.setattr(users_views.UploadStaffsForm.base_fields["file"], "validators", [_infected])

    response = staff_client.post(reverse("accounts:staff_insertions"), {"file": SimpleUploadedFile("staffs.csv", b"x")})

    assert response.json() == {"isValid": False, "message": "Erreur : - Le fichier staffs.csv, n'a pu être téléversé !"}
    assert UploadUserFile.objects.count() == 0


@pytest.mark.parametrize(
    ("route", "type_insert", "other_type"),
    [("delete_staffs_upload_file", 1, 0), ("delete_users_upload_file", 0, 1)],
)
def test_suppression_fichier_televerse(staff_client, make_upload, media_tmp, route, type_insert, other_type):
    """Suppression de son fichier (enregistrement + disque) ; autre type ou inconnu refusés"""
    upload = make_upload(staff_client.user, "mien.csv", b"x", type_insert=type_insert)
    other = make_upload(staff_client.user, "autre.csv", b"x", type_insert=other_type)

    assert (media_tmp / "users" / "mien.csv").is_file()
    assert staff_client.post(reverse(f"accounts:{route}", kwargs={"pk": upload.pk}), **AJAX).json() == {"success": "ok"}
    assert UploadUserFile.objects.filter(pk=upload.pk).exists() is False
    assert (media_tmp / "users" / "mien.csv").is_file() is False
    assert staff_client.post(reverse(f"accounts:{route}", kwargs={"pk": other.pk}), **AJAX).json() == {"success": "ko"}
    assert staff_client.post(reverse(f"accounts:{route}", kwargs={"pk": 99999}), **AJAX).json() == {"success": "ko"}

    plain = staff_client.post(reverse(f"accounts:{route}", kwargs={"pk": other.pk}))
    assert plain.status_code == 302
    assert plain.url == reverse("home")
    assert staff_client.get(reverse(f"accounts:{route}", kwargs={"pk": other.pk})).status_code == 405


@pytest.mark.usefixtures("site")
def test_integrations(staff_client, make_upload):
    """Lancement des intégrations staff (csv) et utilisateurs (excel)"""
    make_upload(staff_client.user, "staffs.csv", staff_csv([f"s@heron.local;S;T;st;Compta;{PASSWORD}"]), type_insert=1)
    make_upload(staff_client.user, "users.xlsx", users_xlsx([["u@heron.local", "U", "V", "uv", ""]]), type_insert=0)

    staff = staff_client.post(reverse("accounts:staff_integrations"), **AJAX).json()
    assert staff["od"] is False
    assert "staffs.csv, a réussi" in staff["html"]
    assert User.objects.get(email="s@heron.local").is_staff is True

    users = staff_client.post(reverse("accounts:users_integrations"), **AJAX).json()
    assert "users.xlsx, a réussi" in users["html"]
    assert User.objects.get(email="u@heron.local").is_staff is False
    assert UploadUserFile.objects.count() == 0

    for route in ("staff_integrations", "users_integrations"):
        plain = staff_client.post(reverse(f"accounts:{route}"))
        assert plain.status_code == 302
        assert plain.url == reverse("home")


# CHANGEMENT D'EMAIL ===============================================================================


def test_changement_email(logged_client, make_user):
    make_user(email="pris@heron.local", username="pris")
    url = reverse("accounts:change_email")
    current = logged_client.user.email

    assert logged_client.get(url).status_code == 200

    cases = [
        ({"last_email": "inconnu@heron.local", "email": "n@heron.local", "email_verif": "n@heron.local"}, "est inconnu"),
        ({"last_email": current, "email": "n@heron.local", "email_verif": "m@heron.local"}, "ne sont pas identiques"),
        ({"last_email": current, "email": "pris@heron.local", "email_verif": "pris@heron.local"}, "existe déjà"),
    ]

    for data, expected in cases:
        response = logged_client.post(url, data)
        assert response.status_code == 200
        assert expected in [m.message for m in get_messages(response.wsgi_request)][-1]
        assert logged_client.session["level"] == 50

    response = logged_client.post(url, {"last_email": current, "email": "n@heron.local", "email_verif": "n@heron.local"})
    assert response.status_code == 302
    assert response.url == reverse("logout_email")
    assert User.objects.filter(email="n@heron.local").exists()
    assert "_auth_user_id" not in logged_client.session
