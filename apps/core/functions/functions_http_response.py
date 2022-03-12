import io

from django.shortcuts import HttpResponse

CONTENT_TYPE_EXCEL = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def response_file(function_file, file_name, content_type, *args, **kwargs):
    """Fonction qui renvoi un fichier par HttpResponse
        :param function_file: Fonction qui génère le fichier
        :param file_name: non à donner au fichier
        :param content_type: content_type http du fichier
        :param args: arguments à passer à la fonction
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
    return response
