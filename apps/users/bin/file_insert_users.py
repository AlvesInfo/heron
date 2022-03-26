# pylint: disable=C0330, C0411, C0303, E1101, C0413, I1101
"""Module l'intégration en masse d'utilisateurs Staff (Admin délégués)

Commentaire:

created at: 2021-10-30
created by: Paulo ALVES

modified at: 2021-10-30
modified by: Paulo ALVES
"""
import uuid
from pathlib import Path
import smtplib
import logging

from xlrd.biffh import XLRDError

from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.template.loader import render_to_string
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.sites.shortcuts import get_current_site

from apps.users.models import AuthGroupAccessStaff
from apps.core.functions.functions_setups import settings
from apps.core.functions.function_imports import IterFileToInsertError, IterFileToInsert
from apps.users.serializers.serializer_for_insert_users import UsersSerializerUsers
from apps.users.models import User, UploadUserFile

from apps.core.functions.functions_excel import ExcelToCsv

logger = logging.getLogger("connexion")


class UserInsertError(Exception):
    """Gestion d'exceptions"""


def insert_users(xls_file, request):
    """Insertion
        :param request: http.request
        :param xls_file: fichier à intégrer au format excel
        :return:
    """
    errors = []

    if xls_file.is_file():
        try:
            csv_file = ExcelToCsv(
                rep=str(xls_file.parents[0]), deletion=True, file_name=str(xls_file.name)
            ).make_csv()[0]

            columns_dict = {
                "email": "email",
                "first_name": "first_name",
                "last_name": "last_name",
                "username": "username",
                "fonction": "fonction",
            }

            with IterFileToInsert(csv_file, columns_dict, first_line=1) as file_iter:
                try:
                    for dict_user in file_iter.chunk_file():
                        user = UsersSerializerUsers(
                            data={
                                **dict_user,
                                **{
                                    "is_superuser": False,
                                    "is_staff": False,
                                    "password": str(uuid.uuid4),
                                },
                            }
                        )

                        if user.is_valid():
                            try:
                                email = str(user.validated_data.get("email")).lower()
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
                                user.save()

                                group_staff = [
                                    row[0]
                                    for row in AuthGroupAccessStaff.objects.all().values_list(
                                        "group_id"
                                    )
                                ]

                                for group_name in Group.objects.filter(id__in=group_staff):
                                    group_name.user_set.add(user)

                                subject = "Heron -  Initialisation du Compte"
                                current_site = get_current_site(request)
                                message = render_to_string(
                                    "users/password_initial_email.html",
                                    {
                                        "user": user,
                                        "domain": current_site,
                                        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                                        "token": PasswordResetTokenGenerator().make_token(user),
                                    },
                                )
                                user.email_user(subject, message)

                            except UserInsertError:
                                logger.exception(
                                    "erreur d envoi de mail pour creation d users en masse"
                                )
                                errors.append(f"erreur de création de l'utilisateur : {email}")
                            except ValidationError:
                                logger.exception(
                                    "erreur d envoi de mail pour creation d users en masse"
                                )
                                errors.append(
                                    f"erreur de création de l'utilisateur : {email}, "
                                    f"le mot de passe ne respecte pas les règles"
                                )
                            except smtplib.SMTPAuthenticationError:
                                logger.exception(
                                    "erreur d envoi de mail pour creation d users en masse"
                                )
                                errors.append(
                                    f"l'utilisateur : {email}, "
                                    f"a été créé, mais l'envoi d'email ne fonctionne pas'"
                                )
                        else:
                            erreur = (
                                f"erreur de création de l'utilisateur : "
                                f"{dict_user.get('email', 'inconnu')}</br>"
                            )

                            for key, error in user.errors.items():
                                erreur += (
                                    f'<span style="margin-left: 2em;">{key} : '
                                    f'{error[0]}</span></br>'
                                )
                            errors.append(erreur)

                except IterFileToInsertError:
                    logger.exception(
                        "erreur d envoi de mail pour creation d users en masse"
                    )
                    erreur = (
                        f'<span style="margin-left: 2em;">'
                        f"Le fichier ne contient pas les colonnes nécessaires"
                        f"</span></br>"
                        f'<span style="margin-left: 2em;">'
                        f'"email", "first_name", "last_name", "username", "fonction"'
                        f"</span></br>"
                    )
                    errors.append(erreur)

        except XLRDError:
            logger.exception(
                "Erreur de conversion d'un fichier excel en csv"
            )
            erreur = (
                f'<span style="margin-left: 2em;">'
                f"La version du fichier excel n'est pas supportée"
                f"</span></br>"
            )
            errors.append(erreur)

    if not errors:
        return True, errors

    return None, errors


def set_insert_users(user_id, request):
    """Snippets pour insertion en base des utilisateurs Staff (Admin délégué)
        :param request: request
        :param user_id: pk de l'utilisateur en cours
        :return: None
    """
    html_messages = ""
    files = UploadUserFile.objects.filter(user_id=user_id, type_insert=0)

    for file in files:
        csv_file = Path(settings.MEDIA_DIR) / str(file.file)

        bol, retour = insert_users(csv_file, request)

        if bol:
            message = f"""
                <li value="o" style="color: #00B050;font-weight: bold;">
                    L'intégration du fichier : {file.base_name_file}, a réussi !
                </li>
                </br>
                """
        else:
            errors = "".join(
                f'<li value="-"style="color: red;font-weight: normal;">{error}</li>\n'
                for error in retour
            )

            text_erreur = "une erreur" if len(retour) == 1 else "des erreurs"
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
