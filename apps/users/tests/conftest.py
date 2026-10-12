# pylint: disable=W0621,E0401,R0913
"""
FR : conftest de l'app users - fabriques des groupes, staffs, superusers et fichiers téléversés
EN : users app conftest

Commentaire:

make_user, logged_client et ajax_client viennent du conftest racine. Les fichiers téléversés
sont écrits dans un répertoire temporaire (MEDIA_ROOT / MEDIA_DIR patchés), jamais dans files/.

created at: 2026-10-12
created by: Paulo ALVES
"""
import io
from typing import Any
from collections.abc import Callable

import pytest
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from openpyxl import Workbook

from apps.users import views as users_views
from apps.users.models import AuthGroupName, UploadUserFile

STAFF_HEADER = "email;first_name;last_name;username;fonction;password"
USERS_HEADER = ["email", "first_name", "last_name", "username", "fonction"]
PASSWORD = "MotDePasse!2026"


@pytest.fixture
def make_group(db) -> Callable[..., Group]:  # pylint: disable=W0613
    """Fabrique de groupes Django avec leur libellé d'affichage (AuthGroupName)"""

    def _factory(name: str = "Comptabilité", group_name: str | None = None) -> Group:
        group, _ = Group.objects.get_or_create(name=name)
        AuthGroupName.objects.get_or_create(group=group, defaults={"group_name": group_name or name})
        return group

    return _factory


@pytest.fixture
def make_staff(make_user) -> Callable[..., Any]:
    """Fabrique d'Admin délégués (is_staff)"""

    def _factory(email: str = "staff@heron.local", username: str = "staff", **kwargs: Any):
        kwargs.setdefault("is_staff", True)
        return make_user(email=email, username=username, password=PASSWORD, **kwargs)

    return _factory


@pytest.fixture
def make_superuser(make_user) -> Callable[..., Any]:
    """Fabrique de superusers"""

    def _factory(email: str = "admin@heron.local", username: str = "admin", **kwargs: Any):
        return make_user(email=email, username=username, password=PASSWORD, is_staff=True, is_superuser=True, **kwargs)

    return _factory


@pytest.fixture
def staff_client(make_staff) -> Client:
    """Client authentifié en Admin délégué (utilisateur en `client.user`)"""
    client = Client()
    client.user = make_staff()
    client.force_login(client.user)
    return client


@pytest.fixture
def superuser_client(make_superuser) -> Client:
    """Client authentifié en superuser (utilisateur en `client.user`)"""
    client = Client()
    client.user = make_superuser()
    client.force_login(client.user)
    return client


@pytest.fixture
def media_tmp(settings, tmp_path):
    """Répertoire media temporaire pour les fichiers téléversés"""
    settings.MEDIA_ROOT = tmp_path
    settings.MEDIA_DIR = tmp_path
    return tmp_path


@pytest.fixture
def clamd_off(monkeypatch):
    """Désactive la validation antivirus (clamd) du formulaire de téléversement"""
    monkeypatch.setattr(users_views.UploadStaffsForm.base_fields["file"], "validators", [])


@pytest.fixture
def site(settings):
    """Site courant (SITE_ID) pour la construction des liens des emails"""
    return Site.objects.get_or_create(pk=settings.SITE_ID, defaults={"domain": "heron.local", "name": "Héron"})[0]


@pytest.fixture
def no_error_mail(monkeypatch):
    """Neutralise l'écriture du log fichier et l'envoi de mail d'erreur des vues ajax"""
    calls = []
    monkeypatch.setattr(users_views, "write_log", lambda *args: calls.append(("log", args)))
    monkeypatch.setattr(users_views, "envoi_mail_erreur", lambda *args: calls.append(("mail", args)))
    return calls


def staff_csv(rows: list[str], header: str = STAFF_HEADER) -> bytes:
    """Contenu csv d'un fichier de staffs (entête + lignes `;`)"""
    return ("\n".join([header, *rows]) + "\n").encode("utf8")


def users_xlsx(rows: list[list[str]], header: list[str] | None = None) -> bytes:
    """Contenu xlsx d'un fichier d'utilisateurs"""
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(header or USERS_HEADER)

    for row in rows:
        sheet.append(row)

    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


@pytest.fixture
def make_upload(media_tmp) -> Callable[..., UploadUserFile]:  # pylint: disable=W0613
    """Fabrique de fichiers téléversés (enregistrement + fichier physique dans media_tmp)"""

    def _factory(user, name: str, content: bytes, type_insert: int = 1) -> UploadUserFile:
        return UploadUserFile.objects.create(
            file=SimpleUploadedFile(name, content), base_name_file=name, user=user, type_insert=type_insert
        )

    return _factory
