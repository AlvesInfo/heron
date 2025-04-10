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

from psycopg2 import sql
from django.utils import timezone

from apps.core.functions.functions_setups import connection
from apps.core.functions.functions_postgresql import query_execute
from apps.data_flux.trace import get_trace
from heron.loggers import LOGGER_EDI
from apps.users.models import User
from apps.compta.bin.generate_ca import set_ca
from apps.invoices.sql_files.sql_subscriptions import SQL_SUBSCRIPTIONS


def set_invoice_amounts(flow_name: str):
    """Set des totaux par flow names, car il peut y avoir plusieurs fois le même type d'abonnement
    par flow name
    :param flow_name: non de l'abonnemment
    :return:
    """
    with connection.cursor() as cursor:
        # ID Minimum pour le premier import
        sql_update = sql.SQL(
            """
            update "edi_ediimport" "ee"
            set "invoice_amount_without_tax" = "req"."invoice_amount_without_tax",
                "invoice_amount_tax" = "req"."invoice_amount_tax",
                "invoice_amount_with_tax" = "req"."invoice_amount_with_tax"
            from (
                select
                    "third_party_num",
                    "flow_name",
                    "supplier",
                    "invoice_number",
                    sum(net_amount) as invoice_amount_without_tax, 
                    sum(vat_amount) as invoice_amount_tax, 
                    sum(amount_with_vat) as invoice_amount_with_tax
                from "edi_ediimport"
                where "flow_name" = %(flow_name)s
                group by 
                        "third_party_num", 
                        "flow_name",
                        "supplier",
                        "invoice_number"
            ) "req"
            where "req"."third_party_num" = "ee"."third_party_num"
            and "req"."flow_name" = "ee"."flow_name"
            and "req"."supplier" = "ee"."supplier"
            and "req"."invoice_number" = "ee"."invoice_number"
            """
        )
        cursor.execute(sql_update, {"flow_name": flow_name})


def set_data(dte_d: AnyStr, dte_f: AnyStr, user_uuid: UUID, flow_name: Dict):
    """Insert en base les abonnements
    :param dte_d: Date de début de période au format texte isoformat
    :param dte_f: Date de fin de période au format texte isoformat
    :param user_uuid: UUID de l'utilisateur lançant la génération
    :param flow_name: non de l'abonnemment
    :return:
    """
    set_ca(dte_d, dte_f, user_uuid)
    rows = query_execute(
        connection,
        SQL_SUBSCRIPTIONS,
        {
            "dte_d": dte_d,
            "dte_f": dte_f,
            "flow_name": flow_name,
            "uuid_identification": uuid4(),
            "created_by": user_uuid,
        },
    )

    return rows


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
    error = False
    rows = 0

    try:
        rows = set_data(dte_d, dte_f, user_uuid, flow_name)
        set_invoice_amounts(flow_name)

    except Exception as except_error:
        error = True
        LOGGER_EDI.exception(f"Exception Générale : {except_error!r}")

    if error:
        trace.errors = True
        trace.comment = (
            trace.comment + ". Une erreur c'est produite veuillez consulter les logs"
            if rows
            else ""
        )

    to_print = (
        "Génération des redevances meuleuses "
        if rows
        else (
            f"Erreur Génération des redevances meuleuses, pas d'abonnements '{flow_name}' à générer"
        )
    )
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
    error = False
    rows = 0

    try:
        rows = set_data(dte_d, dte_f, user_uuid, flow_name)
        set_invoice_amounts(flow_name)

    except Exception as except_error:
        error = True
        LOGGER_EDI.exception(f"Exception Générale : {except_error!r}")

    if error:
        trace.errors = True
        trace.comment = (
            trace.comment + ". Une erreur c'est produite veuillez consulter les logs"
            if rows
            else ""
        )

    to_print = (
        "Génération des prestations "
        if rows
        else f"Erreur Génération des prestations, pas d'abonnements '{flow_name}' à générer"
    )
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
    error = False
    rows = 0

    try:
        rows = set_data(dte_d, dte_f, user_uuid, flow_name)
        set_invoice_amounts(flow_name)

    except Exception as except_error:
        error = True
        LOGGER_EDI.exception(f"Exception Générale : {except_error!r}")

    if error:
        trace.errors = True
        trace.comment = (
            trace.comment + ". Une erreur c'est produite veuillez consulter les logs"
            if rows
            else ""
        )

    to_print = (
        "Génération des redevances de publicité "
        if rows
        else (
            f"Erreur Génération des redevances de publicité, "
            f"pas d'abonnements '{flow_name}' à générer"
        )
    )
    trace.time_to_process = (timezone.now() - trace.created_at).total_seconds()
    trace.created_by = User.objects.get(uuid_identification=user_uuid)
    trace.final_at = timezone.now()
    trace.save()

    return trace, to_print


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
    rows = 0

    try:
        rows = set_data(dte_d, dte_f, user_uuid, flow_name)
        set_invoice_amounts(flow_name)

    except Exception as except_error:
        error = True
        LOGGER_EDI.exception(f"Exception Générale : {except_error!r}")

    if error:
        trace.errors = True
        trace.comment = (
            trace.comment + ". Une erreur c'est produite veuillez consulter les logs"
            if rows
            else ""
        )

    to_print = (
        "Génération des royalties "
        if rows
        else f"Erreur Génération des royalties, pas d'abonnements '{flow_name}' à générer"
    )
    trace.time_to_process = (timezone.now() - trace.created_at).total_seconds()
    trace.final_at = timezone.now()
    trace.created_by = User.objects.get(uuid_identification=user_uuid)
    trace.save()

    return trace, to_print
