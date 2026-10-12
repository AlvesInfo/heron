"""FR : Module générique de donwload de fichiers.

EN : Generic file download module.

Commentaire:

created at: 2021-09-08
created by: Paulo ALVES

modified at: 2022-05-19
modified by: Paulo ALVES
"""

import io
from pathlib import Path

from django.conf import settings
from django.http import HttpResponse

CONTENT_TYPE_EXCEL = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
CONTENT_TYPE_CSV = "text/csv"


def download_status_key(download_token: str) -> str:
    """Clé de session du marqueur de fin de téléchargement d'un jeton."""
    return f"download_complete_{download_token}"


def response_file(
    function_file, file_name, content_type, *args, download_token=None, session=None, **kwargs
):
    """Fonction qui renvoi un fichier par HttpResponse.

    :param function_file: Fonction qui génère le fichier
    :param file_name: non à donner au fichier
    :param content_type: content_type http du fichier
    :param args: arguments à passer à la fonction
    :param download_token: jeton pour signaler la fin du téléchargement au JavaScript (optionnel)
    :param session: session de la requête, porteuse du marqueur de fin de téléchargement
    :param kwargs: arguments nommés à passer à la fonction
    :return: HttpResponse.
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

    # Fin de téléchargement signalée au JavaScript de la page (qui interroge core:download_status)
    # par un marqueur en session : rien n'est écrit dans un cookie
    if download_token and session is not None:
        session[download_status_key(download_token)] = True

    return response


def x_accel_exists_file_response(
    file_path: Path,
    mime_type: str = CONTENT_TYPE_EXCEL,
):
    """Retourne l'objet response pour le téléchargement d'un fichier existant et rendu soit par nginx.

    directement si on est en production, soit par l'objet content type de django
    :param file_path: non à donner au fichier
    :param mime_type: type mime du fichier à renvoyer
    :return: HttpResponse.
    """
    response = HttpResponse()

    if settings.DEBUG:
        with Path(file_path).open("rb") as file:
            application = mime_type
            response = HttpResponse(file, content_type=application)
    else:
        response["content-type"] = ""
        response["X-Accel-Redirect"] = "/excel_media/" + file_path.name

    attachment = f'attachment; filename="{file_path.name}"'
    response["Content-Disposition"] = attachment

    return response
