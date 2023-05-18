# pylint: disable=E0401,R0903
"""
FR : Vue générique d'import et traitement de fichiers en base de donnée
EN : Generic view for importing and processing files in the database

Commentaire:

created at: 2023-05-18
created by: Paulo ALVES

modified at: 2023-05-18
modified by: Paulo ALVES
"""

from typing import AnyStr

from django.shortcuts import render, redirect, reverse
from django.http import HttpRequest, HttpResponse
from django.contrib import messages

from apps.core.exceptions import LaunchDoesNotExistsError
from apps.parameters.bin.core import get_object
from apps.parameters.models import InvoiceFunctions


def processing_files(request: HttpRequest, function_name: AnyStr) -> HttpResponse:
    """Traitement des imports de fichiers, les fonctions de traitements doivent avoir
    été programmées et paramétrées dans la table InvoiceFunctions
    :param request: request Django
    :param function_name: fonction à appliquer au fichier
    :return:
    """
    function = None

    try:
        function = get_object(task_to_launch=function_name)
    except LaunchDoesNotExistsError:
        messages.add_message(
            request,
            50,
            f"La fonction d'import '{function_name}' que vous souhaitez réaliser, "
            "n'est pas paramétrée. Veuillez en faire la programmation et la définir sur cette page"
        )
        request.session["level"] = 50

    if function is None:
        return redirect(reverse("parameters:functions_list"))

    context = {
        "titre_table": f"Import en masse de données - Fonction : {function_name}"
    }

    if request.method == "POST":
        pass

    return render(request, "data_flux/import_file.html", context=context)
