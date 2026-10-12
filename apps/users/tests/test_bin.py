# pylint: disable=E0401,W0621
"""
FR : Tests de l'intégration en masse des staffs (csv) et des utilisateurs (excel)
EN : Tests for staffs (csv) and users (excel) mass insertion

created at: 2026-10-12
created by: Paulo ALVES
"""
import smtplib
from pathlib import Path

import pytest
from django.core import mail
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import RequestFactory

from apps.users.bin import file_insert_users, insert_staffs
from apps.users.bin.file_insert_users import insert_users, set_insert_users
from apps.users.bin.insert_staffs import UserInsertError, set_insert_staffs
from apps.users.models import AuthGroupAccessStaff, UploadUserFile, User
from apps.users.tests.conftest import PASSWORD, staff_csv, users_xlsx

pytestmark = pytest.mark.django_db

STAFF_ROW = f"nouveau@heron.local;Paul;Alves;paul;Compta;{PASSWORD}"


@pytest.fixture
def request_factory(site):  # pylint: disable=W0613
    """Request minimale pour la construction des liens d'initialisation de mot de passe"""
    return RequestFactory().get("/")


def _write(tmp_path, name, content):
    path = tmp_path / name
    path.write_bytes(content)
    return path


# STAFFS (CSV) =====================================================================================


def test_insert_staffs(tmp_path, make_group, make_user):
    """Création des staffs rattachés aux groupes d'accès, lignes en erreur signalées"""
    make_user(email="existe@heron.local", username="existe")
    AuthGroupAccessStaff.objects.create(group=make_group("Comptabilité"))
    csv_file = _write(
        tmp_path,
        "staffs.csv",
        staff_csv([STAFF_ROW, f"existe@heron.local;X;Y;x;Compta;{PASSWORD}", f"long@heron.local;{'P' * 90};Alves;long;;{PASSWORD}"]),
    )

    bol, errors = insert_staffs.insert_staffs(csv_file, "ACF")

    created = User.objects.get(email="nouveau@heron.local")
    assert bol is None
    assert len(errors) == 1
    assert "existe@heron.local" in errors[0]
    assert "email" in errors[0]
    assert (created.is_staff, created.is_superuser, created.code_child_center, created.function) == (True, False, "ACF", "Compta")
    assert created.check_password(PASSWORD)
    assert [group.name for group in created.groups.all()] == ["Comptabilité"]
    assert len(User.objects.get(email="long@heron.local").first_name) == 80


def test_insert_staffs_sans_erreur_et_fichiers_invalides(tmp_path, monkeypatch):
    ok_file = _write(tmp_path, "ok.csv", staff_csv([STAFF_ROW]))
    bad_columns = _write(tmp_path, "colonnes.csv", staff_csv(["a@b.fr;x"], header="email;autre"))

    assert insert_staffs.insert_staffs(ok_file, "ACF") == (True, [])
    assert insert_staffs.insert_staffs(tmp_path / "absent.csv", "ACF") == (None, ["le fichier absent.csv est introuvable"])

    bol, errors = insert_staffs.insert_staffs(bad_columns, "ACF")
    assert bol is None
    assert "colonnes nécessaires" in errors[0]

    def _raise(*_args, **_kwargs):
        raise IntegrityError("doublon")

    User.objects.filter(email="nouveau@heron.local").delete()
    monkeypatch.setattr(User.objects, "create_user", _raise)
    assert insert_staffs.insert_staffs(ok_file, "ACF") == (None, ["erreur de création de l'utilisateur : nouveau@heron.local"])
    assert issubclass(UserInsertError, Exception)


def test_set_insert_staffs(make_staff, make_upload, media_tmp):
    """Un fichier réussi, un fichier avec une erreur, un avec plusieurs ; tous supprimés ensuite"""
    staff = make_staff()
    make_upload(staff, "ok.csv", staff_csv([STAFF_ROW]), type_insert=1)
    make_upload(staff, "une.csv", staff_csv(["pas-un-email;a;b;c;d;e"]), type_insert=1)
    make_upload(staff, "deux.csv", staff_csv(["pas-un-email;a;b;c;d;e", "autre;a;b;c;d;e"]), type_insert=1)
    make_upload(staff, "users.xlsx", b"ignore", type_insert=0)

    result, html = set_insert_staffs(staff)

    assert result is None
    assert "ok.csv, a réussi" in html
    assert "une.csv à généré une erreur" in html
    assert "deux.csv à généré des erreurs" in html
    assert User.objects.filter(email="nouveau@heron.local", code_child_center="ACU").exists()
    assert list(UploadUserFile.objects.values_list("base_name_file", flat=True)) == ["users.xlsx"]
    assert sorted(path.name for path in Path(media_tmp / "users").iterdir()) == ["users.xlsx"]
    assert set_insert_staffs(staff) == (None, "")

    # Fichier physique déjà absent : seul l'enregistrement est supprimé
    orphan = make_upload(staff, "orphelin.csv", b"x", type_insert=1)
    (media_tmp / "users" / "orphelin.csv").unlink()
    insert_staffs.delete_upload_file(orphan)
    assert UploadUserFile.objects.filter(pk=orphan.pk).exists() is False


