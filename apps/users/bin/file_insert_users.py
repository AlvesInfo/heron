"""Module l'intégration en masse d'utilisateurs depuis un fichier Excel.

Commentaire:

created at: 2021-10-30
created by: Paulo ALVES

modified at: 2026-10-12
modified by: Paulo ALVES
"""

import logging
import smtplib
import uuid
from pathlib import Path

from django.contrib.auth.models import Group
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from apps.core.functions.function_imports import (
    ExcelToCsvError,
    IterFileToInsert,
    IterFileToInsertError,
)
from apps.core.functions.functions_setups import settings
from apps.users.bin.insert_staffs import (
    UserInsertError,
    _file_message,
    _serializer_errors,
    delete_upload_file,
)
from apps.users.forms.forms_serializers.serializer_for_insert_users import UsersSerializerUsers
from apps.users.models import AuthGroupAccessStaff, UploadUserFile, User

logger = logging.getLogger("connexion")

# Colonnes attendues dans le fichier excel (clé = champ du modèle, valeur = entête du fichier)
USERS_COLUMNS = {
    "email": "email",
    "first_name": "first_name",
    "last_name": "last_name",
    "username": "username",
    "function": "fonction",
}
COLUMNS_ERROR = (
    '<span style="margin-left: 2em;">Le fichier ne contient pas les colonnes nécessaires</span></br>'
    '<span style="margin-left: 2em;">'
    + ", ".join(f'"{column}"' for column in USERS_COLUMNS.values())
    + "</span></br>"
)


def send_initial_password_email(user, request):
    """Envoi à l'utilisateur créé du lien d'initialisation de son mot de passe."""
    current_site = get_current_site(request)
    message = render_to_string(
        "users/password_initial_email.txt",
        {
            "user": user,
            "domain": current_site,
            "uid": urlsafe_base64_encode(force_bytes(user.pk)),
            "token": PasswordResetTokenGenerator().make_token(user),
        },
    )
    user.email_user("Heron -  Initialisation du Compte", message)


def _create_user(validated, request):
    """Création d'un utilisateur validé, rattachement aux groupes des staffs et envoi du mail."""
    user = User.objects.create_user(
        validated.get("username"),
        str(validated.get("email")).lower(),
        validated.get("password"),
        first_name=validated.get("first_name"),
        last_name=validated.get("last_name"),
        function=validated.get("function"),
        code_child_center=validated.get("code_child_center"),
    )
    group_staff = AuthGroupAccessStaff.objects.values_list("group_id", flat=True)

    for group in Group.objects.filter(id__in=list(group_staff)):
        group.user_set.add(user)

    send_initial_password_email(user, request)


def _insert_one_user(validated_data: dict, request, errors: list) -> None:
    """Crée un utilisateur validé ; une erreur est journalisée et ajoutée à `errors`."""
    email = str(validated_data.get("email")).lower()

    try:
        _create_user(validated_data, request)
    except (UserInsertError, IntegrityError, ValueError):
        logger.exception("erreur de creation d users en masse")
        errors.append(f"erreur de création de l'utilisateur : {email}")
    except ValidationError:
        logger.exception("erreur de creation d users en masse")
        errors.append(
            f"erreur de création de l'utilisateur : {email}, "
            f"le mot de passe ne respecte pas les règles"
        )
    except smtplib.SMTPException:
        logger.exception("erreur d envoi de mail pour creation d users en masse")
        errors.append(
            f"l'utilisateur : {email}, a été créé, mais l'envoi d'email ne fonctionne pas'"
        )


def insert_users(xls_file: Path, request, code_child_center: str):
    """Insertion des utilisateurs depuis un fichier excel.

    :param xls_file: fichier à intégrer au format excel
    :param request: http.request (construction du lien d'initialisation du mot de passe)
    :param code_child_center: centrale par défaut des utilisateurs créés (celle de l'importateur)
    :return: (True, []) si tout est passé, sinon (None, liste des erreurs html).
    """
    errors = []

    if not xls_file.is_file():
        return None, [f"le fichier {xls_file.name} est introuvable"]

    try:
        with IterFileToInsert(xls_file, USERS_COLUMNS, first_line=1) as file_iter:
            for dict_user in file_iter.chunk_dict():
                data = {
                    "code_child_center": code_child_center,
                    **dict_user,
                    "is_superuser": False,
                    "is_staff": False,
                    "password": str(uuid.uuid4()),
                }
                serializer = UsersSerializerUsers(data=data)

                if not serializer.is_valid():
                    errors.append(_serializer_errors(dict_user, serializer))
                    continue

                _insert_one_user(serializer.validated_data, request, errors)

    except IterFileToInsertError:
        logger.exception("colonnes manquantes pour creation d users en masse")
        errors.append(COLUMNS_ERROR)

    except ExcelToCsvError:
        logger.exception("Erreur de conversion d'un fichier excel en csv")
        errors.append(
            '<span style="margin-left: 2em;">'
            "La version du fichier excel n'est pas supportée"
            "</span></br>"
        )

    if not errors:
        return True, errors

    return None, errors


def set_insert_users(user, request):
    """Insertion en base des utilisateurs depuis les fichiers excel téléversés.

    :param user: utilisateur en cours (importateur)
    :param request: request
    :return: (None, messages html).
    """
    html_messages = ""

    for file in UploadUserFile.objects.filter(user=user, type_insert=0):
        xls_file = Path(settings.MEDIA_DIR) / str(file.file)
        bol, retour = insert_users(xls_file, request, user.code_child_center)
        html_messages += _file_message(file, bol, retour)
        delete_upload_file(file)

    return None, html_messages
