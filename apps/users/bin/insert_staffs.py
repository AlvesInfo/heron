# pylint: disable=C0330, C0411, C0303, E1101, C0413, I1101
"""Module l'intégration en masse d'utilisateurs Staff (Admin délégués)

Commentaire:

created at: 2021-10-30
created by: Paulo ALVES

modified at: 2021-10-30
modified by: Paulo ALVES
"""
from pathlib import Path

from django.contrib.auth.models import Group

from apps.users.models import AuthGroupAccessStaff
from apps.core.functions.functions_setups import settings
from apps.core.functions.function_imports import IterFileToInsert
from apps.users.serializers.serializer_for_insert_users import UsersSerializer
from apps.users.models import User, UploadUserFile


class UserInsertError(Exception):
    """Gestion d'exceptions"""


def insert_staffs(csv_file):
    """Insertion
        :param csv_file: fichier à intégrer
        :return:
    """
    errors = []

    if csv_file.is_file():
        columns_dict = {
            "email": "email",
            "first_name": "first_name",
            "last_name": "last_name",
            "username": "username",
            "fonction": "fonction",
            "password": "password",
        }

        with IterFileToInsert(csv_file, columns_dict, first_line=1) as file_iter:
            for dict_user in file_iter.chunk_file():
                user = UsersSerializer(
                    data={**dict_user, **{"is_superuser": False, "is_staff": True}}
                )

                if user.is_valid():
                    try:
                        email = user.validated_data.get("email")
                        first_name = user.validated_data.get("first_name")
                        last_name = user.validated_data.get("last_name")
                        username = user.validated_data.get("username")
                        fonction = user.validated_data.get("fonction")
                        password = user.validated_data.get("password")

                        user = User.objects.create_user(
                            username,
                            email,
                            password,
                            first_name=first_name,
                            last_name=last_name,
                            fonction=fonction,
                        )
                        user.is_staff = True
                        user.is_superuser = False
                        user.save()

                        group_staff = [
                            row[0]
                            for row in AuthGroupAccessStaff.objects.all().values_list(
                                "group_id"
                            )
                        ]

                        if group_staff:
                            groupes = Group.objects.filter(id__in=group_staff)
                            # Pour chancun des groupes on va créer l'entrée
                            for group_name in groupes:
                                group_name.user_set.add(user)

                    except UserInsertError:
                        errors.append(f"erreur de création de l'utilisateur : {email}")
                else:
                    erreur = (
                        f"erreur de création de l'utilisateur : "
                        f"{dict_user.get('email', 'inconnu')}</br>"
                    )

                    for key, error in user.errors.items():
                        erreur += f'<span style="margin-left: 2em;">{key} : {error[0]}</span></br>'

                    errors.append(erreur)

    if not errors:
        return True, errors

    return None, errors


def set_insert_staffs(user_id):
    """Snippets pour insertion en base des utilisateurs Staff (Admin délégué)
        :param user_id: pk de l'utilisateur en cours
        :return: None
    """
    html_messages = ""
    files = UploadUserFile.objects.filter(user_id=user_id)

    for file in files:
        csv_file = Path(settings.MEDIA_DIR) / str(file.file)

        bol, retour = insert_staffs(csv_file)

        if bol:
            message = f"""
                <li value="o" style="color: #00B050;font-weight: bold;">
                    L'intégration du fichier : {file.base_name_file}, a réussi !
                </li>
                </br>
                """
            html_messages += message

        else:
            errors = ""
            for error in retour:
                errors += f'<li value="-"style="color: red;font-weight: normal;">{error}</li>\n'
            if len(retour) == 1:
                text_erreur = "une erreur"
            else:
                text_erreur = "des erreurs"

            message = f"""
                <li value="o" style="color: red;font-weight: bold;">
                    L'intégration du fichier : {file.base_name_file} à généré {text_erreur} :
                    <ol>
                        {errors}
                    </ol>
                </li>
                </br>
                """
            html_messages += message

        try:
            file.delete()
            delete = Path(settings.MEDIA_DIR) / str(file.file)

            if delete.is_file():
                delete.unlink()

        except UploadUserFile.DoesNotExist:
            pass

    return None, html_messages
