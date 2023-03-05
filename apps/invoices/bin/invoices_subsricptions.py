# pylint: disable=E0401,E1101,W0703,W1203
"""
Génération des factures d'abonnements: Royalties, Meuleuse, Publicité, Prestations
FR : Module de génération des factures de Royalties
EN : Royalties invoice generation module

Commentaire:

created at: 2023-03-03
created by: Paulo ALVES

modified at: 2023-03-03
modified by: Paulo ALVES
"""
from typing import AnyStr, Dict
from uuid import UUID, uuid4
from functools import lru_cache

from django.utils import timezone

from apps.core.functions.functions_setups import connection
from apps.core.functions.functions_postgresql import query_dict
from apps.accountancy.models import SectionSage
from apps.data_flux.trace import get_trace
from apps.edi.loggers import EDI_LOGGER
from apps.edi.models import EdiImport
from apps.parameters.models import UnitChoices, IconOriginChoice
from apps.users.models import User
from apps.compta.bin.generate_ca import set_ca
from apps.invoices.sql_files.sql_subscriptions import SQL_SUBSCRIPTIONS


@lru_cache(maxsize=256)
def get_unity(unity: int) -> UnitChoices:
    """Retourne l'instance de UnitChoices, en lui fournissant son N°
    :param unity: num de UnitChoices
    :return: UnitChoices.instance
    """
    return UnitChoices.objects.get(num=unity)


@lru_cache(maxsize=256)
def get_icon(origin: int) -> IconOriginChoice:
    """Retourne l'instance de IconOriginChoice, en lui fournissant son N°
    :param origin: origin de IconOriginChoice
    :return: IconOriginChoice.instance
    """
    return IconOriginChoice.objects.get(origin=origin)


@lru_cache(maxsize=512)
def get_axes(uuid_axe: UUID) -> SectionSage:
    """Retourne l'instance de UnitChoices, en lui fournissant son N°
    :param uuid_axe: uuid_identification de l'instance l'axe à retourner
    :return: SectionSage.instance
    """
    return SectionSage.objects.get(uuid_identification=uuid_axe)


def set_data(dte_d: AnyStr, dte_f: AnyStr, user_uuid: UUID, flow_name: Dict):
    """Insert en base les abonnements
    :param dte_d: Date de début de période au format texte isoformat
    :param dte_f: Date de fin de période au format texte isoformat
    :param user_uuid: UUID de l'utilisateur lançant la génération
    :param flow_name: non de l'abonnemment
    :return:
    """
    set_ca(dte_d, dte_f, user_uuid)
    subscriptions_list = query_dict(
        connection,
        SQL_SUBSCRIPTIONS,
        {
            "dte_d": dte_d,
            "dte_f": dte_f,
            "flow_name": flow_name,
        },
    )
    uuid_identification = uuid4()
    user = User.objects.get(uuid_identification=user_uuid)
    EdiImport.objects.bulk_create(
        [
            EdiImport(
                **{
                    **line_dict,
                    **{
                        "uuid_identification": uuid_identification,
                        "invoice_number": "inv",
                        "created_by": user,
                        "axe_bu": get_axes(line_dict.get("axe_bu")),
                        "axe_prj": get_axes(line_dict.get("axe_prj")),
                        "axe_pro": get_axes(line_dict.get("axe_pro")),
                        "axe_pys": get_axes(line_dict.get("axe_pys")),
                        "axe_rfa": get_axes(line_dict.get("axe_rfa")),
                        "origin": get_icon(line_dict.get("origin")),
                        "unity": get_unity(line_dict.get("unity")),
                    },
                }
            )
            for line_dict in subscriptions_list
        ]
    )


def royalties(dte_d: AnyStr, dte_f: AnyStr, user_uuid: UUID):
    """Génération de factures de Royalties
    :param dte_d: Date de début de période au format texte isoformat
    :param dte_f: Date de fin de période au format texte isoformat
    :param user_uuid: UUID de l'utilisateur lançant la génération
    :return:
    """
    file_name = "royalties"
    trace_name = "Génération des royalties"
    application_name = "royalties"
    flow_name = "ROYALTIES"
    comment = ""
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)
    error = False

    try:
        set_data(dte_d, dte_f, user_uuid, flow_name)

    except Exception as except_error:
        error = True
        EDI_LOGGER.exception(f"Exception Générale : {except_error!r}")

    if error:
        trace.errors = True
        trace.comment = trace.comment + "\n. Une erreur c'est produite veuillez consulter les logs"

    to_print = "Génération des royalties"

    trace.time_to_process = (timezone.now() - trace.created_at).total_seconds()
    trace.final_at = timezone.now()
    trace.created_by = User.objects.get(uuid_identification=user_uuid)
    trace.save()

    return trace, to_print


def meuleuse(dte_d: AnyStr, dte_f: AnyStr, user_uuid: UUID):
    """Génération de factures de redevance Meuleuse
    :param dte_d: Date de début de période au format texte isoformat
    :param dte_f: Date de fin de période au format texte isoformat
    :param user_uuid: UUID de l'utilisateur lançant la génération
    :return:
    """
    file_name = "redevance_meuleuses"
    trace_name = "Génération des redevances meuleuses"
    application_name = "redevance_meuleuses"
    flow_name = "MEULEUSE"
    comment = ""
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)

    to_print = "Génération des redevances meuleuses"

    trace.time_to_process = (timezone.now() - trace.created_at).total_seconds()
    trace.created_by = User.objects.get(uuid_identification=user_uuid)
    trace.final_at = timezone.now()
    trace.save()

    return trace, to_print


def publicity(dte_d: AnyStr, dte_f: AnyStr, user_uuid: UUID):
    """Génération de factures de redevance de Pubilicité
    :param dte_d: Date de début de période au format texte isoformat
    :param dte_f: Date de fin de période au format texte isoformat
    :param user_uuid: UUID de l'utilisateur lançant la génération
    :return:
    """
    file_name = "redevance_publicite"
    trace_name = "Génération des redevances de publicité"
    application_name = "redevance_publicite"
    flow_name = "PUBLICITE"
    comment = ""
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)

    to_print = "Génération des redevances de publicité"

    trace.time_to_process = (timezone.now() - trace.created_at).total_seconds()
    trace.created_by = User.objects.get(uuid_identification=user_uuid)
    trace.final_at = timezone.now()
    trace.save()

    return trace, to_print


def services(dte_d: AnyStr, dte_f: AnyStr, user_uuid: UUID):
    """Génération de factures de Prestations
    :param dte_d: Date de début de période au format texte isoformat
    :param dte_f: Date de fin de période au format texte isoformat
    :param user_uuid: UUID de l'utilisateur lançant la génération
    :return:
    """
    file_name = "prestations"
    trace_name = "Génération des prestations"
    application_name = "prestations"
    flow_name = "PRESTATIONS"
    comment = ""
    trace = get_trace(trace_name, file_name, application_name, flow_name, comment)

    to_print = "Génération des prestations"

    trace.time_to_process = (timezone.now() - trace.created_at).total_seconds()
    trace.created_by = User.objects.get(uuid_identification=user_uuid)
    trace.final_at = timezone.now()
    trace.save()

    return trace, to_print
