"""Module pour intégration de fichiers depuis une requête ajax, pour lres models

Commentaire:

created at: 2022-02-19
created by: Paulo ALVES

modified at: 2022-01-22
modified by: Paulo ALVES
"""
from django.contrib import messages

from core.bin.validate_file import IterFileToInsertError
from apps.projets.forms import ImportExcelFileForm
from apps.projets.imports.import_excel_files_models_factory import ImportExcelFactory


def import_file_to_model(request, projet_pk, model, url, object_plan=None, object_pk=None):
    """Fonction d'import et de validation d'un fichier excel, pour insertion en base des modèles à
    importer
        :param request: request issu de django
        :param projet_pk: id du projet
        :param model: modèle à importer
        :param url: url de redirection en cas d'erreurs
        :param object_plan: model de content_type pour le plan d'action
        :param object_pk: pk du model dans le content_type du plan d'action
        :return: le message à renvoyer à la requête Ajax
    """
    message = {}
    form = ImportExcelFileForm(request.POST, request.FILES)

    if form.is_valid() and request.FILES and request.method == "POST":
        file = request.FILES["file"]

        if file.name.split(".")[-1] not in {"xls", "xlsx"}:
            return {
                "success": "ko",
                "message": [
                    "Erreur dans le type de fichier ",
                    "Le fichier, doit être un fichier excel (xls, xlsx)",
                ],
            }

        try:
            excel_import = ImportExcelFactory(
                model, file, projet_pk, request.user, object_plan, object_pk
            )
            excel_import.validate_by_serializer()
            message["success"] = "ko"
            all_errors = excel_import.errors

            if all_errors:
                all_errors.append(
                    {"Les autres lignes (si il y en avaient) : ": [{"": "ont été importées"}]}
                )

            if excel_import.errors:
                messages.warning(
                    request, message=excel_import.errors, extra_tags="import_file_insert_errors"
                )
                request.session["level"] = 30
            else:
                request.session["level"] = 20
                messages.success(
                    request, message="Insertion réussie!", extra_tags=excel_import.modele
                )

            message["url"] = url

        except IterFileToInsertError as err:
            message["success"] = "ko"
            message["message"] = f"{str(err)}".replace("\n", " ").split(":")

    else:
        message = {"message": "une erreur c'est produite"}

    return message
