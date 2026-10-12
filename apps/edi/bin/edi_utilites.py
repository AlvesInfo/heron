"""FR : Module des outils de gestion de l'application edi.

EN : Edi application management tools module.

Commentaire:

created at: 2023-01-18
created by: Paulo ALVES

modified at: 2023-01-18
modified by: Paulo ALVES
"""

from collections.abc import Iterable

import pendulum
from django.db import connection
from django.db.models import Case, Q, Value, When
from django.db.models.functions import Concat
from django.utils import timezone

from apps.articles.models import Article
from apps.core.bin.change_traces import caller_frame
from apps.core.bin.typing_helpers import required
from apps.core.models import ChangesTrace
from apps.data_flux.models import Trace
from apps.edi.models import EdiImport
from apps.parameters.models import Nature
from apps.users.models import User


def form_errors_message(form) -> str:
    """Message à afficher pour un formulaire invalide : "champ : erreur, erreur - champ : erreur".

    :param form: formulaire django invalide.
    """
    return " - ".join(
        f"{key} : {', '.join(list(error_list))}" for key, error_list in dict(form.errors).items()
    )


def get_sens(sens: str):
    """Retourne le sens de facturation AC, AC/VE, VE."""
    if sens == "2":
        return {"purchase_invoice": "true", "sale_invoice": "true"}

    if sens == "1":
        return {"purchase_invoice": "false", "sale_invoice": "true"}

    return {"purchase_invoice": "true", "sale_invoice": "false"}


def set_trace_hand_invoice(
    invoice_category: str,
    invoice_number: str,
    user: User,
    edi_objects: Iterable[EdiImport] | None = None,
    numbers: int = 0,
    *,
    errors: bool = False,
):
    """Création des traces et log.

    :param invoice_category: catégorie ( marchandises, formations, personnel)
    :param invoice_number: N° de Facture
    :param user: User faisant la création
    :param edi_objects: Lignes de factures Créées
    :param numbers: Nombre de factures saisies
    :param errors: s'il a eu des erreurs
    :return:
    """
    function_call = caller_frame()
    Trace.objects.create(
        trace_name=f"Saisie Facture de {invoice_category.capitalize()}",
        file_name=f"Ecran de saisie : edi/create_hand_invoices/{invoice_category}/",
        application_name="set_hand_invoice",
        flow_name="Saisie",
        errors=errors,
        comment=f"Saisie de la facture N° {invoice_number}",
        created_numbers_records=numbers,
        updated_numbers_records=0,
        errors_numbers_records=0,
        unknown_numbers_records=0,
        created_by=user,
        invoices=True,
    )

    # S'il n'y a pas d'erreurs alors on crée la change_trace
    if not errors:
        for edi_line in edi_objects or []:
            after_dict = {
                key: value for key, value in edi_line.__dict__.items() if key != "_state" and value
            }
            ChangesTrace.objects.create(
                action_datetime=timezone.now(),
                action_type=1,
                function_name=function_call,
                action_by=user,
                before={},
                after=after_dict,
                difference={"avant": {}, "après": after_dict},
                model_name=EdiImport._meta.model_name,
                model=str(EdiImport._meta.model),
                db_table=EdiImport._meta.db_table,
            )


def data_dict_invoices_clean(invoice_category: str, data_dict: dict):
    """Nettoyage de la donnée pour se conformer aux données necessaires à chaque.

    type de saisies manuelles (marchandises, formations, personnel)
    :param invoice_category: Catégorie ( marchandises, formations, personnel)
    :param data_dict: dictionnaire des données arrivées par la request
    :return: In place data_dict nettoyé.
    """
    # On supprime toutes les lignes qui n'ont pas d'article et ont les classes pour mettre le cct
    # s'il n'a pas été mis sur toutes les lignes
    lignes_list = data_dict.get("lignes") or []
    lignes_list = [row_dict for row_dict in lignes_list if row_dict.get("reference_article")]
    data_dict["lignes"] = sorted(lignes_list, key=lambda line_sort_dict: line_sort_dict.get("num"))

    if invoice_category == "marchandises":
        ...

    if invoice_category == "formation":
        data_dict["entete"]["third_party_num"] = "ZFORM"
        data_dict["entete"]["sens"] = "1"

        for ligne_dict in data_dict["lignes"]:
            ligne_dict["qty"] = "1"
            ligne_dict["unit_weight"] = "9"

            ligne_dict["formation_month"] = (
                pendulum.parse(ligne_dict.get("initial_date")).start_of("month").date().isoformat()
            )

    if invoice_category == "personnel":
        data_dict["entete"]["sens"] = "1"

        for ligne_dict in data_dict["lignes"]:
            ligne_dict["unit_weight"] = "7"


def get_query_articles(invoice_category: str):
    """Filtre les articles à afficher dans le select du template.

    :param invoice_category: Catégorie ( marchandises, formations, personnel)
    :return: Query object django filtré.
    """
    if invoice_category == "marchandises":
        return ""

    queryset = Article.objects.annotate(
        model=Concat(
            "third_party_num",
            Value(" - "),
            "reference",
            Value(" - "),
            Case(
                When(
                    Q(libelle_heron__isnull=True) | Q(libelle_heron=""),
                    then="libelle",
                ),
                default="libelle_heron",
            ),
        ),
    ).values_list("pk", "model")

    return [{"pk": "", "model": "---"}] + [
        {"pk": key, "model": value}
        for key, value in queryset.filter(big_category__slug_name=invoice_category)
    ]


def delete_orphans_controls():
    """Supprime tous les Contrôles edi_ediimport_control orphelins.

    Ceux qui ne sont pas dans edi_ediimport et ceux qui ne sont pas dans invoives_invoice
    :return:
    """
    with connection.cursor() as cursor:
        sql_delete = """
        delete from "edi_ediimportcontrol" "edic"
        where not exists (
            select 1 from (
                select
                    "uuid_control"
                from "edi_ediimport" "ee"
                group by "uuid_control"
                union all
                select
                    "uuid_control"
                from "invoices_invoicecommondetails" "ii"
                group by "uuid_control"
            ) "alls"
            where "alls"."uuid_control" = "edic"."uuid_identification"
        )
        """
        cursor.execute(sql_delete)


def set_signboard(edi_objects: Iterable[EdiImport]) -> None:
    """On va setter les centrales filles et les enseignes des factures saisies manuellement.

    :param edi_objects: Queryset Objets EdiImport créé
    :return:
    """
    for edi_line in edi_objects:
        edi_line.code_center = required(
            edi_line.cct_uuid_identification, "maison"
        ).center_purchase.code
        edi_line.code_signboard = required(
            edi_line.cct_uuid_identification, "maison"
        ).sign_board.code
        edi_line.save()


def get_personal_profession_type():
    """Retourne les types de personnel.

    :return: Query object django filtré.
    """
    return [{"uuid_identification": "", "to_display": "---"}] + [
        {"uuid_identification": ident, "to_display": display}
        for ident, display in Nature.objects.filter(for_personnel=True).values_list(
            "uuid_identification", "to_display"
        )
    ]
