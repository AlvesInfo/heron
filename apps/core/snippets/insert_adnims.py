# pylint: disable=C0330, C0411, C0303, E1101, C0413, I1101
"""Module l'intégration en masse d'utilisateurs Admins

Commentaire:

created at: 2021-10-30
created by: Paulo ALVES

modified at: 2021-10-30
modified by: Paulo ALVES
"""
from pathlib import Path

from django.contrib.auth.models import Group

from apps.core.functions.function_imports import IterFileToInsert
from apps.users.snippets.serializer_for_insert_users import UsersSerializer
from apps.users.models import User


class UserInsertError(Exception):
    """Gestion d'exceptions"""


def set_insert_admins(file):
    """Snippets pour insertion en base des premiers utilisateurs
        :param file:
        :return: None
    """

    csv_file = Path(file)

    if csv_file.is_file():
        columns_dict = {
            "email": "email",
            "first_name": "first_name",
            "last_name": "last_name",
            "username": "username",
            "fonction": "fonction",
            "password": "password",
        }

        with IterFileToInsert(csv_file, columns_dict, first_line=0) as file_iter:
            for dict_user in file_iter.chunk_file():
                user = UsersSerializer(
                    data={**dict_user, **{"is_superuser": True, "is_staff": True}}
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
                        user.is_superuser = True
                        user.save()

                        groupes = Group.objects.all()

                        # Pour chancun des groupes on vas créer l'entrée
                        for group_name in groupes:
                            group_name.user_set.add(user)

                        print(f"l'utilisateur {email}, a été créé")

                    except UserInsertError:
                        print(f"erreur pour l'utilisateur : {email}")
                else:
                    print(user.errors)