# UTILISATEURS (EXCEL) =============================================================================


def test_insert_users(tmp_path, request_factory, make_group):
    """Création, rattachement aux groupes d'accès, mot de passe aléatoire et mail d'initialisation"""
    AuthGroupAccessStaff.objects.create(group=make_group("Achats"))
    xlsx = _write(tmp_path, "users.xlsx", users_xlsx([["Nouveau@Heron.LOCAL", "Paul", "Alves", "paul", ""], ["pas-un-email", "", "", "", ""]]))

    bol, errors = insert_users(xlsx, request_factory, "ACF")

    user = User.objects.get(email="nouveau@heron.local")
    assert bol is None
    assert len(errors) == 1
    assert "pas-un-email" in errors[0]
    assert (user.is_staff, user.function, user.code_child_center) == (False, "Utilisateur", "ACF")
    assert user.has_usable_password()
    assert [group.name for group in user.groups.all()] == ["Achats"]
    assert len(mail.outbox) == 1
    assert mail.outbox[0].subject == "Heron -  Initialisation du Compte"
    assert "password-reset-confirm" in mail.outbox[0].body or "reset" in mail.outbox[0].body
    assert "nouveau@heron.local" in mail.outbox[0].body


def test_insert_users_fichiers_invalides(tmp_path, request_factory):
    bad_columns = _write(tmp_path, "colonnes.xlsx", users_xlsx([["a@b.fr"]], header=["email"]))
    corrupted = _write(tmp_path, "corrompu.xlsx", b"pas un fichier excel")

    bol, errors = insert_users(bad_columns, request_factory, "ACF")
    assert bol is None
    assert "colonnes nécessaires" in errors[0]

    bol, errors = insert_users(corrupted, request_factory, "ACF")
    assert bol is None
    assert "n'est pas supportée" in errors[0]

    assert insert_users(tmp_path / "absent.xlsx", request_factory, "ACF") == (None, ["le fichier absent.xlsx est introuvable"])


@pytest.mark.parametrize(
    ("exception", "expected", "created"),
    [
        (smtplib.SMTPAuthenticationError(535, b"refus"), "l'envoi d'email ne fonctionne pas", True),
        (ValidationError("règles"), "ne respecte pas les règles", True),
        (IntegrityError("doublon"), "erreur de création de l'utilisateur : a@heron.local", True),
    ],
)
def test_insert_users_erreurs_de_creation(tmp_path, request_factory, monkeypatch, exception, expected, created):
    """Les erreurs à la création ou à l'envoi du mail sont rapportées, ligne par ligne"""
    xlsx = _write(tmp_path, "users.xlsx", users_xlsx([["a@heron.local", "A", "B", "ab", "Vendeur"]]))

    def _raise(*_args, **_kwargs):
        raise exception

    monkeypatch.setattr(file_insert_users, "send_initial_password_email", _raise)

    bol, errors = insert_users(xlsx, request_factory, "ACF")

    assert bol is None
    assert expected in errors[0]
    assert User.objects.filter(email="a@heron.local").exists() is created


def test_insert_users_sans_erreur(tmp_path, request_factory):
    xlsx = _write(tmp_path, "users.xlsx", users_xlsx([["a@heron.local", "A", "B", "ab", "Vendeur"]]))

    assert insert_users(xlsx, request_factory, "ACF") == (True, [])
    assert User.objects.get(email="a@heron.local").function == "Vendeur"


def test_set_insert_users(make_staff, make_upload, media_tmp, request_factory):
    staff = make_staff()
    make_upload(staff, "ok.xlsx", users_xlsx([["a@heron.local", "A", "B", "ab", ""]]), type_insert=0)
    make_upload(staff, "ko.xlsx", users_xlsx([["pas-un-email", "", "", "", ""]]), type_insert=0)
    make_upload(staff, "staffs.csv", staff_csv([STAFF_ROW]), type_insert=1)

    result, html = set_insert_users(staff, request_factory)

    assert result is None
    assert "ok.xlsx, a réussi" in html
    assert "ko.xlsx à généré une erreur" in html
    assert User.objects.get(email="a@heron.local").code_child_center == "ACU"
    assert list(UploadUserFile.objects.values_list("base_name_file", flat=True)) == ["staffs.csv"]
    assert sorted(path.name for path in Path(media_tmp / "users").iterdir()) == ["staffs.csv"]
