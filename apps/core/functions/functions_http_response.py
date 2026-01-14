# pylint: disable=E0401
"""
FR : Module générique de donwload de fichiers
EN : Generic file download module

Commentaire:

created at: 2021-09-08
created by: Paulo ALVES

modified at: 2022-05-19
modified by: Paulo ALVES
"""
import io
from pathlib import Path

from django.shortcuts import HttpResponse

from heron.settings import DEBUG

CONTENT_TYPE_EXCEL = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
CONTENT_TYPE_CSV = "text/csv"


def response_file(function_file, file_name, content_type, *args, download_token=None, **kwargs):
    """Fonction qui renvoi un fichier par HttpResponse
    :param function_file: Fonction qui génère le fichier
    :param file_name: non à donner au fichier
    :param content_type: content_type http du fichier
    :param args: arguments à passer à la fonction
    :param download_token: token pour signaler la fin du téléchargement au JavaScript (optionnel)
    :param kwargs: arguments nommés à passer à la fonction
    :return: HttpResponse
    """
    file_io = io.BytesIO()

    if args and kwargs:
        function_file(file_io, file_name, *args, **kwargs)
    elif args:
        function_file(file_io, file_name, *args)
    elif kwargs:
        function_file(file_io, file_name, **kwargs)
    else:
        function_file(file_io, file_name)

    file_io.seek(0)
    response = HttpResponse(file_io.read(), content_type=content_type)
    response["Content-Disposition"] = f"attachment; filename={file_name}"
    file_io.close()

    # Définir le cookie pour signaler la fin du téléchargement au JavaScript
    if download_token:
        response.set_cookie(
            f"download_complete_{download_token}",
            "true",
            max_age=60,
            samesite="Lax"
        )

    return response


def x_accel_exists_file_response(
    file_path: Path,
    mime_type: str = CONTENT_TYPE_EXCEL,
):
    """
    Retourne l'objet response pour le téléchargement d'un fichier existant et rendu soit par nginx
    directement si on est en production, soit par l'objet content type de django
    :param file_path: non à donner au fichier
    :param mime_type: type mime du fichier à renvoyer
    :return: HttpResponse
    """
    response = HttpResponse()

    if DEBUG:
        with open(file_path, "rb") as file:
            application = mime_type
            response = HttpResponse(file, content_type=application)
    else:
        response["content-type"] = ""
        response["X-Accel-Redirect"] = "/excel_media/" + file_path.name

    attachment = f'attachment; filename="{file_path.name}"'
    response["Content-Disposition"] = attachment

    return response
