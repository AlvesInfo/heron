"""Module l'intégration en masse d'utilisateurs Staff (Admin délégués).

Commentaire:

created at: 2021-10-30
created by: Paulo ALVES

modified at: 2026-10-12
modified by: Paulo ALVES
"""

from pathlib import Path

from django.contrib.auth.models import Group
from django.db import IntegrityError

from apps.core.functions.function_imports import (
    ExcelToCsvError,
    IterFileToInsert,
    IterFileToInsertError,
)
from apps.core.functions.functions_setups import settings
from apps.users.forms.forms_serializers.serializer_for_insert_users import UsersSerializer
from apps.users.models import AuthGroupAccessStaff, UploadUserFile, User

# Colonnes attendues dans le fichier csv (clé = champ du modèle, valeur = entête du fichier)
STAFFS_COLUMNS = {
    "email": "email",
    "first_name": "first_name",
    "last_name": "last_name",
    "username": "username",
    "function": "fonction",
    "password": "password",
}
COLUMNS_ERROR = (
    '<span style="margin-left: 2em;">Le fichier ne contient pas les colonnes nécessaires</span></br>'
    '<span style="margin-left: 2em;">'
    + ", ".join(f'"{column}"' for column in STAFFS_COLUMNS.values())
    + "</span></br>"
)


class UserInsertError(Exception):
    """Gestion d'exceptions."""


def _serializer_errors(dict_user, serializer):
    """Message html des erreurs de validation d'une ligne du fichier."""
    erreur = f"erreur de création de l'utilisateur : {dict_user.get('email', 'inconnu')}</br>"

    for key, error in serializer.errors.items():
        erreur += f'<span style="margin-left: 2em;">{key} : {error[0]}</span></br>'

    return erreur


def _add_staff_groups(user):
    """Rattachement du staff aux groupes autorisés pour les Admin délégués."""
    group_staff = AuthGroupAccessStaff.objects.values_list("group_id", flat=True)

    for group in Group.objects.filter(id__in=list(group_staff)):
        group.user_set.add(user)


def insert_staffs(csv_file: Path, code_child_center: str):
    """Insertion des utilisateurs Staff depuis un fichier csv.

    :param csv_file: fichier à intégrer
    :param code_child_center: centrale par défaut des utilisateurs créés (celle de l'importateur)
    :return: (True, []) si tout est passé, sinon (None, liste des erreurs html).
    """
    errors = []

    if not csv_file.is_file():
        return None, [f"le fichier {csv_file.name} est introuvable"]

    try:
        with IterFileToInsert(csv_file, STAFFS_COLUMNS, first_line=1) as file_iter:
            for dict_user in file_iter.chunk_dict():
                data = {
                    "code_child_center": code_child_center,
                    **dict_user,
                    "is_superuser": False,
                    "is_staff": True,
                }
                serializer = UsersSerializer(data=data)

                if not serializer.is_valid():
                    errors.append(_serializer_errors(dict_user, serializer))
                    continue

                validated = serializer.validated_data
                email = validated.get("email")

                try:
                    user = User.objects.create_user(
                        validated.get("username"),
                        email,
                        validated.get("password"),
                        is_staff=True,
                        first_name=validated.get("first_name"),
                        last_name=validated.get("last_name"),
                        function=validated.get("function"),
                        code_child_center=validated.get("code_child_center"),
                    )
                    _add_staff_groups(user)
                except (UserInsertError, IntegrityError, ValueError):
                    errors.append(f"erreur de création de l'utilisateur : {email}")

    except (IterFileToInsertError, ExcelToCsvError):
        errors.append(COLUMNS_ERROR)

    if not errors:
        return True, errors

    return None, errors


def _file_message(file, bol, retour):
    """Message html du résultat d'intégration d'un fichier."""
    if bol:
        return f"""
                <li value="o" style="color: #00B050;font-weight: bold;">
                    L'intégration du fichier : {file.base_name_file}, a réussi !
                </li>
                </br>
                """

    errors = "".join(
        f'<li value="-"style="color: red;font-weight: normal;">{error}</li>\n' for error in retour
    )
    text_erreur = "une erreur" if len(retour) == 1 else "des erreurs"
    return f"""
                <li value="o" style="color: red;font-weight: bold;">
                    L'intégration du fichier : {file.base_name_file} à généré {text_erreur} :
                    <ol>
                        {errors}
                    </ol>
                </li>
                </br>
                """


def delete_upload_file(file):
    """Suppression de l'enregistrement du fichier téléversé et du fichier physique."""
    path = Path(settings.MEDIA_DIR) / str(file.file)
    file.delete()

    if path.is_file():
        path.unlink()


def set_insert_staffs(user):
    """Insertion en base des utilisateurs Staff (Admin délégué) depuis les fichiers téléversés.

    :param user: utilisateur en cours (importateur)
    :return: (None, messages html).
    """
    html_messages = ""

    for file in UploadUserFile.objects.filter(user=user, type_insert=1):
        csv_file = Path(settings.MEDIA_DIR) / str(file.file)
        bol, retour = insert_staffs(csv_file, user.code_child_center)
        html_messages += _file_message(file, bol, retour)
        delete_upload_file(file)

    return None, html_messages
