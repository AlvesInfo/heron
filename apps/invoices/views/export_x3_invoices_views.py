"""FR : View des lancements des exports X3.

EN : View of exports X3 launches.

Commentaire:

created at: 2023-08-17
created by: Paulo ALVES

modified at: 2023-08-17
modified by: Paulo ALVES
"""

from pathlib import Path
from zipfile import ZipFile

from celery import group
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.html import format_html
from django.views.generic import ListView

from apps.core.bin.content_types import CONTENT_TYPE_FILE
from apps.core.functions.functions_setups import settings
from apps.edi.models import EdiValidation
from apps.invoices.bin.invoives_nums import (
    get_bicpar_num,
    get_bispar_num,
    get_bispard_num,
    get_gaspar_num,
    get_zip_num,
)
from apps.invoices.models import ExportX3, Invoice, SaleInvoice
from heron import celery_app
from heron.loggers import LOGGER_VIEWS, LOGGER_X3


def _x3_exports() -> list[tuple]:
    """Exports X3 à lancer : (type d'export, centrale, champ du fichier dans ExportX3, nom du fichier).

    Les compteurs sont consommés dans l'ordre de la liste.
    """
    return [
        ("odana", "AC00", "odana_file", f"AC00_{get_gaspar_num()!s}.txt"),
        ("sale", "AC00", "sale_file", f"AC00_{get_bicpar_num()!s}.txt"),
        ("purchase", "AC00", "purchase_file", f"AC00_{get_bispard_num()!s}.txt"),
        ("gdaud", "GA00", "ga_file", f"GA00_{get_bispar_num()!s}.txt"),
        ("sdoa", "SD00", "sd_file", f"SD00_{get_bispar_num()!s}.txt"),
        ("do", "DO00", "do_file", f"DO00_{get_bispar_num()!s}.txt"),
    ]


def _launch_x3_exports(exports: list[tuple], user_pk) -> list:
    """Lance les tâches celery d'export et renvoie leurs résultats (True si l'export a réussi)."""
    tasks_list = [
        celery_app.signature(
            "launch_export_x3",
            kwargs={
                "export_type": export_type,
                "centrale": centrale,
                "file_name": file_name,
                "user_pk": str(user_pk),
                "nb_fac": 50_000,
            },
        )
        for export_type, centrale, _, file_name in exports
    ]

    return group(*tasks_list)().get(3600)


def _save_x3_exports(exports: list[tuple], file_name_zip: str) -> None:
    """Enregistre les fichiers générés (et leur zip) sur la période de validation en cours."""
    edi_validations = EdiValidation.objects.filter(Q(final=False) | Q(final__isnull=True)).first()
    export_x3, _ = ExportX3.objects.get_or_create(uuid_edi_validation=edi_validations)
    generated = {
        field: file_name
        for _, _, field, file_name in exports
        if (Path(settings.EXPORT_DIR) / file_name).is_file()
    }

    with ZipFile((Path(settings.EXPORT_DIR) / file_name_zip), "w") as zip_file:
        for file_name in generated.values():
            zip_file.write(Path(settings.EXPORT_DIR) / file_name, file_name)

    for _, _, field, _ in exports:
        setattr(export_x3, field, generated.get(field))

    export_x3.alls_zip_file = file_name_zip
    export_x3.save()


def _delete_x3_files(exports: list[tuple]) -> None:
    """Supprime les fichiers d'export générés (cas d'erreur)."""
    for *_, file_name in exports:
        (Path(settings.EXPORT_DIR) / file_name).unlink(missing_ok=True)


@transaction.atomic
def generate_exports_x3(request):
    """View de lancement des exports X3, (GASPAR - OD, BICPAR - Clients, BISPAR - Fournisseurs).

    :param request:
    :return:
    """
    titre_table = format_html(
        "{} <br>{}",
        "Génération des fichiers pour imports X3",
        "(GASPAR - OD, BICPAR - Clients, BISPARD - Fournisseurs)",
    )

    context = {
        "margin_table": 50,
        "titre_table": titre_table,
        "export": True,
    }
    sales = SaleInvoice.objects.filter(Q(export__isnull=True) | Q(export=False))
    purchases = Invoice.objects.filter(Q(export__isnull=True) | Q(export=False))

    if not any([sales.exists(), purchases.exists()]):
        context["export"] = False
        request.session["level"] = 50
        messages.add_message(request, 50, "Il n'y a rien a exporter")

        return render(request, "invoices/export_x3_invoices.html", context=context)

    if request.method == "POST":
        # On lance la génération des factures de vente et d'achat
        exports = _x3_exports()
        file_name_zip = f"AC00_{get_zip_num()!s}.zip"
        result_list = _launch_x3_exports(exports, request.user.pk)

        # On check s'il y a eu des erreurs
        if all(result_list):
            # Si on n'a pas d'erreur, on enregistre les fichiers dans la table
            _save_x3_exports(exports, file_name_zip)
            sales.update(export=True)
            purchases.update(export=True)
            level, message = 20, "Les fichiers d'export X3 ont bien été générés !"
        else:
            # En cas d'erreur, on supprime les fichiers générés
            _delete_x3_files(exports)
            level, message = 50, "Une erreur c'est produite veuillez consulter les traces !"

        request.session["level"] = level
        messages.add_message(request, level, message)
        LOGGER_X3.warning("%s, %s, %s", result_list, all(result_list), type(result_list))

    return render(request, "invoices/export_x3_invoices.html", context=context)


class ExportX3Files(ListView):
    """View pour download des fihiers X3 générés."""

    model = ExportX3
    context_object_name = "exports"
    template_name = "invoices/export_x3_list.html"
    extra_context = {"titre_table": "Fichiers X3"}

    def get_context_data(self, **kwargs):
        """On surcharge la méthode get_context_data, pour ajouter du contexte au template."""
        context = super().get_context_data(**kwargs)
        context["datatable_ordering"] = {"order": [(1, "desc")]}
        return context


def _check_inside(directory: Path, file_path: Path, message: str) -> None:
    """PermissionError si le chemin sort du répertoire autorisé (le nom vient de l'URL)."""
    if directory not in file_path.parents:
        raise PermissionError(message)


def get_export_x3_file(request, file_name):
    """Récupération des fichiers d'export X3 produits.

    :param request: Request Django
    :param file_name: Paramètres get du nom du fichier à télécharger
    :return: response_file.
    """
    try:
        if request.method == "GET":
            export_dir = Path(settings.EXPORT_DIR).resolve()
            file_path = (export_dir / file_name).resolve()

            _check_inside(
                export_dir, file_path, f"chemin hors du répertoire d'export : {file_name!r}"
            )

            content_type = CONTENT_TYPE_FILE.get(file_path.suffix, "text/plain")
            response = HttpResponse(file_path.open("rb").read(), content_type=content_type)
            response["Content-Disposition"] = f"attachment; filename={file_name}"
            return response

    except Exception:
        LOGGER_VIEWS.exception("view : get_export_x3_file")

    return redirect(reverse("home"))
