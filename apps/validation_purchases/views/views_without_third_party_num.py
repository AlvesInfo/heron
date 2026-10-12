"""
FR: Module qui change les integration venues sans tiers identifés
EN: Module that changes integrations without identified third parties

Commentaire:

created at: 2021-12-30
created by: Paulo ALVES

modified at: 2021-12-30
modified by: Paulo ALVES
"""

from django.contrib import messages
from django.http import JsonResponse

from apps.core.functions.functions_http import is_ajax
from heron.loggers import LOGGER_VIEWS

from django.db import transaction
from django.db.models import Q, Count
from django.shortcuts import render, redirect
from django.urls import reverse

from apps.parameters.bin.core import get_in_progress
from apps.core.bin.change_traces import trace_change
from apps.book.models import Society
from apps.parameters.models import Category
from apps.edi.models import EdiImport
from apps.validation_purchases.forms import UpdateThirdpartynumForm


def _edi_without_third_party_num():
    """Intégrations sans tiers X3 identifié, regroupées par import"""
    return (
        EdiImport.objects.filter(Q(third_party_num="") | Q(third_party_num__isnull=True))
        .values(
            "uuid_identification",
            "third_party_num",
            "flow_name",
            "supplier",
            "supplier_ident",
        )
        .annotate(dcount=Count("uuid_identification"))
    )


def purchase_without_suppliers(request):
    """Visualisation des intégrations sans Tiers Identifiés"""

    context = {
        "titre_table": "Factures Intégrées sans Tiers X3",
        "elements_list": _edi_without_third_party_num(),
        "form": UpdateThirdpartynumForm(),
        "margin_table": 50,
    }

    if get_in_progress():
        context["en_cours"] = True
        context["titre_table"] = "DES INTEGRATIONS SONT EN COURS, PATIENTEZ..."

    return render(
        request,
        "validation_purchases/integration_without_third_party_num.html",
        context=context,
    )


def _supplier_identifiers(society: Society, supplier_ident: str) -> str:
    """Identifiants fournisseur du tiers (séparés par |), complétés sans doublon par supplier_ident.
    """
    identifiers = [
        ident for ident in (society.centers_suppliers_indentifier or "").split("|") if ident
    ]

    if supplier_ident and supplier_ident not in identifiers:
        identifiers.append(supplier_ident)

    return "|".join(identifiers) + "|"


def _set_third_party_num(request, data_dict: dict, data: dict) -> None:
    """
    Rattache le tiers X3 à l'intégration : identifiant fournisseur ajouté au tiers, puis tiers,
    fournisseur et grande catégorie posés sur les lignes de l'import, dans une même transaction
    (si l'import ne peut pas être mis à jour, l'identifiant du tiers n'est pas modifié).
    'data` (réponse json) passe à "success" quand l'import est rattaché, puis à l'url de l'écran
    des intégrations s'il ne reste plus d'intégration sans tiers.
    :param request: Request Django
    :param data_dict: données validées du formulaire
    :param data: dictionnaire de la réponse json, modifié en place
    """
    third_party_num = data_dict.pop("third_party_num")
    society = Society.objects.get(third_party_num=third_party_num)
    center_identifier = _supplier_identifiers(society, data_dict.get("supplier_ident") or "")
    message = ""
    data_dict.pop("supplier")
    update_kwargs = {
        "third_party_num": third_party_num,
        "supplier": society.name,
    }
    big_category_object = (
        society.big_category_default or Category.objects.filter(slug_name="marchandises").first()
    )

    if big_category_object:
        update_kwargs["big_category_id"] = big_category_object.uuid_identification

    with transaction.atomic():
        if center_identifier != (society.centers_suppliers_indentifier or ""):
            _, message = trace_change(
                request,
                model=Society,
                before_kwargs={"third_party_num": society.third_party_num},
                update_kwargs={"centers_suppliers_indentifier": center_identifier},
            )

        changed, message_edi = trace_change(
            request,
            model=EdiImport,
            before_kwargs=data_dict,
            update_kwargs=update_kwargs,
        )

    if not changed:
        messages.add_message(request, 50, message + message_edi)
    else:
        data["success"] = "success"
        message = (
            f"L'intégration pour le flow name : {data_dict.get('flow_name')}, "
            f"a bien comme nouveau tiers : {third_party_num}"
        )
        messages.add_message(request, 20, message)

    if not _edi_without_third_party_num():
        data["success"] = reverse("validation_purchases:integration_purchases")


def _form_errors_text(form) -> str:
    """Texte des erreurs du formulaire, champ par champ"""
    errors_list = []

    for key, errors in form.errors.items():
        error = errors.as_text().replace("* ", "").replace("\n", ", ")
        errors_list.append(f"Erreur{'s' if len(errors) > 1 else ''} sur le champ {key} : {error}")

    return ", ".join(errors_list)


def purchase_without_suppliers_update(request):
    """Fonction d'insertion d'un tiers dans une intégration sans tiers X3"""

    if not is_ajax(request) or request.method != "POST":
        return redirect("home")

    data = {"success": "ko"}
    form = UpdateThirdpartynumForm(request.POST)
    request.session["level"] = 50

    if form.is_valid() and form.cleaned_data:
        try:
            _set_third_party_num(request, form.cleaned_data, data)

        except Exception as error:
            messages.add_message(
                request, 50, "Une erreur c'est produite veuillez consulter les logs"
            )
            LOGGER_VIEWS.exception(
                f"view : purchase_without_suppliers_update \n {error!r}"
            )
    else:
        messages.add_message(
            request, 50, f"Une erreur c'est produite : {_form_errors_text(form)}"
        )
        LOGGER_VIEWS.error(f"purchase_without_suppliers_update, form invalid : {form.errors!r}")

    return JsonResponse(data)
